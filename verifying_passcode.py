import os
import bcrypt
import libsql  # Make sure 'libsql' is in your requirements.txt

# --- Centralized Database Connection ---
def get_db_connection():
    """Connects directly to your Turso Cloud database over the network."""
    url = os.environ.get("TURSO_DATABASE_URL")
    auth_token = os.environ.get("TURSO_AUTH_TOKEN")
    
    if not url or not auth_token:
        raise ValueError("Missing TURSO_DATABASE_URL or TURSO_AUTH_TOKEN environment variables!")
        
    # This connects directly to the cloud database via HTTP. No local file needed!
    return libsql.connect(database=url, auth_token=auth_token)

# --- Database Initialization ---
try:
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("PRAGMA foreign_keys = ON;")

    Table = {
        "Users": '''Username TEXT UNIQUE, Password BLOB, Email TEXT UNIQUE'''
    }

    for table_name, columns in Table.items():
        query = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns});"
        cursor.execute(query)

    conn.commit()
    print(f"The tables created are: {len(Table)}")
    conn.close()
except Exception as e:
    print(f"Failed to initialize database: {e}")


def fetch_tables(table_name):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        query = f"SELECT * FROM {table_name};"
        cursor.execute(query)
        rows = cursor.fetchall()
        
        # Extract column names to create dictionaries (Safe replacement for sqlite3.Row)
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in rows]
    finally:
        conn.close()

def add_user(username, plain_password, email):
    password_bytes = plain_password.encode('utf-8')
    hashed_password = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO Users (Username, Password, Email) VALUES(?,?,?);",
            (username, hashed_password, email)
        )
        conn.commit()
        print(f"User {username} added successfully!!!!")
    except Exception as e: 
        # Catches the equivalent of sqlite3.IntegrityError and other DB errors
        print(f"Registration Failed (Username or Email already exists?): {e}")
    finally:
        conn.close()

def verify_user(username, plain_password):
    conn = get_db_connection()
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
            
    except Exception as e:
        print(f"Database error during verification: {e}")
        return False
    finally:
        conn.close()

def reset_password(username, email, new_plain_password):
    password_bytes = new_plain_password.encode('utf-8')
    hashed_password = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM Users WHERE Username = ? AND Email = ?;", (username, email))
        if cursor.fetchone() is None:
            raise ValueError("Username or Email does not match our records.")

        cursor.execute("UPDATE Users SET Password = ? WHERE Username = ? AND Email = ?;", 
                       (hashed_password, username, email))
        conn.commit()
        print(f"Password for user {username} reset successfully!")
    except Exception as e:
        raise e
    finally:
        conn.close()

if __name__ == "__main__":
    print("--- Preparing Database State ---")
    # Dynamically inject the user before testing to guarantee they exist
    add_user("Apostle", "password1234", "samsung@gmail.com")

    print("\n--- Starting Verification Tests ---")
    
    print("Attempt 1: Wrong Password")
    verify_user("Apostle", "Wrong_pass")

    print("\nAttempt 2: Correct Password")
    verify_user("Apostle", "password1234")
