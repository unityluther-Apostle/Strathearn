from datetime import datetime
import random
import sqlite3
import insert
import lower
from nicegui import app, ui

# --- DATABASE CONFIG ---
DB = 'School_Results_Database.db'


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


# --- 1. DYNAMIC ANALYTICS LOGIC ---
def get_dashboard_metrics():
  try:
    with sqlite3.connect(DB) as conn:
      conn.row_factory = sqlite3.Row
      rows = conn.execute('SELECT * FROM academic_records').fetchall()
      if not rows:
        return None

      # Calculate Averages per Subject
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

      # Find Best/Worst
      best_sub = max(subs, key=subs.get)
      worst_sub = min(subs, key=subs.get)

      # Calculate Class Average for Rising Stars
      all_avgs = [r['Average'] for r in rows if r['Average']]
      class_avg = sum(all_avgs) / len(all_avgs) if all_avgs else 0

      # Rising Stars: Above class average AND above 60
      rising_stars = [
          r for r in rows if r['Average'] > class_avg and r['Average'] > 60
      ]

      # At Risk: Students with average below 50, sorted by lowest score first
      at_risk = sorted(
          [r for r in rows if (r['Average'] or 0) < 50],
          key=lambda x: x['Average'] or 0,
      )

      return {
          'best': best_sub,
          'worst': worst_sub,
          'at_risk': at_risk,
          'rising': rising_stars[:3],
      }
  except:
    return None


# --- 1.1 PER-CLASS PERFORMANCE ANALYTICS LOGIC ---
def get_class_analytics(selected_class, level_type):
  try:
    with sqlite3.connect(DB) as conn:
      conn.row_factory = sqlite3.Row

      if level_type == 'Upper Primary':
        query = 'SELECT * FROM academic_records WHERE Class = ?'
        rows = [
            dict(r) for r in conn.execute(query, (selected_class,)).fetchall()
        ]
        if not rows:
          return None

        # Subject breakdown
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

        all_avgs = [
            r['Average'] for r in rows if r.get('Average') is not None
        ]
        class_avg = sum(all_avgs) / len(all_avgs) if all_avgs else 0

        sorted_rows = sorted(
            rows, key=lambda x: x.get('Average') or 0, reverse=True
        )
        top_students = sorted_rows[:3]

        # At Risk / Intervention: Students with average below 50
        at_risk = sorted(
            [r for r in rows if (r.get('Average') or 0) < 50],
            key=lambda x: x.get('Average') or 0,
        )

        return {
            'total_students': len(rows),
            'class_avg': round(class_avg, 1),
            'best_sub': (
                f"{best_sub} ({round(subs[best_sub], 1)}%)" if subs else 'N/A'
            ),
            'worst_sub': (
                f"{worst_sub} ({round(subs[worst_sub], 1)}%)" if subs else 'N/A'
            ),
            'top_students': top_students,
            'at_risk': at_risk,
        }

      else:  # Lower Primary
        query = 'SELECT * FROM lower_primary_results WHERE class_level = ?'
        rows = [
            dict(r) for r in conn.execute(query, (selected_class,)).fetchall()
        ]
        if not rows:
          return None

        subject_keys = [
            'literacy_i',
            'literacy_ii',
            'reading',
            'luganda',
            'mathematics',
            'english',
            'social_studies',
            'science',
            're_religious_education',
        ]

        sub_totals = {}
        sub_counts = {}
        for r in rows:
          for sk in subject_keys:
            val = r.get(sk)
            if val is not None:
              sub_totals[sk] = sub_totals.get(sk, 0) + val
              sub_counts[sk] = sub_counts.get(sk, 0) + 1

        subs_avg = {
            sk: (sub_totals[sk] / sub_counts[sk])
            for sk in sub_totals
            if sub_counts[sk] > 0
        }
        best_sub = max(subs_avg, key=subs_avg.get) if subs_avg else 'N/A'
        worst_sub = min(subs_avg, key=subs_avg.get) if subs_avg else 'N/A'

        # Compute individual totals for ranking
        processed = []
        for r in rows:
          scores = [
              r.get(sk) for sk in subject_keys if r.get(sk) is not None
          ]
          tot = sum(scores)
          avg = tot / len(scores) if scores else 0
          r['_calc_total'] = tot
          r['_calc_avg'] = avg
          processed.append(r)

        all_avgs = [p['_calc_avg'] for p in processed]
        class_avg = sum(all_avgs) / len(all_avgs) if all_avgs else 0

        sorted_processed = sorted(
            processed, key=lambda x: x['_calc_total'], reverse=True
        )
        top_students = sorted_processed[:3]

        # At Risk / Intervention: Students with average below 50
        at_risk = sorted(
            [p for p in processed if p['_calc_avg'] < 50],
            key=lambda x: x['_calc_avg'],
        )

        readable_names = {
            'literacy_i': 'Lit I',
            'literacy_ii': 'Lit II',
            'reading': 'Reading',
            'luganda': 'Luganda',
            'mathematics': 'Maths',
            'english': 'English',
            'social_studies': 'S.S.T',
            'science': 'Science',
            're_religious_education': 'R.E',
        }

        return {
            'total_students': len(rows),
            'class_avg': round(class_avg, 1),
            'best_sub': (
                f"{readable_names.get(best_sub, best_sub)}"
                f' ({round(subs_avg.get(best_sub, 0), 1)}%)'
                if best_sub != 'N/A'
                else 'N/A'
            ),
            'worst_sub': (
                f"{readable_names.get(worst_sub, worst_sub)}"
                f' ({round(subs_avg.get(worst_sub, 0), 1)}%)'
                if worst_sub != 'N/A'
                else 'N/A'
            ),
            'top_students': top_students,
            'at_risk': at_risk,
        }
  except Exception as e:
    print(f'Analytics error: {e}')
    return None


