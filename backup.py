import sqlite3
import smtplib
import os
import time
import threading
from email.message import EmailMessage

# Configuration
DB = 'School_Results_Database.db'
BACKUP_FILE = 'School_Results_Backup.db'
SENDER_EMAIL = "Postywalker@gmail.com"  # Use a dedicated sender account
PASSWORD = "ba"        # Use an App Password, NOT your main password
RECIPIENT = "unityluther@gmail.com"

def backup_db():
    # 1. Create a safe binary copy of the database
    source = sqlite3.connect(DB)
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

def run_backup_job():
    try:
        backup_file = backup_db()
        send_email(backup_file)
        print("Database backup and email sent successfully.")
    except Exception as e:
        print(f"Backup failed: {e}")

def trigger_immediate_backup():
    """Call this function right after saving or updating critical grades to backup immediately in the background."""
    print("Critical data updated! Triggering immediate background backup...")
    threading.Thread(target=run_backup_job, daemon=True).start()

def background_backup_loop():
    while True:
        # Wait for 12 hours (12 hours * 60 minutes * 60 seconds)
        time.sleep(12 * 60 * 60)
        run_backup_job()

if __name__ == "__main__":
    # Optional: Run immediately on startup once, or comment out if you only want to wait for the first 12-hour interval
    run_backup_job()

    # Start the background backup thread as a daemon so it runs continuously without blocking app shutdown
    backup_thread = threading.Thread(target=background_backup_loop, daemon=True)
    backup_thread.start()
