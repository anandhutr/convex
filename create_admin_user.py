from werkzeug.security import generate_password_hash
import sqlite3

# CHANGE THESE VALUES BEFORE RUNNING
username = 'admin'
password = 'admin123'  # Change to a secure password
role = 'admin'

hashed_pw = generate_password_hash(password)

conn = sqlite3.connect('inventory.db')
c = conn.cursor()
# Check if user already exists
c.execute('SELECT id FROM employees WHERE name = ?', (username,))
if c.fetchone():
    print(f"User '{username}' already exists.")
else:
    c.execute('INSERT INTO employees (name, role, password) VALUES (?, ?, ?)', (username, role, hashed_pw))
    conn.commit()
    print(f"Admin user '{username}' created.")
conn.close() 