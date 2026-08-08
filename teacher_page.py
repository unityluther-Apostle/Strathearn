from datetime import datetime
import random
import os
import libsql
import insert
import lower
import nursery
from nicegui import app, ui
from verifying_passcode import get_db_connection


# --- INITIALIZE CHAT DATABASE TABLE ---
def init_chat_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS staff_chat (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender TEXT,
                message TEXT,
                timestamp TEXT
            )
        """)
        conn.commit()
    finally:
        conn.close()

init_chat_db()


def init_nursery_database():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS nursery_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                payment_code TEXT,
                pupil_name TEXT,
                class_level TEXT,
                term TEXT DEFAULT 'Term I',
                age TEXT,
                color TEXT,
                days_present INTEGER DEFAULT 0,
                days_absent INTEGER DEFAULT 0,
                date TEXT,
                listening_speaking_sequencing TEXT,
                music_rhymes_dance TEXT,
                punctuality TEXT,
                numeracy TEXT,
                vocabulary TEXT,
                literacy TEXT,
                general_science TEXT,
                environmental_awareness TEXT,
                writing_skills TEXT,
                physical_education TEXT,
                gods_creation TEXT,
                sharing TEXT,
                smartness TEXT,
                news TEXT,
                stories TEXT,
                life_skills TEXT,
                general_comment TEXT,
                headteachers_comment TEXT,
                next_term_begins_on TEXT,
                class_teacher TEXT
            )
        """)
        cursor.execute("PRAGMA table_info(nursery_results)")
        existing_columns = [col[1] for col in cursor.fetchall()]
        if "pupil_name" not in existing_columns:
            cursor.execute("ALTER TABLE nursery_results ADD COLUMN pupil_name TEXT")
        if "current_date_eat" in existing_columns and "date" not in existing_columns:
            cursor.execute("ALTER TABLE nursery_results RENAME COLUMN current_date_eat TO date")
        elif "date" not in existing_columns:
            cursor.execute("ALTER TABLE nursery_results ADD COLUMN date TEXT")
        conn.commit()
    finally:
        conn.close()

init_nursery_database()


# --- VIEW RECORDS FOR NURSERY ---
def view_nursery_records_content():
    columns = [
        {'name': 'payment_code', 'label': 'Payment Code', 'field': 'payment_code', 'align': 'left'},
        {'name': 'pupil_name', 'label': 'Pupil Name', 'field': 'pupil_name', 'align': 'left'},
        {'name': 'class_level', 'label': 'Class', 'field': 'class_level', 'align': 'center'},
        {'name': 'term', 'label': 'Term', 'field': 'term', 'align': 'center'},
        {'name': 'age', 'label': 'Age', 'field': 'age', 'align': 'center'},
        {'name': 'color', 'label': 'Color', 'field': 'color', 'align': 'center'},
        {'name': 'days_present', 'label': 'Days Present', 'field': 'days_present', 'align': 'center'},
        {'name': 'days_absent', 'label': 'Days Absent', 'field': 'days_absent', 'align': 'center'},
        {'name': 'date', 'label': 'Date', 'field': 'date', 'align': 'center'},
        {'name': 'listening_speaking_sequencing', 'label': 'Listening / Speaking & Sequencing', 'field': 'listening_speaking_sequencing', 'align': 'center'},
        {'name': 'music_rhymes_dance', 'label': 'Music / Rhymes & Dance', 'field': 'music_rhymes_dance', 'align': 'center'},
        {'name': 'punctuality', 'label': 'Punctuality', 'field': 'punctuality', 'align': 'center'},
        {'name': 'numeracy', 'label': 'Numeracy', 'field': 'numeracy', 'align': 'center'},
        {'name': 'vocabulary', 'label': 'Vocabulary', 'field': 'vocabulary', 'align': 'center'},
        {'name': 'literacy', 'label': 'Literacy', 'field': 'literacy', 'align': 'center'},
        {'name': 'general_science', 'label': 'General Science', 'field': 'general_science', 'align': 'center'},
        {'name': 'environmental_awareness', 'label': 'Environmental Awareness', 'field': 'environmental_awareness', 'align': 'center'},
        {'name': 'writing_skills', 'label': 'Writing Skills', 'field': 'writing_skills', 'align': 'center'},
        {'name': 'physical_education', 'label': 'Physical Education', 'field': 'physical_education', 'align': 'center'},
        {'name': 'gods_creation', 'label': "God's Creation", 'field': 'gods_creation', 'align': 'center'},
        {'name': 'sharing', 'label': 'Sharing', 'field': 'sharing', 'align': 'center'},
        {'name': 'smartness', 'label': 'Smartness', 'field': 'smartness', 'align': 'center'},
        {'name': 'news', 'label': 'News', 'field': 'news', 'align': 'center'},
        {'name': 'stories', 'label': 'Stories', 'field': 'stories', 'align': 'center'},
        {'name': 'life_skills', 'label': 'Life Skills', 'field': 'life_skills', 'align': 'center'},
        {'name': 'general_comment', 'label': 'General Comment', 'field': 'general_comment', 'align': 'left'},
        {'name': 'headteachers_comment', 'label': "Headteacher's Comment", 'field': 'headteachers_comment', 'align': 'left'},
        {'name': 'next_term_begins_on', 'label': 'Next Term Begins On', 'field': 'next_term_begins_on', 'align': 'center'},
        {'name': 'class_teacher', 'label': 'Teacher', 'field': 'class_teacher', 'align': 'left'},
        {'name': 'actions', 'label': 'Actions', 'field': 'actions', 'align': 'center'},
    ]

    content_area = ui.column().classes('w-full')

    def load_data():
        content_area.clear()
        with content_area:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                try:
                    cursor.execute('SELECT * FROM nursery_results ORDER BY id DESC')
                    db_columns = [col[0] for col in cursor.description] if cursor.description else []
                    raw_rows = [dict(zip(db_columns, r)) for r in cursor.fetchall()]
                finally:
                    conn.close()

                if not raw_rows:
                    with ui.card().classes('w-full p-12 items-center bg-white/80 backdrop-blur-md rounded-3xl shadow-sm border border-emerald-100/60'):
                        ui.icon('folder_open', size='3rem', color='emerald')
                        ui.label('No nursery records found.').classes('text-emerald-950 font-semibold mt-2')
                else:
                    nursery_table = (
                        ui.table(columns=columns, rows=raw_rows, row_key='id')
                        .classes('w-full bg-white/90 backdrop-blur-md rounded-3xl shadow-xl border border-emerald-100 overflow-hidden')
                        .props('flat bordered wrap-cells')
                    )
                    nursery_table.add_slot('body-cell-actions', """
                        <q-td :props="props">
                            <q-btn icon="edit" flat dense color="emerald-850" class="hover:bg-emerald-50 rounded-lg" @click="$parent.$emit('edit_nursery', props.row)"></q-btn>
                        </q-td>
                    """)
                    nursery_table.on('edit_nursery', lambda msg: edit_nursery_record(msg.args, load_data))
            except Exception as e:
                ui.label(f'⚠️ Error loading nursery records: {e}').classes('text-red-500 p-4')

    load_data()
    return load_data


