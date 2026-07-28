import sqlite3
import io
from datetime import datetime, timedelta
import random
from nicegui import ui, app
import polars as pl
import insert
import report
import lower

# Set the primary color theme for NiceGUI elements (Forest Dark Green)
ui.colors(primary='#1b4d3e', secondary='#ffffff', accent='#f59e0b')

student_records = []
all_records = []
student_table = None
activity_table = None
all_logs = []
DB = 'School_Results_Database.db'

# Initialize database tables and safely add columns (like Year, Aggregates, Division, Term) if they do not exist
def init_db_and_load_records():
    global student_records
    current_year_str = str(datetime.now().year)
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        
        # Create academic records table if it doesn't already exist
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS academic_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                Name TEXT, 
                PaymentCode TEXT, 
                Class TEXT, 
                Year TEXT DEFAULT '{current_year_str}', 
                Term TEXT,
                ExamType TEXT, 
                ExamDate TEXT, 
                Attendance TEXT, 
                Remarks TEXT, 
                Maths INTEGER, 
                Maths_Grade TEXT, 
                English INTEGER, 
                English_Grade TEXT, 
                SST INTEGER, 
                SST_Grade TEXT, 
                Science INTEGER, 
                Science_Grade TEXT, 
                Total INTEGER, 
                Average REAL, 
                Grade TEXT, 
                Aggregates INTEGER,
                Division TEXT,
                Rank TEXT
            )
        ''')

        # Safely add columns to pre-existing tables if missing
        for col_def in [
            (f"Year TEXT DEFAULT '{current_year_str}'"),
            ("Aggregates INTEGER"),
            ("Division TEXT"),
            ("PaymentCode TEXT"),
            ("Term TEXT")
        ]:
            try:
                cursor.execute(f"ALTER TABLE academic_records ADD COLUMN {col_def}")
            except sqlite3.OperationalError:
                pass

        # Backfill any blank or null year values with the current year
        cursor.execute(f"UPDATE academic_records SET Year = '{current_year_str}' WHERE Year IS NULL OR Year = ''")

        # Create activity logs tracking table
        cursor.execute('CREATE TABLE IF NOT EXISTS activity_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, timestamp TEXT, status TEXT)')
        
        # Ensure lower primary table has year and term columns
        try:
            cursor.execute(f"ALTER TABLE lower_primary_results ADD COLUMN year TEXT DEFAULT '{current_year_str}'")
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute("ALTER TABLE lower_primary_results ADD COLUMN term TEXT")
        except sqlite3.OperationalError:
            pass
            
        cursor.execute(f"UPDATE lower_primary_results SET year = '{current_year_str}' WHERE year IS NULL OR year = ''")

        conn.commit()

# Run database setup FIRST before any migration updates
init_db_and_load_records()

# --- AUTOMATIC INACTIVITY LOGOUT CHECKER & COUNTDOWN BANNER ---
INACTIVITY_LIMIT_MINUTES = 30

def check_inactivity():
    if not app.storage.user.get('logged_in'):
        return
    
    last_active = app.storage.user.get('last_active')
    if last_active:
        last_active_time = datetime.fromisoformat(last_active)
        elapsed = datetime.now() - last_active_time
        remaining_seconds = int((timedelta(minutes=INACTIVITY_LIMIT_MINUTES) - elapsed).total_seconds())
        
        # Update the live countdown badge if present on the page
        if 'countdown_label' in globals() and countdown_label:
            if remaining_seconds > 0:
                mins, secs = divmod(remaining_seconds, 60)
                countdown_label.text = f"Auto-logout in: {mins:02d}:{secs:02d}"
                if remaining_seconds <= 300: # Turn warning orange/red in the last 5 minutes
                    countdown_label.classes('text-amber-600 font-bold animate-pulse', remove='text-slate-600')
            else:
                countdown_label.text = "Session expired. Logging out..."

        if elapsed > timedelta(minutes=INACTIVITY_LIMIT_MINUTES):
            username = app.storage.user.get('username', 'User')
            log_activity(username, "Auto-logged out due to 30 minutes of inactivity")
            app.storage.user.clear()
            ui.notify("You have been logged out due to 30 minutes of inactivity.", type='warning')
            ui.run_javascript('window.location.replace("/login")')

# Global background timer to check for user inactivity and update countdown every 1 second for smooth reflection
ui.timer(1.0, check_inactivity)

# Function to update user last active timestamp on interaction
def update_activity_timestamp():
    if app.storage.user.get('logged_in'):
        app.storage.user['last_active'] = datetime.now().isoformat()

# Function to generate and trigger bulk printing for all currently loaded academic reports
def download_all_reports():
    if not all_records:
        ui.notify("No records to export", type='warning')
        return

    import report

    # Combine all individual report HTML strings with page breaks between them
    all_html = ""
    for record in all_records:
        single_report = report.report(record)
        all_html += f"<div style='page-break-after: always;'>{single_report}</div>"

    # Open a temporary browser window containing the combined reports and trigger the print dialog
    ui.run_javascript(f'''
        const win = window.open('', '_blank');
        win.document.write(`{all_html}`);
        win.document.close();
        win.print();
    ''')
    ui.notify("Bulk report generation triggered", type='positive')

# Function to log system actions
def log_activity(username, status):
    try:
        with sqlite3.connect(DB) as conn:
            cursor = conn.cursor()
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute("INSERT INTO activity_logs (username, timestamp, status) VALUES (?, ?, ?)", (username, timestamp, status))
            conn.commit()
        refresh_activity_table()
    except Exception as e:
        print(f"Failed to log activity: {e}")

# Function to calculate individual subject grades, aggregates, and divisions using Polars
def local_calculate_grades(raw_data):
    def get_grade_expr(col):
        return pl.when(pl.col(col) >= 80).then(pl.lit("1")) \
                 .when(pl.col(col) >= 70).then(pl.lit("2")) \
                 .when(pl.col(col) >= 60).then(pl.lit("3")) \
                 .when(pl.col(col) >= 50).then(pl.lit("4")) \
                 .when(pl.col(col) >= 45).then(pl.lit("5")) \
                 .when(pl.col(col) >= 40).then(pl.lit("6")) \
                 .when(pl.col(col) >= 30).then(pl.lit("8")) \
                 .otherwise(pl.lit("9"))
                 
    calc_df = pl.DataFrame([raw_data]).with_columns([
        get_grade_expr("Maths").alias("Maths_Grade"),
        get_grade_expr("English").alias("English_Grade"),
        get_grade_expr("SST").alias("SST_Grade"),
        get_grade_expr("Science").alias("Science_Grade"),
        (pl.col("Maths") + pl.col("English") + pl.col("SST") + pl.col("Science")).alias("Total"),
        ((pl.col("Maths") + pl.col("English") + pl.col("SST") + pl.col("Science")) / 4).alias("Average"),
    ])
    
    row = calc_df.to_dicts()[0]
    
    def safe_int_grade(val):
        try:
            return int(val)
        except (TypeError, ValueError):
            return 9

    agg_total = (
        safe_int_grade(row["English_Grade"]) +
        safe_int_grade(row["Maths_Grade"]) +
        safe_int_grade(row["Science_Grade"]) +
        safe_int_grade(row["SST_Grade"])
    )
    row["Aggregates"] = agg_total

    eng_grade = safe_int_grade(row["English_Grade"])
    math_grade = safe_int_grade(row["Maths_Grade"])

    if 4 <= agg_total <= 12:
        base_division = "Div 1"
    elif 13 <= agg_total <= 23:
        base_division = "Div 2"
    elif 24 <= agg_total <= 29:
        base_division = "Div 3"
    elif 30 <= agg_total <= 34:
        base_division = "Div 4"
    else:
        base_division = "Div U"

    if eng_grade == 9 or math_grade == 9:
        if base_division == "Div 1":
            row["Division"] = "Div 2"
        elif base_division == "Div 2":
            row["Division"] = "Div 3"
        elif base_division == "Div 3":
            row["Division"] = "Div 4"
        else:
            row["Division"] = "Div U"
    else:
        row["Division"] = base_division

    row["Grade"] = row["Division"]
    row["Rank"] = "N/A"
    return row

# Helper to query student enrollment counts per class from SQLite (including lower primary)
def get_class_enrollment_counts():
    counts = {}
    try:
        with sqlite3.connect(DB) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT Class, COUNT(*) as count FROM academic_records GROUP BY Class")
            for row in cursor.fetchall():
                if row[0]:
                    cls_key = str(row[0]).strip().upper()
                    counts[cls_key] = counts.get(cls_key, 0) + row[1]
    except Exception:
        pass
        
    try:
        with sqlite3.connect(DB) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT class_level, COUNT(*) as count FROM lower_primary_results GROUP BY class_level")
            for row in cursor.fetchall():
                if row[0]:
                    cls_key = str(row[0]).strip().upper()
                    if not cls_key.startswith('P'):
                        cls_key = f"P{cls_key}"
                    counts[cls_key] = counts.get(cls_key, 0) + row[1]
    except Exception:
        pass
        
    return counts

# Retrieve aggregate dashboard statistics from SQLite
def get_dashboard_stats():
    stats = {
        'total_students': 0, 
        'pass_rate': 0.0, 
        'subject_averages': {'Maths': 0, 'English': 0, 'SST': 0, 'Science': 0}, 
        'class_subject_averages': {}, 
        'class_enrollment': {},
        'top_students': [], 
        'user_logs': []
    }
    try:
        with sqlite3.connect(DB) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) as count FROM academic_records")
            upper_count = cursor.fetchone()['count']
            
            lower_count = 0
            try:
                cursor.execute("SELECT COUNT(*) as count FROM lower_primary_results")
                lower_count = cursor.fetchone()['count']
            except Exception:
                pass

            stats['total_students'] = upper_count + lower_count
            
            if upper_count > 0:
                cursor.execute("SELECT COUNT(*) as passing FROM academic_records WHERE Division != 'Div U'")
                stats['pass_rate'] = round((cursor.fetchone()['passing'] / upper_count), 2)
            
            cursor.execute("SELECT AVG(Maths) as m, AVG(English) as e, AVG(SST) as sst, AVG(Science) as sci FROM academic_records")
            row = cursor.fetchone()
            if row and row['m'] is not None:
                stats['subject_averages'] = {'Maths': round(row['m'], 1), 'English': round(row['e'], 1), 'SST': round(row['sst'], 1), 'Science': round(row['sci'], 1)}

            cursor.execute("SELECT Class, AVG(Maths) as m, AVG(English) as e, AVG(SST) as sst, AVG(Science) as sci FROM academic_records GROUP BY Class")
            for class_row in cursor.fetchall():
                if class_row['Class']:
                    stats['class_subject_averages'][class_row['Class']] = {
                        'Maths': round(class_row['m'] or 0, 1),
                        'English': round(class_row['e'] or 0, 1),
                        'SST': round(class_row['sst'] or 0, 1),
                        'Science': round(class_row['sci'] or 0, 1)
                    }

            stats['class_enrollment'] = get_class_enrollment_counts()

            cursor.execute("SELECT Name, Class, Total, Average, Grade, Aggregates, Division, Rank, Maths, English, SST, Science FROM academic_records ORDER BY Aggregates ASC LIMIT 3")
            stats['top_students'] = [dict(r) for r in cursor.fetchall()]

            cursor.execute('''
                SELECT username, timestamp, status,
                       (SELECT COUNT(*) FROM activity_logs al2 WHERE al2.username = activity_logs.username AND al2.id <= activity_logs.id AND al2.status='Active') as login_sequence
                FROM activity_logs
                ORDER BY id DESC
                LIMIT 5
            ''')
            stats['user_logs'] = [dict(r) for r in cursor.fetchall()]
    except Exception:
        pass
    return stats

# System Logs Tab Panel
def view_system_logs_content(logs_tab):
    with ui.tab_panel(logs_tab).classes('p-0 gap-4 flex flex-col'):
        with ui.card().classes('w-full p-6 bg-white shadow-xl rounded-3xl border border-slate-100 flex flex-col gap-4'):
            log_columns = [
                {'name': 'id', 'label': 'ID', 'field': 'id', 'align': 'center', 'sortable': True},
                {'name': 'username', 'label': 'User / Operator', 'field': 'username', 'align': 'left', 'sortable': True},
                {'name': 'timestamp', 'label': 'Timestamp', 'field': 'timestamp', 'align': 'center', 'sortable': True},
                {'name': 'status', 'label': 'Activity / Status', 'field': 'status', 'align': 'left'}
            ]

            global activity_table, all_log_records
            all_log_records = []
            activity_table = ui.table(columns=log_columns, rows=[], row_key='id').classes('w-full shadow-inner border border-slate-100 rounded-2xl')

            def refresh_activity_table():
                global activity_table, all_log_records
                if activity_table is None:
                    return
                try:
                    with sqlite3.connect(DB) as conn:
                        conn.row_factory = sqlite3.Row
                        raw_rows = [dict(r) for r in conn.execute('SELECT * FROM activity_logs ORDER BY id DESC').fetchall()]
                        all_log_records = raw_rows
                        activity_table.rows = all_log_records
                        activity_table.update()
                except Exception as e:
                    ui.notify(f"Error loading system logs: {e}", type='negative')

            def apply_log_filter(query):
                global activity_table, all_log_records
                if not query:
                    activity_table.rows = all_log_records
                else:
                    q = query.lower()
                    activity_table.rows = [
                        r for r in all_log_records 
                        if q in str(r.get('username', '')).lower() or q in str(r.get('status', '')).lower()
                    ]
                activity_table.update()

            def clear_old_logs():
                with ui.dialog() as confirm_dialog, ui.card().classes('w-[400px] p-6 gap-4 rounded-3xl shadow-2xl bg-white border border-slate-100'):
                    ui.label('Clear System Logs').classes('text-lg font-bold text-slate-800')
                    ui.label('Are you sure you want to delete all recorded system activity logs? This action cannot be undone.').classes('text-sm text-slate-600')

                    def confirm_delete():
                        try:
                            with sqlite3.connect(DB) as conn:
                                cursor = conn.cursor()
                                cursor.execute('DELETE FROM activity_logs')
                                conn.commit()
                            ui.notify('All system logs cleared successfully', type='positive')
                            log_activity(app.storage.user.get('username', 'Admin'), "Cleared all system activity logs")
                            confirm_dialog.close()
                            refresh_activity_table()
                        except Exception as e:
                            ui.notify(f"Failed to clear logs: {e}", type='negative')

                    with ui.row().classes('w-full justify-end gap-2 mt-2'):
                        ui.button('Cancel', on_click=confirm_dialog.close).props('flat rounded').classes('text-slate-600')
                        ui.button('Delete All Logs', on_click=confirm_delete).props('unelevated color="red" rounded').classes('px-5 text-white')
                
                confirm_dialog.open()

            with ui.row().classes('w-full justify-between items-center flex-wrap gap-2'):
                ui.label('System Activity Logs & User Management').classes('text-xl font-bold text-slate-800')

                with ui.row().classes('items-center gap-2 flex-wrap'):
                    search_input = ui.input(placeholder='Search username or activity...').props('dense outlined clearable rounded').classes('bg-slate-50')
                    ui.button(icon='search', on_click=lambda: apply_log_filter(search_input.value)).props('dense unelevated color="primary"').classes('rounded-xl')
                    ui.button('Clear Logs', icon='delete_sweep', on_click=clear_old_logs).props('outline dense color="red"').classes('rounded-xl')
                    ui.button('Refresh', icon='refresh', on_click=refresh_activity_table).props('outline dense text-color="primary"').classes('rounded-xl')

            with ui.row().classes('w-full gap-3 items-center bg-slate-50/70 backdrop-blur-sm p-4 rounded-2xl border border-slate-200'):
                ui.label('Quick User Actions:').classes('font-semibold text-sm text-slate-700')
                target_user_input = ui.input(placeholder='Enter username...').props('dense outlined bg-white rounded').classes('w-48')

                def force_logout_user():
                    username = target_user_input.value
                    if not username:
                        ui.notify("Please enter a username", type='warning')
                        return
                    try:
                        with sqlite3.connect(DB) as conn:
                            cursor = conn.cursor()
                            cursor.execute("UPDATE users SET is_active = 0 WHERE username = ?", (username,))
                            conn.commit()
                        ui.notify(f"User '{username}' has been forced to log out", type='positive')
                        log_activity(app.storage.user.get('username', 'Admin'), f"Force logged out user: {username}")
                        target_user_input.value = ''
                        refresh_activity_table()
                    except Exception:
                        log_activity(app.storage.user.get('username', 'Admin'), f"Force logged out user: {username}")
                        ui.notify(f"Force logout recorded for '{username}'", type='positive')
                        target_user_input.value = ''
                        refresh_activity_table()

                ui.button('Force Logout', icon='logout', on_click=force_logout_user).props('dense unelevated color="orange"').classes('rounded-xl text-white')

            refresh_activity_table()

# Query database records based on selected class, year, and term filters for Upper Primary
def refresh_table_data(class_filter='All', year_filter='', term_filter='All'):
    global student_table, all_records
    if student_table is None:
        return
    try:
        with sqlite3.connect(DB) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = "SELECT * FROM academic_records WHERE 1=1"
            params = []
            
            if class_filter != 'All':
                query += " AND Class = ?"
                params.append(class_filter)
            if year_filter and year_filter.strip():
                query += " AND Year LIKE ?"
                params.append(f"%{year_filter.strip()}%")
            if term_filter != 'All':
                query += " AND Term = ?"
                params.append(term_filter)
                
            cursor.execute(query, params)
            all_records = [dict(r) for r in cursor.fetchall()]
            student_table.rows = all_records
            student_table.update()
    except Exception as e:
        ui.notify(f"Error loading records: {e}", type='negative')

# Refresh activity logs table data
def refresh_activity_table():
    global activity_table, all_logs
    if activity_table is None:
        return
    try:
        with sqlite3.connect(DB) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT id, username, timestamp, status FROM activity_logs ORDER BY id DESC")
            all_logs = [dict(r) for r in cursor.fetchall()]
            activity_table.rows = all_logs
            activity_table.update()
    except Exception as e:
        ui.notify(f"Error loading activity logs: {e}", type='negative')

# Delete a specific student record by its unique database ID
def delete_record(record_id):
    try:
        with sqlite3.connect(DB) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM academic_records WHERE id = ?", (record_id,))
            conn.commit()
        ui.notify("Record removed successfully", type='positive')
        update_all_ranks()
        refresh_table_data()
        log_activity(app.storage.user.get('username', 'Admin'), f"Deleted student record ID {record_id}")
    except Exception as e:
        ui.notify(f"Delete failed: {e}", type='negative')

# Open an interactive dialog window to edit an existing student record's details
def open_edit_dialog(record):
    with ui.dialog() as edit_dialog, ui.card().classes('w-[450px] p-8 gap-4 rounded-3xl shadow-2xl bg-white border border-slate-100'):
        ui.label(f"Edit Record: {record['Name']}").classes('text-xl font-bold text-slate-800')

        edit_name = ui.input('Name', value=record['Name']).classes('w-full').props('outlined rounded')
        edit_payment_code = ui.input('Payment Code', value=record.get('PaymentCode', '')).classes('w-full').props('outlined rounded')
        edit_class = ui.input('Class', value=record['Class']).classes('w-full').props('outlined rounded')
        edit_year = ui.input('Year', value=record.get('Year', str(datetime.now().year))).classes('w-full').props('outlined rounded')
        edit_term = ui.input('Term', value=record.get('Term', '')).classes('w-full').props('outlined rounded')
        edit_maths = ui.number('Maths', value=record['Maths']).classes('w-full').props('outlined rounded')
        edit_english = ui.number('English', value=record['English']).classes('w-full').props('outlined rounded')
        edit_sst = ui.number('SST', value=record['SST']).classes('w-full').props('outlined rounded')
        edit_science = ui.number('Science', value=record['Science']).classes('w-full').props('outlined rounded')

        def save_changes():
            if not edit_name.value or not edit_class.value:
                ui.notify("Name and Class cannot be empty!", type='warning')
                return

            raw_scores = {
                "Maths": int(edit_maths.value or 0),
                "English": int(edit_english.value or 0),
                "SST": int(edit_sst.value or 0),
                "Science": int(edit_science.value or 0)
            }
            updated_metrics = local_calculate_grades(raw_scores)

            try:
                with sqlite3.connect(DB) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE academic_records SET
                            Name=?, PaymentCode=?, Class=?, Year=?, Term=?, Maths=?, Maths_Grade=?,
                            English=?, English_Grade=?, SST=?, SST_Grade=?,
                            Science=?, Science_Grade=?, Total=?, Average=?, Grade=?, Aggregates=?, Division=?
                        WHERE id=?
                    ''', (
                        edit_name.value, edit_payment_code.value, edit_class.value, edit_year.value, edit_term.value,
                        raw_scores['Maths'], updated_metrics['Maths_Grade'],
                        raw_scores['English'], updated_metrics['English_Grade'],
                        raw_scores['SST'], updated_metrics['SST_Grade'],
                        raw_scores['Science'], updated_metrics['Science_Grade'],
                        updated_metrics['Total'], updated_metrics['Average'], updated_metrics['Grade'],
                        updated_metrics['Aggregates'], updated_metrics['Division'],
                        record['id']
                    ))
                    conn.commit()

                # Ensure class-wide ranks and divisions sync properly across the table view
                update_all_ranks()

                ui.notify("Record updated and divisions recalculated successfully!", type='positive')
                edit_dialog.close()
                refresh_table_data(class_filter='All', year_filter='')
                log_activity(app.storage.user.get('username', 'Admin'), f"Edited record for {edit_name.value}")
            except Exception as e:
                ui.notify(f"Update failed: {e}", type='negative')

        with ui.row().classes('w-full justify-end gap-2 mt-4'):
            ui.button('Cancel', on_click=edit_dialog.close).props('flat rounded').classes('text-slate-600')
            ui.button('Save Changes', on_click=save_changes).props('unelevated color="primary" rounded').classes('px-6 shadow-md')

    edit_dialog.open()

