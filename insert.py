import os
import libsql
from nicegui import ui
import polars as pl
import report
from verifying_passcode import get_db_connection


def load_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        records = cursor.execute('SELECT * FROM academic_records ORDER BY Rank ASC').fetchall()
        columns = [col[0] for col in cursor.description] if cursor.description else []

        updated_rows = []
        for r in records:
            row = dict(zip(columns, r))
            count_cursor = conn.execute('SELECT COUNT(*) FROM academic_records WHERE Class = ?', (row['Class'],))
            total_count = count_cursor.fetchone()[0]
            row['Total_In_Class'] = total_count
            updated_rows.append(row)

        student_table.rows = []
        student_table.update()
        student_table.rows = updated_rows
        student_table.update()
    finally:
        conn.close()


# --- 1. DATABASE SETUP & MIGRATION ---
def migrate_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('CREATE TABLE IF NOT EXISTS academic_records (id INTEGER PRIMARY KEY AUTOINCREMENT)')

        required_columns = {
            "Name": "TEXT", "PaymentCode": "TEXT", "Class": "TEXT", "ExamType": "TEXT",
            "ExamDate": "TEXT", "Attendance": "TEXT", "Remarks": "TEXT",
            "Maths": "INTEGER", "Maths_Grade": "TEXT", "English": "INTEGER",
            "English_Grade": "TEXT", "SST": "INTEGER", "SST_Grade": "TEXT",
            "Science": "INTEGER", "Science_Grade": "TEXT", "Total": "INTEGER",
            "Average": "REAL", "Grade": "TEXT", "Rank": "INTEGER DEFAULT 0",
            "Term": "INTEGER", "AcademicYear": "INTEGER", "FeesBalance": "REAL",
            "ClassTeacherRemarks": "TEXT", "HeadteacherRemarks": "TEXT",
            "Conduct": "TEXT", "Interest": "TEXT"
        }

        for col, col_type in required_columns.items():
            try:
                cursor.execute(f'ALTER TABLE academic_records ADD COLUMN {col} {col_type}')
            except Exception:
                pass
        conn.commit()
    finally:
        conn.close()


