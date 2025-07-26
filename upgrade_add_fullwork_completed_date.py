import sqlite3

DB_PATH = 'inventory.db'
COLUMN_NAME = 'fullwork_completed_date'
TABLE_NAME = 'work_projects'

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Check if the column already exists
def column_exists(cursor, table, column):
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    return column in columns

if column_exists(c, TABLE_NAME, COLUMN_NAME):
    print(f"Column '{COLUMN_NAME}' already exists in '{TABLE_NAME}'. No changes made.")
else:
    c.execute(f"ALTER TABLE {TABLE_NAME} ADD COLUMN {COLUMN_NAME} TEXT")
    conn.commit()
    print(f"Column '{COLUMN_NAME}' added to '{TABLE_NAME}'.")

conn.close() 