# --- INITIALIZE CHAT DATABASE TABLE ---
def init_chat_db():
    with sqlite3.connect(DB) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS staff_chat (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender TEXT,
                message TEXT,
                timestamp TEXT
            )
        ''')

init_chat_db()

# --- STAFF CHAT ROOM CONTENT ---
def staff_chat_content():
    chat_container = ui.column().classes(
        'w-full h-[450px] overflow-y-auto p-5 bg-[#f0f4f8] rounded-2xl gap-3 shadow-inner'
    )

    room_vibes = [
        "☕ Staff Lounge • Ready for updates",
        "📢 Staff Hub • Share announcements and ideas",
        "✨ Staff Connect • Working together",
        "📝 Staff Room • Lesson plans & discussions"
    ]

    current_vibe = random.choice(room_vibes)

    def delete_message(msg_id):
        try:
            with sqlite3.connect(DB) as conn:
                conn.execute(
                    'DELETE FROM staff_chat WHERE id = ?',
                    (msg_id,)
                )
            ui.notify('Message deleted', type='warning')
            load_messages()
        except Exception as e:
            ui.notify(f'Delete failed: {e}', type='negative')

    def load_messages():
        chat_container.clear()

        with chat_container:
            try:
                with sqlite3.connect(DB) as conn:
                    conn.row_factory = sqlite3.Row
                    messages = conn.execute(
                        'SELECT * FROM staff_chat ORDER BY id ASC'
                    ).fetchall()

                if not messages:
                    with ui.column().classes(
                        'w-full items-center justify-center h-full gap-2'
                    ):
                        ui.icon('chat_bubble_outline', size='48px', color='#1b4d3e').classes('opacity-40')
                        ui.label('No messages yet').classes('text-slate-500 font-semibold')
                        ui.label('Start the staff conversation').classes('text-xs text-slate-400')
                else:
                    current_user = app.storage.user.get('username', 'Teacher')

                    for msg in messages:
                        sender = msg['sender']
                        mine = sender == current_user
                        align = 'items-end' if mine else 'items-start'

                        with ui.column().classes(f'w-full {align} gap-1'):
                            if not mine:
                                ui.label(sender).classes('text-xs font-bold text-[#1b4d3e] ml-2')

                            bubble = (
                                'bg-[#1b4d3e] text-white rounded-br-sm shadow-md'
                                if mine
                                else
                                'bg-white text-slate-700 border border-slate-200 rounded-bl-sm shadow-sm'
                            )

                            with ui.card().classes(f'{bubble} max-w-[75%] px-4 py-3 rounded-2xl'):
                                ui.label(msg['message']).classes('text-sm leading-relaxed whitespace-pre-wrap')

                                with ui.row().classes('justify-end items-center gap-1 mt-1'):
                                    ui.label(msg['timestamp']).classes('text-[10px] opacity-70')

                                    if mine:
                                        ui.icon('done_all', size='13px').classes('text-emerald-200')
                                        ui.button(
                                            icon='delete_outline',
                                            on_click=lambda mid=msg['id']: delete_message(mid)
                                        ).props('flat dense round').classes('text-white/70 hover:bg-white/10')
            except Exception as e:
                ui.label(f'Chat error: {e}').classes('text-red-500')

    with ui.column().classes(
        'w-full max-w-4xl mx-auto bg-white rounded-3xl shadow-xl border border-slate-100 overflow-hidden'
    ):
        with ui.row().classes(
            'w-full items-center justify-between bg-white px-6 py-4 border-b border-slate-100'
        ):
            with ui.row().classes('items-center gap-3'):
                with ui.avatar().classes('bg-[#1b4d3e] text-white shadow-md'):
                    ui.icon('school')

                with ui.column().classes('gap-0'):
                    ui.label('Staff Chat Hub').classes('font-bold text-slate-800 text-lg')
                    ui.label(current_vibe).classes('text-xs font-medium text-emerald-700')

            with ui.row().classes('items-center gap-2'):
                ui.badge('Online').classes('bg-emerald-50 text-emerald-700 text-xs font-semibold border border-emerald-200 px-3 py-1 rounded-full')
                ui.button(icon='refresh', on_click=load_messages).props('flat round').classes('text-[#1b4d3e] hover:bg-emerald-50')
                ui.timer(3, load_messages)

        load_messages()

        emojis = ["👍", "😂", "🔥", "❤️", "👏", "☕", "📚", "📝", "⚡", "🎉"]

        with ui.row().classes(
            'w-full px-5 py-2 bg-slate-50 border-t border-slate-100 gap-1 overflow-x-auto'
        ):
            for emoji in emojis:
                def add_emoji(e=emoji):
                    msg_input.value = (msg_input.value or '') + e
                    msg_input.update()

                ui.button(emoji, on_click=add_emoji).props('flat dense').classes('rounded-full hover:bg-emerald-100/50 text-base')

        with ui.row().classes('w-full items-center gap-3 p-4 bg-white border-t border-slate-100'):
            msg_input = ui.input(placeholder='Write a message...').props('borderless dense').classes('flex-1 bg-slate-100 rounded-full px-6 py-1 text-slate-700')

            def send_message():
                text = (msg_input.value or '').strip()
                if not text:
                    return

                sender = app.storage.user.get('username', 'Teacher')
                timestamp = datetime.now().strftime('%H:%M')

                try:
                    with sqlite3.connect(DB) as conn:
                        conn.execute(
                            'INSERT INTO staff_chat (sender, message, timestamp) VALUES (?, ?, ?)',
                            (sender, text, timestamp)
                        )
                    msg_input.value = ''
                    load_messages()
                except Exception as e:
                    ui.notify(f'Failed sending message: {e}', type='negative')

            msg_input.on('keydown.enter', send_message)
            ui.button(icon='send', on_click=send_message).props('round unelevated').classes('bg-[#1b4d3e] text-white w-11 h-11 shadow-md hover:opacity-90')

def edit_lower_record(record, on_save):
    with ui.dialog() as edit_dialog, ui.card().classes('w-[480px] p-8 gap-4 rounded-3xl shadow-2xl bg-white border border-slate-100'):
        ui.label(f"Edit Lower Primary Record: {record.get('name', '')}").classes('text-xl font-bold text-slate-800')

        edit_name = ui.input('Pupil Name', value=record.get('name', '')).classes('w-full').props('outlined rounded')
        edit_payment_code = ui.input('Payment Code', value=record.get('payment_code', '')).classes('w-full').props('outlined rounded')
        edit_class = ui.input('Class', value=str(record.get('class_level', ''))).classes('w-full').props('outlined rounded')
        edit_year = ui.input('Year', value=str(record.get('year', datetime.now().year))).classes('w-full').props('outlined rounded')
        edit_term = ui.input('Term', value=str(record.get('term', ''))).classes('w-full').props('outlined rounded')
        
        edit_lit_i = ui.number('Lit I', value=record.get('literacy_i', 0)).classes('w-full').props('outlined rounded')
        edit_lit_ii = ui.number('Lit II', value=record.get('literacy_ii', 0)).classes('w-full').props('outlined rounded')
        edit_reading = ui.number('Reading', value=record.get('reading', 0)).classes('w-full').props('outlined rounded')
        edit_luganda = ui.number('Luganda', value=record.get('luganda', 0)).classes('w-full').props('outlined rounded')
        edit_maths = ui.number('Maths', value=record.get('mathematics', 0)).classes('w-full').props('outlined rounded')
        edit_english = ui.number('English', value=record.get('english', 0)).classes('w-full').props('outlined rounded')
        edit_sst = ui.number('S.S.T', value=record.get('social_studies', 0)).classes('w-full').props('outlined rounded')
        edit_science = ui.number('Science', value=record.get('science', 0)).classes('w-full').props('outlined rounded')
        edit_re = ui.number('R.E', value=record.get('re_religious_education', 0)).classes('w-full').props('outlined rounded')

        def save_lower_changes():
            try:
                with sqlite3.connect(DB) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE lower_primary_results SET
                            name=?, payment_code=?, class_level=?, year=?, term=?, literacy_i=?, literacy_ii=?,
                            reading=?, luganda=?, mathematics=?, english=?, social_studies=?,
                            science=?, re_religious_education=?
                        WHERE id=?
                    ''', (
                        edit_name.value, edit_payment_code.value, edit_class.value, edit_year.value, edit_term.value,
                        int(edit_lit_i.value or 0), int(edit_lit_ii.value or 0),
                        int(edit_reading.value or 0), int(edit_luganda.value or 0),
                        int(edit_maths.value or 0), int(edit_english.value or 0),
                        int(edit_sst.value or 0), int(edit_science.value or 0),
                        int(edit_re.value or 0), record['id']
                    ))
                    conn.commit()

                ui.notify("Lower primary record updated successfully!", type='positive')
                edit_dialog.close()
                on_save()
                log_activity(app.storage.user.get('username', 'Admin'), f"Edited lower primary record for {edit_name.value}")
            except Exception as e:
                ui.notify(f"Update failed: {e}", type='negative')

        with ui.row().classes('w-full justify-end gap-2 mt-4'):
            ui.button('Cancel', on_click=edit_dialog.close).props('flat rounded').classes('text-slate-600')
            ui.button('Save Changes', on_click=save_lower_changes).props('unelevated color="primary" rounded').classes('px-6 shadow-md')

    edit_dialog.open()