# --- 2. EDIT RECORD LOGIC ---
def edit_record(record, on_save):
  with ui.dialog() as dialog, ui.card().classes('w-[700px] p-8'):
    ui.label(f"Edit Record: {record['Name']}").classes('text-2xl font-bold mb-4')
    with ui.grid(columns=2).classes('w-full gap-4'):
      fields = {
          'Name': ui.input('Name', value=record['Name']),
          'Admin': ui.input('Admin', value=record['Admin']),
          'Class': ui.input('Class', value=record['Class']),
          'Maths': ui.number('Maths', value=record['Maths']),
          'English': ui.number('English', value=record['English']),
          'SST': ui.number('SST', value=record['SST']),
          'Science': ui.number('Science', value=record['Science']),
          'Remarks': ui.input('Remarks', value=record['Remarks']),
      }

    def save():
      with sqlite3.connect(DB) as conn:
        conn.execute(
            '''UPDATE academic_records SET 
                    Name=?, Admin=?, Class=?, Maths=?, English=?, 
                    SST=?, Science=?, Remarks=? WHERE id=?''',
            (
                fields['Name'].value,
                fields['Admin'].value,
                fields['Class'].value,
                fields['Maths'].value,
                fields['English'].value,
                fields['SST'].value,
                fields['Science'].value,
                fields['Remarks'].value,
                record['id'],
            ),
        )

      ui.notify('Record updated successfully!', color='positive')
      dialog.close()
      on_save()

    ui.button('Save Changes', on_click=save).classes(
        'w-full mt-6 bg-[#800000] text-white'
    )
  dialog.open()


# --- EDIT LOWER PRIMARY RECORD LOGIC ---
def edit_lower_record(record, on_save):
  with ui.dialog() as dialog, ui.card().classes('w-[700px] p-8'):
    ui.label(f"Edit Lower Primary Record: {record['pupil_name']}").classes(
        'text-2xl font-bold mb-4'
    )
    with ui.grid(columns=2).classes('w-full gap-4'):
      fields = {
          'payment_code': ui.input(
              'Payment Code', value=record.get('payment_code', '')
          ),
          'pupil_name': ui.input('Pupil Name', value=record['pupil_name']),
          'class_level': ui.input('Class', value=record['class_level']),
          'term': ui.input('Term', value=record['term']),
          'literacy_i': ui.number('Lit I', value=record['literacy_i']),
          'literacy_ii': ui.number('Lit II', value=record['literacy_ii']),
          'reading': ui.number('Reading', value=record['reading']),
          'luganda': ui.number('Luganda', value=record['luganda']),
          'mathematics': ui.number('Maths', value=record['mathematics']),
          'english': ui.number('English', value=record['english']),
          'social_studies': ui.number('S.S.T', value=record['social_studies']),
          'science': ui.number('Science', value=record['science']),
          're_religious_education': ui.number(
              'R.E', value=record['re_religious_education']
          ),
          'class_teacher': ui.input('Teacher', value=record['class_teacher']),
      }

    def save():
      with sqlite3.connect(DB) as conn:
        conn.execute(
            '''UPDATE lower_primary_results SET 
                    payment_code=?, pupil_name=?, class_level=?, term=?, literacy_i=?, literacy_ii=?, 
                    reading=?, luganda=?, mathematics=?, english=?, social_studies=?, 
                    science=?, re_religious_education=?, class_teacher=? WHERE id=?''',
            (
                fields['payment_code'].value,
                fields['pupil_name'].value,
                fields['class_level'].value,
                fields['term'].value,
                fields['literacy_i'].value,
                fields['literacy_ii'].value,
                fields['reading'].value,
                fields['luganda'].value,
                fields['mathematics'].value,
                fields['english'].value,
                fields['social_studies'].value,
                fields['science'].value,
                fields['re_religious_education'].value,
                fields['class_teacher'].value,
                record['id'],
            ),
        )

      ui.notify('Lower primary record updated successfully!', color='positive')
      dialog.close()
      on_save()

    ui.button('Save Changes', on_click=save).classes(
        'w-full mt-6 bg-[#800000] text-white'
    )
  dialog.open()


# --- HELPER FUNCTIONS FOR LOWER PRIMARY CALCULATIONS ---
def compute_lower_derived_fields(rows):
  """Calculates Total, Grade, and Rank per Class for lower primary records."""
  classes = {}
  for r in rows:
    c_level = r.get('class_level') or 'Unknown'
    classes.setdefault(c_level, []).append(r)

  processed_rows = []
  for c_level, group in classes.items():
    for r in group:
      scores = [
          r.get('literacy_i'),
          r.get('literacy_ii'),
          r.get('reading'),
          r.get('luganda'),
          r.get('mathematics'),
          r.get('english'),
          r.get('social_studies'),
          r.get('science'),
          r.get('re_religious_education'),
      ]
      valid_scores = [s for s in scores if s is not None]
      total = sum(valid_scores)
      r['_calc_total'] = total

      avg = total / len(valid_scores) if valid_scores else 0
      if avg >= 80:
        grade = '1'
      elif avg >= 60:
        grade = '2'
      elif avg >= 50:
        grade = '3'
      elif avg >= 40:
        grade = '4'
      else:
        grade = '7'
      r['_calc_grade'] = grade

    group_sorted = sorted(group, key=lambda x: x['_calc_total'], reverse=True)
    for index, r in enumerate(group_sorted, start=1):
      r['_calc_rank'] = index
      processed_rows.append(r)

  return processed_rows


