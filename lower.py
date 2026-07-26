from datetime import datetime
import sqlite3
from nicegui import ui

# Define the shared database constant
DB = 'School_Results_Database.db'


def init_db():
  """Initializes the database table and checks for missing columns."""
  with sqlite3.connect(DB) as conn:
    cursor = conn.cursor()
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

    with sqlite3.connect(DB) as conn:
      cursor = conn.cursor()
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

    ui.notify(
        f"🎉 ¡Órale! {pupil_name}'s results saved successfully!",
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


# Build the data entry form UI with a vibrant, stylish Mexican-inspired aesthetic (Papel picado / Fiesta color palette)
def lower():
  init_db()

  # Mexican-inspired vibrant theme background (warm terracotta / desert sunset gradient feel using Tailwind classes)
  with ui.column().classes(
      'w-full min-h-screen justify-center items-center bg-amber-50 p-4'
  ):
    with ui.card().classes(
        'w-full max-w-[700px] p-8 bg-white shadow-2xl hover:shadow-3xl'
        ' transition-shadow duration-300 rounded-3xl border-t-8 border-rose-600'
        ' my-8'
    ):

      # Header styling featuring festive Mexican colors (Deep Red/Ruby & Vibrant Teal/Gold accents)
      ui.label('🌵 Lower Primary Results Entry').classes(
          'text-3xl font-black text-rose-700 text-center w-full mb-1'
          ' tracking-wide'
      )
      ui.label('✨ ¡Felicidades & Evaluation Portal! ✨').classes(
          'text-xs font-bold text-teal-600 text-center w-full mb-6 uppercase'
          ' tracking-widest'
      )

      with ui.column().classes('w-full gap-5'):

        # --- STUDENT DETAILS ---
        ui.label('👤 Student Profile').classes(
            'text-lg font-bold text-amber-900 border-b-2 border-amber-200'
            ' w-full pb-1'
        )

        with ui.row().classes('w-full gap-4'):
          payment_code_input = (
              ui.input('Payment Code')
              .classes('flex-1 text-lg')
              .props('outlined dense clearable color=rose')
          )
          name_input = (
              ui.input('Pupil Full Name')
              .classes('flex-1 text-lg')
              .props('outlined dense clearable color=rose')
          )

        with ui.row().classes('w-full gap-4'):
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
              .classes('flex-1')
              .props('outlined dense color=rose')
          )

          term_select = (
              ui.select(
                  ['Term I', 'Term II', 'Term III'],
                  label='Term',
                  with_input=True,
              )
              .classes('flex-1')
              .props('outlined dense color=rose')
          )

        # --- SUBJECT SCORES ---
        ui.label('📝 Subject Scores (0-100)').classes(
            'text-lg font-bold text-amber-900 border-b-2 border-amber-200'
            ' w-full pb-1 mt-4'
        )

        with ui.row().classes('w-full gap-4 items-center'):
          lit_i_input = (
              ui.number('🗣️ Literacy I')
              .classes('flex-1')
              .props('outlined dense color=amber')
          )
          lit_ii_input = (
              ui.number('✍️ Literacy II')
              .classes('flex-1')
              .props('outlined dense color=amber')
          )

        with ui.row().classes('w-full gap-4'):
          reading_input = (
              ui.number('📖 Reading')
              .classes('flex-1')
              .props('outlined dense color=amber')
          )
          luganda_input = (
              ui.number('🥁 Luganda')
              .classes('flex-1')
              .props('outlined dense color=amber')
          )

        with ui.row().classes('w-full gap-4'):
          math_input = (
              ui.number('🧮 Mathematics')
              .classes('flex-1')
              .props('outlined dense color=amber')
          )
          eng_input = (
              ui.number('🇬🇧 English')
              .classes('flex-1')
              .props('outlined dense color=amber')
          )

        with ui.row().classes('w-full gap-4'):
          sst_input = (
              ui.number('🌍 Social Studies')
              .classes('flex-1')
              .props('outlined dense color=teal')
          )
          science_input = (
              ui.number('🔬 Science')
              .classes('flex-1')
              .props('outlined dense color=teal')
          )
          re_input = (
              ui.number('🕊️ Religious Ed.')
              .classes('flex-1')
              .props('outlined dense color=teal')
          )

        # --- ADMIN & REMARKS DETAILS ---
        ui.label('👩‍🏫 Administration & Remarks').classes(
            'text-lg font-bold text-amber-900 border-b-2 border-amber-200'
            ' w-full pb-1 mt-4'
        )
        teacher_input = (
            ui.input('Class Teacher Name')
            .classes('w-full')
            .props('outlined dense clearable color=teal')
        )

        teacher_remarks_input = (
            ui.textarea('💬 Class Teacher Remarks')
            .classes('w-full')
            .props('outlined dense clearable color=teal')
        )
        head_comment_input = (
            ui.textarea("🏆 Head Teacher’s Comment")
            .classes('w-full')
            .props('outlined dense clearable color=teal')
        )
        conduct_input = (
            ui.textarea('⭐ Conduct & Discipline')
            .classes('w-full')
            .props('outlined dense clearable color=teal')
        )
        interest_input = (
            ui.textarea('⚽ Co-curricular / Interest')
            .classes('w-full')
            .props('outlined dense clearable color=teal')
        )

        # --- SUBMISSION LOGIC ---
        def handle_submit():
          success = save_result(
              payment_code_input.value,
              name_input.value,
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
            name_input.value = None
            lit_i_input.value = None
            lit_ii_input.value = None
            reading_input.value = None
            luganda_input.value = None
            math_input.value = None
            eng_input.value = None
            sst_input.value = None
            science_input.value = None
            re_input.value = None
            teacher_remarks_input.value = None
            head_comment_input.value = None
            conduct_input.value = None
            interest_input.value = None
            refresh_table()

        # Stylish Mexican fiesta button (Vibrant Amber/Orange-to-Rose gradient feel via Tailwind)
        ui.button(
            '🌵 SAVE STUDENT RESULTS ', on_click=handle_submit
        ).classes(
            'w-full py-4 mt-4 text-white font-black bg-gradient-to-r'
            ' from-rose-600 via-orange-600 to-amber-600 hover:opacity-90'
            ' transition-opacity rounded-2xl shadow-xl tracking-wider text-base'
        )

        # --- RECENT ENTRIES TABLE CONTAINER ---
        ui.label('📊 Recent Saved Entries').classes(
            'text-lg font-bold text-amber-900 border-b-2 border-amber-200'
            ' w-full pb-1 mt-6'
        )

        table_container = ui.column().classes('w-full')

        def refresh_table():
          table_container.clear()
          with table_container:
            try:
              with sqlite3.connect(DB) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(
                    'SELECT payment_code, pupil_name, class_level, literacy_i,'
                    ' literacy_ii, reading, luganda, mathematics, english,'
                    ' social_studies, science, re_religious_education FROM'
                    ' lower_primary_results ORDER BY id DESC LIMIT 5'
                ).fetchall()

                table_data = []
                for r in rows:
                  scores = [
                      r['literacy_i'],
                      r['literacy_ii'],
                      r['reading'],
                      r['luganda'],
                      r['mathematics'],
                      r['english'],
                      r['social_studies'],
                      r['science'],
                      r['re_religious_education'],
                  ]
                  valid_scores = [s for s in scores if s is not None]
                  avg = (
                      sum(valid_scores) / len(valid_scores)
                      if valid_scores
                      else 0
                  )

                  table_data.append({
                      'payment_code': r['payment_code'],
                      'pupil_name': r['pupil_name'],
                      'class_level': r['class_level'],
                      'average': round(avg, 1),
                  })

                if table_data:
                  columns = [
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
                      columns=columns, rows=table_data, row_key='payment_code'
                  ).classes('w-full border border-amber-200 rounded-xl')
                else:
                  ui.label(
                      '📭 No records saved yet.'
                  ).classes('text-amber-700/60 text-sm italic py-2')
            except Exception as e:
              ui.label(f'⚠️ Could not load table: {e}').classes(
                  'text-red-600 text-sm'
              )

        refresh_table()
