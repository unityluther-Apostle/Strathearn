import base64
import datetime
import os
import random
from nicegui import ui
import polars as pl


def get_image_base64(path):
  if os.path.exists(path):
    with open(path, "rb") as image_file:
      return base64.b64encode(image_file.read()).decode("utf-8")
  return None


def get_comment(score):
  try:
    val = float(score)
  except (ValueError, TypeError):
    return "-"

  if val >= 4.5:
    return "Star Pupil"
  elif 3.5 <= val < 4.5:
    return "Great Job"
  elif 2.5 <= val < 3.5:
    return "Good Effort"
  elif 2.0 <= val < 2.5:
    return "Growing"
  else:
    return "Keep Trying"


def get_field(data, keys, default="N/A"):
  if not data:
    return default
  for key in keys:
    if key in data and data[key] is not None:
      return data[key]
  return default


def report(row_data):
  print(f"DEBUG: Data received in nursery report: {row_data}")
  
  if row_data is None:
    row_data = {}

  today = datetime.datetime.now().strftime("%d %B %Y")
  current_year = datetime.datetime.now().year
  
  admin_id = get_field(row_data, ["Admin", "admin", "AdminNo", "AdmissionNo", "admission_no", "admin_no", "id"], "000")
  unique_id = f"KID-REP-{current_year}-{admin_id}-{random.randint(100, 999)}"

  student_name = get_field(row_data, ["Name", "name", "StudentName", "student_name", "PupilName", "pupil_name"], "N/A")
  student_class = get_field(row_data, ["Class", "class", "GradeLevel", "grade_level", "ClassName", "class_name"], "N/A")
  term = get_field(row_data, ["Term", "term"], "N/A")
  age = get_field(row_data, ["Age", "age"], "N/A")
  attendance = get_field(row_data, ["Attendance", "attendance"], "0")
  days_absent = get_field(row_data, ["DaysAbsent", "days_absent", "Absent", "absent"], "0")
  
  ct_remarks = get_field(row_data, ["ClassTeacherRemarks", "class_teacher_remarks", "Remarks", "remarks", "ct_remarks"], "N/A")
  ht_remarks = get_field(row_data, ["HeadteacherRemarks", "headteacher_remarks", "HeadTeacherRemarks", "head_teacher_remarks", "ht_remarks"], "N/A")

  config = {
      "school_name": "STRATHEARN NURSERY SCHOOL MASANAFU",
      "motto": "Learning through Play and Discovery",
      "contacts": (
          "P.O. Box 1234, Kampala | Tel: 0770 000 000 | Email:"
          " nursery@strathearn.ac.ug"
      ),
      "badge_filename": "badge.jpeg",
      "issue_date": today,
      "next_term_begins": "07 September 2026",
      "report_id": unique_id,
  }

  badge_data = get_image_base64(config["badge_filename"])
  badge_html = (
      f'<img src="data:image/jpeg;base64,{badge_data}" style="width: 70px;'
      ' height: auto;">'
      if badge_data
      else ""
  )
  watermark_bg = (
      f"url('data:image/jpeg;base64,{badge_data}')"
      if badge_data
      else "none"
  )

  categories = [
      {
          "name": "Cognitive Skills",
          "color": "#06d6a0",
          "border": "#118ab2",
          "bg": "#eefcfa",
          "items": [
              ("Numeracy", get_field(row_data, ["Numeracy", "numeracy"], "-")),
              ("Vocabulary", get_field(row_data, ["Vocabulary", "vocabulary"], "-")),
              ("Science", get_field(row_data, ["Science", "science"], "-")),
          ]
      },
      {
          "name": "Communication & Language",
          "color": "#118ab2",
          "border": "#073b4c",
          "bg": "#eef4f8",
          "items": [
              ("Listening", get_field(row_data, ["Listening", "listening"], "-")),
              ("Speaking", get_field(row_data, ["Speaking", "speaking"], "-")),
              ("Sequencing", get_field(row_data, ["Sequencing", "sequencing"], "-")),
          ]
      },
      {
          "name": "Creative & Expressive Arts",
          "color": "#ff70a6",
          "border": "#ef476f",
          "bg": "#fff0f5",
          "items": [
              ("Music", get_field(row_data, ["Music", "music"], "-")),
              ("Rhymes", get_field(row_data, ["Rhymes", "rhymes"], "-")),
              ("Dance", get_field(row_data, ["Dance", "dance"], "-")),
          ]
      },
      {
          "name": "Physical Development",
          "color": "#ffd166",
          "border": "#f4a261",
          "bg": "#fffdf4",
          "items": [
              ("Gross Motor Development", get_field(row_data, ["GrossMotor", "gross_motor"], "-")),
          ]
      },
      {
          "name": "Affective & Social Skills",
          "color": "#7b2cbf",
          "border": "#3c096c",
          "bg": "#f7f0fc",
          "items": [
              ("Sharing", get_field(row_data, ["Sharing", "sharing"], "-")),
              ("Stories", get_field(row_data, ["Stories", "stories"], "-")),
              ("Life Skills", get_field(row_data, ["LifeSkills", "life_skills"], "-")),
          ]
      }
  ]

  def generate_category_table(cat):
    rows_html = ""
    for skill, score in cat["items"]:
      comment = get_comment(score)
      rows_html += f"""
        <tr>
            <td class="value">{skill}</td>
            <td class="score-cell">{score}</td>
            <td><span class="comment-badge">{comment}</span></td>
        </tr>
      """
    return f"""
      <table class="marks-table" style="border-color: {cat['border']};">
          <thead>
              <tr style="background: {cat['color']}; color: #ffffff;">
                  <th colspan="3" style="padding: 6px 12px; font-size: 14px; font-weight: 700; text-align: left; text-shadow: 1px 1px 0px rgba(0,0,0,0.1);">{cat['name']}</th>
              </tr>
          </thead>
          <tbody style="background: {cat['bg']};">
              {rows_html}
          </tbody>
      </table>
    """

  grid_html = ""
  for i in range(0, len(categories), 2):
    table1 = generate_category_table(categories[i])
    table2 = generate_category_table(categories[i+1]) if i + 1 < len(categories) else '<div style="flex: 1;"></div>'
    grid_html += f"""
      <div class="table-row">
          <div class="table-cell-wrapper">{table1}</div>
          <div class="table-cell-wrapper">{table2}</div>
      </div>
    """

  return f"""
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Fredoka:wght@400;600;700&display=swap');
            @page {{ size: A4; margin: 3mm; }}
            body {{ font-family: 'Fredoka', cursive, sans-serif; color: #374151; background: #fffdf9; padding: 0px; margin: 0px; box-sizing: border-box; -webkit-font-smoothing: antialiased; }}
            
            .card {{ 
                background: #ffffff; padding: 12px 18px; 
                border: 10px solid #ff70a6; 
                border-style: solid;
                border-radius: 20px;
                outline: 4px dashed #ffd166; 
                outline-offset: -14px;
                position: relative;
                box-sizing: border-box;
                width: 100%;
                height: 291mm; 
                max-height: 291mm;
                overflow: hidden;
                display: flex;
                flex-direction: column;
                justify-content: space-between; 
                page-break-inside: avoid;
                break-inside: avoid;
                margin: 0 auto;
            }}

            .card::before {{ 
                content: ""; 
                position: absolute; 
                top: 0; 
                left: 0; 
                width: 100%; 
                height: 100%; 
                background-image: {watermark_bg}; 
                background-repeat: no-repeat; 
                background-position: center; 
                background-size: 400px auto; 
                opacity: 0.04; 
                z-index: 0; 
                pointer-events: none; 
            }}

            .card > * {{ position: relative; z-index: 1; }}
            
            @media print {{ 
                body {{ background: white; }}
                .page-break {{ page-break-after: always; break-after: page; }}
                .card {{ width: 100%; height: 291mm; max-height: 291mm; padding: 12px 18px; border: 10px solid #ff70a6; border-radius: 20px; outline: 4px dashed #ffd166; outline-offset: -14px; page-break-inside: avoid; break-inside: avoid; margin: 0; }} 
            }}
            
            .header {{ text-align: center; margin-bottom: 2px; }}
            .school-title {{ font-size: 20px; font-weight: 700; color: #118ab2; letter-spacing: 0.5px; line-height: 1.1; text-shadow: 1px 1px 0px #ffd166; }}
            .motto {{ font-size: 11px; font-style: italic; color: #ef476f; margin-top: 1px; font-weight: 600; }}
            .contact-info {{ font-size: 10px; color: #6c757d; margin-top: 1px; font-weight: 500; border-top: 2px dotted #e9ecef; padding-top: 2px; }}
            .report-title {{ font-size: 12.5px; font-weight: 700; color: #073b4c; text-transform: uppercase; letter-spacing: 1px; margin-top: 2px; background: #ffd166; display: inline-block; padding: 2px 12px; border-radius: 10px; }}
            .report-id {{ font-size: 9.5px; font-weight: 600; color: #adb5bd; text-align: right; margin-bottom: 0px; }}
            
            .meta-table {{ width: 100%; margin-bottom: 4px; background: #e0fbfc; border-radius: 8px; padding: 4px 10px; border-collapse: separate; border-spacing: 0 2px; }}
            .meta-table td {{ padding: 3px 6px; font-size: 12px; }}
            .label {{ font-weight: 600; color: #118ab2; width: 105px; }}
            .value {{ font-weight: 700; color: #2b2d42; }}
            
            .tables-grid {{ display: flex; flex-direction: column; gap: 6px; width: 100%; margin: 0 auto; }}
            .table-row {{ display: flex; gap: 8px; width: 100%; }}
            .table-cell-wrapper {{ flex: 1; }}
            
            .marks-table {{ width: 100%; border-collapse: collapse; border-radius: 6px; overflow: hidden; border: 2px solid; box-shadow: 0 1px 3px rgba(0,0,0,0.02); }}
            .marks-table td {{ padding: 6px 12px; border-bottom: 1px solid rgba(0,0,0,0.05); font-size: 13px; color: #334155; }}
            .score-cell {{ font-weight: 700; color: #ef476f; width: 60px; text-align: center; font-size: 13.5px; }}
            
            .comment-badge {{ background: #ffffff; color: #073b4c; padding: 2px 8px; border-radius: 8px; font-weight: 600; font-size: 12px; border: 1px solid rgba(0,0,0,0.1); display: inline-block; }}
            
            .remarks-container {{ display: flex; gap: 8px; margin-top: 4px; }}
            .remarks-box {{ flex: 1; border: 2px dashed #118ab2; padding: 6px 10px; border-radius: 8px; font-size: 11.5px; background: #f0f3ff; line-height: 1.25; }}
            
            .next-term-banner {{ background: #ff70a6; color: #ffffff; text-align: center; padding: 6px 10px; border-radius: 8px; font-size: 13px; font-weight: 700; margin-top: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border: 2px dashed #ffd166; }}
            .next-term-banner span {{ background: #ffffff; color: #ef476f; padding: 1px 8px; border-radius: 6px; font-size: 13.5px; margin-left: 6px; }}

            .footer-container {{ display: flex; justify-content: space-between; align-items: flex-end; margin-top: 4px; }}
            .stamp-area {{ border: 2px dashed #118ab2; width: 130px; height: 45px; display: flex; align-items: center; justify-content: center; font-size: 10px; font-weight: 700; color: #118ab2; text-align: center; border-radius: 8px; background: #f0f3ff; }}
            .footer-sign {{ flex: 1; display: flex; flex-direction: column; align-items: center; }}
            .signature-line {{ border-top: 2px dotted #118ab2; padding-top: 4px; width: 160px; text-align: center; font-size: 11px; font-weight: 700; color: #118ab2; }}
            
            .footer-info {{ text-align: center; font-size: 10px; font-weight: 600; color: #6c757d; margin-top: 4px; padding-top: 2px; border-top: 1px solid #e9ecef; }}
        </style>
    </head>
    <body>
        <div class="card">
            <div>
                <div class="report-id">ID: {config['report_id']}</div>
                <div class="header">
                    {badge_html}
                    <div class="school-title">{config['school_name']}</div>
                    <div class="motto">"{config['motto']}"</div>
                    <div class="contact-info">{config['contacts']}</div>
                    <div class="report-title">Little Star Progress Report</div>
                </div>
                
                <table class="meta-table">
                    <tr><td class="label">PUPIL NAME:</td><td class="value">{student_name}</td><td class="label">CLASS:</td><td class="value">{student_class}</td></tr>
                    <tr><td class="label">AGE:</td><td class="value">{age}</td><td class="label">TERM:</td><td class="value">{term}</td></tr>
                    <tr><td class="label">PRESENT:</td><td class="value">{attendance} days</td><td class="label">ABSENT:</td><td class="value">{days_absent} days</td></tr>
                </table>

                <div class="tables-grid">
                    {grid_html}
                </div>

                <div class="remarks-container">
                    <div class="remarks-box"><div class="label" style="margin-bottom:2px; font-size:11px;">Teacher's Sweet Notes:</div><i>"{ct_remarks}"</i></div>
                    <div class="remarks-box"><div class="label" style="margin-bottom:2px; font-size:11px;">Headteacher's Cheers:</div><i>"{ht_remarks}"</i></div>
                </div>
            </div>
            
            <div>
                <div class="next-term-banner">
                    NEXT TERM BEGINS ON: <span>{config['next_term_begins']}</span>
                </div>

                <div class="footer-container">
                    <div class="stamp-area">Official Stamp area</div>
                    <div class="footer-sign">
                        <div class="signature-line">Headteacher Signature</div>
                    </div>
                </div>

                <div class="footer-info">
                    Issued on: {config['issue_date']}
                </div>
            </div>
        </div>
    </body>
    </html>
    """
