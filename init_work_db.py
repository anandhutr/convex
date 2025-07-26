import sqlite3

def init_work_db():
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    
    # Drop work_projects table if it exists
    c.execute('DROP TABLE IF EXISTS work_projects')
    
    # Create work projects table with all required columns
    c.execute('''CREATE TABLE IF NOT EXISTS work_projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_name TEXT NOT NULL,
        referred_by TEXT,
        wedding_date TEXT,
        engagement_date TEXT,
        services TEXT NOT NULL,
        notes TEXT,
        status TEXT DEFAULT 'Active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        religion TEXT,
        custom_religion TEXT,
        christian_subcategory TEXT,
        requirements TEXT,
        sides TEXT
    )''')
    
    conn.commit()
    conn.close()
    print("Work projects table created successfully!")

def add_work_assignment_columns():
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    columns = [
        ('reel_assigned_to', 'TEXT'),
        ('reel_date_assigned', 'TEXT'),
        ('reel_status', 'TEXT'),
        ('album_assigned_to', 'TEXT'),
        ('album_date_assigned', 'TEXT'),
        ('album_status', 'TEXT'),
        ('highlight_assigned_to', 'TEXT'),
        ('highlight_date_assigned', 'TEXT'),
        ('highlight_status', 'TEXT'),
        ('fullwork_assigned_to', 'TEXT'),
        ('fullwork_date_assigned', 'TEXT'),
        ('fullwork_status', 'TEXT'),
    ]
    for col, coltype in columns:
        try:
            c.execute(f'ALTER TABLE work_projects ADD COLUMN {col} {coltype}')
        except sqlite3.OperationalError:
            pass  # Column already exists
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_work_db()
    add_work_assignment_columns() 