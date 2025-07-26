import sqlite3

DB_PATH = 'inventory.db'
TABLE_NAME = 'work_projects'
COLUMNS = [
    ('reel_assigned_to', 'TEXT'),
    ('reel_date_assigned', 'TEXT'),
    ('reel_status', 'TEXT'),
    ('reel_completed_date', 'TEXT'),
    ('album_assigned_to', 'TEXT'),
    ('album_date_assigned', 'TEXT'),
    ('album_status', 'TEXT'),
    ('album_completed_date', 'TEXT'),
    ('highlight_assigned_to', 'TEXT'),
    ('highlight_date_assigned', 'TEXT'),
    ('highlight_status', 'TEXT'),
    ('highlight_completed_date', 'TEXT'),
    ('fullwork_assigned_to', 'TEXT'),
    ('fullwork_date_assigned', 'TEXT'),
    ('fullwork_status', 'TEXT'),
    ('fullwork_completed_date', 'TEXT'),
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