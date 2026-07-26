import sqlite3
import bcrypt

passkey = "passkey.db"

Table = {
    "Users": '''Username TEXT UNIQUE, Password  BLOB, Email TEXT UNIQUE '''
}
conn = sqlite3.connect("passkey.db")
cursor = conn.cursor()

cursor.execute("PRAGMA foreign_keys = ON;")

for table_name, columns in Table.items():
    query = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns});"
    cursor.execute(query)

conn.commit()
conn.close()

def  fetch_tables(table_name):
    conn = sqlite3.connect("passkey.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = f"SELECT * FROM {table_name};"
    cursor.execute(query)
    rows = cursor.fetchall()

    conn.close()
    return [dict(row) for row in rows]

print(f"The tables created are: {len(Table)}")


def  add_user(username, plain_password, email):
    password_bytes = plain_password.encode('utf-8')
    hashed_password = bcrypt.hashpw(password_bytes, bcrypt.gensalt() )
    conn = sqlite3.connect("passkey.db")
    cursor = conn.cursor()

    try:
        cursor.execute(
        "INSERT INTO Users (Username, Password, Email) VALUES(?,?,?);",(username, hashed_password,email)
        )
        conn.commit()
        print(f"User {username} added successfully!!!!")
    except sqlite3.IntegrityError as e:
        print(f"Registration Failed: Username or Email already exists. {e}")
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        conn.close()

#this block of code helps in fetching the username from the database and verifies the password
def verify_user(username, plain_password):

    conn = sqlite3.connect("passkey.db")
    cursor = conn.cursor()
    
    try:
        # this block of code helps in  Securely fetching only the password for the given username
        cursor.execute("SELECT Password FROM Users WHERE Username = ?;", (username,))
        row = cursor.fetchone()
        
        if row is None:
            print(f"Verification Failed: User '{username}' not found.")
            return False
            
        stored_hash = row[0] # This is the string we stored
        
        # this block of code is to encode the plain text password text input
        provided_password_bytes = plain_password.encode('utf-8')
                
        # this block of code Checks if the provided password matches the hash
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

#this block of code allows a user reset their password incase he forgots it but after verifying that the username and email exist in the database
def reset_password(username, email, new_plain_password):

    password_bytes = new_plain_password.encode('utf-8')
    hashed_password = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    conn = sqlite3.connect("passkey.db")
    cursor = conn.cursor()

    try:
        #this block of code first Checks if the username and email match an existing account first
        cursor.execute("SELECT * FROM Users WHERE Username = ? AND Email = ?;", (username, email))
        if cursor.fetchone() is None:
            conn.close()
            raise ValueError("Username or Email does not match our records.")

        # this block of code Updates the created password  to the new secure hashed password
        cursor.execute("UPDATE Users SET Password = ? WHERE Username = ? AND Email = ?;", 
                       (hashed_password, username, email))
        conn.commit()
        print(f"Password for user {username} reset successfully!")
    except Exception as e:
        conn.close()
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
