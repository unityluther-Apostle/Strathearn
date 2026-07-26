import base64
import datetime
import io
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

  if val >= 80:
    return "Excellent"
  elif 70 <= val < 80:
    return "Very good"
  elif 60 <= val < 70:
    return "good"
  elif 50 <= val < 60:
    return "Credit"
  elif 45 <= val < 50:
    return "fair good"
  elif 40 <= val < 45:
    return "Fair"
  else:
    return "Improve"


def get_grade(score):
  try:
    val = float(score)
  except (ValueError, TypeError):
    return "-"

  if val >= 80:
    return "D1"
  elif 70 <= val < 80:
    return "D2"
  elif 60 <= val < 70:
    return "C3"
  elif 50 <= val < 60:
    return "C4"
  elif 45 <= val < 50:
    return "C5"
  elif 40 <= val < 45:
    return "C6"
  elif 30 <= val < 40:
    return "P8"
  else:
    return "F9"


def get_field(data, keys, default="N/A"):
  if not data:
    return default
  for key in keys:
    if key in data and data[key] is not None:
      return data[key]
  return default


def report(row_data):
  print(f"DEBUG: Data received in report: {row_data}")
  
  if row_data is None:
    row_data = {}

  today = datetime.datetime.now().strftime("%d %B %Y")
  current_year = datetime.datetime.now().year
  
  admin_id = get_field(row_data, ["Admin", "admin", "AdminNo", "AdmissionNo", "admission_no", "admin_no", "payment_code", "id"], "000")
  unique_id = f"REP-{current_year}-{admin_id}-{random.randint(100, 999)}"

  student_name = get_field(row_data, ["Name", "name", "StudentName", "student_name", "PupilName", "pupil_name"], "N/A")
  student_class = get_field(row_data, ["Class", "class", "GradeLevel", "grade_level", "ClassName", "class_name", "class_level"], "N/A")
  term = get_field(row_data, ["Term", "term"], "N/A")
  attendance = get_field(row_data, ["Attendance", "attendance"], "0")
  
  total_score = get_field(row_data, ["Total", "total", "_calc_total"], 0)
  position = get_field(row_data, ["Position", "position", "_calc_rank"], "-")
  
  ct_remarks = get_field(row_data, ["ClassTeacherRemarks", "class_teacher_remarks", "Remarks", "remarks", "ct_remarks"], "N/A")
  ht_remarks = get_field(row_data, ["HeadteacherRemarks", "headteacher_remarks", "HeadTeacherRemarks", "head_teacher_remarks", "HeadRemarks", "head_remarks", "ht_remarks", "head_teacher_comment"], "N/A")
  
  conduct = get_field(row_data, ["Conduct", "conduct", "Behaviour", "behaviour", "discipline"], "-")
  interest = get_field(row_data, ["Interest", "interest", "Hobby", "hobby", "games"], "-")

  config = {
      "school_name": "STRATHEARN PRIMARY SCHOOL MASANAFU",
      "motto": "Knowledge for Service",
      "contacts": (
          "P.O. Box 1234, Kampala | Tel: 0770 000 000 | Email:"
          " info@strathearn.ac.ug"
      ),
      "badge_filename": "badge.jpeg",
      "issue_date": today,
      "next_term_begins": "07 September 2026",
      "report_id": unique_id,
      "default_initials": {
          "maths": "T.M",
          "english": "T.E",
          "lit1": "T.L1",
          "lit2": "T.L2",
          "reading": "T.R",
          "sst": "T.S",
          "science": "T.SC",
          "re": "T.RE",
          "luganda": "T.UG"
      }
  }

  badge_data = get_image_base64(config["badge_filename"])
  badge_html = (
      f'<img src="data:image/jpeg;base64,{badge_data}" style="width: 90px;'
      ' height: auto;">'
      if badge_data
      else ""
  )
  watermark_bg = (
      f"url('data:image/jpeg;base64,{badge_data}')"
      if badge_data
      else "none"
  )

  math_score = get_field(row_data, ["Maths", "maths", "Mathematics", "mathematics"], 0)
  eng_score = get_field(row_data, ["English", "english"], 0)
  lit1_score = get_field(row_data, ["Lit1", "lit1", "Literacy1", "literacy_1", "literacy_i"], 0)
  lit2_score = get_field(row_data, ["Lit2", "lit2", "Literacy2", "literacy_2", "literacy_ii"], 0)
  reading_score = get_field(row_data, ["Reading", "reading"], 0)
  sst_score = get_field(row_data, ["SST", "sst", "SocialStudies", "social_studies"], 0)
  sci_score = get_field(row_data, ["Science", "science", "SCI", "sci"], 0)
  re_score = get_field(row_data, ["ReligiousEducation", "religious_education", "RE", "re", "re_religious_education"], 0)
  luganda_score = get_field(row_data, ["Luganda", "luganda"], 0)

  math_grade = get_field(row_data, ["Maths_Grade", "maths_grade"]) if get_field(row_data, ["Maths_Grade", "maths_grade"], None) else get_grade(math_score)
  eng_grade = get_field(row_data, ["English_Grade", "english_grade"]) if get_field(row_data, ["English_Grade", "english_grade"], None) else get_grade(eng_score)
  lit1_grade = get_field(row_data, ["Lit1_Grade", "lit1_grade"]) if get_field(row_data, ["Lit1_Grade", "lit1_grade"], None) else get_grade(lit1_score)
  lit2_grade = get_field(row_data, ["Lit2_Grade", "lit2_grade"]) if get_field(row_data, ["Lit2_Grade", "lit2_grade"], None) else get_grade(lit2_score)
  reading_grade = get_field(row_data, ["Reading_Grade", "reading_grade"]) if get_field(row_data, ["Reading_Grade", "reading_grade"], None) else get_grade(reading_score)
  sst_grade = get_field(row_data, ["SST_Grade", "sst_grade", "SocialStudies_Grade"], None) if get_field(row_data, ["SST_Grade", "sst_grade", "SocialStudies_Grade"], None) else get_grade(sst_score)
  sci_grade = get_field(row_data, ["Science_Grade", "science_grade"], None) if get_field(row_data, ["Science_Grade", "science_grade"], None) else get_grade(sci_score)
  re_grade = get_field(row_data, ["ReligiousEducation_Grade", "re_grade"], None) if get_field(row_data, ["ReligiousEducation_Grade", "re_grade"], None) else get_grade(re_score)
  luganda_grade = get_field(row_data, ["Luganda_Grade", "luganda_grade"], None) if get_field(row_data, ["Luganda_Grade", "luganda_grade"], None) else get_grade(luganda_score)

  math_comment = get_field(row_data, ["Maths_Comment", "maths_comment"], None) if get_field(row_data, ["Maths_Comment", "maths_comment"], None) else get_comment(math_score)
  eng_comment = get_field(row_data, ["English_Comment", "english_comment"], None) if get_field(row_data, ["English_Comment", "english_comment"], None) else get_comment(eng_score)
  lit1_comment = get_field(row_data, ["Lit1_Comment", "lit1_comment"], None) if get_field(row_data, ["Lit1_Comment", "lit1_comment"], None) else get_comment(lit1_score)
  lit2_comment = get_field(row_data, ["Lit2_Comment", "lit2_comment"], None) if get_field(row_data, ["Lit2_Comment", "lit2_comment"], None) else get_comment(lit2_score)
  reading_comment = get_field(row_data, ["Reading_Comment", "reading_comment"], None) if get_field(row_data, ["Reading_Comment", "reading_comment"], None) else get_comment(reading_score)
  sst_comment = get_field(row_data, ["SST_Comment", "sst_comment"], None) if get_field(row_data, ["SST_Comment", "sst_comment"], None) else get_comment(sst_score)
  sci_comment = get_field(row_data, ["Science_Comment", "science_comment"], None) if get_field(row_data, ["Science_Comment", "science_comment"], None) else get_comment(sci_score)
  re_comment = get_field(row_data, ["ReligiousEducation_Comment", "re_comment"], None) if get_field(row_data, ["ReligiousEducation_Comment", "re_comment"], None) else get_comment(re_score)
  luganda_comment = get_field(row_data, ["Luganda_Comment", "luganda_comment"], None) if get_field(row_data, ["Luganda_Comment", "luganda_comment"], None) else get_comment(luganda_score)

  math_initials = get_field(row_data, ["Maths_Initials", "maths_initials"], config["default_initials"]["maths"])
  eng_initials = get_field(row_data, ["English_Initials", "english_initials"], config["default_initials"]["english"])
  lit1_initials = get_field(row_data, ["Lit1_Initials", "lit1_initials"], config["default_initials"]["lit1"])
  lit2_initials = get_field(row_data, ["Lit2_Initials", "lit2_initials"], config["default_initials"]["lit2"])
  reading_initials = get_field(row_data, ["Reading_Initials", "reading_initials"], config["default_initials"]["reading"])
  sst_initials = get_field(row_data, ["SST_Initials", "sst_initials"], config["default_initials"]["sst"])
  sci_initials = get_field(row_data, ["Science_Initials", "science_initials"], config["default_initials"]["science"])
  re_initials = get_field(row_data, ["ReligiousEducation_Initials", "re_initials"], config["default_initials"]["re"])
  luganda_initials = get_field(row_data, ["Luganda_Initials", "luganda_initials"], config["default_initials"]["luganda"])

  return f"""
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            @page {{ size: A4; margin: 4mm; }}
            body {{ font-family: 'Inter', system-ui, -apple-system, sans-serif; color: #1f2937; background: #ffffff; padding: 0px; margin: 0px; box-sizing: border-box; -webkit-font-smoothing: antialiased; }}
            
            .card {{ 
                background: white; padding: 18px 26px; 
                border: 12px solid #1b4d3e; 
                border-style: groove;
                outline: 3px dashed #d97706; 
                outline-offset: -15px;
                position: relative;
                box-sizing: border-box;
                width: 100%;
                height: 289mm; 
                max-height: 289mm;
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
                background-size: 500px auto; 
                opacity: 0.05; 
                z-index: 0; 
                pointer-events: none; 
            }}

            .card > * {{ position: relative; z-index: 1; }}
            
            @media print {{ 
                body {{ background: white; }}
                .page-break {{ page-break-after: always; break-after: page; }}
                .card {{ width: 100%; height: 289mm; max-height: 289mm; padding: 18px 26px; border: 12px solid #1b4d3e; border-style: groove; outline: 3px dashed #d97706; outline-offset: -15px; page-break-inside: avoid; break-inside: avoid; margin: 0; }} 
            }}
            
            .header {{ text-align: center; margin-bottom: 6px; }}
            .school-title {{ font-size: 24px; font-weight: 800; color: #1b4d3e; letter-spacing: -0.3px; line-height: 1.2; }}
            .motto {{ font-size: 13px; font-style: italic; color: #d97706; margin-top: 2px; font-weight: 700; }}
            .contact-info {{ font-size: 11.5px; color: #4b5563; margin-top: 3px; font-weight: 600; border-top: 1px solid #e5e7eb; padding-top: 4px; }}
            .report-title {{ font-size: 14.5px; font-weight: 800; color: #1b4d3e; text-transform: uppercase; letter-spacing: 1.2px; margin-top: 4px; }}
            .report-id {{ font-size: 11px; font-weight: 600; color: #6b7280; text-align: right; margin-bottom: 0px; }}
            
            .meta-table {{ width: 100%; margin-bottom: 8px; border-collapse: separate; border-spacing: 0 3px; }}
            .meta-table td {{ padding: 4px 6px; font-size: 13.5px; }}
            .label {{ font-weight: 700; color: #1b4d3e; width: 135px; }}
            .value {{ font-weight: 800; color: #111827; }}
            
            .marks-table {{ width: 100%; border-collapse: collapse; margin-top: 4px; border-radius: 6px; overflow: hidden; border: 1px solid #d1d5db; }}
            .marks-table th {{ background: #1b4d3e; color: white; padding: 7px 9px; text-align: left; font-size: 13px; font-weight: 700; }}
            .marks-table td {{ padding: 6px 9px; border-bottom: 1px solid #e5e7eb; font-size: 13px; color: #1f2937; }}
            .marks-table td.full-marks-cell {{ background: #fef3c7; color: #92400e; font-weight: 800; }}
            
            /* Initial styling with a distinct color */
            .initials-badge {{ color: #1e3a8a; font-weight: 800; background: #eff6ff; padding: 2px 6px; border-radius: 4px; border: 1px solid #bfdbfe; display: inline-block; }}
            
            .key-table {{ width: 100%; margin-top: 8px; font-size: 11.5px; font-weight: 500; text-align: center; color: #374151; border: 1px solid #d1d5db; padding: 5px; border-radius: 5px; background: #f9fafb; }}
            .grade-badge {{ background: #ecfdf5; color: #065f46; padding: 2px 8px; border-radius: 99px; font-weight: 800; font-size: 13px; border: 1px solid #a7f3d0; display: inline-block; }}
            
            .summary-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin-top: 8px; }}
            .metric-card {{ background: #f0fdf4; border: 1px solid #bbf7d0; padding: 7px; text-align: center; border-radius: 6px; }}
            .metric-title {{ font-size: 11.5px; color: #166534; font-weight: 700; text-transform: uppercase; }}
            .metric-value {{ font-size: 18px; font-weight: 800; color: #14532d; margin-top: 1px; }}
            
            .remarks-container {{ display: flex; gap: 10px; margin-top: 8px; }}
            .remarks-box {{ flex: 1; border: 1px solid #d1d5db; padding: 7px 10px; border-radius: 6px; font-size: 13px; background: #fafafa; line-height: 1.35; }}
            
            .extra-info-bar {{ display: flex; flex-direction: column; gap: 6px; margin-top: 8px; background: #fffbeb; border: 1px solid #fcd34d; padding: 7px 12px; border-radius: 6px; font-size: 12.5px; }}
            .extra-info-item {{ width: 100%; display: flex; justify-content: space-between; align-items: center; }}
            .extra-label {{ font-weight: 700; color: #92400e; text-transform: uppercase; font-size: 12px; }}
            .extra-val {{ font-weight: 800; color: #111827; font-size: 13px; }}

            .footer-container {{ display: flex; justify-content: space-between; align-items: flex-end; margin-top: 8px; }}
            .stamp-area {{ border: 2px dashed #9ca3af; width: 95px; height: 52px; display: flex; align-items: center; justify-content: center; font-size: 10.5px; font-weight: 700; color: #6b7280; text-align: center; border-radius: 5px; background: #fafafa; }}
            .footer-sign {{ flex: 1; display: flex; flex-direction: column; align-items: center; }}
            .signature-line {{ border-top: 2px solid #1b4d3e; padding-top: 10px; width: 220px; text-align: center; font-size: 13px; font-weight: 700; color: #1b4d3e; }}
            
            .footer-info {{ text-align: center; font-size: 11.5px; font-weight: 600; color: #4b5563; margin-top: 8px; padding-top: 4px; border-top: 1px solid #e5e7eb; }}
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
                    <div class="report-title">Primary Terminal Report Card</div>
                </div>
                
                <table class="meta-table">
                    <tr><td class="label">STUDENT:</td><td class="value">{student_name}</td><td class="label">CLASS:</td><td class="value">{student_class}</td></tr>
                    <tr><td class="label">PAYMENT CODE:</td><td class="value">{admin_id}</td><td class="label">TERM:</td><td class="value">{term}</td></tr>
                    <tr><td class="label">ATTENDANCE:</td><td class="value">{attendance} days</td><td class="label"></td><td class="value"></td></tr>
                </table>

                <table class="marks-table">
                    <thead>
                        <tr>
                            <th>Subject</th>
                            <th>Full Marks</th>
                            <th>Marks Scored</th>
                            <th>Grade</th>
                            <th>Comment</th>
                            <th>Initials</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td class="value">Mathematics</td>
                            <td class="full-marks-cell">{get_field(row_data, ['Maths_Full', 'maths_full'], 100)}</td>
                            <td>{math_score}</td>
                            <td><span class="grade-badge">{math_grade}</span></td>
                            <td>{math_comment}</td>
                            <td><span class="initials-badge">{math_initials}</span></td>
                        </tr>
                        <tr>
                            <td class="value">English</td>
                            <td class="full-marks-cell">{get_field(row_data, ['English_Full', 'english_full'], 100)}</td>
                            <td>{eng_score}</td>
                            <td><span class="grade-badge">{eng_grade}</span></td>
                            <td>{eng_comment}</td>
                            <td><span class="initials-badge">{eng_initials}</span></td>
                        </tr>
                        <tr>
                            <td class="value">Literacy I</td>
                            <td class="full-marks-cell">{get_field(row_data, ['Lit1_Full', 'lit1_full'], 100)}</td>
                            <td>{lit1_score}</td>
                            <td><span class="grade-badge">{lit1_grade}</span></td>
                            <td>{lit1_comment}</td>
                            <td><span class="initials-badge">{lit1_initials}</span></td>
                        </tr>
                        <tr>
                            <td class="value">Literacy II</td>
                            <td class="full-marks-cell">{get_field(row_data, ['Lit2_Full', 'lit2_full'], 100)}</td>
                            <td>{lit2_score}</td>
                            <td><span class="grade-badge">{lit2_grade}</span></td>
                            <td>{lit2_comment}</td>
                            <td><span class="initials-badge">{lit2_initials}</span></td>
                        </tr>
                        <tr>
                            <td class="value">Reading</td>
                            <td class="full-marks-cell">{get_field(row_data, ['Reading_Full', 'reading_full'], 100)}</td>
                            <td>{reading_score}</td>
                            <td><span class="grade-badge">{reading_grade}</span></td>
                            <td>{reading_comment}</td>
                            <td><span class="initials-badge">{reading_initials}</span></td>
                        </tr>
                        <tr>
                            <td class="value">Social Studies (SST)</td>
                            <td class="full-marks-cell">{get_field(row_data, ['SST_Full', 'sst_full'], 100)}</td>
                            <td>{sst_score}</td>
                            <td><span class="grade-badge">{sst_grade}</span></td>
                            <td>{sst_comment}</td>
                            <td><span class="initials-badge">{sst_initials}</span></td>
                        </tr>
                        <tr>
                            <td class="value">Integrated Science</td>
                            <td class="full-marks-cell">{get_field(row_data, ['Science_Full', 'science_full'], 100)}</td>
                            <td>{sci_score}</td>
                            <td><span class="grade-badge">{sci_grade}</span></td>
                            <td>{sci_comment}</td>
                            <td><span class="initials-badge">{sci_initials}</span></td>
                        </tr>
                        <tr>
                            <td class="value">Religious Education</td>
                            <td class="full-marks-cell">{get_field(row_data, ['ReligiousEducation_Full', 'religious_education_full'], 100)}</td>
                            <td>{re_score}</td>
                            <td><span class="grade-badge">{re_grade}</span></td>
                            <td>{re_comment}</td>
                            <td><span class="initials-badge">{re_initials}</span></td>
                        </tr>
                        <tr>
                            <td class="value">Luganda</td>
                            <td class="full-marks-cell">{get_field(row_data, ['Luganda_Full', 'luganda_full'], 100)}</td>
                            <td>{luganda_score}</td>
                            <td><span class="grade-badge">{luganda_grade}</span></td>
                            <td>{luganda_comment}</td>
                            <td><span class="initials-badge">{luganda_initials}</span></td>
                        </tr>
                    </tbody>
                </table>
            
                <div class="summary-grid">
                    <div class="metric-card"><div class="metric-title">Total Marks</div><div class="metric-value">{total_score}</div></div>
                    <div class="metric-card"><div class="metric-title">Position</div><div class="metric-value">{position}</div></div>
                </div>

                <div class="key-table">
                    <b>Grading Key:</b> D1 (80-100) | D2 (70-79) | C3 (60-69) | C4 (50-59) | C5 (45-49) | C6 (40-44) | P8 (30-39) | F9 (0-29)
                </div>

                <div class="remarks-container">
                    <div class="remarks-box"><div class="label" style="margin-bottom:2px; font-size:12px;">Class Teacher's Remarks:</div><i>"{ct_remarks}"</i></div>
                    <div class="remarks-box"><div class="label" style="margin-bottom:2px; font-size:12px;">Headteacher's Remarks:</div><i>"{ht_remarks}"</i></div>
                </div>

                <div class="extra-info-bar">
                    <div class="extra-info-item"><span class="extra-label">Conduct & Discipline:</span> <span class="extra-val">{conduct}</span></div>
                    <div class="extra-info-item" style="border-top: 1px solid #fde68a; padding-top: 3px;"><span class="extra-label">Co-Curricular/Interest:</span> <span class="extra-val">{interest}</span></div>
                </div>
            </div>
            
            <div>
                <div class="footer-container">
                    <div class="stamp-area">OFFICIAL<br>STAMP</div>
                    <div class="footer-sign">
                        <div class="signature-line">Headteacher Signature</div>
                    </div>
                </div>

                <div class="footer-info">
                    Issued on: {config['issue_date']} | Next Term Begins: {config['next_term_begins']}
                </div>
            </div>
        </div>
    </body>
    </html>
    """
