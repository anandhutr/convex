import sqlite3

conn = sqlite3.connect('inventory.db')
c = conn.cursor()
c.execute('''
CREATE TABLE IF NOT EXISTS work_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    section TEXT NOT NULL, -- e.g., 'reel', 'album', 'highlight', 'fullwork'
    event_type TEXT NOT NULL, -- e.g., 'rework', 'completed', etc.
    event_date TEXT NOT NULL, -- ISO date string
    user TEXT, -- who performed the action
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES work_projects(id)
)
''')
conn.commit()
conn.close()
print("work_logs table created.") 