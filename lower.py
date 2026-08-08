from datetime import datetime
import os
import libsql
from nicegui import ui
from verifying_passcode import get_db_connection


def init_db():
  """Initializes the database table and checks for missing columns."""
  conn = get_db_connection()
  cursor = conn.cursor()
  try:
    cursor.execute('''
            CREATE TABLE IF NOT EXISTS lower_primary_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                payment_code TEXT,
                pupil_name TEXT,
                class_level TEXT,
                term TEXT,
                literacy_i INTEGER,
                literacy_ii INTEGER,
                reading INTEGER,
                luganda INTEGER,
                mathematics INTEGER,
                english INTEGER,
                social_studies INTEGER,
                science INTEGER,
                re_religious_education INTEGER,
                class_teacher TEXT,
                class_teacher_remarks TEXT,
                head_teacher_comment TEXT,
                conduct TEXT,
                interest TEXT,
                timestamp TEXT
            )
        ''')

    # Safely add columns if running on an older existing database version
    existing_cols = [
        col[1]
        for col in cursor.execute(
            'PRAGMA table_info(lower_primary_results)'
        ).fetchall()
    ]

    if 'payment_code' not in existing_cols:
      cursor.execute(
          'ALTER TABLE lower_primary_results ADD COLUMN payment_code TEXT'
      )

    if 'pupil_name' not in existing_cols:
      cursor.execute(
          'ALTER TABLE lower_primary_results ADD COLUMN pupil_name TEXT'
      )

    if 'social_studies' not in existing_cols:
      cursor.execute(
          'ALTER TABLE lower_primary_results ADD COLUMN social_studies INTEGER'
      )

    if 'science' not in existing_cols:
      cursor.execute(
          'ALTER TABLE lower_primary_results ADD COLUMN science INTEGER'
      )

    if 'class_teacher_remarks' not in existing_cols:
      cursor.execute(
          'ALTER TABLE lower_primary_results ADD COLUMN class_teacher_remarks'
          ' TEXT'
      )

    if 'head_teacher_comment' not in existing_cols:
      cursor.execute(
          'ALTER TABLE lower_primary_results ADD COLUMN head_teacher_comment'
          ' TEXT'
      )

    if 'conduct' not in existing_cols:
      cursor.execute('ALTER TABLE lower_primary_results ADD COLUMN conduct TEXT')

    if 'interest' not in existing_cols:
      cursor.execute('ALTER TABLE lower_primary_results ADD COLUMN interest TEXT')

    conn.commit()
  finally:
    conn.close()


def save_result(
    payment_code,
    pupil_name,
    class_level,
    term,
    lit_i,
    lit_ii,
    reading,
    luganda,
    math,
    eng,
    sst,
    science,
    re_sub,
    teacher,
    teacher_remarks,
    head_comment,
    conduct,
    interest,
):
  """Saves the entered results and returns True if successful to trigger a form reset."""
  if (
      not payment_code
      or not pupil_name
      or not class_level
      or not term
      or not teacher
  ):
    ui.notify(
        '⚠️ Please fill in Payment Code, Name, Class, Term, and Teacher!',
        color='warning',
        position='top',
    )
    return False

  try:
    scores = {
        'Literacy I': int(lit_i) if lit_i else 0,
        'Literacy II': int(lit_ii) if lit_ii else 0,
        'Reading': int(reading) if reading else 0,
        'Luganda': int(luganda) if luganda else 0,
        'Mathematics': int(math) if math else 0,
        'English': int(eng) if eng else 0,
        'Social Studies': int(sst) if sst else 0,
        'Science': int(science) if science else 0,
        'R.E': int(re_sub) if re_sub else 0,
    }

    for subject, score in scores.items():
      if not (0 <= score <= 100):
        ui.notify(
            f'❌ {subject} score must be between 0 and 100!',
            color='negative',
            position='top',
        )
        return False

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
      cursor.execute(
          """
                INSERT INTO lower_primary_results 
                (payment_code, pupil_name, class_level, term, literacy_i, literacy_ii, reading, luganda, mathematics, english, social_studies, science, re_religious_education, class_teacher, class_teacher_remarks, head_teacher_comment, conduct, interest, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now', 'localtime'))
            """,
          (
              payment_code.strip(),
              pupil_name.strip(),
              class_level,
              term,
              scores['Literacy I'],
              scores['Literacy II'],
              scores['Reading'],
              scores['Luganda'],
              scores['Mathematics'],
              scores['English'],
              scores['Social Studies'],
              scores['Science'],
              scores['R.E'],
              teacher.strip(),
              teacher_remarks.strip() if teacher_remarks else '',
              head_comment.strip() if head_comment else '',
              conduct.strip() if conduct else '',
              interest.strip() if interest else '',
          ),
      )
      conn.commit()
    finally:
      conn.close()

    ui.notify(
        f"✨ {pupil_name}'s results saved successfully!",
        color='positive',
        position='top',
    )
    return True

  except ValueError:
    ui.notify('🔢 Marks must be valid numbers!', color='negative', position='top')
    return False
  except Exception as e:
    ui.notify(f'💾 Database error: {e}', color='negative', position='top')
    return False


