import sqlite3
import smtplib
import os
from email.message import EmailMessage

# Configuration
DB_FILE = 'School_Results_Database.db'
BACKUP_FILE = 'School_Results_Backup.db'
SENDER_EMAIL = "your_email@gmail.com"  # Use a dedicated sender account
PASSWORD = "your_app_password"         # Use an App Password, NOT your main password
RECIPIENT = "unityluther@gmail.com"

def backup_db():
    # 1. Create a safe binary copy of the database
    source = sqlite3.connect(DB_FILE)
    backup = sqlite3.connect(BACKUP_FILE)
    source.backup(backup)
    backup.close()
    source.close()
    return BACKUP_FILE

def send_email(file_path):
    msg = EmailMessage()
    msg['Subject'] = 'School Database Automated Backup'
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECIPIENT
    msg.set_content('Attached is the latest automated database backup.')

    with open(file_path, 'rb') as f:
        msg.add_attachment(f.read(), maintype='application', subtype='octet-stream', filename=os.path.basename(file_path))

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(SENDER_EMAIL, PASSWORD)
        smtp.send_message(msg)

if __name__ == "__main__":
    backup_file = backup_db()
    send_email(backup_file)
