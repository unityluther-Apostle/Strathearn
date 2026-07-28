import sqlite3
import bcrypt

passkey = "School_Results_Database.db"

Table = {
    "Users": '''Username TEXT UNIQUE, Password BLOB, Email TEXT UNIQUE, current_session_id TEXT'''
}
conn = sqlite3.connect(passkey)
cursor = conn.cursor()

cursor.execute("PRAGMA foreign_keys = ON;")

for table_name, columns in Table.items():
    query = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns});"
    cursor.execute(query)

# Ensure current_session_id column exists if table was already created previously without it
try:
    cursor.execute("PRAGMA table_info(Users)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'current_session_id' not in columns:
        cursor.execute("ALTER TABLE Users ADD COLUMN current_session_id TEXT")
except Exception as e:
    print(f"Migration error: {e}")

conn.commit()
conn.close()

def fetch_tables(table_name):
    conn = sqlite3.connect(passkey)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = f"SELECT * FROM {table_name};"
    cursor.execute(query)
    rows = cursor.fetchall()

    conn.close()
    return [dict(row) for row in rows]

print(f"The tables created are: {len(Table)}")


def add_user(username, plain_password, email):
    password_bytes = plain_password.encode('utf-8')
    hashed_password = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    conn = sqlite3.connect(passkey)
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO Users (Username, Password, Email) VALUES(?,?,?);", (username, hashed_password, email)
        )
        conn.commit()
        print(f"User {username} added successfully!!!!")
    except sqlite3.IntegrityError as e:
        print(f"Registration Failed: Username or Email already exists. {e}")
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        conn.close()

def verify_user(username, plain_password):
    conn = sqlite3.connect(passkey)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT Password FROM Users WHERE Username = ?;", (username,))
        row = cursor.fetchone()
        
        if row is None:
            print(f"Verification Failed: User '{username}' not found.")
            return False
            
        stored_hash = row[0]
        provided_password_bytes = plain_password.encode('utf-8')
                
        if bcrypt.checkpw(provided_password_bytes, stored_hash):
            print(f"Verification Successful: Welcome back, {username}!")
            return True
        else:
            print("Verification Failed: Invalid password.")
            return False
            
    except sqlite3.Error as e:
        print(f"Database error during verification: {e}")
        return False
    finally:
        conn.close()

def reset_password(username, email, new_plain_password):
    password_bytes = new_plain_password.encode('utf-8')
    hashed_password = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    conn = sqlite3.connect(passkey)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM Users WHERE Username = ? AND Email = ?;", (username, email))
        if cursor.fetchone() is None:
            conn.close()
            raise ValueError("Username or Email does not match our records.")

        cursor.execute("UPDATE Users SET Password = ? WHERE Username = ? AND Email = ?;", 
                       (hashed_password, username, email))
        conn.commit()
        print(f"Password for user {username} reset successfully!")
    except Exception as e:
        conn.close()
        raise e
    finally:
        conn.close()
