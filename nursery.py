from datetime import datetime
import os
import libsql
from nicegui import ui
from verifying_passcode import get_db_connection


# --- Database Setup ---
def init_db():
  conn = get_db_connection()
  cursor = conn.cursor()
  try:
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS nursery_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                payment_code TEXT,
                pupil_name TEXT,
                class_level TEXT,
                term TEXT,
                age TEXT,
                color TEXT,
                days_present TEXT,
                current_date TEXT,
                days_absent TEXT,
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
    
    # Check and add new columns if the table already existed without them
    cursor.execute("PRAGMA table_info(nursery_results)")
    existing_columns = [col[1] for col in cursor.fetchall()]
    
    new_columns = [
        ("age", "TEXT"),
        ("color", "TEXT"),
        ("days_present", "TEXT"),
        ("current_date", "TEXT"),
        ("days_absent", "TEXT")
    ]
    
    for col_name, col_type in new_columns:
      if col_name not in existing_columns:
        cursor.execute(f"ALTER TABLE nursery_results ADD COLUMN {col_name} {col_type}")
        
    conn.commit()
  finally:
    conn.close()


init_db()


# --- NiceGUI Layout & State ---
def nursery():
  # Dictionary to hold all form inputs cleanly
  form_data = {
      "payment_code": "",
      "pupil_name": "",
      "class_level": "",
      "term": "",
      "age": "",
      "color": "",
      "days_present": "",
      "current_date": "",
      "days_absent": "",
      "listening_speaking_sequencing": "",
      "music_rhymes_dance": "",
      "punctuality": "",
      "numeracy": "",
      "vocabulary": "",
      "literacy": "",
      "general_science": "",
      "environmental_awareness": "",
      "writing_skills": "",
      "physical_education": "",
      "gods_creation": "",
      "sharing": "",
      "smartness": "",
      "news": "",
      "stories": "",
      "life_skills": "",
      "general_comment": "",
      "headteachers_comment": "",
      "next_term_begins_on": "",
      "class_teacher": "",
  }

  def save_to_db():
    if not form_data["pupil_name"] or not form_data["payment_code"]:
      ui.notify(
          "Please fill in at least the Pupil Name and Payment Code.",
          color="negative",
          position="top",
      )
      return

    try:
      conn = get_db_connection()
      cursor = conn.cursor()
      try:
        cursor.execute(
            """
                    INSERT INTO nursery_results (
                        payment_code, pupil_name, class_level, term, 
                        age, color, days_present, current_date, days_absent,
                        listening_speaking_sequencing, music_rhymes_dance, punctuality, 
                        numeracy, vocabulary, literacy, general_science, 
                        environmental_awareness, writing_skills, physical_education, 
                        gods_creation, sharing, smartness, news, stories, 
                        life_skills, general_comment, headteachers_comment, 
                        next_term_begins_on, class_teacher
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
            (
                form_data["payment_code"],
                form_data["pupil_name"],
                form_data["class_level"],
                form_data["term"],
                form_data["age"],
                form_data["color"],
                form_data["days_present"],
                form_data["current_date"],
                form_data["days_absent"],
                form_data["listening_speaking_sequencing"],
                form_data["music_rhymes_dance"],
                form_data["punctuality"],
                form_data["numeracy"],
                form_data["vocabulary"],
                form_data["literacy"],
                form_data["general_science"],
                form_data["environmental_awareness"],
                form_data["writing_skills"],
                form_data["physical_education"],
                form_data["gods_creation"],
                form_data["sharing"],
                form_data["smartness"],
                form_data["news"],
                form_data["stories"],
                form_data["life_skills"],
                form_data["general_comment"],
                form_data["headteachers_comment"],
                form_data["next_term_begins_on"],
                form_data["class_teacher"],
            ),
        )
        conn.commit()
      finally:
        conn.close()
      ui.notify("✨ Report saved successfully!", color="positive", position="top")
    except Exception as e:
      ui.notify(
          f"Error saving record: {e}", color="negative", position="top"
      )

  # Fully responsive, mobile-first container using clean slate and navy blue themes
  with ui.column().classes(
      "w-full min-h-screen justify-start items-center bg-slate-50 p-2 sm:p-4 md:p-6"
  ):
    with ui.card().classes(
        "w-full max-w-4xl p-3 sm:p-6 md:p-8 bg-white shadow-xl rounded-2xl md:rounded-3xl border border-blue-100 my-2"
    ):

      # Header with Navy Blue styling
      with ui.row().classes(
          "w-full items-center justify-between bg-gradient-to-r from-blue-900 to-indigo-900 p-3 sm:p-4 rounded-xl text-white mb-4 shadow-sm"
      ):
        ui.label("🧸 Nursery Assessment Entry Form").classes(
            "text-base sm:text-lg md:text-xl font-bold"
        )
        ui.icon("child_care", size="md").classes("text-white")

      with ui.column().classes("w-full gap-3 sm:gap-4"):
        # Section 1: General Info
        with ui.expansion(
            "General & Administrative Info", icon="info"
        ).classes(
            "w-full mb-1 bg-blue-50/40 rounded-xl border border-blue-100"
        ):
          with ui.column().classes(
              "w-full gap-3 grid grid-cols-1 md:grid-cols-2 p-2 sm:p-3"
          ):
            (
                ui.input("Payment Code")
                .bind_value(form_data, "payment_code")
                .classes("w-full")
                .props("outlined dense clearable color=blue-9")
            )
            (
                ui.input("Pupil Name")
                .bind_value(form_data, "pupil_name")
                .classes("w-full")
                .props("outlined dense clearable color=blue-9")
            )
            (
                ui.select(
                    ["Baby Class", "Middle Class", "Top Class"],
                    label="Class Level",
                )
                .bind_value(form_data, "class_level")
                .classes("w-full")
                .props("outlined dense clearable color=blue-9")
            )
            (
                ui.select(
                    ["Term 1", "Term 2", "Term 3"],
                    label="Term",
                )
                .bind_value(form_data, "term")
                .classes("w-full")
                .props("outlined dense clearable color=blue-9")
            )
            (
                ui.input("Age")
                .bind_value(form_data, "age")
                .classes("w-full")
                .props("outlined dense clearable color=blue-9")
            )
            (
                ui.input("Color")
                .bind_value(form_data, "color")
                .classes("w-full")
                .props("outlined dense clearable color=blue-9")
            )
            (
                ui.input("Days Present")
                .bind_value(form_data, "days_present")
                .classes("w-full")
                .props("outlined dense clearable color=blue-9")
            )
            (
                ui.input("Days Absent")
                .bind_value(form_data, "days_absent")
                .classes("w-full")
                .props("outlined dense clearable color=blue-9")
            )
            (
                ui.input("Current Date")
                .bind_value(form_data, "current_date")
                .classes("w-full")
                .props(
                    "outlined dense clearable mask='##/##/####'"
                    " placeholder='DD/MM/YYYY' color=blue-9"
                )
            )
            (
                ui.input("Class Teacher")
                .bind_value(form_data, "class_teacher")
                .classes("w-full")
                .props("outlined dense clearable color=blue-9")
            )
            (
                ui.input("Next Term Begins On")
                .bind_value(form_data, "next_term_begins_on")
                .classes("w-full")
                .props(
                    "outlined dense clearable mask='##/##/####'"
                    " placeholder='DD/MM/YYYY' color=blue-9"
                )
            )

        # Section 2: Core Academic Competencies
        with ui.expansion(
            "Core Competencies & Skills", icon="school"
        ).classes(
            "w-full mb-1 bg-blue-50/40 rounded-xl border border-blue-100"
        ):
          with ui.column().classes(
              "w-full gap-3 grid grid-cols-1 md:grid-cols-2 p-2 sm:p-3"
          ):
            (
                ui.input("Listening, Speaking & Sequencing")
                .bind_value(form_data, "listening_speaking_sequencing")
                .classes("w-full")
                .props("outlined dense clearable color=blue-9")
            )
            (
                ui.input("Numeracy")
                .bind_value(form_data, "numeracy")
                .classes("w-full")
                .props("outlined dense clearable color=blue-9")
            )
            (
                ui.input("Literacy")
                .bind_value(form_data, "literacy")
                .classes("w-full")
                .props("outlined dense clearable color=blue-9")
            )
            (
                ui.input("Vocabulary")
                .bind_value(form_data, "vocabulary")
                .classes("w-full")
                .props("outlined dense clearable color=blue-9")
            )
            (
                ui.input("Writing Skills")
                .bind_value(form_data, "writing_skills")
                .classes("w-full")
                .props("outlined dense clearable color=blue-9")
            )
            (
                ui.input("General Science")
                .bind_value(form_data, "general_science")
                .classes("w-full")
                .props("outlined dense clearable color=blue-9")
            )
            (
                ui.input("Environmental Awareness")
                .bind_value(form_data, "environmental_awareness")
                .classes("w-full")
                .props("outlined dense clearable color=blue-9")
            )
            (
                ui.input("God's Creation")
                .bind_value(form_data, "gods_creation")
                .classes("w-full")
                .props("outlined dense clearable color=blue-9")
            )

        # Section 3: Behavioral & Co-Curricular Traits
        with ui.expansion(
            "Behavior, Life Skills & Co-Curricular", icon="psychology"
        ).classes(
            "w-full mb-1 bg-blue-50/40 rounded-xl border border-blue-100"
        ):
          with ui.column().classes(
              "w-full gap-3 grid grid-cols-1 md:grid-cols-2 p-2 sm:p-3"
          ):
            (
                ui.input("Music, Rhymes & Dance")
                .bind_value(form_data, "music_rhymes_dance")
                .classes("w-full")
                .props("outlined dense clearable color=blue-9")
            )
            (
                ui.input("Physical Education")
                .bind_value(form_data, "physical_education")
                .classes("w-full")
                .props("outlined dense clearable color=blue-9")
            )
            (
                ui.input("Punctuality")
                .bind_value(form_data, "punctuality")
                .classes("w-full")
                .props("outlined dense clearable color=blue-9")
            )
            (
                ui.input("Smartness")
                .bind_value(form_data, "smartness")
                .classes("w-full")
                .props("outlined dense clearable color=blue-9")
            )
            (
                ui.input("Sharing")
                .bind_value(form_data, "sharing")
                .classes("w-full")
                .props("outlined dense clearable color=blue-9")
            )
            (
                ui.input("Life Skills")
                .bind_value(form_data, "life_skills")
                .classes("w-full")
                .props("outlined dense clearable color=blue-9")
            )
            (
                ui.input("News")
                .bind_value(form_data, "news")
                .classes("w-full")
                .props("outlined dense clearable color=blue-9")
            )
            (
                ui.input("Stories")
                .bind_value(form_data, "stories")
                .classes("w-full")
                .props("outlined dense clearable color=blue-9")
            )

        # Section 4: Comments
        with ui.expansion("Remarks & Comments", icon="comment").classes(
            "w-full mb-1 bg-blue-50/40 rounded-xl border border-blue-100"
        ):
          with ui.column().classes("w-full gap-3 p-2 sm:p-3"):
            (
                ui.textarea("General Comment")
                .bind_value(form_data, "general_comment")
                .classes("w-full")
                .props("outlined dense clearable color=blue-9 rows=2")
            )
            (
                ui.textarea("Headteacher's Comment")
                .bind_value(form_data, "headteachers_comment")
                .classes("w-full")
                .props("outlined dense clearable color=blue-9 rows=2")
            )

        # Submit Action Button (Smaller, compact, Navy Blue styling aligned nicely)
        with ui.row().classes("w-full justify-end mt-3"):
          ui.button("Save Report Entry", on_click=save_to_db).classes(
              "px-6 py-2.5 text-white font-semibold bg-[#0A192F]"
              " hover:bg-[#020C1B] transition-all rounded-xl shadow-md text-xs"
              " sm:text-sm cursor-pointer"
          )
