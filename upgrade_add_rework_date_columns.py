import sqlite3

DB_PATH = 'inventory.db'
TABLE_NAME = 'work_projects'
COLUMNS = [
    ('reel_rework_date', 'TEXT'),
    ('album_rework_date', 'TEXT'),
    ('highlight_rework_date', 'TEXT'),
    ('fullwork_rework_date', 'TEXT'),
]

def column_exists(cursor, table, column):
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    return column in columns

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
for col, col_type in COLUMNS:
    if column_exists(c, TABLE_NAME, col):
        print(f"Column '{col}' already exists.")
    else:
        c.execute(f"ALTER TABLE {TABLE_NAME} ADD COLUMN {col} {col_type}")
        print(f"Column '{col}' added.")
conn.commit()
conn.close() 