# --- EDIT NURSERY RECORD LOGIC ---
def edit_nursery_record(record, on_save):
    with ui.dialog() as dialog, ui.card().classes(
        'w-full max-w-[700px] p-6 md:p-8 bg-gradient-to-br from-emerald-50'
        ' via-teal-50 to-cyan-50 rounded-3xl shadow-2xl border border-emerald-100'
    ):
        with ui.row().classes('items-center gap-3 mb-4'):
            with ui.avatar(color='emerald-700', text_color='white').props('size=md'):
                ui.icon('edit_note', size='1.5rem')
            ui.label(f"Edit Nursery Record: {record.get('pupil_name', '')}").classes(
                'text-xl md:text-2xl font-black text-emerald-950'
            )
        with ui.grid(columns=1).classes('w-full gap-4 md:grid-cols-2'):
            fields = {
                'payment_code': ui.input('Payment Code', value=record.get('payment_code', '')).classes('w-full bg-white/80 rounded-xl'),
                'pupil_name': ui.input('Pupil Name', value=record.get('pupil_name', '')).classes('w-full bg-white/80 rounded-xl'),
                'class_level': ui.input('Class Level', value=record.get('class_level', '')).classes('w-full bg-white/80 rounded-xl'),
                'term': ui.input('Term', value=record.get('term', '')).classes('w-full bg-white/80 rounded-xl'),
                'age': ui.input('Age', value=record.get('age', '')).classes('w-full bg-white/80 rounded-xl'),
                'color': ui.input('Color', value=record.get('color', '')).classes('w-full bg-white/80 rounded-xl'),
                'days_present': ui.input('Days Present', value=record.get('days_present', '')).classes('w-full bg-white/80 rounded-xl'),
                'days_absent': ui.input('Days Absent', value=record.get('days_absent', '')).classes('w-full bg-white/80 rounded-xl'),
                'date': ui.input('Date', value=record.get('date', '')).classes('w-full bg-white/80 rounded-xl'),
                'listening_speaking_sequencing': ui.input('Listening / Speaking & Sequencing', value=record.get('listening_speaking_sequencing', '')).classes('w-full bg-white/80 rounded-xl'),
                'music_rhymes_dance': ui.input('Music / Rhymes & Dance', value=record.get('music_rhymes_dance', '')).classes('w-full bg-white/80 rounded-xl'),
                'punctuality': ui.input('Punctuality', value=record.get('punctuality', '')).classes('w-full bg-white/80 rounded-xl'),
                'numeracy': ui.input('Numeracy', value=record.get('numeracy', '')).classes('w-full bg-white/80 rounded-xl'),
                'vocabulary': ui.input('Vocabulary', value=record.get('vocabulary', '')).classes('w-full bg-white/80 rounded-xl'),
                'literacy': ui.input('Literacy', value=record.get('literacy', '')).classes('w-full bg-white/80 rounded-xl'),
                'general_science': ui.input('General Science', value=record.get('general_science', '')).classes('w-full bg-white/80 rounded-xl'),
                'environmental_awareness': ui.input('Environmental Awareness', value=record.get('environmental_awareness', '')).classes('w-full bg-white/80 rounded-xl'),
                'writing_skills': ui.input('Writing Skills', value=record.get('writing_skills', '')).classes('w-full bg-white/80 rounded-xl'),
                'physical_education': ui.input('Physical Education', value=record.get('physical_education', '')).classes('w-full bg-white/80 rounded-xl'),
                'gods_creation': ui.input("God's Creation", value=record.get('gods_creation', '')).classes('w-full bg-white/80 rounded-xl'),
                'sharing': ui.input('Sharing', value=record.get('sharing', '')).classes('w-full bg-white/80 rounded-xl'),
                'smartness': ui.input('Smartness', value=record.get('smartness', '')).classes('w-full bg-white/80 rounded-xl'),
                'news': ui.input('News', value=record.get('news', '')).classes('w-full bg-white/80 rounded-xl'),
                'stories': ui.input('Stories', value=record.get('stories', '')).classes('w-full bg-white/80 rounded-xl'),
                'life_skills': ui.input('Life Skills', value=record.get('life_skills', '')).classes('w-full bg-white/80 rounded-xl'),
                'general_comment': ui.input('General Comment', value=record.get('general_comment', '')).classes('w-full bg-white/80 rounded-xl'),
                'headteachers_comment': ui.input("Headteacher's Comment", value=record.get('headteachers_comment', '')).classes('w-full bg-white/80 rounded-xl'),
                'next_term_begins_on': ui.input('Next Term Begins On', value=record.get('next_term_begins_on', '')).classes('w-full bg-white/80 rounded-xl'),
                'class_teacher': ui.input('Teacher', value=record.get('class_teacher', '')).classes('w-full bg-white/80 rounded-xl'),
            }

        def save():
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                try:
                    cursor.execute(
                        '''UPDATE nursery_results SET
                                payment_code=?, pupil_name=?, class_level=?, term=?,
                                age=?, color=?, days_present=?, days_absent=?, date=?,
                                listening_speaking_sequencing=?, music_rhymes_dance=?, punctuality=?,
                                numeracy=?, vocabulary=?, literacy=?, general_science=?,
                                environmental_awareness=?, writing_skills=?, physical_education=?,
                                gods_creation=?, sharing=?, smartness=?, news=?, stories=?,
                                life_skills=?, general_comment=?, headteachers_comment=?,
                                next_term_begins_on=?, class_teacher=? WHERE id=?''',
                        (
                            fields['payment_code'].value,
                            fields['pupil_name'].value,
                            fields['class_level'].value,
                            fields['term'].value,
                            fields['age'].value,
                            fields['color'].value,
                            fields['days_present'].value,
                            fields['days_absent'].value,
                            fields['date'].value,
                            fields['listening_speaking_sequencing'].value,
                            fields['music_rhymes_dance'].value,
                            fields['punctuality'].value,
                            fields['numeracy'].value,
                            fields['vocabulary'].value,
                            fields['literacy'].value,
                            fields['general_science'].value,
                            fields['environmental_awareness'].value,
                            fields['writing_skills'].value,
                            fields['physical_education'].value,
                            fields['gods_creation'].value,
                            fields['sharing'].value,
                            fields['smartness'].value,
                            fields['news'].value,
                            fields['stories'].value,
                            fields['life_skills'].value,
                            fields['general_comment'].value,
                            fields['headteachers_comment'].value,
                            fields['next_term_begins_on'].value,
                            fields['class_teacher'].value,
                            record['id'],
                        ),
                    )
                    conn.commit()
                finally:
                    conn.close()
                ui.notify('✨ Nursery record updated successfully!', color='positive', icon='check_circle')
                dialog.close()
                on_save()
            except Exception as e:
                ui.notify(f'Update failed: {e}', type='negative')

        ui.button('Save Changes', on_click=save).classes(
            'w-full mt-6 bg-gradient-to-r from-emerald-600 to-teal-700 text-white'
            ' font-extrabold py-3.5 rounded-2xl hover:from-emerald-700'
            ' hover:to-teal-800 transition-all shadow-lg shadow-emerald-700/20'
        )
    dialog.open()


# --- 1. DYNAMIC ANALYTICS LOGIC ---
def get_dashboard_metrics():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT * FROM academic_records')
            db_columns = [col[0] for col in cursor.description] if cursor.description else []
            rows = [dict(zip(db_columns, r)) for r in cursor.fetchall()]
        finally:
            conn.close()

        if not rows:
            return None
        maths = [r['Maths'] for r in rows if r['Maths'] is not None]
        eng = [r['English'] for r in rows if r['English'] is not None]
        sst = [r['SST'] for r in rows if r['SST'] is not None]
        sci = [r['Science'] for r in rows if r['Science'] is not None]
        subs = {
            'Maths': sum(maths) / len(maths) if maths else 0,
            'English': sum(eng) / len(eng) if eng else 0,
            'SST': sum(sst) / len(sst) if sst else 0,
            'Science': sum(sci) / len(sci) if sci else 0,
        }
        best_sub = max(subs, key=subs.get)
        worst_sub = min(subs, key=subs.get)
        all_avgs = [r['Average'] for r in rows if r['Average']]
        class_avg = sum(all_avgs) / len(all_avgs) if all_avgs else 0
        rising_stars = [r for r in rows if r['Average'] > class_avg and r['Average'] > 60]
        at_risk = sorted([r for r in rows if (r['Average'] or 0) < 50], key=lambda x: x['Average'] or 0)
        return {
            'best': best_sub,
            'worst': worst_sub,
            'at_risk': at_risk,
            'rising': rising_stars[:3],
        }
    except Exception:
        return None


