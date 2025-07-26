import sqlite3

conn = sqlite3.connect('inventory.db')
c = conn.cursor()
c.execute('''
CREATE TABLE IF NOT EXISTS payment_details (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    quoted_amount REAL DEFAULT 0,
    discount REAL DEFAULT 0,
    advance_amount REAL DEFAULT 0,
    remaining_amount AS (quoted_amount - discount - advance_amount) STORED,
    FOREIGN KEY (project_id) REFERENCES work_projects(id)
)
''')
conn.commit()
conn.close()
print("payment_details table created.") 