# --- 2. THE INSERT UI FUNCTION ---
def insert():
    migrate_db()

    def get_grade(score):
        if score is None: return "F9"
        if score >= 90: return "D1"
        if score >= 80: return "D2"
        if score >= 70: return "C3"
        if score >= 60: return "C4"
        if score >= 50: return "C5"
        if score >= 45: return "C6"
        if score >= 40: return "P7"
        if score >= 35: return "P8"
        return "F9"

    def save():
        for key, field in inputs.items():
            if field.value is None or (isinstance(field.value, str) and not field.value.strip()):
                ui.notify(f"Field {key} is required", type='warning', position='top')
                return

        payload = {k: v.value for k, v in inputs.items()}
        df = pl.DataFrame([payload])

        df = df.with_columns([
            pl.col("Maths").map_elements(get_grade, return_dtype=pl.String).alias("Maths_Grade"),
            pl.col("English").map_elements(get_grade, return_dtype=pl.String).alias("English_Grade"),
            pl.col("SST").map_elements(get_grade, return_dtype=pl.String).alias("SST_Grade"),
            pl.col("Science").map_elements(get_grade, return_dtype=pl.String).alias("Science_Grade"),
            (pl.col("Maths") + pl.col("English") + pl.col("SST") + pl.col("Science")).alias("Total")
        ]).with_columns(
            (pl.col("Total") / 4).alias("Average")
        ).with_columns(
            pl.col("Average").map_elements(lambda x: f"{round(x, 1)}", return_dtype=pl.String).alias("Grade")
        )

        row = df.to_dicts()[0]

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''INSERT INTO academic_records
                (Name, PaymentCode, Class, ExamType, ExamDate, Attendance, Remarks, Maths, Maths_Grade,
                 English, English_Grade, SST, SST_Grade, Science, Science_Grade, Total, Average,
                 Grade, Rank, Term, AcademicYear, FeesBalance, ClassTeacherRemarks, HeadteacherRemarks, Conduct, Interest)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                (row['Name'], row['PaymentCode'], row['Class'], row['ExamType'], row['ExamDate'],
                 row['Attendance'], row['Remarks'], row['Maths'], row['Maths_Grade'],
                 row['English'], row['English_Grade'], row['SST'], row['SST_Grade'],
                 row['Science'], row['Science_Grade'], row['Total'], row['Average'],
                 row['Grade'], 0, row['Term'], row['AcademicYear'],
                 row['FeesBalance'], row['ClassTeacherRemarks'], row['HeadteacherRemarks'],
                 row['Conduct'], row['Interest']))

            cursor.execute('SELECT id FROM academic_records WHERE Class = ? ORDER BY Average DESC', (row['Class'],))
            for rank_val, (student_id,) in enumerate(cursor.fetchall(), start=1):
                cursor.execute('UPDATE academic_records SET Rank = ? WHERE id = ?', (rank_val, student_id))
            conn.commit()
        finally:
            conn.close()

        ui.notify(f"Record saved for {row['Name']}!", type='positive', position='top')
        load_table()

    def load_table():
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            records = cursor.execute('SELECT * FROM academic_records ORDER BY Rank ASC').fetchall()
            columns = [col[0] for col in cursor.description] if cursor.description else []

            rows = []
            for r in records:
                row_dict = dict(zip(columns, r))
                count_cursor = conn.execute('SELECT COUNT(*) FROM academic_records WHERE Class = ?', (row_dict['Class'],))
                row_dict['Total_In_Class'] = count_cursor.fetchone()[0]
                rows.append(row_dict)

            student_table.rows = rows
        finally:
            conn.close()
        student_table.update()

    # --- UI LAYOUT ---
    with ui.column().classes('w-full min-h-screen justify-start items-center bg-white p-2 md:p-6'):
        inputs = {}

        with ui.column().classes('w-full max-w-6xl mx-auto gap-6 items-center'):

            # Assessment Entry Form Card with Dark Green & White Theme
            with ui.card().classes('w-full max-w-2xl p-4 md:p-8 bg-white shadow-xl rounded-2xl md:rounded-3xl border-t-8 border-green-900 my-2'):
                ui.label("Student Assessment Entry").classes('text-base md:text-lg font-extrabold text-green-950 mb-4 border-b-2 border-green-100 pb-1')

                with ui.column().classes('w-full gap-3 md:flex-row'):
                    inputs['Name'] = ui.input("Student Name").classes('w-full md:flex-1').props('outlined dense color=green-9')
                    inputs['PaymentCode'] = ui.input('Payment Code').classes('w-full md:flex-1').props('outlined dense color=green-9')

                with ui.column().classes('w-full gap-3 md:flex-row'):
                    inputs['Class'] = ui.select(['P4','P5','P6', 'P7'], label='Class').classes('w-full md:flex-1').props('outlined dense color=green-9')
                    inputs['ExamType'] = ui.select(['Beginning', 'Mid-Term', 'End-Term', 'Tests'], label='Exam Type').classes('w-full md:flex-1').props('outlined dense color=green-9')

                with ui.column().classes('w-full gap-3 md:grid md:grid-cols-3'):
                    inputs['Term'] = ui.select([1, 2, 3], label='Term').classes('w-full').props('outlined dense color=green-9')
                    inputs['AcademicYear'] = ui.input('Year', value='2026').classes('w-full').props('outlined dense color=green-9')
                    inputs['FeesBalance'] = ui.number('Fees Bal (UGX)', value=0).classes('w-full').props('outlined dense color=green-9')

                ui.label("Subject Scores").classes('text-sm font-bold text-green-900 mt-2')
                with ui.column().classes('w-full gap-3 md:grid md:grid-cols-2'):
                    inputs['Maths'] = ui.number('Maths', min=0, max=100).classes('w-full').props('outlined dense color=green-9')
                    inputs['English'] = ui.number('English', min=0, max=100).classes('w-full').props('outlined dense color=green-9')
                    inputs['SST'] = ui.number('SST', min=0, max=100).classes('w-full').props('outlined dense color=green-9')
                    inputs['Science'] = ui.number('Science', min=0, max=100).classes('w-full').props('outlined dense color=green-9')

                ui.label("Administrative Details").classes('text-sm font-bold text-green-900 mt-2')
                with ui.column().classes('w-full gap-3 md:flex-row'):
                    inputs['ExamDate'] = ui.input('Date (dd/mm/yyyy)').classes('w-full md:flex-1').props('outlined dense color=green-9')
                    inputs['Attendance'] = ui.input('Attendance').classes('w-full md:flex-1').props('outlined dense color=green-9')

                with ui.column().classes('w-full gap-3 md:grid md:grid-cols-2'):
                    inputs['Remarks'] = ui.textarea('General Remarks').classes('w-full').props('outlined dense color=green-9 rows=2')
                    inputs['ClassTeacherRemarks'] = ui.textarea('Class Teacher Remarks').classes('w-full').props('outlined dense color=green-9 rows=2')
                    inputs['HeadteacherRemarks'] = ui.textarea('Head Teacher Remarks').classes('w-full').props('outlined dense color=green-9 rows=2')
                    inputs['Conduct'] = ui.textarea('Conduct & Discipline').classes('w-full').props('outlined dense color=green-9 rows=2')
                    inputs['Interest'] = ui.textarea('Co-Curricular/Interest').classes('w-full').props('outlined dense color=green-9 rows=2')

                ui.button('Save Student Record', on_click=save).classes('w-full mt-4 py-3.5 text-white font-bold bg-green-900 hover:bg-green-950 transition-all rounded-xl shadow-md text-sm md:text-base')

            # Records Database Display Card
            with ui.card().classes('w-full max-w-4xl p-4 md:p-6 bg-white shadow-xl rounded-2xl md:rounded-3xl border border-green-100'):
                ui.label("Student Records Database").classes('text-base md:text-lg font-extrabold text-green-950 mb-4 border-b-2 border-green-100 pb-1')

                global student_table
                student_table = ui.table(columns=[
                    {'name': 'Rank', 'label': 'Rank', 'field': 'Rank', 'align': 'center'},
                    {'name': 'Name', 'label': 'Name', 'field': 'Name', 'align': 'left'},
                    {'name': 'Class', 'label': 'Class', 'field': 'Class', 'align': 'center'},
                    {'name': 'Average', 'label': 'Avg', 'field': 'Average', 'align': 'center'},
                    {'name': 'actions', 'label': 'Action', 'field': 'actions', 'align': 'center'}
                ], rows=[], row_key='id').classes('w-full border border-green-100 rounded-xl bg-white').props('flat bordered dense')

                student_table.add_slot('body-cell-actions', '''
                    <q-td :props="props">
                        <q-btn icon="download" flat dense color="green-9" @click="$parent.$emit('generate', props.row)"></q-btn>
                    </q-td>
                ''')
                student_table.on('generate', lambda msg: report.report(msg.args))

    load_table()

if __name__ in {"__main__", "__mp_main__"}:
    insert()
