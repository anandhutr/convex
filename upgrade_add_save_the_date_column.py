import sqlite3

conn = sqlite3.connect('inventory.db')
c = conn.cursor()
c.execute("ALTER TABLE work_projects ADD COLUMN save_the_date TEXT")
conn.commit()
conn.close()
print("Added save_the_date column to work_projects.") 