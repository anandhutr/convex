import sqlite3

conn = sqlite3.connect('inventory.db')
c = conn.cursor()
c.execute("ALTER TABLE work_projects ADD COLUMN maduaram_veypu_date TEXT")
c.execute("ALTER TABLE work_projects ADD COLUMN maduaram_veypu_type TEXT")
conn.commit()
conn.close()
print("Added maduaram_veypu_date and maduaram_veypu_type columns to work_projects.") 