# --- HELPER FUNCTIONS FOR UPPER PRIMARY CALCULATIONS ---
def compute_upper_ranks(rows):
  """Calculates and assigns Rank per Class for upper primary records."""
  classes = {}
  for r in rows:
    c_level = r.get('Class') or 'Unknown'
    classes.setdefault(c_level, []).append(r)

  processed_rows = []
  for c_level, group in classes.items():
    group_sorted = sorted(
        group, key=lambda x: x.get('Total') or 0, reverse=True
    )
    for index, r in enumerate(group_sorted, start=1):
      r['_calc_rank'] = index
      processed_rows.append(r)

  return processed_rows


# View records for lower primary
def view_lower_records_content():
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
      {'name': 'term', 'label': 'Term', 'field': 'term', 'align': 'center'},
      {
          'name': 'literacy_i',
          'label': 'Lit I',
          'field': 'literacy_i',
          'align': 'center',
      },
      {
          'name': 'literacy_ii',
          'label': 'Lit II',
          'field': 'literacy_ii',
          'align': 'center',
      },
      {
          'name': 'reading',
          'label': 'Reading',
          'field': 'reading',
          'align': 'center',
      },
      {
          'name': 'luganda',
          'label': 'Luganda',
          'field': 'luganda',
          'align': 'center',
      },
      {
          'name': 'mathematics',
          'label': 'Maths',
          'field': 'mathematics',
          'align': 'center',
      },
      {
          'name': 'english',
          'label': 'English',
          'field': 'english',
          'align': 'center',
      },
      {
          'name': 'social_studies',
          'label': 'S.S.T',
          'field': 'social_studies',
          'align': 'center',
      },
      {
          'name': 'science',
          'label': 'Science',
          'field': 'science',
          'align': 'center',
      },
      {
          'name': 're_religious_education',
          'label': 'R.E',
          'field': 're_religious_education',
          'align': 'center',
      },
      {
          'name': '_calc_total',
          'label': 'Total',
          'field': '_calc_total',
          'align': 'center',
      },
      {
          'name': '_calc_grade',
          'label': 'Grade',
          'field': '_calc_grade',
          'align': 'center',
      },
      {
          'name': '_calc_rank',
          'label': 'Rank',
          'field': '_calc_rank',
          'align': 'center',
      },
      {
          'name': 'class_teacher',
          'label': 'Teacher',
          'field': 'class_teacher',
          'align': 'left',
      },
      {
          'name': 'actions',
          'label': 'Actions',
          'field': 'actions',
          'align': 'center',
      },
  ]

  content_area = ui.column().classes('w-full')

  def load_data():
    content_area.clear()
    with content_area:
      try:
        with sqlite3.connect(DB) as conn:
          conn.row_factory = sqlite3.Row
          raw_rows = [
              dict(r)
              for r in conn.execute(
                  'SELECT * FROM lower_primary_results ORDER BY id DESC'
              ).fetchall()
          ]

        if not raw_rows:
          ui.label('No lower primary records found.').classes(
              'text-gray-500 p-8 italic'
          )
        else:
          all_rows = compute_lower_derived_fields(raw_rows)
          lower_table = ui.table(
              columns=columns, rows=all_rows, row_key='id'
          ).classes('w-full')
          lower_table.add_slot(
              'body-cell-actions',
              """
                    <q-td :props="props">
                        <q-btn icon="edit" flat dense color="primary" @click="$parent.$emit('edit_lower', props.row)"></q-btn>
                    </q-td>
                """,
          )
          lower_table.on(
              'edit_lower', lambda msg: edit_lower_record(msg.args, load_data)
          )
      except Exception as e:
        ui.label(f'⚠️ Error loading records: {e}').classes(
            'text-red-500 p-4'
        )

  load_data()


