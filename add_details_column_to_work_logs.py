import sqlite3

conn = sqlite3.connect('inventory.db')
c = conn.cursor()
c.execute("ALTER TABLE work_logs ADD COLUMN details TEXT")
conn.commit()
conn.close()
print("Added 'details' column to work_logs.") 