import os
import sqlite3
import psycopg2

# 1. Connect to the SQLite file currently sitting on Render's disk
sqlite_conn = sqlite3.connect("School_Results_Database.db")
sqlite_cursor = sqlite_conn.cursor()

# 2. Grab the Render Environment Variable automatically
database_url = os.environ.get("DATABASE_URL")
if not database_url:
    print("ERROR: DATABASE_URL environment variable is missing!")
    exit(1)

pg_conn = psycopg2.connect(database_url)
pg_cursor = pg_conn.cursor()

# Get your school tables
sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
tables = [row[0] for row in sqlite_cursor.fetchall()]

print(f"Found tables to migrate: {tables}")

for table in tables:
    print(f"Migrating table: {table}...")
    
    # Read the data from SQLite
    sqlite_cursor.execute(f'SELECT * FROM "{table}"')
    rows = sqlite_cursor.fetchall()
    
    if not rows:
        continue

    # Read the columns
    sqlite_cursor.execute(f'PRAGMA table_info("{table}")')
    columns = [row[1] for row in sqlite_cursor.fetchall()]
    columns_str = ", ".join([f'"{col}"' for col in columns])
    placeholders = ", ".join(["%s"] * len(columns))
    
    # Push the data straight to your PostgreSQL database
    insert_query = f'INSERT INTO "{table}" ({columns_str}) VALUES ({placeholders})'
    
    try:
        pg_cursor.executemany(insert_query, rows)
        pg_conn.commit()
        print(f"Successfully migrated {len(rows)} rows into {table}!")
    except Exception as e:
        pg_conn.rollback()
        print(f"Error migrating {table}: {e}")

sqlite_conn.close()
pg_conn.close()
print("Migration process complete!")