# --- 3. VIEW RECORDS TAB for upper primary ---
def view_records_content():
  columns = [
      {'name': 'Name', 'label': 'Name', 'field': 'Name', 'align': 'left'},
      {'name': 'Admin', 'label': 'Admin', 'field': 'Admin', 'align': 'center'},
      {'name': 'Class', 'label': 'Class', 'field': 'Class', 'align': 'center'},
      {'name': 'Maths', 'label': 'Maths', 'field': 'Maths', 'align': 'center'},
      {
          'name': 'English',
          'label': 'English',
          'field': 'English',
          'align': 'center',
      },
      {'name': 'SST', 'label': 'SST', 'field': 'SST', 'align': 'center'},
      {
          'name': 'Science',
          'label': 'Science',
          'field': 'Science',
          'align': 'center',
      },
      {'name': 'Total', 'label': 'Total', 'field': 'Total', 'align': 'center'},
      {'name': 'Grade', 'label': 'Grade', 'field': 'Grade', 'align': 'center'},
      {
          'name': '_calc_rank',
          'label': 'Rank',
          'field': '_calc_rank',
          'align': 'center',
      },
      {
          'name': 'Remarks',
          'label': 'Remarks',
          'field': 'Remarks',
          'align': 'left',
      },
      {
          'name': 'actions',
          'label': 'Actions',
          'field': 'actions',
          'align': 'center',
      },
  ]
  content_area = ui.column().classes('w-full')

  def load_data():
    content_area.clear()
    with content_area:
      try:
        with sqlite3.connect(DB) as conn:
          conn.row_factory = sqlite3.Row
          raw_rows = [
              dict(r)
              for r in conn.execute(
                  'SELECT * FROM academic_records'
              ).fetchall()
          ]
        if not raw_rows:
          ui.label('No records found.').classes('text-gray-500 p-8')
        else:
          all_rows = compute_upper_ranks(raw_rows)
          student_table = ui.table(
              columns=columns, rows=all_rows, row_key='id'
          ).classes('w-full')
          student_table.add_slot(
              'body-cell-actions',
              """
                    <q-td :props="props">
                        <q-btn icon="edit" flat dense color="primary" @click="$parent.$emit('edit', props.row)"></q-btn>
                    </q-td>
                """,
          )
          student_table.on(
              'edit', lambda msg: edit_record(msg.args, load_data)
          )
      except Exception as e:
        ui.label(f'Error: {e}')

  load_data()


# --- 3.1 PERFORMANCE ANALYTICS HUB CONTENT ---
def performance_analytics_hub_content():
  content_container = ui.column().classes('w-full gap-6')

  with content_container:
    ui.label('Per-Class Performance Hub').classes(
        'text-2xl font-bold text-gray-800'
    )
    ui.label(
        'Select a section and class to view isolated performance metrics, top'
        ' achievers, and intervention lists.'
    ).classes('text-sm text-gray-500 mb-2')

    # Fetch available classes dynamically from database
    try:
      with sqlite3.connect(DB) as conn:
        upper_classes = [
            r[0]
            for r in conn.execute(
                'SELECT DISTINCT Class FROM academic_records WHERE Class IS NOT'
                ' NULL'
            ).fetchall()
        ]
        lower_classes = [
            r[0]
            for r in conn.execute(
                'SELECT DISTINCT class_level FROM lower_primary_results WHERE'
                ' class_level IS NOT NULL'
            ).fetchall()
        ]
    except:
      upper_classes = []
      lower_classes = []

    all_options = []
    if upper_classes:
      all_options.extend([f'Upper Primary: {c}' for c in upper_classes])
    if lower_classes:
      all_options.extend([f'Lower Primary: {c}' for c in lower_classes])

    if not all_options:
      all_options = ['No Classes Found']

    selected_dropdown = ui.select(
        label='Select Class Level', options=all_options, value=all_options[0]
    ).classes('w-full md:w-96 bg-white rounded-lg')

    metrics_display_area = ui.column().classes('w-full gap-6 mt-4')

    def update_analytics_view():
      metrics_display_area.clear()
      val = selected_dropdown.value
      if not val or 'No Classes Found' in val:
        with metrics_display_area:
          ui.card().classes('w-full p-8 items-center').default_slot.text(
              'No classes available for analysis.'
          )
        return

      parts = val.split(': ')
      level_type = parts[0].strip()
      class_name = parts[1].strip()

      data = get_class_analytics(class_name, level_type)

      with metrics_display_area:
        if not data:
          with ui.card().classes('w-full p-8 items-center'):
            ui.icon('info', size='2.5rem', color='grey')
            ui.label(f'No student records found for {class_name}.').classes(
                'text-gray-500 mt-2'
            )
          return

        # KPI Summary Row
        with ui.row().classes('w-full gap-4'):
          with ui.card().classes('flex-1 p-5 border-l-4 border-l-indigo-500'):
            ui.label('Total Enrolled').classes(
                'text-xs font-bold text-gray-400 uppercase'
            )
            ui.label(str(data['total_students'])).classes(
                'text-2xl font-extrabold text-indigo-900'
            )

          with ui.card().classes('flex-1 p-5 border-l-4 border-l-blue-500'):
            ui.label('Class Average Score').classes(
                'text-xs font-bold text-gray-400 uppercase'
            )
            ui.label(f"{data['class_avg']}%").classes(
                'text-2xl font-extrabold text-blue-900'
            )

          with ui.card().classes('flex-1 p-5 border-l-4 border-l-green-500'):
            ui.label('Best Subject').classes(
                'text-xs font-bold text-gray-400 uppercase'
            )
            ui.label(data['best_sub']).classes(
                'text-lg font-bold text-green-800 truncate'
            )

          with ui.card().classes('flex-1 p-5 border-l-4 border-l-red-500'):
            ui.label('Weakest Subject').classes(
                'text-xs font-bold text-gray-400 uppercase'
            )
            ui.label(data['worst_sub']).classes(
                'text-lg font-bold text-red-800 truncate'
            )

        # Detailed Breakdown Cards Row
        with ui.row().classes('w-full gap-6 mt-2'):
          # Top Achievers
          with ui.card().classes(
              'flex-1 p-6 bg-green-50/50 border border-green-100'
          ):
            with ui.row().classes('items-center gap-2 mb-4'):
              ui.icon('workspace_premium', color='green', size='1.5rem')
              ui.label(f'Top Achievers — {class_name}').classes(
                  'text-md font-bold text-green-900'
              )

            if not data['top_students']:
              ui.label('No students recorded.').classes(
                  'text-xs text-gray-400 italic'
              )
            else:
              for idx, s in enumerate(data['top_students'], 1):
                name = s.get('Name') or s.get('pupil_name') or 'Unknown'
                score = s.get('Average') or s.get('_calc_avg') or 0
                with ui.row().classes(
                    'w-full justify-between py-2 border-b border-green-100'
                    ' items-center'
                ):
                  ui.label(f'{idx}. {name}').classes(
                      'font-medium text-sm text-gray-800'
                  )
                  ui.label(f'{round(score, 1)}%').classes(
                      'font-mono font-bold text-sm text-green-700'
                  )

          # Students Needing Intervention (< 50 average)
          with ui.card().classes(
              'flex-1 p-6 bg-red-50/50 border border-red-100'
          ):
            with ui.row().classes('items-center gap-2 mb-4'):
              ui.icon('warning_amber', color='red', size='1.5rem')
              ui.label(f'Academic Intervention — {class_name}').classes(
                  'text-md font-bold text-red-900'
              )

            if not data['at_risk']:
              ui.label('No students require urgent intervention.').classes(
                  'text-xs text-gray-400 italic'
              )
            else:
              for s in data['at_risk']:
                name = s.get('Name') or s.get('pupil_name') or 'Unknown'
                score = s.get('Average') or s.get('_calc_avg') or 0
                with ui.row().classes(
                    'w-full justify-between py-2 border-b border-red-100'
                    ' items-center'
                ):
                  ui.label(name).classes('font-medium text-sm text-gray-800')
                  ui.label(f'{round(score, 1)}%').classes(
                      'font-mono font-bold text-sm text-red-700'
                  )

    selected_dropdown.on('update:model-value', lambda: update_analytics_view())
    update_analytics_view()


