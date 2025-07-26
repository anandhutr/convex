import sqlite3

conn = sqlite3.connect('inventory.db')
c = conn.cursor()
try:
    c.execute('ALTER TABLE employees ADD COLUMN password TEXT')
except sqlite3.OperationalError:
    # Column already exists
    pass
conn.commit()
conn.close()
print("Password column added to employees table (if not already present).") 