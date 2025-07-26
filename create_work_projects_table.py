import sqlite3

DB_PATH = 'inventory.db'

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Define the schema based on previous usage in the app and template
schema = '''
CREATE TABLE IF NOT EXISTS work_projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_name TEXT,
    referred_by TEXT,
    wedding_date TEXT,
    engagement_date TEXT,
    services TEXT,
    notes TEXT,
    status TEXT,
    created_at TEXT,
    religion TEXT,
    custom_religion TEXT,
    christian_subcategory TEXT,
    requirements TEXT,
    sides TEXT,
    reel_assigned_to TEXT,
    reel_date_assigned TEXT,
    reel_status TEXT,
    reel_completed_date TEXT,
    album_assigned_to TEXT,
    album_date_assigned TEXT,
    album_status TEXT,
    album_completed_date TEXT,
    highlight_assigned_to TEXT,
    highlight_date_assigned TEXT,
    highlight_status TEXT,
    highlight_completed_date TEXT,
    fullwork_assigned_to TEXT,
    fullwork_date_assigned TEXT,
    fullwork_status TEXT,
    fullwork_completed_date TEXT
);
'''

c.execute(schema)
conn.commit()
print("work_projects table created or already exists.")
conn.close() 