def view_lower_records_content(lower_primary_tab):
    with ui.tab_panel(lower_primary_tab).classes('p-0 gap-4 flex flex-col'):
        with ui.card().classes('w-full p-6 bg-white shadow-xl rounded-3xl border border-slate-100 flex flex-col gap-4'):
            
            def download_all_lower_reports():
                if not all_lower_records:
                    ui.notify("No lower primary records to export", type='warning')
                    return
                try:
                    import lower_report
                    all_html = ""
                    for record in all_lower_records:
                        single_report = lower_report.report(record)
                        all_html += f"<div style='page-break-after: always;'>{single_report}</div>"

                    ui.run_javascript(f'''
                        const win = window.open('', '_blank');
                        win.document.write(`{all_html}`);
                        win.document.close();
                        win.print();
                    ''')
                    ui.notify("Bulk lower primary report generation triggered", type='positive')
                except Exception as e:
                    ui.notify(f"Failed to generate bulk reports: {e}", type='negative')

            with ui.row().classes('w-full justify-between items-center flex-wrap gap-3'):
                ui.label('Lower Primary Academic Records').classes('text-xl font-bold text-slate-800')

                with ui.row().classes('items-center gap-2 flex-wrap'):
                    class_select = ui.select(
                        ['All', 'P1', 'P2', 'P3'],
                        value='All',
                        label='Class'
                    ).props('dense outlined rounded').classes('w-28 bg-slate-50')
                    class_select.on('update:model-value', lambda: refresh_lower_table_data(class_select.value, year_input.value, lower_term_select.value))

                    lower_term_select = ui.select(
                        ['All', 'Term I', 'Term II', 'Term III'],
                        value='All',
                        label='Term'
                    ).props('dense outlined rounded').classes('w-32 bg-slate-50')
                    lower_term_select.on('update:model-value', lambda: refresh_lower_table_data(class_select.value, year_input.value, lower_term_select.value))

                    year_input = ui.input(placeholder='Year...').props('dense outlined clearable rounded').classes('w-28 bg-slate-50')
                    year_input.on('change', lambda: refresh_lower_table_data(class_select.value, year_input.value, lower_term_select.value))

                with ui.row().classes('items-center gap-2 flex-wrap'):
                    def export_csv():
                        if not all_lower_records:
                            ui.notify("No data to export", type='warning')
                            return
                        df = pl.DataFrame(all_lower_records)
                        buffer = io.StringIO()
                        df.write_csv(buffer)
                        ui.download(src=buffer.getvalue().encode('utf-8'), filename='lower_primary_records.csv')
                        ui.notify("Download started", type='positive')

                    search_input = ui.input(placeholder='Search pupil...').props('dense outlined clearable rounded').classes('bg-slate-50')
                    ui.button(icon='search', on_click=lambda: apply_lower_filter(search_input.value)).props('dense unelevated color="primary"').classes('rounded-xl')
                    ui.button('Print All', icon='print', on_click=download_all_lower_reports).props('flat dense color="primary"').classes('rounded-xl')
                    ui.button('Export CSV', icon='download', on_click=export_csv).props('flat dense color="primary"').classes('rounded-xl')
                    ui.button('Refresh', icon='refresh', on_click=lambda: refresh_lower_table_data(class_select.value, year_input.value, lower_term_select.value)).props('outline dense text-color="primary"').classes('rounded-xl')

            columns = [
                {'name': 'name', 'label': 'Pupil Name', 'field': 'name', 'align': 'left', 'sortable': True},
                {'name': 'payment_code', 'label': 'Payment Code', 'field': 'payment_code', 'align': 'center', 'sortable': True},
                {'name': 'class_level', 'label': 'Class', 'field': 'class_level', 'align': 'center', 'sortable': True},
                {'name': 'year', 'label': 'Year', 'field': 'year', 'align': 'center', 'sortable': True},
                {'name': 'term', 'label': 'Term', 'field': 'term', 'align': 'center'},
                {'name': 'literacy_i', 'label': 'Lit I', 'field': 'literacy_i', 'align': 'center'},
                {'name': 'literacy_ii', 'label': 'Lit II', 'field': 'literacy_ii', 'align': 'center'},
                {'name': 'reading', 'label': 'Reading', 'field': 'reading', 'align': 'center'},
                {'name': 'luganda', 'label': 'Luganda', 'field': 'luganda', 'align': 'center'},
                {'name': 'mathematics', 'label': 'Maths', 'field': 'mathematics', 'align': 'center'},
                {'name': 'english', 'label': 'English', 'field': 'english', 'align': 'center'},
                {'name': 'social_studies', 'label': 'S.S.T', 'field': 'social_studies', 'align': 'center'},
                {'name': 'science', 'label': 'Science', 'field': 'science', 'align': 'center'},
                {'name': 're_religious_education', 'label': 'R.E', 'field': 're_religious_education', 'align': 'center'},
                {'name': '_calc_total', 'label': 'Total', 'field': '_calc_total', 'sortable': True, 'align': 'center'},
                {'name': '_calc_grade', 'label': 'Grade', 'field': '_calc_grade', 'align': 'center'},
                {'name': '_calc_rank', 'label': 'Rank', 'field': '_calc_rank', 'align': 'center', 'sortable': True},
                {'name': 'class_teacher', 'label': 'Teacher', 'field': 'class_teacher', 'align': 'left'},
                {'name': 'actions', 'label': 'Actions', 'field': 'actions', 'align': 'center'}
            ]
            
            global lower_student_table, all_lower_records
            all_lower_records = []
            lower_student_table = ui.table(columns=columns, rows=[], row_key='id').classes('w-full shadow-inner border border-slate-100 rounded-2xl')
            
            lower_student_table.add_slot('body-cell-_calc_grade', '''
                <q-td :props="props">
                    <q-badge :color="['D', 'E', 'F', 'F9'].includes(props.value) ? 'red' : 'green'" class="px-2 py-1 rounded-full font-bold">
                        {{ props.value }}
                    </q-badge>
                </q-td>
            ''')

            lower_student_table.add_slot('body-cell-actions', '''
                <q-td :props="props">
                    <q-btn flat dense round icon="download" color="green-7" @click="$parent.$emit('download_lower_row', props.row)">
                        <q-tooltip>Download Report</q-tooltip>
                    </q-btn>
                    <q-btn flat dense round icon="edit" color="blue-7" @click="$parent.$emit('edit_lower_row', props.row)">
                        <q-tooltip>Edit Record</q-tooltip>
                    </q-btn>
                    <q-btn flat dense round icon="delete" color="red-7" @click="$parent.$emit('delete_lower_row', props.row.id)">
                        <q-tooltip>Delete Record</q-tooltip>
                    </q-btn>
                </q-td>
            ''')

            def compute_lower_derived_fields(rows):
                if not rows:
                    return []
                df = pl.DataFrame(rows)
                subject_cols = ['literacy_i', 'literacy_ii', 'reading', 'luganda', 'mathematics', 'english', 'social_studies', 'science', 're_religious_education']
                existing_subs = [c for c in subject_cols if c in df.columns]
                
                df = df.with_columns([pl.col(c).fill_null(0) for c in existing_subs])
                total_expr = pl.sum_horizontal(existing_subs) if existing_subs else pl.lit(0)
                df = df.with_columns(total_expr.alias('_calc_total'))

                if 'class_level' in df.columns:
                    df = df.with_columns(
                        pl.col("_calc_total").rank(descending=True, method="dense").over("class_level").alias("_calc_rank")
                    )
                else:
                    df = df.with_columns(
                        pl.col("_calc_total").rank(descending=True, method="dense").alias("_calc_rank")
                    )

                def get_lower_grade(avg):
                    if avg >= 80: return "1"
                    elif avg >= 70: return "2"
                    elif avg >= 60: return "3"
                    elif avg >= 50: return "4"
                    elif avg >= 45: return "5"
                    elif avg >= 40: return "6"
                    elif avg >= 30: return "8"
                    else: return "9"

                num_subs = len(existing_subs) if existing_subs else 1
                df = df.with_columns(
                    (pl.col("_calc_total") / num_subs).alias("_avg")
                ).with_columns(
                    pl.col("_avg").map_elements(get_lower_grade, return_dtype=pl.Utf8).alias('_calc_grade')
                ).drop("_avg")

                return df.to_dicts()

            def download_single_lower_report(student_data):
                try:
                    import lower_report
                    single_html = lower_report.report(student_data)
                    ui.run_javascript(f'''
                        const win = window.open('', '_blank');
                        win.document.write(`{single_html}`);
                        win.document.close();
                        win.print();
                    ''')
                    ui.notify(f"Lower primary report window opened for {student_data.get('name', '')}", type='positive')
                except Exception as e:
                    ui.notify(f"Failed to generate lower report: {e}", type='negative')

            def delete_lower_record(record_id):
                try:
                    with sqlite3.connect(DB) as conn:
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM lower_primary_results WHERE id = ?", (record_id,))
                        conn.commit()
                    ui.notify("Lower primary record removed successfully", type='positive')
                    refresh_lower_table_data(class_select.value, year_input.value, lower_term_select.value)
                    log_activity(app.storage.user.get('username', 'Admin'), f"Deleted lower primary record ID {record_id}")
                except Exception as e:
                    ui.notify(f"Delete failed: {e}", type='negative')

            def refresh_lower_table_data(class_filter='All', year_filter='', term_filter='All'):
                global lower_student_table, all_lower_records
                if lower_student_table is None:
                    return
                try:
                    with sqlite3.connect(DB) as conn:
                        conn.row_factory = sqlite3.Row
                        
                        cursor = conn.cursor()
                        cursor.execute("PRAGMA table_info(lower_primary_results)")
                        columns_info = [col[1] for col in cursor.fetchall()]
                        if 'pupil_name' in columns_info and 'name' not in columns_info:
                            cursor.execute("ALTER TABLE lower_primary_results RENAME COLUMN pupil_name TO name")
                            conn.commit()
                        if 'admission_number' in columns_info and 'payment_code' not in columns_info:
                            cursor.execute("ALTER TABLE lower_primary_results RENAME COLUMN admission_number TO payment_code")
                            conn.commit()
                        elif 'payment_code' not in columns_info:
                            try:
                                cursor.execute("ALTER TABLE lower_primary_results ADD COLUMN payment_code TEXT")
                                conn.commit()
                            except Exception:
                                pass
                        if 'year' not in columns_info:
                            try:
                                cursor.execute(f"ALTER TABLE lower_primary_results ADD COLUMN year TEXT DEFAULT '{datetime.now().year}'")
                                conn.commit()
                            except Exception:
                                pass
                        if 'term' not in columns_info:
                            try:
                                cursor.execute("ALTER TABLE lower_primary_results ADD COLUMN term TEXT")
                                conn.commit()
                            except Exception:
                                pass

                        query = "SELECT * FROM lower_primary_results WHERE 1=1"
                        params = []

                        if year_filter and year_filter.strip():
                            query += " AND year LIKE ?"
                            params.append(f"%{year_filter.strip()}%")
                        if term_filter != 'All':
                            query += " AND term = ?"
                            params.append(term_filter)

                        raw_rows = [dict(r) for r in cursor.execute(query, params).fetchall()]
                        
                        all_lower_records = compute_lower_derived_fields(raw_rows)
                        
                        if class_filter != 'All':
                            lower_student_table.rows = [r for r in all_lower_records if str(r.get('class_level')).upper() in [class_filter.upper(), class_filter.upper().replace('P', '')]]
                        else:
                            lower_student_table.rows = all_lower_records
                            
                        lower_student_table.update()
                except Exception as e:
                    ui.notify(f"Error loading lower primary records: {e}", type='negative')

            def apply_lower_filter(query):
                global lower_student_table, all_lower_records
                if not query:
                    refresh_lower_table_data(class_select.value, year_input.value, lower_term_select.value)
                else:
                    filtered = [r for r in all_lower_records if query.lower() in str(r.get('name', '')).lower()]
                    if class_select.value != 'All':
                        filtered = [r for r in filtered if str(r.get('class_level')).upper() in [class_select.value.upper(), class_select.value.upper().replace('P', '')]]
                    lower_student_table.rows = filtered
                    lower_student_table.update()

            def handle_edit_wrapper(row_data):
                edit_lower_record(row_data, lambda: refresh_lower_table_data(class_select.value, year_input.value, lower_term_select.value))

            lower_student_table.on('download_lower_row', lambda msg: download_single_lower_report(msg.args))
            lower_student_table.on('edit_lower_row', lambda msg: handle_edit_wrapper(msg.args))
            lower_student_table.on('delete_lower_row', lambda msg: delete_lower_record(msg.args))

            refresh_lower_table_data()