# --- 1.1 PER-CLASS PERFORMANCE ANALYTICS LOGIC ---
def get_class_analytics(selected_class, level_type):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            if level_type == 'Upper Primary':
                query = 'SELECT * FROM academic_records WHERE Class = ?'
                cursor.execute(query, (selected_class,))
                db_columns = [col[0] for col in cursor.description] if cursor.description else []
                rows = [dict(zip(db_columns, r)) for r in cursor.fetchall()]
                if not rows:
                    return None
                maths = [r['Maths'] for r in rows if r['Maths'] is not None]
                eng = [r['English'] for r in rows if r['English'] is not None]
                sst = [r['SST'] for r in rows if r['SST'] is not None]
                sci = [r['Science'] for r in rows if r['Science'] is not None]
                subs = {
                    'Maths': sum(maths) / len(maths) if maths else 0,
                    'English': sum(eng) / len(eng) if eng else 0,
                    'SST': sum(sst) / len(sst) if sst else 0,
                    'Science': sum(sci) / len(sci) if sci else 0,
                }
                best_sub = max(subs, key=subs.get) if subs else 'N/A'
                worst_sub = min(subs, key=subs.get) if subs else 'N/A'
                all_avgs = [r['Average'] for r in rows if r.get('Average') is not None]
                class_avg = sum(all_avgs) / len(all_avgs) if all_avgs else 0
                sorted_rows = sorted(rows, key=lambda x: x.get('Average') or 0, reverse=True)
                top_students = sorted_rows[:3]
                at_risk = sorted([r for r in rows if (r.get('Average') or 0) < 50], key=lambda x: x.get('Average') or 0)
                return {
                    'total_students': len(rows),
                    'class_avg': round(class_avg, 1),
                    'best_sub': f"{best_sub} ({round(subs[best_sub], 1)}%)" if subs else 'N/A',
                    'worst_sub': f"{worst_sub} ({round(subs[worst_sub], 1)}%)" if subs else 'N/A',
                    'top_students': top_students,
                    'at_risk': at_risk,
                }
            else:
                query = 'SELECT * FROM lower_primary_results WHERE class_level = ?'
                cursor.execute(query, (selected_class,))
                db_columns = [col[0] for col in cursor.description] if cursor.description else []
                rows = [dict(zip(db_columns, r)) for r in cursor.fetchall()]
                if not rows:
                    return None
                subject_keys = ['literacy_i', 'literacy_ii', 'reading', 'luganda', 'mathematics', 'english', 'social_studies', 'science', 're_religious_education']
                sub_totals = {}
                sub_counts = {}
                for r in rows:
                    for sk in subject_keys:
                        val = r.get(sk)
                        if val is not None:
                            sub_totals[sk] = sub_totals.get(sk, 0) + val
                            sub_counts[sk] = sub_counts.get(sk, 0) + 1
                subs_avg = {sk: (sub_totals[sk] / sub_counts[sk]) for sk in sub_totals if sub_counts[sk] > 0}
                best_sub = max(subs_avg, key=subs_avg.get) if subs_avg else 'N/A'
                worst_sub = min(subs_avg, key=subs_avg.get) if subs_avg else 'N/A'
                processed = []
                for r in rows:
                    scores = [r.get(sk) for sk in subject_keys if r.get(sk) is not None]
                    tot = sum(scores)
                    avg = tot / len(scores) if scores else 0
                    r['_calc_total'] = tot
                    r['_calc_avg'] = avg
                    processed.append(r)
                all_avgs = [p['_calc_avg'] for p in processed]
                class_avg = sum(all_avgs) / len(all_avgs) if all_avgs else 0
                sorted_processed = sorted(processed, key=lambda x: x['_calc_total'], reverse=True)
                top_students = sorted_processed[:3]
                at_risk = sorted([p for p in processed if p['_calc_avg'] < 50], key=lambda x: x['_calc_avg'])
                readable_names = {
                    'literacy_i': 'Lit I', 'literacy_ii': 'Lit II', 'reading': 'Reading',
                    'luganda': 'Luganda', 'mathematics': 'Maths', 'english': 'English',
                    'social_studies': 'S.S.T', 'science': 'Science', 're_religious_education': 'R.E',
                }
                return {
                    'total_students': len(rows),
                    'class_avg': round(class_avg, 1),
                    'best_sub': f"{readable_names.get(best_sub, best_sub)} ({round(subs_avg.get(best_sub, 0), 1)}%)" if best_sub != 'N/A' else 'N/A',
                    'worst_sub': f"{readable_names.get(worst_sub, worst_sub)} ({round(subs_avg.get(worst_sub, 0), 1)}%)" if worst_sub != 'N/A' else 'N/A',
                    'top_students': top_students,
                    'at_risk': at_risk,
                }
        finally:
            conn.close()
    except Exception as e:
        print(f'Analytics error: {e}')
        return None


# --- 2. EDIT RECORD LOGIC ---
def edit_record(record, on_save):
    with ui.dialog() as dialog, ui.card().classes(
        'w-full max-w-[700px] p-6 md:p-8 bg-gradient-to-br from-emerald-50'
        ' via-teal-50 to-cyan-50 rounded-3xl shadow-2xl border border-emerald-100'
    ):
        with ui.row().classes('items-center gap-3 mb-4'):
            with ui.avatar(color='emerald-700', text_color='white').props('size=md'):
                ui.icon('edit_note', size='1.5rem')
            ui.label(f"Edit Record: {record['Name']}").classes('text-xl md:text-2xl font-black text-emerald-950')
        with ui.grid(columns=1).classes('w-full gap-4 md:grid-cols-2'):
            fields = {
                'Name': ui.input('Name', value=record['Name']).classes('w-full bg-white/80 rounded-xl'),
                'Admin': ui.input('Admin', value=record['Admin']).classes('w-full bg-white/80 rounded-xl'),
                'Class': ui.input('Class', value=record['Class']).classes('w-full bg-white/80 rounded-xl'),
                'Maths': ui.number('Maths', value=record['Maths']).classes('w-full bg-white/80 rounded-xl'),
                'English': ui.number('English', value=record['English']).classes('w-full bg-white/80 rounded-xl'),
                'SST': ui.number('SST', value=record['SST']).classes('w-full bg-white/80 rounded-xl'),
                'Science': ui.number('Science', value=record['Science']).classes('w-full bg-white/80 rounded-xl'),
                'Remarks': ui.input('Remarks', value=record['Remarks']).classes('w-full bg-white/80 rounded-xl'),
            }

        def save():
            maths_val = float(fields['Maths'].value or 0)
            eng_val = float(fields['English'].value or 0)
            sst_val = float(fields['SST'].value or 0)
            sci_val = float(fields['Science'].value or 0)
            new_total = maths_val + eng_val + sst_val + sci_val
            new_avg = new_total / 4.0
            if new_avg >= 80: new_grade = 'Division 1'
            elif new_avg >= 60: new_grade = 'Division 2'
            elif new_avg >= 50: new_grade = 'Division 3'
            elif new_avg >= 40: new_grade = 'Division 4'
            else: new_grade = 'Division U'
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                try:
                    cursor.execute(
                        '''UPDATE academic_records SET
                                Name=?, Admin=?, Class=?, Maths=?, English=?,
                                SST=?, Science=?, Total=?, Grade=?, Remarks=? WHERE id=?''',
                        (
                            fields['Name'].value, fields['Admin'].value, fields['Class'].value,
                            maths_val, eng_val, sst_val, sci_val, new_total, new_grade,
                            fields['Remarks'].value, record['id'],
                        ),
                    )
                    conn.commit()
                finally:
                    conn.close()
                ui.notify('✨ Record and automatic totals/grades updated successfully!', color='positive', icon='check_circle')
                dialog.close()
                on_save()
            except Exception as e:
                ui.notify(f'Update failed: {e}', type='negative')

        ui.button('Save Changes', on_click=save).classes(
            'w-full mt-6 bg-gradient-to-r from-emerald-600 to-teal-700 text-white'
            ' font-extrabold py-3.5 rounded-2xl hover:from-emerald-700'
            ' hover:to-teal-800 transition-all shadow-lg shadow-emerald-700/20'
        )
    dialog.open()


