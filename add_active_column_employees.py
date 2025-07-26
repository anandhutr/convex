import sqlite3

conn = sqlite3.connect('inventory.db')
c = conn.cursor()
try:
    c.execute('ALTER TABLE employees ADD COLUMN active INTEGER DEFAULT 1')
except sqlite3.OperationalError:
    # Column already exists
    pass
conn.commit()
conn.close()
print("'active' column added to employees table (if not already present).") 