# Main page layout and UI configuration function for NiceGUI
def home(client=None):
    global countdown_label
    if not app.storage.user.get('logged_in'):
        ui.run_javascript('window.location.replace("/login")')
        return
    
    app.storage.user['last_active'] = datetime.now().isoformat()
    ui.on('click', update_activity_timestamp)

    global student_table, activity_table
    ui.query('.q-page, .nicegui-content').style('max-width: none !important; width: 100% !important; padding: 0 !important;')
    ui.query('.nicegui-content').classes('flex flex-col items-center bg-slate-100/60 p-6')

    dashboard_data = get_dashboard_stats()

    with ui.column().classes('w-full max-w-[1300px] items-center gap-6'):
        # Modern Top Header Navigation Card with Glassmorphism
        with ui.card().classes('w-full p-3 bg-white/90 backdrop-blur-xl shadow-xl rounded-3xl border border-white/40').tight():
            with ui.row().classes('w-full items-center justify-between px-6 py-2'):
                with ui.row().classes('items-center gap-3'):
                    with ui.avatar().classes('bg-[#1b4d3e] text-white shadow-md'):
                        ui.icon('school', size='24px')
                    with ui.column().classes('gap-0'):
                        ui.label('Strathearn Primary School').classes('text-2xl font-black text-slate-900 tracking-tight')
                        ui.label('Masanafu • Academic Management Portal').classes('text-xs font-semibold text-emerald-800')
                    
                    ui.add_head_html('''
                        <style>
                            .big-tabs .q-tab__label {
                                font-size: 15px !important;
                                font-weight: 600 !important;
                            }
                            .big-tabs .q-icon {
                                font-size: 22px !important;
                            }
                            .big-tabs {
                                min-height: 60px !important;
                            }
                            body {
                                background-color: #f8fafc;
                                font-family: 'Inter', ui-sans-serif, system-ui, sans-serif;
                            }
                            
                            /* Ensure A4 report print fits single page and respects page breaks */
                            @media print {
                                body {
                                    background: white !important;
                                }
                                .q-page-container, .q-page, .nicegui-content {
                                    padding: 0 !important;
                                    margin: 0 !important;
                                }
                            }
                        </style>
                    ''')
                
                with ui.row().classes('items-center gap-4'):
                    with ui.row().classes('items-center gap-2 bg-emerald-50/80 px-4 py-2 rounded-2xl border border-emerald-100 shadow-sm'):
                        ui.icon('timer', size='18px', color='primary')
                        countdown_label = ui.label('Auto-logout in: 30:00').classes('text-xs font-bold text-[#1b4d3e]')

                    global unread_notifications_badge, notifications_menu
                    with ui.row().classes('items-center gap-2 relative'):
                        with ui.button(icon='notifications').props('flat round dense').classes('text-slate-700 bg-slate-100 hover:bg-emerald-100/60 transition-all'):
                            unread_notifications_badge = ui.badge('0', color='red').props('floating').classes('text-[10px] font-bold')
                        
                        with ui.menu() as notifications_menu:
                            with ui.card().classes('w-80 p-4 shadow-2xl rounded-3xl border border-slate-100'):
                                ui.label('Live System Notifications').classes('text-sm font-bold text-slate-800 mb-3 border-b pb-2')
                                notifications_container = ui.column().classes('w-full gap-2 max-h-60 overflow-y-auto')
                                
                                def update_notifications_dropdown():
                                    notifications_container.clear()
                                    try:
                                        with sqlite3.connect(DB) as conn:
                                            conn.row_factory = sqlite3.Row
                                            recent_logs = conn.execute("SELECT username, timestamp, status FROM activity_logs ORDER BY id DESC LIMIT 5").fetchall()
                                            if not recent_logs:
                                                with notifications_container:
                                                    ui.label('No new activity notifications').classes('text-xs text-slate-400 italic py-2')
                                                if 'unread_notifications_badge' in globals() and unread_notifications_badge:
                                                    unread_notifications_badge.text = '0'
                                            else:
                                                count = len(recent_logs)
                                                if 'unread_notifications_badge' in globals() and unread_notifications_badge:
                                                    unread_notifications_badge.text = str(count)
                                                with notifications_container:
                                                    for log in recent_logs:
                                                        with ui.row().classes('w-full justify-between items-start py-2 border-b border-slate-50 last:border-none'):
                                                            with ui.column().classes('gap-0.5 flex-1'):
                                                                ui.label(f"{log['username']}: {log['status']}").classes('text-xs text-slate-800 font-semibold')
                                                                ui.label(log['timestamp']).classes('text-[10px] text-slate-400')
                                    except Exception:
                                        pass

                                update_notifications_dropdown()
                                ui.timer(5.0, update_notifications_dropdown)

            with ui.tabs().classes(
                    'w-full bg-slate-100/70 p-2 rounded-2xl shadow-inner border border-slate-200/50 big-tabs'
                ) as nav_tabs:
                nav_tabs.classes('items-center justify-center gap-1')

                home_tab = ui.tab('Dashboard', icon='dashboard').classes('rounded-xl transition-all duration-300 hover:bg-white/80 data-[selected]:bg-[#1b4d3e] data-[selected]:text-white data-[selected]:shadow-md')
                teachers_tab = ui.tab('Entry Manager', icon='edit_note').classes('rounded-xl transition-all duration-300 hover:bg-white/80 data-[selected]:bg-[#1b4d3e] data-[selected]:text-white data-[selected]:shadow-md')
                Upper_primary_tab = ui.tab('Upper Primary', icon='assignment').classes('rounded-xl transition-all duration-300 hover:bg-white/80 data-[selected]:bg-[#1b4d3e] data-[selected]:text-white data-[selected]:shadow-md')
                lower_primary_tab = ui.tab('Lower Primary', icon='menu_book').classes('rounded-xl transition-all duration-300 hover:bg-white/80 data-[selected]:bg-[#1b4d3e] data-[selected]:text-white data-[selected]:shadow-md')
                staff_chat_tab = ui.tab('Staff Chat', icon='forum').classes('rounded-xl transition-all duration-300 hover:bg-white/80 data-[selected]:bg-[#1b4d3e] data-[selected]:text-white data-[selected]:shadow-md')
                logs_tab = ui.tab('System Logs', icon='history').classes('rounded-xl transition-all duration-300 hover:bg-white/80 data-[selected]:bg-[#1b4d3e] data-[selected]:text-white data-[selected]:shadow-md')
                logout_tab = ui.tab('Log Out', icon='logout').classes('rounded-xl transition-all duration-300 hover:bg-red-50 text-red-600 data-[selected]:bg-red-600 data-[selected]:text-white data-[selected]:shadow-md')
            starting_tab = home_tab

        with ui.tab_panels(nav_tabs, value=starting_tab).classes('w-full bg-transparent'):
            with ui.tab_panel(home_tab).classes('p-0 gap-6 flex flex-col'):
                # Hero Welcome Banner Card
                with ui.card().classes('w-full p-8 bg-gradient-to-r from-[#1b4d3e] to-[#2d6a4f] text-white shadow-2xl rounded-3xl relative overflow-hidden'):
                    with ui.row().classes('w-full items-center justify-between relative z-10 flex-wrap gap-4'):
                        with ui.row().classes('items-center gap-6'):
                            ui.image('badge.jpeg') \
                                .classes('w-20 h-20 md:w-24 md:h-24 rounded-2xl shadow-lg object-cover border-2 border-white/30 flex-shrink-0 bg-white/10')

                            with ui.column().classes('gap-1'):
                                ui.label("Administrator Overview") \
                                    .classes('text-3xl md:text-4xl font-extrabold tracking-tight text-white')
                                ui.label(f"System Status: Operational • {datetime.now().strftime('%A, %B %d, %Y')}") \
                                    .classes('text-emerald-100 text-sm font-medium opacity-90')
                                ui.label('Centralized oversight for student academic progression and comprehensive report generation.') \
                                    .classes('text-emerald-200/80 text-xs mt-1 max-w-xl')

                # Quick Actions Grid
                with ui.row().classes('w-full gap-4 items-stretch'):
                    with ui.card().classes('flex-1 p-5 bg-white shadow-lg rounded-3xl border border-slate-100 cursor-pointer hover:shadow-xl hover:border-emerald-600 transition-all group') as btn_card1:
                        with ui.row().classes('items-center gap-4'):
                            ui.icon('person_add', color='primary').classes('text-3xl p-3 bg-emerald-50 rounded-2xl group-hover:scale-110 transition-transform')
                            with ui.column().classes('gap-0'):
                                ui.label('Add New Scores').classes('text-base font-bold text-slate-800')
                                ui.label('Open marks entry form').classes('text-xs text-slate-400')
                        btn_card1.on('click', lambda: nav_tabs.set_value(teachers_tab))

                    with ui.card().classes('flex-1 p-5 bg-white shadow-lg rounded-3xl border border-slate-100 cursor-pointer hover:shadow-xl hover:border-emerald-600 transition-all group') as btn_card2:
                        with ui.row().classes('items-center gap-4'):
                            ui.icon('print', color='primary').classes('text-3xl p-3 bg-emerald-50 rounded-2xl group-hover:scale-110 transition-transform')
                            with ui.column().classes('gap-0'):
                                ui.label('Bulk Print Reports').classes('text-base font-bold text-slate-800')
                                ui.label('Export class report sheets').classes('text-xs text-slate-400')
                        btn_card2.on('click', download_all_reports)

                    with ui.card().classes('flex-1 p-5 bg-white shadow-lg rounded-3xl border border-slate-100 cursor-pointer hover:shadow-xl hover:border-emerald-600 transition-all group') as btn_card3:
                        with ui.row().classes('items-center gap-4'):
                            ui.icon('forum', color='primary').classes('text-3xl p-3 bg-emerald-50 rounded-2xl group-hover:scale-110 transition-transform')
                            with ui.column().classes('gap-0'):
                                ui.label('Staff Chat Hub').classes('text-base font-bold text-slate-800')
                                ui.label('Check teacher discussions').classes('text-xs text-slate-400')
                        btn_card3.on('click', lambda: nav_tabs.set_value(staff_chat_tab))

                # Statistics Cards Row
                with ui.row().classes('w-full gap-4 items-stretch'):
                    with ui.card().classes('flex-1 p-6 bg-white shadow-xl rounded-3xl border border-slate-100'):
                        with ui.row().classes('items-center justify-between'):
                            ui.label('TOTAL ENROLLMENT').classes('text-xs font-bold uppercase tracking-wider text-slate-400')
                            ui.icon('group', color='primary').classes('text-xl bg-emerald-50 p-2 rounded-xl')
                        ui.label(str(dashboard_data.get('total_students', 0))).classes('text-4xl font-black text-slate-900 mt-3')
                        ui.label('Active Student Records').classes('text-xs font-semibold text-emerald-800 mt-1')

                    with ui.card().classes('flex-1 p-6 bg-white shadow-xl rounded-3xl border border-slate-100'):
                        with ui.row().classes('items-center justify-between'):
                            ui.label('PRIMARY CLASSES').classes('text-xs font-bold uppercase tracking-wider text-slate-400')
                            ui.icon('school', color='primary').classes('text-xl bg-emerald-50 p-2 rounded-xl')
                        ui.label('P1 - P7').classes('text-4xl font-black text-slate-900 mt-3')
                        ui.label('Managing controlled classrooms.').classes('text-xs font-semibold text-emerald-800 mt-1')

                    with ui.card().classes('flex-1 p-6 bg-white shadow-xl rounded-3xl border border-slate-100'):
                        with ui.row().classes('items-center justify-between'):
                            ui.label('SUCCESS RATE').classes('text-xs font-bold uppercase tracking-wider text-slate-400')
                            ui.icon('trending_up', color='primary').classes('text-xl bg-emerald-50 p-2 rounded-xl')

                        perc = dashboard_data.get('pass_rate', 0) * 100
                        percentage = round(perc, 1)
                        status = "Optimal" if percentage >= 85 else "Satisfactory" if percentage >= 70 else "Needs Review"
                        ui.label(f"{percentage}%").classes('text-4xl font-black text-slate-900 mt-3')
                        ui.label(f"Performance Level: {status}").classes('text-xs font-semibold text-emerald-800 mt-1')

                # Enrollment Breakdown Section
                with ui.card().classes('w-full p-6 bg-white shadow-xl rounded-3xl border border-slate-100'):
                    with ui.row().classes('items-center gap-2 mb-6'):
                        ui.icon('groups', color='primary').classes('text-2xl')
                        ui.label('Number of Pupils per Class').classes('text-lg font-bold text-slate-800')

                    class_counts = dashboard_data.get('class_enrollment', {})

                    class_colors = {
                        'P1': {'bg': 'bg-blue-50/80', 'border': 'border-blue-200', 'text': 'text-blue-700'},
                        'P2': {'bg': 'bg-emerald-50/80', 'border': 'border-emerald-200', 'text': 'text-emerald-700'},
                        'P3': {'bg': 'bg-amber-50/80', 'border': 'border-amber-200', 'text': 'text-amber-700'},
                        'P4': {'bg': 'bg-purple-50/80', 'border': 'border-purple-200', 'text': 'text-purple-700'},
                        'P5': {'bg': 'bg-rose-50/80', 'border': 'border-rose-200', 'text': 'text-rose-700'},
                        'P6': {'bg': 'bg-cyan-50/80', 'border': 'border-cyan-200', 'text': 'text-cyan-700'},
                        'P7': {'bg': 'bg-indigo-50/80', 'border': 'border-indigo-200', 'text': 'text-indigo-700'}
                    }

                    ui.label('Lower Primary (P1 - P3)').classes('text-xs font-bold uppercase tracking-wider text-slate-400 mb-3')
                    lower_classes = ['P1', 'P2', 'P3']
                    with ui.row().classes('w-full gap-4 flex-wrap mb-6'):
                        for cls_name in lower_classes:
                            count = (
                                class_counts.get(cls_name, 0) or 
                                class_counts.get(cls_name.lower(), 0) or 
                                class_counts.get(cls_name.replace('P', ''), 0)
                            )
                            style = class_colors.get(cls_name, {'bg': 'bg-slate-50', 'border': 'border-slate-200', 'text': 'text-slate-700'})
                            with ui.card().classes(f"flex-1 min-w-[140px] p-5 {style['bg']} rounded-2xl border {style['border']} items-center justify-center shadow-sm"):
                                ui.label(cls_name).classes(f"text-xs font-extrabold {style['text']} uppercase tracking-wider")
                                ui.label(str(count)).classes('text-3xl font-black text-slate-900 mt-2')
                                ui.label('Pupils').classes('text-[11px] font-medium text-slate-500 mt-0.5')

                    ui.label('Upper Primary (P4 - P7)').classes('text-xs font-bold uppercase tracking-wider text-slate-400 mb-3')
                    upper_classes = ['P4', 'P5', 'P6', 'P7']
                    with ui.row().classes('w-full gap-4 flex-wrap'):
                        for cls_name in upper_classes:
                            count = (
                                class_counts.get(cls_name, 0) or 
                                class_counts.get(cls_name.lower(), 0) or 
                                class_counts.get(cls_name.replace('P', ''), 0)
                            )
                            style = class_colors.get(cls_name, {'bg': 'bg-slate-50', 'border': 'border-slate-200', 'text': 'text-slate-700'})
                            with ui.card().classes(f"flex-1 min-w-[140px] p-5 {style['bg']} rounded-2xl border {style['border']} items-center justify-center shadow-sm"):
                                ui.label(cls_name).classes(f"text-xs font-extrabold {style['text']} uppercase tracking-wider")
                                ui.label(str(count)).classes('text-3xl font-black text-slate-900 mt-2')
                                ui.label('Pupils').classes('text-[11px] font-medium text-slate-500 mt-0.5')

                # Subject Averages & Top Performers Grid
                with ui.row().classes('w-full gap-6 items-stretch'):
                    with ui.card().classes('flex-1 p-6 bg-white shadow-xl rounded-3xl border border-slate-100'):
                        with ui.row().classes('w-full justify-between items-center mb-6'):
                            ui.label('Subject Averages by Class').classes('text-lg font-bold text-slate-800')
                            
                            available_classes = list(dashboard_data.get('class_subject_averages', {}).keys()) or ['P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7']
                            class_avg_select = ui.select(
                                available_classes,
                                value=available_classes[0] if available_classes else 'P1'
                            ).props('dense outlined rounded').classes('w-32 bg-slate-50')
                            class_avg_select.on('update:model-value', lambda e: update_class_averages(e.value))

                        averages_container = ui.column().classes('w-full gap-3')

                        def update_class_averages(selected_class):
                            averages_container.clear()
                            class_data = dashboard_data.get('class_subject_averages', {}).get(selected_class, {'Maths': 0, 'English': 0, 'SST': 0, 'Science': 0})
                            with averages_container:
                                if not any(class_data.values()):
                                    ui.label('No records found for this class.').classes('text-xs text-slate-400 italic py-6 text-center w-full')
                                else:
                                    for sub, val in class_data.items():
                                        with ui.column().classes('w-full gap-1.5 bg-slate-50/70 p-3 rounded-2xl border border-slate-100'):
                                            with ui.row().classes('w-full justify-between items-center'):
                                                ui.label(sub).classes('text-xs font-bold text-slate-700')
                                                ui.label(f"{val}%").classes('text-xs font-extrabold text-[#1b4d3e]')
                                            ui.linear_progress(value=val/100 if val > 0 else 0.05, color='primary').classes('w-full rounded-full h-2')

                        update_class_averages(class_avg_select.value)

                    with ui.card().classes('flex-1 p-6 bg-white shadow-xl rounded-3xl border border-slate-100'):
                        with ui.row().classes('items-center gap-2 mb-6'):
                            ui.icon('emoji_events', color='amber-7').classes('text-2xl')
                            ui.label('Top Academic Performers').classes('text-lg font-bold text-slate-800')

                        performers = dashboard_data.get('top_students', [])
                        if not performers:
                            ui.label('No top performers recorded yet.').classes('text-xs text-slate-400 italic py-6 text-center w-full')
                        else:
                            with ui.column().classes('w-full gap-3'):
                                for idx, stud in enumerate(performers):
                                    with ui.row().classes('w-full items-center justify-between p-4 bg-slate-50/80 rounded-2xl border border-slate-100'):
                                        with ui.row().classes('items-center gap-3'):
                                            ui.badge(str(idx+1), color='primary').classes('rounded-full text-xs font-bold w-7 h-7 flex items-center justify-center')
                                            with ui.column().classes('gap-0'):
                                                ui.label(stud.get('Name', 'Unknown')).classes('text-sm font-bold text-slate-900')
                                                ui.label(f"Class: {stud.get('Class', 'N/A')}").classes('text-xs text-slate-500')
                                        ui.badge(f"Agg: {stud.get('Aggregates', 0)} | {stud.get('Division', 'N/A')}", color='emerald-50') \
                                            .classes('text-emerald-800 font-bold text-xs px-3 py-1 rounded-full border border-emerald-200')

                # Recent System Activity Card
                with ui.card().classes('w-full p-6 bg-white shadow-xl rounded-3xl border border-slate-100'):
                    with ui.row().classes('items-center justify-between mb-4'):
                        with ui.row().classes('items-center gap-2'):
                            ui.icon('history', color='primary').classes('text-2xl')
                            ui.label('Recent System Activity').classes('text-lg font-bold text-slate-800')
                        ui.button('View All', on_click=lambda: nav_tabs.set_value(logs_tab)).props('flat dense text-color="primary" size="sm"')

                    logs_list = dashboard_data.get('user_logs', [])
                    if not logs_list:
                        ui.label('No recent activities logged.').classes('text-xs text-slate-400 italic py-2')
                    else:
                        with ui.column().classes('w-full gap-2'):
                            for log in logs_list[:4]:
                                with ui.row().classes('w-full justify-between items-center p-3 bg-slate-50/50 rounded-2xl border border-slate-100'):
                                    with ui.row().classes('items-center gap-3'):
                                        ui.badge(log.get('username', 'System'), color='slate-200').classes('text-slate-700 text-xs font-semibold px-2.5 py-0.5 rounded-full')
                                        ui.label(log.get('status', '')).classes('text-xs font-medium text-slate-700')
                                    ui.label(log.get('timestamp', '')).classes('text-xs text-slate-400 font-mono')

            with ui.tab_panel(teachers_tab).classes('p-0 gap-6 flex flex-col'):
                with ui.card().classes('w-full p-6 bg-white shadow-xl rounded-3xl border border-slate-100'):
                    with ui.row().classes('w-full items-center justify-between mb-2'):
                        ui.label('Upper Primary Marks Entry Manager').classes('text-lg font-bold text-slate-800')
                        with ui.row().classes('gap-2 items-center'):
                            launch_btn = ui.button('Run Upper Insert', icon='add_circle').props('color="primary" unelevated rounded').classes('shadow-md')
                            minimize_btn = ui.button('Minimize', icon='keyboard_arrow_up').props('color="grey-7" flat dense rounded')
                    form_container = ui.column().classes('w-full gap-4 transition-all duration-300 mt-2')
                    form_container.set_visibility(False)
                    launch_btn.on_click(lambda: (form_container.set_visibility(True), form_container.clear(), exec('with form_container: insert.insert()')))
                    minimize_btn.on_click(lambda: form_container.set_visibility(False))

                with ui.card().classes('w-full p-6 bg-white shadow-xl rounded-3xl border border-slate-100'):
                    with ui.row().classes('w-full items-center justify-between mb-2'):
                        ui.label('Lower Primary Marks Entry Manager (P.1 - P.3)').classes('text-lg font-bold text-slate-800')
                        with ui.row().classes('gap-2 items-center'):
                            launch_lower_btn = ui.button('Run Lower Insert', icon='add_circle').props('color="primary" unelevated rounded').classes('shadow-md')
                            minimize_lower_btn = ui.button('Minimize', icon='keyboard_arrow_up').props('color="grey-7" flat dense rounded')
                    lower_form_container = ui.column().classes('w-full gap-4 transition-all duration-300 mt-2')
                    lower_form_container.set_visibility(False)
                    launch_lower_btn.on_click(lambda: (lower_form_container.set_visibility(True), lower_form_container.clear(), exec('with lower_form_container: lower.lower()')))
                    minimize_lower_btn.on_click(lambda: lower_form_container.set_visibility(False))

            with ui.tab_panel(Upper_primary_tab).classes('p-0 gap-6 flex flex-col'):
                with ui.card().classes('w-full p-6 bg-white shadow-xl rounded-3xl border border-slate-100 flex flex-col gap-5'):
                    with ui.row().classes('w-full justify-between items-center flex-wrap gap-3'):
                        ui.label('Upper Primary Academic Records').classes('text-xl font-bold text-slate-800')

                        with ui.row().classes('items-center gap-2 flex-wrap'):
                            class_select = ui.select(
                                ['All', 'P4', 'P5', 'P6', 'P7'],
                                value='All',
                                label='Class'
                            ).props('dense outlined rounded').classes('w-28 bg-slate-50')
                            class_select.on('update:model-value', lambda: refresh_table_data(class_select.value, year_input.value, term_select.value))

                            term_select = ui.select(
                                ['All', 'Term 1', 'Term 2', 'Term 3'],
                                value='All',
                                label='Term'
                            ).props('dense outlined rounded').classes('w-32 bg-slate-50')
                            term_select.on('update:model-value', lambda: refresh_table_data(class_select.value, year_input.value, term_select.value))

                            year_input = ui.input(placeholder='Year...').props('dense outlined clearable rounded').classes('w-28 bg-slate-50')
                            year_input.on('change', lambda: refresh_table_data(class_select.value, year_input.value, term_select.value))

                        with ui.row().classes('items-center gap-2 flex-wrap'):
                            def export_csv():
                                if not all_records:
                                    ui.notify("No data to export", type='warning')
                                    return
                                df = pl.DataFrame(all_records)
                                buffer = io.StringIO()
                                df.write_csv(buffer)
                                ui.download(src=buffer.getvalue().encode('utf-8'), filename='student_records.csv')
                                ui.notify("Download started", type='positive')

                            search_input = ui.input(placeholder='Search student...').props('dense outlined clearable rounded').classes('bg-slate-50')
                            ui.button(icon='search', on_click=lambda: apply_filter(search_input.value)).props('dense unelevated color="primary"').classes('rounded-xl')
                            ui.button('Print All', icon='print', on_click=download_all_reports).props('flat dense color="primary"').classes('rounded-xl')
                            ui.button('Export CSV', icon='download', on_click=export_csv).props('flat dense color="primary"').classes('rounded-xl')
                            ui.button('Refresh', icon='refresh', on_click=lambda: refresh_table_data(class_select.value, year_input.value, term_select.value)).props('outline dense text-color="primary"').classes('rounded-xl')

                    columns = [
                        {'name': 'Name', 'label': 'Student', 'field': 'Name', 'align': 'left', 'sortable': True},
                        {'name': 'PaymentCode', 'label': 'Payment Code', 'field': 'PaymentCode', 'align': 'center', 'sortable': True},
                        {'name': 'Class', 'label': 'Class', 'field': 'Class', 'align': 'center'},
                        {'name': 'Year', 'label': 'Year', 'field': 'Year', 'align': 'center', 'sortable': True},
                        {'name': 'Term', 'label': 'Term', 'field': 'Term', 'align': 'center'},
                        {'name': 'Maths', 'label': 'Maths', 'field': 'Maths', 'align': 'center'},
                        {'name': 'Maths_Grade', 'label': 'M. Grade', 'field': 'Maths_Grade', 'align': 'center'},
                        {'name': 'English', 'label': 'English', 'field': 'English', 'align': 'center'},
                        {'name': 'English_Grade', 'label': 'E. Grade', 'field': 'English_Grade', 'align': 'center'},
                        {'name': 'SST', 'label': 'SST', 'field': 'SST', 'align': 'center'},
                        {'name': 'SST_Grade', 'label': 'SST Grade', 'field': 'SST_Grade', 'align': 'center'},
                        {'name': 'Science', 'label': 'Science', 'field': 'Science', 'align': 'center'},
                        {'name': 'Science_Grade', 'label': 'Sci. Grade', 'field': 'Science_Grade', 'align': 'center'},
                        {'name': 'Total', 'label': 'Total', 'field': 'Total', 'sortable': True, 'align': 'center'},
                        {'name': 'Aggregates', 'label': 'Aggregates', 'field': 'Aggregates', 'sortable': True, 'align': 'center'},
                        {'name': 'Division', 'label': 'Division', 'field': 'Division', 'sortable': True, 'align': 'center'},
                        {'name': 'Rank', 'label': 'Rank', 'field': 'Rank', 'align': 'center', 'sortable': True},
                        {'name': 'actions', 'label': 'Actions', 'field': 'actions', 'align': 'center'}
                    ]
                    
                    student_table = ui.table(columns=columns, rows=[], row_key='id').classes('w-full shadow-inner border border-slate-100 rounded-2xl')
                    
                    student_table.add_slot('body-cell-Division', '''
                        <q-td :props="props">
                            <q-badge :color="props.value == 'Div U' ? 'red' : 'green'" class="px-2.5 py-1 rounded-full font-bold">
                                {{ props.value }}
                            </q-badge>
                        </q-td>
                    ''')

                    student_table.add_slot('body-cell-actions', '''
                        <q-td :props="props">
                            <q-btn flat dense round icon="download" color="green-7" @click="$parent.$emit('download_row', props.row)">
                                <q-tooltip>Download Report</q-tooltip>
                            </q-btn>
                            <q-btn flat dense round icon="edit" color="blue-7" @click="$parent.$emit('edit_row', props.row)">
                                <q-tooltip>Edit Record</q-tooltip>
                            </q-btn>
                            <q-btn flat dense round icon="delete" color="red-7" @click="$parent.$emit('delete_row', props.row.id)">
                                <q-tooltip>Delete Record</q-tooltip>
                            </q-btn>
                        </q-td>
                    ''')

                    def apply_filter(query):
                        global student_table, all_records
                        if not query:
                            refresh_table_data(class_select.value, year_input.value, term_select.value)
                        else:
                            q = query.lower()
                            student_table.rows = [r for r in all_records if q in str(r.get('Name', '')).lower()]
                            student_table.update()

                    def download_single_report(student_data):
                        try:
                            import report
                            single_html = report.report(student_data)
                            ui.run_javascript(f'''
                                const win = window.open('', '_blank');
                                win.document.write(`{single_html}`);
                                win.document.close();
                                win.print();
                            ''')
                            ui.notify(f"Report window opened for {student_data['Name']}", type='positive')
                        except Exception as e:
                            ui.notify(f"Failed to generate report: {e}", type='negative')

                    student_table.on('download_row', lambda msg: download_single_report(msg.args))
                    student_table.on('edit_row', lambda msg: open_edit_dialog(msg.args))
                    student_table.on('delete_row', lambda msg: delete_record(msg.args))

                    refresh_table_data()
            
            with ui.tab_panel(lower_primary_tab):
                view_lower_records_content(lower_primary_tab)

            with ui.tab_panel(staff_chat_tab):
                staff_chat_content()

            with ui.tab_panel(logs_tab).classes('p-0 gap-6 flex flex-col'):
                view_system_logs_content(logs_tab)

            with ui.tab_panel(logout_tab).classes('p-0 justify-center items-center flex min-h-[50vh]'):
                with ui.card().classes('w-full max-w-md p-10 text-center items-center flex flex-col gap-6 shadow-2xl rounded-3xl border border-slate-100 bg-white'):
                    ui.icon('power_settings_new', color='red-600') \
                        .classes('text-6xl bg-red-50 p-6 rounded-full shadow-inner')
                    
                    with ui.column().classes('gap-1'):
                        ui.label('Ready to leave?').classes('text-2xl font-black text-slate-900')
                        ui.label('Your session will be securely terminated.').classes('text-sm text-slate-500')
                    
                    with ui.row().classes('w-full gap-3 mt-4 justify-center'):
                        def perform_logout():
                            log_activity(app.storage.user.get('username', 'Admin'), "User Signed Out")
                            app.storage.user.clear()
                            ui.navigate.to('/')
                        ui.button('Sign Out', icon='logout', on_click=perform_logout) \
                            .props('color="red" unelevated size="md" rounded') \
                            .classes('px-8 shadow-md')
                        
                        ui.button('Cancel', on_click=lambda: nav_tabs.set_value(starting_tab)) \
                            .props('flat color="grey-7" rounded').classes('px-8')

# Function to recalculate class positions/ranks prioritizing Total (descending) then Aggregates (ascending)
def update_all_ranks():
    with sqlite3.connect(DB) as conn:
        df = pl.read_database("SELECT * FROM academic_records", conn)
        
        if not df.is_empty():
            df = df.sort(
                by=["Total", "Aggregates"], 
                descending=[True, False], 
                maintain_order=True
            ).with_columns(
                pl.col("Total").rank(method="dense", descending=True).over("Class").alias("Rank")
            )
            
            cursor = conn.cursor()
            for row in df.to_dicts():
                cursor.execute("UPDATE academic_records SET Rank = ? WHERE id = ?", (str(row['Rank']), row['id']))
            conn.commit()