# --- EDIT LOWER PRIMARY RECORD LOGIC ---
def edit_lower_record(record, on_save):
    with ui.dialog() as dialog, ui.card().classes(
        'w-full max-w-[700px] p-6 md:p-8 bg-gradient-to-br from-emerald-50'
        ' via-teal-50 to-cyan-50 rounded-3xl shadow-2xl border border-emerald-100'
    ):
        with ui.row().classes('items-center gap-3 mb-4'):
            with ui.avatar(color='emerald-700', text_color='white').props('size=md'):
                ui.icon('edit_note', size='1.5rem')
            ui.label(f"Edit Lower Primary: {record['pupil_name']}").classes('text-xl md:text-2xl font-black text-emerald-950')
        with ui.grid(columns=1).classes('w-full gap-4 md:grid-cols-2'):
            fields = {
                'payment_code': ui.input('Payment Code', value=record.get('payment_code', '')).classes('w-full bg-white/80 rounded-xl'),
                'pupil_name': ui.input('Pupil Name', value=record['pupil_name']).classes('w-full bg-white/80 rounded-xl'),
                'class_level': ui.input('Class', value=record['class_level']).classes('w-full bg-white/80 rounded-xl'),
                'term': ui.input('Term', value=record['term']).classes('w-full bg-white/80 rounded-xl'),
                'literacy_i': ui.number('Lit I', value=record['literacy_i']).classes('w-full bg-white/80 rounded-xl'),
                'literacy_ii': ui.number('Lit II', value=record['literacy_ii']).classes('w-full bg-white/80 rounded-xl'),
                'reading': ui.number('Reading', value=record['reading']).classes('w-full bg-white/80 rounded-xl'),
                'luganda': ui.number('Luganda', value=record['luganda']).classes('w-full bg-white/80 rounded-xl'),
                'mathematics': ui.number('Maths', value=record['mathematics']).classes('w-full bg-white/80 rounded-xl'),
                'english': ui.number('English', value=record['english']).classes('w-full bg-white/80 rounded-xl'),
                'social_studies': ui.number('S.S.T', value=record['social_studies']).classes('w-full bg-white/80 rounded-xl'),
                'science': ui.number('Science', value=record['science']).classes('w-full bg-white/80 rounded-xl'),
                're_religious_education': ui.number('R.E', value=record['re_religious_education']).classes('w-full bg-white/80 rounded-xl'),
                'class_teacher': ui.input('Teacher', value=record['class_teacher']).classes('w-full bg-white/80 rounded-xl'),
            }

        def save():
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                try:
                    cursor.execute(
                        '''UPDATE lower_primary_results SET
                                payment_code=?, pupil_name=?, class_level=?, term=?, literacy_i=?, literacy_ii=?,
                                reading=?, luganda=?, mathematics=?, english=?, social_studies=?,
                                science=?, re_religious_education=?, class_teacher=? WHERE id=?''',
                        (
                            fields['payment_code'].value, fields['pupil_name'].value,
                            fields['class_level'].value, fields['term'].value,
                            fields['literacy_i'].value, fields['literacy_ii'].value,
                            fields['reading'].value, fields['luganda'].value,
                            fields['mathematics'].value, fields['english'].value,
                            fields['social_studies'].value, fields['science'].value,
                            fields['re_religious_education'].value, fields['class_teacher'].value,
                            record['id'],
                        ),
                    )
                    conn.commit()
                finally:
                    conn.close()
                ui.notify('✨ Lower primary record updated successfully!', color='positive', icon='check_circle')
                dialog.close()
                on_save()
            except Exception as e:
                ui.notify(f'Update failed: {e}', type='negative')

        ui.button('Save Changes', on_click=save).classes(
            'w-full mt-6 bg-gradient-to-r from-emerald-600 to-teal-700 text-white'
            ' font-extrabold py-3.5 rounded-2xl hover:from-emerald-700'
            ' hover:to-teal-800 transition-all shadow-lg shadow-emerald-700/20'
        )
    dialog.open()


# --- HELPER FUNCTIONS FOR LOWER PRIMARY CALCULATIONS ---
def compute_lower_derived_fields(rows):
    classes = {}
    for r in rows:
        c_level = r.get('class_level') or 'Unknown'
        classes.setdefault(c_level, []).append(r)
    processed_rows = []
    for c_level, group in classes.items():
        for r in group:
            scores = [
                r.get('literacy_i'), r.get('literacy_ii'), r.get('reading'),
                r.get('luganda'), r.get('mathematics'), r.get('english'),
                r.get('social_studies'), r.get('science'), r.get('re_religious_education'),
            ]
            valid_scores = [s for s in scores if s is not None]
            total = sum(valid_scores)
            r['_calc_total'] = total
            avg = total / len(valid_scores) if valid_scores else 0
            if avg >= 80: grade = '1'
            elif avg >= 60: grade = '2'
            elif avg >= 50: grade = '3'
            elif avg >= 40: grade = '4'
            else: grade = '7'
            r['_calc_grade'] = grade
        group_sorted = sorted(group, key=lambda x: x['_calc_total'], reverse=True)
        for index, r in enumerate(group_sorted, start=1):
            r['_calc_rank'] = index
            processed_rows.append(r)
    return processed_rows


# --- HELPER FUNCTIONS FOR UPPER PRIMARY CALCULATIONS ---
def compute_upper_ranks(rows):
    classes = {}
    for r in rows:
        c_level = r.get('Class') or 'Unknown'
        classes.setdefault(c_level, []).append(r)
    processed_rows = []
    for c_level, group in classes.items():
        group_sorted = sorted(group, key=lambda x: x.get('Total') or 0, reverse=True)
        for index, r in enumerate(group_sorted, start=1):
            r['_calc_rank'] = index
            processed_rows.append(r)
    return processed_rows


# --- VIEW RECORDS FOR LOWER PRIMARY ---
def view_lower_records_content():
    columns = [
        {'name': 'payment_code', 'label': 'Payment Code', 'field': 'payment_code', 'align': 'left'},
        {'name': 'pupil_name', 'label': 'Pupil Name', 'field': 'pupil_name', 'align': 'left'},
        {'name': 'class_level', 'label': 'Class', 'field': 'class_level', 'align': 'center'},
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
        {'name': '_calc_total', 'label': 'Total', 'field': '_calc_total', 'align': 'center'},
        {'name': '_calc_grade', 'label': 'Grade', 'field': '_calc_grade', 'align': 'center'},
        {'name': '_calc_rank', 'label': 'Rank', 'field': '_calc_rank', 'align': 'center'},
        {'name': 'class_teacher', 'label': 'Teacher', 'field': 'class_teacher', 'align': 'left'},
        {'name': 'actions', 'label': 'Actions', 'field': 'actions', 'align': 'center'},
    ]
    content_area = ui.column().classes('w-full')

    def load_data():
        content_area.clear()
        with content_area:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                try:
                    cursor.execute('SELECT * FROM lower_primary_results ORDER BY id DESC')
                    db_columns = [col[0] for col in cursor.description] if cursor.description else []
                    raw_rows = [dict(zip(db_columns, r)) for r in cursor.fetchall()]
                finally:
                    conn.close()

                if not raw_rows:
                    with ui.card().classes('w-full p-12 items-center bg-white/80 backdrop-blur-md rounded-3xl shadow-sm border border-emerald-100/60'):
                        ui.icon('folder_open', size='3rem', color='emerald')
                        ui.label('No lower primary records found.').classes('text-emerald-950 font-semibold mt-2')
                else:
                    all_rows = compute_lower_derived_fields(raw_rows)
                    lower_table = (
                        ui.table(columns=columns, rows=all_rows, row_key='id')
                        .classes('w-full bg-white/90 backdrop-blur-md rounded-3xl shadow-xl border border-emerald-100 overflow-hidden')
                        .props('flat bordered wrap-cells')
                    )
                    lower_table.add_slot('body-cell-actions', """
                        <q-td :props="props">
                            <q-btn icon="edit" flat dense color="emerald-850" class="hover:bg-emerald-50 rounded-lg" @click="$parent.$emit('edit_lower', props.row)"></q-btn>
                        </q-td>
                    """)
                    lower_table.on('edit_lower', lambda msg: edit_lower_record(msg.args, load_data))
            except Exception as e:
                ui.label(f'⚠️ Error loading records: {e}').classes('text-red-500 p-4')

    load_data()