# --- 3.2 STAFF CHAT ROOM CONTENT ---
def staff_chat_content():
  chat_container = ui.column().classes(
      'w-full h-[450px] overflow-y-auto p-4 bg-slate-50 rounded-2xl'
      ' shadow-inner border border-slate-200 gap-3'
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
      with sqlite3.connect(DB) as conn:
        conn.execute('DELETE FROM staff_chat WHERE id = ?', (msg_id,))
      ui.notify('🗑️ Message deleted successfully', color='warning')
      load_messages()
    except Exception as e:
      ui.notify(f'Failed to delete message: {e}', color='negative')

  def load_messages():
    chat_container.clear()
    with chat_container:
      try:
        with sqlite3.connect(DB) as conn:
          conn.row_factory = sqlite3.Row
          rows = conn.execute(
              'SELECT * FROM staff_chat ORDER BY id ASC'
          ).fetchall()

        if not rows:
          with ui.column().classes(
              'w-full items-center justify-center my-16 gap-2'
          ):
            ui.icon('local_cafe', size='2.5rem', color='amber-600')
            ui.label(
                'The kettle is boiling, but nobody has spoken yet!'
            ).classes('text-slate-600 text-xs font-semibold')
            ui.label(
                'Drop a complaint about the printer or start the morning'
                ' gossip.'
            ).classes('text-slate-400 text-[11px] italic')
        else:
          current_user = app.storage.user.get('username', 'Teacher')

          for r in rows:
            msg_id = r['id']
            sender = r['sender']
            is_me = sender == current_user

            align_cls = 'items-end' if is_me else 'items-start'
            bubble_bg = (
                'bg-[#800000] text-white rounded-tr-sm'
                if is_me
                else (
                    'bg-white text-slate-800 rounded-tl-sm border border-slate-200'
                    ' shadow-sm'
                )
            )

            with ui.column().classes(f'w-full {align_cls} gap-0.5 my-1'):
              with ui.row().classes('items-center gap-2 px-1'):
                if not is_me:
                  ui.label(sender).classes('text-[11px] font-bold text-[#800000]')

                if is_me:
                  ui.button(
                      icon='delete_outline',
                      on_click=lambda mid=msg_id: delete_message(mid),
                  ).props('flat dense').classes(
                      'text-red-400 hover:text-red-600 text-[10px] p-0 min-h-0'
                      ' min-w-0'
                  )

              with ui.card().classes(
                  f'{bubble_bg} p-3 rounded-2xl max-w-[75%] shadow-sm'
              ):
                ui.label(r['message']).classes(
                    'text-sm whitespace-pre-wrap leading-relaxed break-words'
                )
                with ui.row().classes(
                    'w-full justify-end items-center gap-1 mt-0.5'
                ):
                  ui.label(r['timestamp']).classes(
                      'text-[9px] text-amber-200'
                      if is_me
                      else 'text-slate-400'
                  )
                  if is_me:
                    ui.icon('done_all', size='12px', color='amber-300')
      except Exception as e:
        ui.label(f'⚠️ Printer jam in chat: {e}').classes('text-red-500 text-xs')

  with ui.column().classes(
      'w-full max-w-3xl mx-auto bg-white rounded-2xl shadow-md border'
      ' border-slate-200 overflow-hidden'
  ):
    # Professional Maroon & Amber Header with Online Counter & Clear Feed Option
    with ui.row().classes(
        'items-center justify-between w-full bg-[#800000] px-5 py-3.5 text-white'
        ' border-b border-red-900'
    ):
      with ui.row().classes('items-center gap-3'):
        with ui.avatar(size='sm').classes(
            'bg-amber-500 text-[#800000] font-extrabold shadow-sm'
        ):
          ui.icon('school', size='1.1rem')
        with ui.column().classes('gap-0'):
          ui.label('Staff Common Room').classes(
              'text-sm font-extrabold text-white'
          )
          ui.label(current_vibe).classes(
              'text-[11px] text-amber-300 font-medium'
          )

      with ui.row().classes('items-center gap-1'):
        # Live online indicator badge
        ui.badge('Live Sync', color='amber-600').props('dense').classes(
            'text-[10px] text-white font-bold'
        )
        ui.timer(3.0, load_messages)
        ui.button(
            icon='refresh', on_click=load_messages
        ).props('flat round dense').classes(
            'text-white hover:text-amber-300'
        )

    load_messages()

    # Fun Quick Reaction Emojis Bar
    quick_emojis = [
        '😂',
        '💀',
        '🔥',
        '👀',
        '☕',
        '📉',
        '💯',
        '🙏',
        '⚠️',
        '🤷‍♂️',
        '🤦‍♀️',
        '🍎',
        '📝',
        '📢',
    ]
    with ui.row().classes(
        'w-full gap-1 items-center px-3 py-1.5 bg-slate-50 border-t'
        ' border-slate-200 overflow-x-auto'
    ):
      ui.label('Vibe Check:').classes(
          'text-[10px] text-amber-700 font-bold uppercase mr-1 shrink-0'
      )
      for emo in quick_emojis:

        def insert_emoji(e=emo):
          msg_input.value = (msg_input.value or '') + e
          msg_input.update()

        ui.button(emo, on_click=insert_emoji).props('flat dense').classes(
            'text-sm bg-white border border-slate-200 rounded-lg px-2 py-0.5'
            ' text-slate-700 hover:bg-amber-50 shrink-0 shadow-sm'
        )

    # Enhanced Communication Input Bar with Character Counter Hint
    with ui.row().classes(
        'w-full items-center gap-2 p-3 bg-white border-t border-slate-200'
    ):
      msg_input = (
          ui.input(placeholder='Say something before the bell rings...')
          .classes(
              'flex-1 bg-slate-100 text-slate-900 rounded-xl px-3 border-none'
          )
          .props('borderless dense')
      )

      def send_message():
        text = msg_input.value.strip()
        if not text:
          return

        sender = app.storage.user.get('username', 'Teacher')
        timestamp = datetime.now().strftime('%H:%M')

        try:
          with sqlite3.connect(DB) as conn:
            conn.execute(
                'INSERT INTO staff_chat (sender, message, timestamp) VALUES'
                ' (?, ?, ?)',
                (sender, text, timestamp),
            )
          msg_input.value = ''
          load_messages()
        except Exception as e:
          ui.notify(f'Failed to broadcast gossip: {e}', color='negative')

      msg_input.on('keydown.enter', send_message)
      ui.button(icon='send', on_click=send_message).classes(
          'bg-[#800000] text-white rounded-full p-2 h-10 w-10 shadow-sm'
          ' hover:bg-red-900 transition-colors'
      )


# --- 4. STAFF HOME ---
def teacher():
  if not app.storage.user.get('logged_in'):
    ui.run_javascript('window.location.replace("/login")')
    return

  # --- AUTO-LOGOUT MECHANISM (15 Minutes Idle Timeout) ---
  IDLE_TIMEOUT_SECONDS = 900  # 900 seconds = 15 minutes
  last_activity_time = [datetime.now()]

  def reset_timer(e=None):
    last_activity_time[0] = datetime.now()

  # Track user activity globally using ui.on instead of ui.query('body').on
  ui.on('mousemove', reset_timer, throttle=5.0)
  ui.on('keydown', reset_timer, throttle=5.0)

  def check_idle_status():
    elapsed = (datetime.now() - last_activity_time[0]).total_seconds()
    if elapsed > IDLE_TIMEOUT_SECONDS:
      app.storage.user.clear()
      ui.notify(
          '⚠️ Session expired due to inactivity. Logging out.', color='negative'
      )
      ui.navigate.to('/login')

  ui.timer(10.0, check_idle_status)

  ui.query('.nicegui-content').classes('w-full min-h-screen bg-stone-50 p-8')

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
      'Do your best to present yourself to God... — 2 Timothy 2:15',
      'Children are a heritage from the Lord... — Psalm 127:3',
      'The fear of the Lord is the beginning of wisdom... — Proverbs 9:10',
      'Whatever you do, work at it with all your heart... — Colossians 3:23',
      'The Lord is my light and my salvation... — Psalm 27:1',
      'For God has not given us a spirit of fear... — 2 Timothy 1:7',
      'Great are the works of the Lord... — Psalm 111:2',
      'May the Lord give you strength... — Psalm 29:11',
      'Love the Lord your God with all your heart... — Matthew 22:37',
      'The Lord is good to all... — Psalm 145:9',
      'Be kind to one another... — Ephesians 4:32',
      'Let everything you do be done in love... — 1 Corinthians 16:14',
      'I have loved you with an everlasting love... — Jeremiah 31:3',
      (
          'For where your treasure is, there your heart will be... — Matthew'
          ' 6:21'
      ),
      'The Lord will guide you always... — Isaiah 58:11',
      (
          'Blessed are those who hunger and thirst for righteousness... —'
          ' Matthew 5:6'
      ),
      'Commit to the Lord whatever you do... — Proverbs 16:3',
      'With God all things are possible... — Matthew 19:26',
      'Grow in the grace and knowledge of our Lord... — 2 Peter 3:18',
      'A cheerful heart is good medicine... — Proverbs 17:22',
  ]

  with ui.column().classes('w-full items-center'):
    with ui.column().classes('w-[95%] max-w-7xl gap-8'):
      # --- Header ---
      with ui.card().classes(
          'w-full p-12 bg-white shadow-lg rounded-3xl text-center'
      ):
        ui.label("Teacher's Dialogue").classes('text-5xl font-extrabold')

      # --- Daily Inspiration ---
      with ui.card().classes(
          'w-full p-6 bg-amber-50 border-l-8 border-amber-400'
      ):
        ui.label('📖 Daily Inspiration').classes(
            'text-amber-900 font-bold text-sm'
        )
        ui.label(random.choice(verses)).classes('text-amber-800 italic text-xl')

      # --- Tabs ---
      with ui.tabs().classes(
          'w-full bg-white/80 backdrop-blur-md p-2 rounded-3xl shadow-xl border'
          ' border-white/20'
      ) as tabs:
        tabs.classes('items-center justify-center')
        ui.tab('Dashboard', icon='dashboard').classes(
            'rounded-2xl transition-all duration-300 hover:bg-[#800000]/10'
        )
        ui.tab('Class Analytics', icon='analytics').classes(
            'rounded-2xl transition-all duration-300 hover:bg-[#800000]/10'
        )
        ui.tab('Upper Primary entry', icon='add_circle').classes(
            'rounded-2xl transition-all duration-300 hover:bg-[#800000]/10'
        )
        ui.tab('Upper Primary Records', icon='assignment').classes(
            'rounded-2xl transition-all duration-300 hover:bg-[#800000]/10'
        )
        ui.tab('Lower Primary entry', icon='add_circle').classes(
            'rounded-2xl transition-all duration-300 hover:bg-[#800000]/10'
        )
        ui.tab('lower Primary Records', icon='assignment').classes(
            'rounded-2xl transition-all duration-300 hover:bg-[#800000]/10'
        )
        ui.tab('Staff Chat', icon='forum').classes(
            'rounded-2xl transition-all duration-300 hover:bg-[#800000]/10'
        )
        ui.tab('Logout', icon='logout').classes(
            'rounded-2xl transition-all duration-300 hover:bg-red-100'
            ' text-red-600'
        )

      with ui.tab_panels(tabs, value='Dashboard').classes(
          'w-full bg-transparent'
      ):
        # --- Dashboard Panel ---
        with ui.tab_panel('Dashboard'):
          # --- Automatic Term & Calendar Logic ---
          now = datetime.now()
          current_year = now.year
          current_month = now.month

          if 1 <= current_month <= 4:
            current_term = 'Term I'
          elif 5 <= current_month <= 8:
            current_term = 'Term II'
          else:
            current_term = 'Term III'

          # --- Termly Context & Overview Cards ---
          with ui.row().classes('w-full gap-4 mb-6'):
            # Active Term Card (Automatic)
            with ui.card().classes(
                'flex-1 p-5 border-l-4 border-l-[#800000] bg-white shadow-sm'
            ):
              ui.label('ACADEMIC CALENDAR').classes(
                  'text-xs font-bold text-gray-400 uppercase'
              )
              ui.label(f'{current_term}, {current_year}').classes(
                  'text-2xl font-extrabold text-[#800000]'
              )
              ui.label('Primary Section Active').classes(
                  'text-xs text-gray-500 mt-1'
              )

            # Total Enrolled Pupils Card (Automatic from Database)
            try:
              with sqlite3.connect(DB) as conn:
                upper_count = conn.execute(
                    'SELECT COUNT(*) FROM academic_records'
                ).fetchone()[0]
                lower_count = conn.execute(
                    'SELECT COUNT(*) FROM lower_primary_results'
                ).fetchone()[0]
                total_pupils = upper_count + lower_count
            except:
              upper_count, lower_count, total_pupils = 0, 0, 0

            with ui.card().classes(
                'flex-1 p-5 border-l-4 border-l-blue-600 bg-white shadow-sm'
            ):
              ui.label('TOTAL ENROLLED').classes(
                  'text-xs font-bold text-gray-400 uppercase'
              )
              ui.label(str(total_pupils)).classes(
                  'text-2xl font-extrabold text-blue-900'
              )
              ui.label(
                  f'Upper (P.4-P.7): {upper_count} | Lower (P.1-P.3):'
                  f' {lower_count}'
              ).classes('text-xs text-gray-500 mt-1')

            # Candidate Class Focus (Automatic from Database)
            try:
              with sqlite3.connect(DB) as conn:
                p7_count = conn.execute(
                    "SELECT COUNT(*) FROM academic_records WHERE Class LIKE '%7%'"
                ).fetchone()[0]
            except:
              p7_count = 0

            with ui.card().classes(
                'flex-1 p-5 border-l-4 border-l-amber-500 bg-white shadow-sm'
            ):
              ui.label('P.7 CANDIDATE CLASS').classes(
                  'text-xs font-bold text-gray-400 uppercase'
              )
              ui.label(str(p7_count)).classes(
                  'text-2xl font-extrabold text-amber-900'
              )
              ui.label('Registered for PLE Assessment').classes(
                  'text-xs text-gray-500 mt-1'
              )

          metrics = get_dashboard_metrics()
          with ui.row().classes('items-center mb-6'):
            ui.icon('analytics', color='indigo', size='2rem')
            ui.label('Performance Analytics').classes(
                'text-2xl font-bold text-gray-800 ml-2'
            )

          if metrics:
            with ui.row().classes('w-full gap-6'):
              # KPIs
              with ui.card().classes(
                  'w-full md:w-1/3 p-6 shadow-sm border-t-4 border-t-indigo-500'
              ):
                ui.label('Subject Performance Trends').classes(
                    'text-sm font-semibold text-gray-500 mb-4'
                )
                with ui.row().classes('w-full justify-between'):
                  with ui.column().classes('items-center'):
                    ui.icon('trending_up', color='green', size='2rem')
                    ui.label('Top').classes('text-xs text-gray-400 uppercase')
                    ui.label(metrics['best']).classes(
                        'text-lg font-bold text-green-700'
                    )
                  with ui.column().classes('items-center'):
                    ui.icon('trending_down', color='red', size='2rem')
                    ui.label('Low').classes('text-xs text-gray-400 uppercase')
                    ui.label(metrics['worst']).classes(
                        'text-lg font-bold text-red-700'
                    )

              # Support & Achievement Lists
              with ui.card().classes('w-full md:w-[63%] p-6 shadow-sm'):
                with ui.row().classes('w-full gap-8'):
                  # Column 1: Academic Intervention (< 50 average)
                  with ui.column().classes('flex-1'):
                    with ui.row().classes('items-center gap-2 mb-3'):
                      ui.icon('warning_amber', color='red', size='1.5rem')
                      ui.label('Academic Intervention').classes(
                          'text-sm font-bold text-red-800'
                      )
                    if not metrics['at_risk']:
                      ui.label(
                          'No students require urgent intervention.'
                      ).classes('text-xs text-gray-400 italic')
                    else:
                      for s in metrics['at_risk']:
                        with ui.row().classes(
                            'w-full justify-between py-1 border-b border-gray-100'
                        ):
                          ui.label(f"{s['Name']} ({s['Class']})").classes(
                              'text-sm'
                          )
                          ui.label(
                              f"{round(s['Average'] or 0, 1)}%"
                          ).classes('font-mono text-xs text-red-600')

                  # Column 2: Rising Stars
                  with ui.column().classes(
                      'flex-1 bg-green-50 p-4 rounded shadow-sm border'
                      ' border-green-100'
                  ):
                    with ui.row().classes('items-center gap-2 mb-3'):
                      ui.icon('workspace_premium', color='green', size='1.5rem')
                      ui.label('Rising Stars').classes(
                          'text-sm font-bold text-green-800'
                      )
                    for s in metrics['rising']:
                      with ui.row().classes(
                          'w-full justify-between py-1 border-b border-green-100'
                      ):
                        ui.label(f"{s['Name']} ({s['Class']})").classes(
                            'text-sm'
                        )
                        ui.label(f"{round(s['Average'] or 0, 1)}%").classes(
                            'font-mono text-xs text-green-600'
                        )
          else:
            with ui.card().classes('w-full p-10 items-center'):
              ui.icon('analytics', size='3rem', color='grey')
              ui.label('No academic data available for analysis.').classes(
                  'text-gray-500 mt-2'
              )

        # --- Class Analytics Panel ---
        with ui.tab_panel('Class Analytics'):
          with ui.card().classes('w-full p-6'):
            performance_analytics_hub_content()

        # --- Upper Primary Entry Panel ---
        with ui.tab_panel('Upper Primary entry'):
          with ui.card().classes('w-full p-6'):
            insert.insert()

        # --- Upper Primary Records Panel ---
        with ui.tab_panel('Upper Primary Records'):
          with ui.card().classes('w-full p-6'):
            view_records_content()

        # --- Lower Primary Entry Panel ---
        with ui.tab_panel('Lower Primary entry'):
          with ui.card().classes('w-full p-6'):
            lower.lower()

        # --- Lower Primary Records Panel ---
        with ui.tab_panel('lower Primary Records'):
          with ui.card().classes('w-full p-6'):
            view_lower_records_content()

        # --- Staff Chat Panel ---
        with ui.tab_panel('Staff Chat'):
          with ui.card().classes('w-full p-6'):
            staff_chat_content()

        # --- Logout Panel ---
        with ui.tab_panel('Logout'):
          with ui.card().classes('w-[300px] mx-auto items-center p-8'):
            ui.icon('logout', size='4rem', color='red-500')
            ui.label('Ready to leave?').classes('text-xl font-bold mt-4')
            ui.label('Your session will be closed.').classes(
                'text-gray-500 mb-6'
            )

            def perform_logout():
              app.storage.user.clear()
              ui.navigate.to('/')

            ui.button(
                'Confirm Sign Out', color='red', on_click=perform_logout
            ).classes('w-full')
