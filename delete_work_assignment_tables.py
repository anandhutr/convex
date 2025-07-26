import sqlite3

DB_PATH = 'inventory.db'
TABLES_TO_DROP = ['work_projects']  # Add more table names here if needed

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

def table_exists(cursor, table):
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
    return cursor.fetchone() is not None

for table in TABLES_TO_DROP:
    if table_exists(c, table):
        c.execute(f"DROP TABLE {table}")
        print(f"Table '{table}' dropped.")
    else:
        print(f"Table '{table}' does not exist.")

conn.commit()
conn.close() 