# --- 3. VIEW RECORDS TAB for upper primary ---
def view_records_content():
    columns = [
        {'name': 'Name', 'label': 'Name', 'field': 'Name', 'align': 'left'},
        {'name': 'Admin', 'label': 'Admin', 'field': 'Admin', 'align': 'center'},
        {'name': 'Class', 'label': 'Class', 'field': 'Class', 'align': 'center'},
        {'name': 'Maths', 'label': 'Maths', 'field': 'Maths', 'align': 'center'},
        {'name': 'English', 'label': 'English', 'field': 'English', 'align': 'center'},
        {'name': 'SST', 'label': 'SST', 'field': 'SST', 'align': 'center'},
        {'name': 'Science', 'label': 'Science', 'field': 'Science', 'align': 'center'},
        {'name': 'Total', 'label': 'Total', 'field': 'Total', 'align': 'center'},
        {'name': 'Grade', 'label': 'Grade', 'field': 'Grade', 'align': 'center'},
        {'name': '_calc_rank', 'label': 'Rank', 'field': '_calc_rank', 'align': 'center'},
        {'name': 'Remarks', 'label': 'Remarks', 'field': 'Remarks', 'align': 'left'},
        {'name': 'actions', 'label': 'Actions', 'field': 'actions', 'align': 'center'},
    ]
    content_area = ui.column().classes('w-full')

    def load_data():
        content_area.clear()
        with content_area:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                try:
                    cursor.execute('SELECT * FROM academic_records')
                    db_columns = [col[0] for col in cursor.description] if cursor.description else []
                    raw_rows = [dict(zip(db_columns, r)) for r in cursor.fetchall()]
                finally:
                    conn.close()

                if not raw_rows:
                    with ui.card().classes('w-full p-12 items-center bg-white/80 backdrop-blur-md rounded-3xl shadow-sm border border-emerald-100/60'):
                        ui.icon('folder_open', size='3rem', color='emerald')
                        ui.label('No upper primary records found.').classes('text-emerald-950 font-semibold mt-2')
                else:
                    all_rows = compute_upper_ranks(raw_rows)
                    student_table = (
                        ui.table(columns=columns, rows=all_rows, row_key='id')
                        .classes('w-full bg-white/90 backdrop-blur-md rounded-3xl shadow-xl border border-emerald-100 overflow-hidden')
                        .props('flat bordered wrap-cells')
                    )
                    student_table.add_slot('body-cell-actions', """
                        <q-td :props="props">
                            <q-btn icon="edit" flat dense color="emerald-850" class="hover:bg-emerald-50 rounded-lg" @click="$parent.$emit('edit', props.row)"></q-btn>
                        </q-td>
                    """)
                    student_table.on('edit', lambda msg: edit_record(msg.args, load_data))
            except Exception as e:
                ui.label(f'Error: {e}').classes('text-red-500 p-4')

    load_data()


# --- 3.1 PERFORMANCE ANALYTICS HUB CONTENT ---
def performance_analytics_hub_content():
    content_container = ui.column().classes('w-full gap-6')
    with content_container:
        with ui.row().classes('items-center gap-3'):
            with ui.avatar(color='emerald-700', text_color='white', size='md').classes('shadow-md shadow-emerald-700/20'):
                ui.icon('insights', size='1.5rem')
            with ui.column().classes('gap-0'):
                ui.label('Per-Class Performance Hub').classes('text-2xl font-black text-emerald-950')
                ui.label('Select a section and class to view isolated performance metrics, top achievers, and intervention lists.').classes('text-xs text-emerald-800/80 font-medium')

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            try:
                cursor.execute('SELECT DISTINCT Class FROM academic_records WHERE Class IS NOT NULL')
                upper_classes = [r[0] for r in cursor.fetchall()]
                cursor.execute('SELECT DISTINCT class_level FROM lower_primary_results WHERE class_level IS NOT NULL')
                lower_classes = [r[0] for r in cursor.fetchall()]
            finally:
                conn.close()
        except Exception:
            upper_classes = []
            lower_classes = []

        all_options = []
        if upper_classes:
            all_options.extend([f'Upper Primary: {c}' for c in upper_classes])
        if lower_classes:
            all_options.extend([f'Lower Primary: {c}' for c in lower_classes])
        if not all_options:
            all_options = ['No Classes Found']

        selected_dropdown = ui.select(label='Select Class Level', options=all_options, value=all_options[0]).classes('w-full md:w-96 bg-white/90 backdrop-blur-md rounded-2xl shadow-sm border border-emerald-100')
        metrics_display_area = ui.column().classes('w-full gap-6 mt-4')

        def update_analytics_view():
            metrics_display_area.clear()
            val = selected_dropdown.value
            if not val or 'No Classes Found' in val:
                with metrics_display_area:
                    with ui.card().classes('w-full p-8 items-center bg-white/80 rounded-3xl shadow-sm border border-emerald-100'):
                        ui.label('No classes available for analysis.').classes('text-emerald-950 font-medium')
                return
            parts = val.split(': ')
            level_type = parts[0].strip()
            class_name = parts[1].strip()
            data = get_class_analytics(class_name, level_type)
            with metrics_display_area:
                if not data:
                    with ui.card().classes('w-full p-10 items-center bg-white/90 rounded-3xl shadow-sm border border-emerald-100'):
                        ui.icon('info', size='2.5rem', color='emerald')
                        ui.label(f'No student records found for {class_name}.').classes('text-emerald-950 font-semibold mt-2')
                    return
                with ui.row().classes('w-full gap-4 flex-col md:flex-row'):
                    with ui.card().classes('flex-1 p-6 bg-gradient-to-br from-emerald-600 to-teal-800 text-white rounded-3xl shadow-lg shadow-emerald-800/20 relative overflow-hidden'):
                        ui.icon('groups', size='2.5rem').classes('absolute right-4 bottom-4 opacity-15')
                        ui.label('Total Enrolled').classes('text-xs font-bold text-emerald-200 uppercase tracking-wider')
                        ui.label(str(data['total_students'])).classes('text-3xl font-black mt-1')
                    with ui.card().classes('flex-1 p-6 bg-gradient-to-br from-teal-600 to-cyan-800 text-white rounded-3xl shadow-lg shadow-teal-800/20 relative overflow-hidden'):
                        ui.icon('percent', size='2.5rem').classes('absolute right-4 bottom-4 opacity-15')
                        ui.label('Class Average Score').classes('text-xs font-bold text-teal-200 uppercase tracking-wider')
                        ui.label(f"{data['class_avg']}%").classes('text-3xl font-black mt-1 font-mono')
                    with ui.card().classes('flex-1 p-6 bg-gradient-to-br from-green-600 to-emerald-700 text-white rounded-3xl shadow-lg shadow-green-700/20 relative overflow-hidden'):
                        ui.icon('trending_up', size='2.5rem').classes('absolute right-4 bottom-4 opacity-15')
                        ui.label('Best Subject').classes('text-xs font-bold text-green-200 uppercase tracking-wider')
                        ui.label(data['best_sub']).classes('text-lg font-bold mt-1 truncate')
                    with ui.card().classes('flex-1 p-6 bg-gradient-to-br from-amber-600 to-orange-700 text-white rounded-3xl shadow-lg shadow-amber-700/20 relative overflow-hidden'):
                        ui.icon('trending_down', size='2.5rem').classes('absolute right-4 bottom-4 opacity-15')
                        ui.label('Weakest Subject').classes('text-xs font-bold text-amber-200 uppercase tracking-wider')
                        ui.label(data['worst_sub']).classes('text-lg font-bold mt-1 truncate')
                with ui.row().classes('w-full gap-6 mt-2 flex-col md:flex-row'):
                    with ui.card().classes('flex-1 p-6 bg-gradient-to-br from-emerald-50 via-teal-50/50 to-white border border-emerald-200/80 rounded-3xl shadow-xl'):
                        with ui.row().classes('items-center gap-3 mb-4'):
                            with ui.avatar(color='emerald-700', text_color='white', size='sm').classes('shadow-sm'):
                                ui.icon('workspace_premium', size='1.2rem')
                            ui.label(f'Top Achievers — {class_name}').classes('text-md font-black text-emerald-950')
                        if not data['top_students']:
                            ui.label('No students recorded.').classes('text-xs text-stone-400 italic')
                        else:
                            for idx, s in enumerate(data['top_students'], 1):
                                name = s.get('Name') or s.get('pupil_name') or 'Unknown'
                                score = s.get('Average') or s.get('_calc_avg') or 0
                                badge_colors = (
                                    'bg-amber-400 text-amber-950 font-black' if idx == 1
                                    else ('bg-stone-300 text-stone-900 font-bold' if idx == 2 else 'bg-amber-700 text-white font-bold')
                                )
                                with ui.row().classes('w-full justify-between py-2.5 px-3 bg-white/80 rounded-2xl my-1.5 items-center border border-emerald-100 shadow-sm'):
                                    with ui.row().classes('items-center gap-3'):
                                        ui.badge(str(idx)).classes(f'{badge_colors} px-2 py-0.5 rounded-full text-xs')
                                        ui.label(name).classes('font-bold text-sm text-emerald-950')
                                    ui.label(f'{round(score, 1)}%').classes('font-mono font-black text-sm text-emerald-700')
                    with ui.card().classes('flex-1 p-6 bg-gradient-to-br from-amber-50 via-orange-50/50 to-white border border-amber-200/80 rounded-3xl shadow-xl'):
                        with ui.row().classes('items-center gap-3 mb-4'):
                            with ui.avatar(color='amber-700', text_color='white', size='sm').classes('shadow-sm'):
                                ui.icon('warning', size='1.2rem')
                            ui.label(f'Academic Intervention — {class_name}').classes('text-md font-black text-amber-950')
                        if not data['at_risk']:
                            with ui.row().classes('w-full p-4 bg-white/80 rounded-2xl items-center gap-2 border border-amber-100'):
                                ui.icon('check_circle', color='green', size='1.2rem')
                                ui.label('No students require urgent intervention.').classes('text-xs font-semibold text-emerald-800')
                        else:
                            for s in data['at_risk']:
                                name = s.get('Name') or s.get('pupil_name') or 'Unknown'
                                score = s.get('Average') or s.get('_calc_avg') or 0
                                with ui.row().classes('w-full justify-between py-2.5 px-3 bg-white/80 rounded-2xl my-1.5 items-center border border-amber-100 shadow-sm'):
                                    ui.label(name).classes('font-bold text-sm text-stone-900')
                                    ui.badge(f'{round(score, 1)}%').classes('bg-amber-100 text-amber-900 font-mono font-bold')

        selected_dropdown.on('update:model-value', lambda: update_analytics_view())
        update_analytics_view()