# Build the practical, mobile-friendly lower primary results data entry interface
def lower():
  init_db()

  with ui.column().classes(
      'w-full min-h-screen justify-start items-center bg-stone-50 p-2 md:p-6'
  ):
    with ui.card().classes(
        'w-full max-w-[800px] p-4 md:p-8 bg-white shadow-xl rounded-2xl md:rounded-3xl border border-emerald-100 my-2 md:my-4'
    ):

      with ui.column().classes('w-full gap-4 md:gap-5'):

        # --- STUDENT DETAILS ---
        ui.label('👤 Student Profile').classes(
            'text-base md:text-lg font-extrabold text-emerald-950 border-b-2 border-emerald-100 w-full pb-1'
        )

        with ui.column().classes('w-full gap-3 md:flex-row'):
          payment_code_input = (
              ui.input('Payment Code')
              .classes('w-full md:flex-1')
              .props('outlined dense clearable color=emerald')
          )
          pupil_name_input = (
              ui.input('Pupil Full Name')
              .classes('w-full md:flex-1')
              .props('outlined dense clearable color=emerald')
          )

        with ui.column().classes('w-full gap-3 md:flex-row'):
          class_select = (
              ui.select(
                  [
                      'Primary One (P.1)',
                      'Primary Two (P.2)',
                      'Primary Three (P.3)',
                  ],
                  label='Class Level',
                  with_input=True,
              )
              .classes('w-full md:flex-1')
              .props('outlined dense color=emerald')
          )

          term_select = (
              ui.select(
                  ['Term I', 'Term II', 'Term III'],
                  label='Term',
                  with_input=True,
              )
              .classes('w-full md:flex-1')
              .props('outlined dense color=emerald')
          )

        # --- SUBJECT SCORES ---
        ui.label('📝 Subject Scores (0-100)').classes(
            'text-base md:text-lg font-extrabold text-emerald-950 border-b-2 border-emerald-100 w-full pb-1 mt-2'
        )

        with ui.column().classes('w-full gap-3 md:flex-row'):
          lit_i_input = (
              ui.number('Literacy I')
              .classes('w-full md:flex-1')
              .props('outlined dense color=emerald')
          )
          lit_ii_input = (
              ui.number('Literacy II')
              .classes('w-full md:flex-1')
              .props('outlined dense color=emerald')
          )

        with ui.column().classes('w-full gap-3 md:flex-row'):
          reading_input = (
              ui.number('Reading')
              .classes('w-full md:flex-1')
              .props('outlined dense color=emerald')
          )
          luganda_input = (
              ui.number('Luganda')
              .classes('w-full md:flex-1')
              .props('outlined dense color=emerald')
          )

        with ui.column().classes('w-full gap-3 md:flex-row'):
          math_input = (
              ui.number('Mathematics')
              .classes('w-full md:flex-1')
              .props('outlined dense color=emerald')
          )
          eng_input = (
              ui.number('English')
              .classes('w-full md:flex-1')
              .props('outlined dense color=emerald')
          )

        with ui.column().classes('w-full gap-3 md:grid md:grid-cols-3'):
          sst_input = (
              ui.number('Social Studies')
              .classes('w-full')
              .props('outlined dense color=emerald')
          )
          science_input = (
              ui.number('Science')
              .classes('w-full')
              .props('outlined dense color=emerald')
          )
          re_input = (
              ui.number('Religious Ed.')
              .classes('w-full')
              .props('outlined dense color=emerald')
          )

        # --- ADMIN & REMARKS DETAILS ---
        ui.label('👩‍🏫 Administration & Remarks').classes(
            'text-base md:text-lg font-extrabold text-emerald-950 border-b-2 border-emerald-100 w-full pb-1 mt-2'
        )
        teacher_input = (
            ui.input('Class Teacher Name')
            .classes('w-full')
            .props('outlined dense clearable color=emerald')
        )

        with ui.column().classes('w-full gap-3 md:grid md:grid-cols-2'):
          teacher_remarks_input = (
              ui.textarea('Class Teacher Remarks')
              .classes('w-full')
              .props('outlined dense clearable color=emerald rows=2')
          )
          head_comment_input = (
              ui.textarea('Head Teacher’s Comment')
              .classes('w-full')
              .props('outlined dense clearable color=emerald rows=2')
          )
          conduct_input = (
              ui.textarea('Conduct & Discipline')
              .classes('w-full')
              .props('outlined dense clearable color=emerald rows=2')
          )
          interest_input = (
              ui.textarea('Co-curricular / Interest')
              .classes('w-full')
              .props('outlined dense clearable color=emerald rows=2')
          )

        # --- SUBMISSION LOGIC ---
        def handle_submit():
          success = save_result(
              payment_code_input.value,
              pupil_name_input.value,
              class_select.value,
              term_select.value,
              lit_i_input.value,
              lit_ii_input.value,
              reading_input.value,
              luganda_input.value,
              math_input.value,
              eng_input.value,
              sst_input.value,
              science_input.value,
              re_input.value,
              teacher_input.value,
              teacher_remarks_input.value,
              head_comment_input.value,
              conduct_input.value,
              interest_input.value,
          )
          if success:
                payment_code_input.value = None
                pupil_name_input.value = None
                class_select.value = None
                term_select.value = None
                lit_i_input.value = None
                lit_ii_input.value = None
                reading_input.value = None
                luganda_input.value = None
                math_input.value = None
                eng_input.value = None
                sst_input.value = None
                science_input.value = None
                re_input.value = None
                teacher_input.value = None
                teacher_remarks_input.value = None
                head_comment_input.value = None
                conduct_input.value = None
                interest_input.value = None
                refresh_table()

        # Practical high-contrast button optimized for mobile touch targets
        ui.button('Save Student Results', on_click=handle_submit).classes(
            'w-full py-3.5 mt-2 text-white font-bold bg-gradient-to-r from-emerald-700 to-teal-800 hover:from-emerald-800 hover:to-teal-900 transition-all rounded-xl shadow-md text-sm md:text-base'
        )

        # --- RECENT ENTRIES TABLE CONTAINER ---
        ui.label('📊 Recent Saved Entries').classes(
            'text-base md:text-lg font-extrabold text-emerald-950 border-b-2 border-emerald-100 w-full pb-1 mt-4'
        )

        table_container = ui.column().classes('w-full overflow-x-auto')

        def refresh_table():
          table_container.clear()
          with table_container:
            try:
              conn = get_db_connection()
              cursor = conn.cursor()
              try:
                records = cursor.execute(
                    'SELECT payment_code, pupil_name, class_level, literacy_i,'
                    ' literacy_ii, reading, luganda, mathematics, english,'
                    ' social_studies, science, re_religious_education FROM'
                    ' lower_primary_results ORDER BY id DESC LIMIT 5'
                ).fetchall()
                
                columns = [col[0] for col in cursor.description] if cursor.description else []
                
                table_data = []
                for r in records:
                  row = dict(zip(columns, r))
                  scores = [
                      row['literacy_i'],
                      row['literacy_ii'],
                      row['reading'],
                      row['luganda'],
                      row['mathematics'],
                      row['english'],
                      row['social_studies'],
                      row['science'],
                      row['re_religious_education'],
                  ]
                  valid_scores = [s for s in scores if s is not None]
                  avg = (
                      sum(valid_scores) / len(valid_scores)
                      if valid_scores
                      else 0
                  )

                  table_data.append({
                      'payment_code': row['payment_code'],
                      'pupil_name': row['pupil_name'],
                      'class_level': row['class_level'],
                      'average': round(avg, 1),
                  })

                if table_data:
                  ui_columns = [
                      {
                          'name': 'payment_code',
                          'label': 'Payment Code',
                          'field': 'payment_code',
                          'align': 'left',
                      },
                      {
                          'name': 'pupil_name',
                          'label': 'Pupil Name',
                          'field': 'pupil_name',
                          'align': 'left',
                      },
                      {
                          'name': 'class_level',
                          'label': 'Class',
                          'field': 'class_level',
                          'align': 'center',
                      },
                      {
                          'name': 'average',
                          'label': 'Average Score',
                          'field': 'average',
                          'align': 'center',
                      },
                  ]
                  ui.table(
                      columns=ui_columns, rows=table_data, row_key='payment_code'
                  ).classes(
                      'w-full border border-emerald-100 rounded-xl bg-white'
                  ).props('flat bordered dense')
                else:
                  ui.label('📭 No records saved yet.').classes(
                      'text-stone-400 text-xs italic py-2'
                  )
              finally:
                conn.close()
            except Exception as e:
              ui.label(f'⚠️ Could not load table: {e}').classes(
                  'text-red-600 text-xs'
              )

        refresh_table()