# --- 3.2 STAFF CHAT ROOM CONTENT ---
def staff_chat_content():
    chat_container = ui.column().classes(
        'w-full h-[400px] md:h-[450px] overflow-y-auto p-4 bg-gradient-to-b'
        ' from-stone-50 to-emerald-50/30 rounded-3xl shadow-inner border'
        ' border-emerald-100 gap-3'
    )
    room_vibes = [
        '☕ Staff Common Room: 90% Chai, 10% Grading Panic',
        '📢 Staff Common Room: Whoever left their red pen owes everyone mandazi.',
        '🔥 Staff Common Room: Where lesson plans go to get judged.',
        '👀 Staff Common Room: Quiet down, the Deputy Head might be lurking.',
    ]
    current_vibe = random.choice(room_vibes)

    def delete_message(msg_id):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            try:
                cursor.execute('DELETE FROM staff_chat WHERE id = ?', (msg_id,))
                conn.commit()
            finally:
                conn.close()
            ui.notify('🗑️ Message deleted successfully', color='warning')
            load_messages()
        except Exception as e:
            ui.notify(f'Failed to delete message: {e}', color='negative')

    def load_messages():
        chat_container.clear()
        with chat_container:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                try:
                    cursor.execute('SELECT * FROM staff_chat ORDER BY id ASC')
                    db_columns = [col[0] for col in cursor.description] if cursor.description else []
                    rows = [dict(zip(db_columns, r)) for r in cursor.fetchall()]
                finally:
                    conn.close()

                if not rows:
                    with ui.column().classes('w-full items-center justify-center my-16 gap-2'):
                        with ui.avatar(color='emerald-100', text_color='emerald-800', size='lg'):
                            ui.icon('local_cafe', size='1.8rem')
                        ui.label('The kettle is boiling, but nobody has spoken yet!').classes('text-emerald-950 text-sm font-bold mt-2')
                        ui.label('Drop a complaint about the printer or start the morning gossip.').classes('text-emerald-800/70 text-xs italic')
                else:
                    current_user = app.storage.user.get('username', 'Teacher')
                    for r in rows:
                        msg_id = r['id']
                        sender = r['sender']
                        is_me = sender == current_user
                        align_cls = 'items-end' if is_me else 'items-start'
                        bubble_bg = (
                            'bg-gradient-to-r from-emerald-700 to-teal-800 text-white rounded-tr-sm shadow-md shadow-emerald-700/10'
                            if is_me
                            else 'bg-white text-stone-800 rounded-tl-sm border border-emerald-100 shadow-sm'
                        )
                        with ui.column().classes(f'w-full {align_cls} gap-0.5 my-1.5'):
                            with ui.row().classes('items-center gap-2 px-1'):
                                if not is_me:
                                    ui.label(sender).classes('text-[11px] font-bold text-emerald-800')
                                if is_me:
                                    ui.button(icon='delete_outline', on_click=lambda mid=msg_id: delete_message(mid)).props('flat dense').classes('text-stone-400 hover:text-red-600 text-[10px] p-0 min-h-0 min-w-0')
                            with ui.card().classes(f'{bubble_bg} p-3.5 rounded-2xl max-w-[85%] md:max-w-[75%]'):
                                ui.label(r['message']).classes('text-sm whitespace-pre-wrap leading-relaxed break-words')
                                with ui.row().classes('w-full justify-end items-center gap-1 mt-1'):
                                    ui.label(r['timestamp']).classes('text-[9px] text-emerald-200' if is_me else 'text-stone-400')
                                    if is_me:
                                        ui.icon('done_all', size='12px', color='emerald-200')
            except Exception as e:
                ui.label(f'⚠️ Printer jam in chat: {e}').classes('text-red-500 text-xs')

    with ui.column().classes('w-full max-w-3xl mx-auto bg-white/90 backdrop-blur-md rounded-3xl shadow-xl border border-emerald-100 overflow-hidden'):
        with ui.row().classes('items-center justify-between w-full bg-gradient-to-r from-emerald-800 via-teal-800 to-cyan-900 px-5 py-4 text-white border-b border-emerald-950'):
            with ui.row().classes('items-center gap-3'):
                with ui.avatar(size='md').classes('bg-white/20 text-white font-extrabold shadow-sm backdrop-blur-sm'):
                    ui.icon('forum', size='1.2rem')
                with ui.column().classes('gap-0'):
                    ui.label('Staff Common Room').classes('text-base font-black text-white')
                    ui.label(current_vibe).classes('text-[11px] text-emerald-200 font-medium')
            with ui.row().classes('items-center gap-1'):
                ui.badge('Live Sync', color='emerald-700').props('dense').classes('text-[10px] text-white font-bold')
                ui.timer(3.0, load_messages)
                ui.button(icon='refresh', on_click=load_messages).props('flat round dense').classes('text-white hover:text-emerald-200')
        load_messages()
        quick_emojis = ['😂', '💀', '🔥', '👀', '☕', '📉', '💯', '🙏', '⚠️', '🤷‍♂️', '🤦‍♀️', '🍎', '📝', '📢']
        with ui.row().classes('w-full gap-1 items-center px-4 py-2 bg-emerald-50/50 border-t border-emerald-100 overflow-x-auto'):
            ui.label('Vibe Check:').classes('text-[10px] text-emerald-800 font-black uppercase mr-1 shrink-0')
            for emo in quick_emojis:
                def insert_emoji(e=emo):
                    msg_input.value = (msg_input.value or '') + e
                    msg_input.update()
                ui.button(emo, on_click=insert_emoji).props('flat dense').classes('text-sm bg-white border border-emerald-200 rounded-xl px-2 py-0.5 text-stone-700 hover:bg-emerald-100 shrink-0 shadow-sm')
        with ui.row().classes('w-full items-center gap-2 p-3.5 bg-white border-t border-emerald-100'):
            msg_input = (
                ui.input(placeholder='Say something before the bell rings...')
                .classes('flex-1 bg-stone-100 text-stone-900 rounded-2xl px-4 border-none')
                .props('borderless dense')
            )

            def send_message():
                text = msg_input.value.strip()
                if not text:
                    return
                sender = app.storage.user.get('username', 'Teacher')
                timestamp = datetime.now().strftime('%H:%M')
                try:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    try:
                        cursor.execute(
                            'INSERT INTO staff_chat (sender, message, timestamp) VALUES (?, ?, ?)',
                            (sender, text, timestamp),
                        )
                        conn.commit()
                    finally:
                        conn.close()
                    msg_input.value = ''
                    load_messages()
                except Exception as e:
                    ui.notify(f'Failed to broadcast gossip: {e}', color='negative')

            msg_input.on('keydown.enter', send_message)
            ui.button(icon='send', on_click=send_message).classes(
                'bg-gradient-to-r from-emerald-600 to-teal-700 text-white rounded-2xl'
                ' p-2 h-10 w-10 shadow-md shadow-emerald-700/20'
                ' hover:from-emerald-700 hover:to-teal-800 transition-all'
            )


# --- 4. STAFF HOME ---
def teacher():
    if not app.storage.user.get('logged_in'):
        ui.run_javascript('window.location.replace("/login")')
        return
    IDLE_TIMEOUT_SECONDS = 900
    last_activity_time = [datetime.now()]

    def reset_timer(e=None):
        last_activity_time[0] = datetime.now()

    ui.on('mousemove', reset_timer, throttle=5.0)
    ui.on('keydown', reset_timer, throttle=5.0)

    def check_idle_status():
        elapsed = (datetime.now() - last_activity_time[0]).total_seconds()
        if elapsed > IDLE_TIMEOUT_SECONDS:
            app.storage.user.clear()
            ui.notify('⚠️ Session expired due to inactivity. Logging out.', color='negative')
            ui.navigate.to('/login')

    ui.timer(10.0, check_idle_status)
    ui.query('.nicegui-content').classes('w-full min-h-screen bg-gradient-to-br from-emerald-50 via-teal-50/40 to-cyan-50/50 p-4 md:p-8')

    verses = [
        'Train up a child in the way he should go... — Proverbs 22:6',
        'Let the children come to me... — Matthew 19:14',
        'For I know the plans I have for you... — Jeremiah 29:11',
        'I can do all things through Christ... — Philippians 4:13',
        'The Lord bless you and keep you... — Numbers 6:24',
        'Your word is a lamp to my feet... — Psalm 119:105',
        'Be strong and courageous... — Joshua 1:9',
        'Let your light shine before others... — Matthew 5:16',
        'The fruit of the Spirit is love, joy, peace... — Galatians 5:22',
        'Trust in the Lord with all your heart... — Proverbs 3:5',
        'Children are a heritage from the Lord... — Psalm 127:3',
        'God is our refuge and strength... — Psalm 46:1',
        'Whatever you do, work at it with all your heart... — Colossians 3:23',
        'The Lord is my shepherd; I shall not want. — Psalm 23:1',
        'Give thanks to the Lord, for he is good... — Psalm 136:1',
        'Do not let any unwholesome talk come out of your mouths... — Ephesians 4:29',
        'Blessed are the pure in heart, for they will see God. — Matthew 5:8',
        'A friend loves at all times... — Proverbs 17:17',
        'Praise the Lord, my soul... — Psalm 103:2',
        'Walk by faith, not by sight. — 2 Corinthians 5:7',
    ]

    with ui.column().classes('w-full items-center'):
        with ui.column().classes('w-[98%] md:w-[95%] max-w-7xl gap-6 md:gap-8'):
            with ui.card().classes(
                'w-full p-8 md:p-12 bg-gradient-to-r from-emerald-900 via-teal-900'
                ' to-cyan-950 shadow-xl rounded-3xl text-center border border-emerald-700/30'
                ' relative overflow-hidden'
            ):
                ui.icon('school', size='6rem', color='emerald').classes('absolute -right-8 -bottom-8 opacity-10')
                ui.icon('auto_stories', size='6rem', color='teal').classes('absolute -left-8 -top-8 opacity-10')
                ui.label("Teacher's Dialogue").classes('text-3xl md:text-5xl font-black text-white tracking-tight')
                ui.label('School Report & Academic Management System').classes('text-emerald-200 text-sm md:text-base font-medium mt-1')
            with ui.card().classes(
                'w-full p-6 bg-gradient-to-r from-emerald-100/80 via-teal-50 to-white'
                ' border-l-8 border-emerald-600 rounded-3xl shadow-sm border border-emerald-100'
            ):
                with ui.row().classes('items-center gap-2 mb-1'):
                    ui.icon('menu_book', color='emerald-800', size='1.2rem')
                    ui.label('📖 Daily Inspiration').classes('text-emerald-900 font-extrabold text-xs tracking-wider uppercase')
                ui.label(random.choice(verses)).classes('text-emerald-950 italic text-lg md:text-xl font-medium')
            with ui.tabs().classes(
                'w-full bg-white/90 backdrop-blur-md p-2 rounded-3xl shadow-lg'
                ' shadow-emerald-950/5 border border-emerald-100 overflow-x-auto flex-nowrap'
            ) as tabs:
                tabs.classes('items-center justify-start md:justify-center')
                ui.tab('Dashboard', icon='dashboard').classes('rounded-2xl transition-all duration-300 hover:bg-emerald-50 text-emerald-900 font-bold')
                ui.tab('Class Analytics', icon='analytics').classes('rounded-2xl transition-all duration-300 hover:bg-emerald-50 text-emerald-900 font-bold')
                ui.tab('Upper Primary entry', icon='add_circle').classes('rounded-2xl transition-all duration-300 hover:bg-emerald-50 text-emerald-900 font-bold')
                ui.tab('Upper Primary Records', icon='assignment').classes('rounded-2xl transition-all duration-300 hover:bg-emerald-50 text-emerald-900 font-bold')
                ui.tab('Lower Primary entry', icon='add_circle').classes('rounded-2xl transition-all duration-300 hover:bg-emerald-50 text-emerald-900 font-bold')
                ui.tab('lower Primary Records', icon='assignment').classes('rounded-2xl transition-all duration-300 hover:bg-emerald-50 text-emerald-900 font-bold')
                ui.tab('Nursery entry', icon='child_care').classes('rounded-2xl transition-all duration-300 hover:bg-emerald-50 text-emerald-900 font-bold')
                nursery_records_tab = ui.tab('Nursery Records', icon='list_alt').classes('rounded-2xl transition-all duration-300 hover:bg-emerald-50 text-emerald-900 font-bold')
                ui.tab('Staff Chat', icon='forum').classes('rounded-2xl transition-all duration-300 hover:bg-emerald-50 text-emerald-900 font-bold')
                ui.tab('Logout', icon='logout').classes('rounded-2xl transition-all duration-300 hover:bg-red-550 text-red-600 font-bold')
            with ui.tab_panels(tabs, value='Dashboard').classes('w-full bg-transparent'):
                with ui.tab_panel('Dashboard'):
                    now = datetime.now()
                    current_year = now.year
                    current_month = now.month
                    if 1 <= current_month <= 4: current_term = 'Term I'
                    elif 5 <= current_month <= 8: current_term = 'Term II'
                    else: current_term = 'Term III'
                    with ui.row().classes('w-full gap-4 mb-6 flex-col md:flex-row'):
                        with ui.card().classes('flex-1 p-6 bg-gradient-to-br from-emerald-800 to-teal-900 text-white shadow-xl shadow-emerald-900/15 rounded-3xl relative overflow-hidden'):
                            ui.icon('calendar_month', size='2.5rem').classes('absolute right-4 bottom-4 opacity-15')
                            ui.label('ACADEMIC CALENDAR').classes('text-xs font-bold text-emerald-200 uppercase tracking-wider')
                            ui.label(f'{current_term}, {current_year}').classes('text-3xl font-black mt-1')
                            ui.label('Primary Section Active').classes('text-xs text-emerald-100/80 mt-1 font-medium')
                        try:
                            conn = get_db_connection()
                            cursor = conn.cursor()
                            try:
                                cursor.execute('SELECT COUNT(*) FROM academic_records')
                                upper_count = cursor.fetchone()[0]
                                cursor.execute('SELECT COUNT(*) FROM lower_primary_results')
                                lower_count = cursor.fetchone()[0]
                                cursor.execute('SELECT COUNT(*) FROM nursery_results')
                                nursery_count = cursor.fetchone()[0]
                                total_pupils = upper_count + lower_count + nursery_count
                            finally:
                                conn.close()
                        except Exception:
                            upper_count, lower_count, nursery_count, total_pupils = 0, 0, 0, 0
                        with ui.card().classes('flex-1 p-6 bg-gradient-to-br from-teal-700 to-cyan-900 text-white shadow-xl shadow-teal-900/15 rounded-3xl relative overflow-hidden'):
                            ui.icon('badge', size='2.5rem').classes('absolute right-4 bottom-4 opacity-15')
                            ui.label('TOTAL ENROLLED').classes('text-xs font-bold text-teal-200 uppercase tracking-wider')
                            ui.label(str(total_pupils)).classes('text-3xl font-black mt-1')
                            ui.label(f'Upper: {upper_count} | Lower: {lower_count} | Nursery: {nursery_count}').classes('text-xs text-teal-100/80 mt-1 font-medium')
                        try:
                            conn = get_db_connection()
                            cursor = conn.cursor()
                            try:
                                cursor.execute("SELECT COUNT(*) FROM academic_records WHERE Class LIKE '%7%'")
                                p7_count = cursor.fetchone()[0]
                            finally:
                                conn.close()
                        except Exception:
                            p7_count = 0
                        with ui.card().classes('flex-1 p-6 bg-gradient-to-br from-green-700 to-emerald-900 text-white shadow-xl shadow-green-900/15 rounded-3xl relative overflow-hidden'):
                            ui.icon('military_tech', size='2.5rem').classes('absolute right-4 bottom-4 opacity-15')
                            ui.label('P.7 CANDIDATE CLASS').classes('text-xs font-bold text-green-200 uppercase tracking-wider')
                            ui.label(str(p7_count)).classes('text-3xl font-black mt-1')
                            ui.label('Registered for PLE Assessment').classes('text-xs text-green-100/80 mt-1 font-medium')
                    metrics = get_dashboard_metrics()
                    with ui.row().classes('items-center mb-6 gap-3'):
                        with ui.avatar(color='emerald-700', text_color='white', size='md').classes('shadow-md'):
                            ui.icon('monitoring', size='1.5rem')
                        ui.label('Performance Analytics').classes('text-2xl font-black text-emerald-950')
                    if metrics:
                        with ui.row().classes('w-full gap-6 flex-col md:flex-row'):
                            with ui.card().classes('w-full md:w-1/3 p-6 shadow-xl bg-white/90 backdrop-blur-md rounded-3xl border border-emerald-100'):
                                with ui.row().classes('items-center gap-2 mb-4'):
                                    ui.icon('trending_up', color='emerald', size='1.4rem')
                                    ui.label('Subject Performance Trends').classes('text-md font-black text-emerald-950')
                                with ui.row().classes('w-full justify-around mt-2'):
                                    with ui.column().classes('items-center p-4 bg-emerald-50 rounded-2xl flex-1 mr-2 border border-emerald-100'):
                                        ui.icon('arrow_upward', color='green', size='1.8rem')
                                        ui.label('Top').classes('text-xs text-stone-400 font-bold uppercase mt-1')
                                        ui.label(metrics['best']).classes('text-lg font-black text-green-700')
                                    with ui.column().classes('items-center p-4 bg-amber-50 rounded-2xl flex-1 ml-2 border border-amber-100'):
                                        ui.icon('arrow_downward', color='amber', size='1.8rem')
                                        ui.label('Low').classes('text-xs text-stone-400 font-bold uppercase mt-1')
                                        ui.label(metrics['worst']).classes('text-lg font-black text-amber-700')
                            with ui.card().classes('w-full md:w-[63%] p-6 shadow-xl bg-white/90 backdrop-blur-md rounded-3xl border border-emerald-100'):
                                with ui.row().classes('w-full gap-8 flex-col md:flex-row'):
                                    with ui.column().classes('flex-1 bg-amber-50/50 p-4 rounded-2xl border border-amber-100'):
                                        with ui.row().classes('items-center gap-2 mb-3'):
                                            with ui.avatar(color='amber-700', text_color='white', size='xs'):
                                                ui.icon('warning', size='1rem')
                                            ui.label('Academic Intervention').classes('text-sm font-black text-amber-950')
                                        if not metrics['at_risk']:
                                            ui.label('No students require urgent intervention.').classes('text-xs text-stone-400 italic')
                                        else:
                                            for s in metrics['at_risk']:
                                                with ui.row().classes('w-full justify-between py-1.5 px-2 bg-white rounded-2xl my-1 border border-amber-100 shadow-sm items-center'):
                                                    ui.label(f"{s['Name']} ({s['Class']})").classes('text-xs font-bold text-stone-800')
                                                    ui.badge(f"{round(s['Average'] or 0, 1)}%").classes('bg-amber-100 text-amber-900 font-mono font-bold')
                                    with ui.column().classes('flex-1 bg-emerald-50/70 p-4 rounded-2xl border border-emerald-200'):
                                        with ui.row().classes('items-center gap-2 mb-3'):
                                            with ui.avatar(color='emerald-700', text_color='white', size='xs'):
                                                ui.icon('workspace_premium', size='1rem')
                                            ui.label('Rising Stars').classes('text-sm font-black text-emerald-950')
                                        if not metrics['rising']:
                                            ui.label('No rising stars identified yet.').classes('text-xs text-stone-400 italic')
                                        else:
                                            for s in metrics['rising']:
                                                with ui.row().classes('w-full justify-between py-1.5 px-2 bg-white rounded-2xl my-1 border border-emerald-100 shadow-sm items-center'):
                                                    ui.label(f"{s['Name']} ({s['Class']})").classes('text-xs font-bold text-stone-800')
                                                    ui.badge(f"{round(s['Average'] or 0, 1)}%").classes('bg-emerald-100 text-emerald-900 font-mono font-bold')
                    else:
                        with ui.card().classes('w-full p-12 items-center bg-white/90 rounded-3xl shadow-xl border border-emerald-100'):
                            ui.icon('analytics', size='3rem', color='emerald')
                            ui.label('No academic data available for analysis.').classes('text-emerald-950 font-bold mt-2')
                with ui.tab_panel('Class Analytics'):
                    with ui.card().classes('w-full p-6 bg-white/90 backdrop-blur-md rounded-3xl shadow-xl border border-emerald-100'):
                        performance_analytics_hub_content()
                with ui.tab_panel('Upper Primary entry'):
                    with ui.card().classes('w-full p-6 bg-white/90 backdrop-blur-md rounded-3xl shadow-xl border border-emerald-100'):
                        insert.insert()
                with ui.tab_panel('Upper Primary Records'):
                    with ui.card().classes('w-full p-6 bg-white/90 backdrop-blur-md rounded-3xl shadow-xl border border-emerald-100'):
                        view_records_content()
                with ui.tab_panel('Lower Primary entry'):
                    with ui.card().classes('w-full p-6 bg-white/90 backdrop-blur-md rounded-3xl shadow-xl border border-emerald-100'):
                        lower.lower()
                with ui.tab_panel('lower Primary Records'):
                    with ui.card().classes('w-full p-6 bg-white/90 backdrop-blur-md rounded-3xl shadow-xl border border-emerald-100'):
                        view_lower_records_content()
                with ui.tab_panel('Nursery entry'):
                    with ui.card().classes('w-full p-6 bg-white/90 backdrop-blur-md rounded-3xl shadow-xl border border-emerald-100'):
                        nursery.nursery()
                nursery_reload_fn = [None]
                with ui.tab_panel('Nursery Records'):
                    with ui.card().classes('w-full p-6 bg-white/90 backdrop-blur-md rounded-3xl shadow-xl border border-emerald-100'):
                        nursery_reload_fn[0] = view_nursery_records_content()

                def on_tab_change(e=None):
                    if tabs.value == 'Nursery Records' and nursery_reload_fn[0]:
                        nursery_reload_fn[0]()

                tabs.on('update:model-value', on_tab_change)
                with ui.tab_panel('Staff Chat'):
                    with ui.card().classes('w-full p-6 bg-white/90 backdrop-blur-md rounded-3xl shadow-xl border border-emerald-100'):
                        staff_chat_content()
                with ui.tab_panel('Logout'):
                    with ui.card().classes('w-full max-w-[320px] mx-auto items-center p-8 bg-white/90 backdrop-blur-md rounded-3xl shadow-xl border border-emerald-100'):
                        with ui.avatar(color='red-100', text_color='red-600', size='xl').classes('shadow-sm'):
                            ui.icon('logout', size='2.5rem')
                        ui.label('Ready to leave?').classes('text-xl font-black mt-4 text-stone-900')
                        ui.label('Your session will be securely closed.').classes('text-stone-500 mb-6 text-xs text-center')

                        def perform_logout():
                            app.storage.user.clear()
                            ui.navigate.to('/')

                        ui.button('Confirm Sign Out', on_click=perform_logout).classes(
                            'w-full bg-gradient-to-r from-red-600 to-rose-700 text-white'
                            ' font-bold py-3 rounded-2xl hover:from-red-700 hover:to-rose-800'
                            ' shadow-lg shadow-red-600/20 transition-all'
                        )
