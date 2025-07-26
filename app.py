from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify, session, flash
import sqlite3
from datetime import datetime
from werkzeug.utils import secure_filename
import os
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
BACKUP_FOLDER = 'backups'
ALLOWED_EXTENSIONS = {'csv', 'db'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['BACKUP_FOLDER'] = BACKUP_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(BACKUP_FOLDER, exist_ok=True)

app.secret_key = 'your_secret_key_here'  # Change this to a secure random value!

def sentence_case(s):
    s = s.strip() if s else ''
    return s[:1].upper() + s[1:] if s else s

def allowed_file(filename, allowed=ALLOWED_EXTENSIONS):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    
    # Create stock table
    c.execute('''CREATE TABLE IF NOT EXISTS stock (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_type TEXT NOT NULL,
        capacity TEXT NOT NULL,
        serial_number TEXT,
        purchase_date TEXT,
        quantity INTEGER NOT NULL,
        storage_owner TEXT NOT NULL,
        condition TEXT DEFAULT 'New',
        disk_name TEXT
    )''')
    
    # Create orders table
    c.execute('''CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_type TEXT NOT NULL,
        capacity TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        storage_owner TEXT NOT NULL,
        disk_name TEXT,
        order_reason TEXT NOT NULL,
        storage_sent_to TEXT NOT NULL,
        sent_by TEXT NOT NULL,
        order_date TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Create work projects table
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
    
    # Add missing columns to existing tables if they don't exist
    columns_to_add = {
        'stock': [
            ('condition', 'TEXT DEFAULT "New"'),
            ('disk_name', 'TEXT')
        ],
        'orders': [
            ('sent_by', 'TEXT'),
            ('storage_owner', 'TEXT'),
            ('disk_name', 'TEXT'),
            ('order_reason', 'TEXT'),
            ('storage_sent_to', 'TEXT'),
            ('order_date', 'TEXT')
        ],
        'work_projects': [
            ('religion', 'TEXT'),
            ('custom_religion', 'TEXT'),
            ('christian_subcategory', 'TEXT'),
            ('requirements', 'TEXT'),
            ('sides', 'TEXT')
        ]
    }
    
    for table, columns in columns_to_add.items():
        for col_name, col_def in columns:
            try:
                c.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_def}")
            except sqlite3.OperationalError:
                # Column already exists
                pass
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

# Add columns for photo_copied_location and video_copied_location if not exist
with sqlite3.connect('inventory.db') as conn:
    c = conn.cursor()
    try:
        c.execute('ALTER TABLE work_projects ADD COLUMN photo_copied_location TEXT')
    except sqlite3.OperationalError:
        pass
    try:
        c.execute('ALTER TABLE work_projects ADD COLUMN video_copied_location TEXT')
    except sqlite3.OperationalError:
        pass
    try:
        c.execute('ALTER TABLE work_projects ADD COLUMN photo_copied_by TEXT')
    except sqlite3.OperationalError:
        pass
    try:
        c.execute('ALTER TABLE work_projects ADD COLUMN video_copied_by TEXT')
    except sqlite3.OperationalError:
        pass
    try:
        c.execute('ALTER TABLE work_projects ADD COLUMN photo_pc_name TEXT')
    except sqlite3.OperationalError:
        pass
    try:
        c.execute('ALTER TABLE work_projects ADD COLUMN video_pc_name TEXT')
    except sqlite3.OperationalError:
        pass

# Home route: Display inventory
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    user_role = session.get('role')
    user_name = session.get('user_name')
    assigned_work = []
    if user_role != 'Admin Access':
        # Fetch work assigned to this user
        c.execute('''SELECT * FROM work_projects WHERE \
            reel_assigned_to = ? OR album_assigned_to = ? OR highlight_assigned_to = ? OR fullwork_assigned_to = ?
            ORDER BY created_at DESC''', (user_name, user_name, user_name, user_name))
        assigned_work = c.fetchall()
        # Fetch all work projects for the table
        c.execute('''SELECT * FROM work_projects ORDER BY created_at DESC''')
        work_projects = c.fetchall()
    try:
        c.execute("SELECT * FROM stock")
        items = c.fetchall()
        
        # Count in-stock items by type
        pendrive_count = sum(item[5] for item in items if item[1] == 'Pendrive' and item[5] > 0)
        hdd_count = sum(item[5] for item in items if item[1] == 'HDD' and item[5] > 0)
        ssd_count = sum(item[5] for item in items if item[1] == 'SSD' and item[5] > 0)
        
        # Count items by ownership
        convex_count = sum(item[5] for item in items if item[6] == 'Convex' and item[5] > 0)
        client_count = sum(item[5] for item in items if item[6] != 'Convex' and item[5] > 0)
        
        # Calculate pendrive counts grouped by capacity (size)
        pendrive_low_stock_items = [] # If you use this in the template, keep it
        low_stock_count = 0 # If you use this in the template, keep it
        
    except Exception as e:
        # If there's an error, set default values
        print(f"Error in index route: {e}")
        pendrive_count = hdd_count = ssd_count = 0
        convex_count = client_count = 0
        pendrive_low_stock_items = []
        low_stock_count = 0
    
    # Get work projects data
    try:
        c.execute('''SELECT * FROM work_projects ORDER BY created_at DESC LIMIT 5''')
        recent_work = c.fetchall()
        
        # Count work projects by type
        c.execute('''SELECT COUNT(*) FROM work_projects''')
        total_work_projects = c.fetchone()[0]
        
        wedding_count = sum(1 for project in recent_work if project[3] in ['wedding', 'both'])
        engagement_count = sum(1 for project in recent_work if project[3] in ['engagement', 'both'])
    except Exception as e:
        print(f"Error getting work projects: {e}")
        recent_work = []
        wedding_count = engagement_count = 0
    
    conn.close()
    
    if user_role == 'Admin Access':
        return render_template('index.html', 
                             pendrive_count=pendrive_count, 
                             hdd_count=hdd_count, 
                             ssd_count=ssd_count, 
                             convex_count=convex_count, 
                             client_count=client_count, 
                             recent_work=recent_work, 
                             wedding_count=wedding_count, 
                             engagement_count=engagement_count, 
                             pendrive_low_stock_items=pendrive_low_stock_items, 
                             low_stock_count=low_stock_count)
    else:
        return render_template('index.html', assigned_work=assigned_work, work_projects=work_projects)

# Add item
@app.route('/add', methods=['POST'])
def add_item():
    item_type = request.form['item_type']
    capacity = request.form['capacity']
    serial_number = request.form['serial_number']
    purchase_date = request.form['purchase_date']
    quantity = int(request.form['quantity'])
    storage_owner = request.form['storage_owner']
    condition = request.form.get('condition', 'New')  # Default to 'New' if not provided
    disk_name = request.form.get('disk_name', '')  # Get disk name if provided
    
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    for _ in range(quantity):
        c.execute(
            "INSERT INTO stock (item_type, capacity, serial_number, purchase_date, quantity, storage_owner, condition, disk_name) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (item_type, capacity, serial_number, purchase_date, 1, storage_owner, condition, disk_name)
        )
    conn.commit()
    conn.close()
    return redirect(url_for('upload', success='Item added successfully!'))

# Update item
@app.route('/update/<int:id>', methods=['POST'])
def update_item(id):
    quantity = int(request.form['quantity'])
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    c.execute("UPDATE stock SET quantity = ? WHERE id = ?",
              (quantity, id))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

# Edit item - GET route to show edit form
@app.route('/edit_item/<int:id>', methods=['GET'])
def edit_item(id):
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    c.execute("SELECT * FROM stock WHERE id = ?", (id,))
    item = c.fetchone()
    conn.close()
    
    if item is None:
        return redirect(url_for('upload', error='Item not found!'))
    
    return render_template('edit_item.html', item=item)

# Edit item - POST route to update item
@app.route('/edit_item/<int:id>', methods=['POST'])
def edit_item_post(id):
    item_type = request.form['item_type']
    capacity = request.form['capacity']
    serial_number = request.form['serial_number']
    purchase_date = request.form['purchase_date']
    quantity = int(request.form['quantity'])
    storage_owner = request.form['storage_owner']
    condition = request.form.get('condition', 'New')
    disk_name = request.form.get('disk_name', '')
    
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    c.execute("""
        UPDATE stock 
        SET item_type = ?, capacity = ?, serial_number = ?, purchase_date = ?, 
            quantity = ?, storage_owner = ?, condition = ?, disk_name = ? 
        WHERE id = ?
    """, (item_type, capacity, serial_number, purchase_date, quantity, storage_owner, condition, disk_name, id))
    conn.commit()
    conn.close()
    
    return redirect(url_for('upload', success='Item updated successfully!'))

# Delete item
@app.route('/delete_item/<int:id>')
def delete_item(id):
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    c.execute("DELETE FROM stock WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('upload', success='Item deleted successfully!'))

# Bulk delete stock items
@app.route('/bulk_delete_stock', methods=['POST'])
def bulk_delete_stock():
    try:
        data = request.get_json()
        ids = data.get('ids', [])
        
        if not ids:
            return jsonify({'success': False, 'error': 'No IDs provided'})
        
        conn = sqlite3.connect('inventory.db')
        c = conn.cursor()
        
        # Convert IDs to integers and create placeholders for SQL
        id_list = [int(id) for id in ids]
        placeholders = ','.join(['?' for _ in id_list])
        
        # Delete the items
        c.execute(f"DELETE FROM stock WHERE id IN ({placeholders})", id_list)
        deleted_count = c.rowcount
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True, 
            'deleted_count': deleted_count,
            'message': f'Successfully deleted {deleted_count} item(s)'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# Bulk delete orders
@app.route('/bulk_delete_orders', methods=['POST'])
def bulk_delete_orders():
    try:
        data = request.get_json()
        ids = data.get('ids', [])
        
        if not ids:
            return jsonify({'success': False, 'error': 'No IDs provided'})
        
        conn = sqlite3.connect('inventory.db')
        c = conn.cursor()
        
        # Convert IDs to integers and create placeholders for SQL
        id_list = [int(id) for id in ids]
        placeholders = ','.join(['?' for _ in id_list])
        
        # Delete the orders
        c.execute(f"DELETE FROM orders WHERE id IN ({placeholders})", id_list)
        deleted_count = c.rowcount
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True, 
            'deleted_count': deleted_count,
            'message': f'Successfully deleted {deleted_count} order(s)'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# Bulk delete work projects
@app.route('/bulk_delete_work', methods=['POST'])
def bulk_delete_work():
    try:
        data = request.get_json()
        ids = data.get('ids', [])
        
        if not ids:
            return jsonify({'success': False, 'error': 'No IDs provided'})
        
        conn = sqlite3.connect('inventory.db')
        c = conn.cursor()
        
        # Convert IDs to integers and create placeholders for SQL
        id_list = [int(id) for id in ids]
        placeholders = ','.join(['?' for _ in id_list])
        
        # Delete the work projects
        c.execute(f"DELETE FROM work_projects WHERE id IN ({placeholders})", id_list)
        deleted_count = c.rowcount
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True, 
            'deleted_count': deleted_count,
            'message': f'Successfully deleted {deleted_count} work project(s)'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# Upload page
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        # Handle file upload
        if 'file' in request.files:
            file = request.files['file']
            if file and file.filename != '':
                if file and allowed_file(file.filename, {'csv'}):
                    # Process CSV file
                    try:
                        # Read CSV content
                        # Removed io.StringIO and csv.DictReader
                        # This part of the code is no longer relevant for CSV upload
                        # The original code had a CSV upload mechanism, but it was removed.
                        # If the user wants to re-add CSV upload, they need to re-implement it.
                        # For now, we'll just redirect with an error message.
                        return redirect(url_for('upload', error='CSV upload functionality is currently disabled.'))
                        
                    except Exception as e:
                        return redirect(url_for('upload', error=f'Error processing CSV: {str(e)}'))
        else:
            return redirect(url_for('upload', error='Invalid file type. Please upload a CSV file.'))
        
        # Handle single item addition
        item_type = request.form.get('item_type', '').strip()
        capacity = request.form.get('capacity', '').strip()
        quantity = int(request.form.get('quantity', 1))
        storage_owner = request.form.get('storage_owner', 'Convex').strip()
        disk_name = request.form.get('disk_name', '').strip()
        serial_number = request.form.get('serial_number', '').strip()
        
        if not item_type or not capacity:
            return redirect(url_for('upload', error='Item type and capacity are required!'))
        
        conn = sqlite3.connect('inventory.db')
        c = conn.cursor()
        # Insert N rows with quantity 1 each
        for _ in range(quantity):
            c.execute("INSERT INTO stock (item_type, capacity, quantity, storage_owner, disk_name, serial_number) VALUES (?, ?, ?, ?, ?, ?)",
                      (item_type, capacity, 1, storage_owner, disk_name, serial_number))
        conn.commit()
        conn.close()
        
        return redirect(url_for('upload', success='Item added successfully!'))
    
    # Fetch current inventory data for display
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    c.execute("SELECT * FROM stock")
    items = c.fetchall()
    
    # Calculate statistics
    total_items = len(items)
    convex_count = sum(1 for item in items if item[6] == 'Convex')
    client_count = sum(1 for item in items if item[6] != 'Convex')
    pendrive_total = sum(int(item[5]) for item in items if item[1] == 'Pendrive' and str(item[5]).isdigit())
    low_stock_count = 1 if pendrive_total <= 2 else 0
    pendrive_count_total = sum(1 for item in items if item[1] == 'Pendrive')
    
    # Calculate pendrive counts grouped by capacity (size)
    pendrive_size_counts = {} # Removed Counter
    pendrive_low_stock_items = []
    for size, count in pendrive_size_counts.items(): # This loop will now be empty
        if str(count).isdigit() and int(count) <= 2:
            # Find the item type for this size (should be 'Pendrive', but keep generic)
            for item in items:
                if item[1] == 'Pendrive' and item[2] == size:
                    pendrive_low_stock_items.append((size, item[1]))
                    break
    low_stock_count = 1 if pendrive_low_stock_items else 0
    
    conn.close()
    
    # Get success/error messages from query parameters
    success_message = request.args.get('success')
    error_message = request.args.get('error')
    
    return render_template('upload.html', 
                         items=items, 
                         total_items=total_items,
                         convex_count=convex_count,
                         client_count=client_count,
                         low_stock_count=low_stock_count,
                         pendrive_count_total=pendrive_count_total,
                         pendrive_size_counts=pendrive_size_counts,
                         success_message=success_message, 
                         error_message=error_message)

# Order page
@app.route('/order', methods=['GET', 'POST'])
def order():
    if request.method == 'POST':
        # Process the order
        item_type = request.form.get('item_type', '').strip()
        capacity = request.form.get('capacity', '').strip()
        quantity_str = request.form.get('quantity', '').strip()
        storage_owner = request.form.get('storage_owner', '').strip()
        disk_name = request.form.get('disk_name', '').strip()
        order_reason = request.form.get('order_reason', '').strip()
        storage_sent_to = request.form.get('storage_sent_to', '').strip()
        sent_by = request.form.get('sent_by', '').strip()
        order_date = request.form.get('order_date', '').strip()
        
        # Validate required fields
        if not item_type or not capacity or not quantity_str or not storage_owner or not order_reason or not storage_sent_to or not sent_by or not order_date:
            return redirect(url_for('order', error='All fields are required!'))
        
        # Validate disk name for Convex items
        if storage_owner == 'Convex' and not disk_name:
            return redirect(url_for('order', error='Disk name is required for Convex storage items!'))
        
        # Validate quantity
        try:
            quantity = int(quantity_str)
            if quantity <= 0:
                return redirect(url_for('order', error='Quantity must be greater than 0!'))
        except ValueError:
            return redirect(url_for('order', error='Invalid quantity value!'))
        
        # Update the database - reduce quantity for the selected item type and capacity
        conn = sqlite3.connect('inventory.db')
        c = conn.cursor()
        
        # First, check if we have enough quantity
        c.execute("SELECT SUM(quantity) as total_quantity FROM stock WHERE item_type = ? AND capacity = ?", 
                  (item_type, capacity))
        current_quantity = c.fetchone()
        
        if current_quantity and current_quantity[0] >= quantity:
            # Get all rows with this item type and capacity
            c.execute("SELECT id, quantity FROM stock WHERE item_type = ? AND capacity = ? AND quantity > 0 ORDER BY id", 
                      (item_type, capacity))
            rows = c.fetchall()
            
            # Reduce quantities starting from the first row
            remaining_to_reduce = quantity
            for row_id, row_quantity in rows:
                if remaining_to_reduce <= 0:
                    break
                    
                if row_quantity >= remaining_to_reduce:
                    # This row has enough quantity
                    new_quantity = row_quantity - remaining_to_reduce
                    c.execute("UPDATE stock SET quantity = ? WHERE id = ?", (new_quantity, row_id))
                    remaining_to_reduce = 0
                else:
                    # This row doesn't have enough, take all from it
                    c.execute("UPDATE stock SET quantity = 0 WHERE id = ?", (row_id,))
                    remaining_to_reduce -= row_quantity
            
            # Save the order to the orders table
            c.execute("INSERT INTO orders (item_type, capacity, quantity, storage_owner, disk_name, order_reason, storage_sent_to, sent_by, order_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                      (item_type, capacity, quantity, storage_owner, disk_name, order_reason, storage_sent_to, sent_by, order_date))
            
            conn.commit()
            conn.close()
            return redirect(url_for('order', success='Order processed successfully!'))
        else:
            conn.close()
            return redirect(url_for('order', error='Insufficient stock for this order!'))
    
    # GET request - show the order form and orders table
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    
    # Get unique item types
    c.execute("SELECT DISTINCT item_type FROM stock WHERE quantity > 0")
    item_types = [row[0] for row in c.fetchall()]
    
    # Get all orders for the table
    c.execute("SELECT * FROM orders ORDER BY created_at DESC")
    orders_list = c.fetchall()
    
    conn.close()
    
    # Get success/error messages from query parameters
    success_message = request.args.get('success')
    error_message = request.args.get('error')
    
    return render_template('order.html', 
                         item_types=item_types, 
                         orders=orders_list,
                         success_message=success_message,
                         error_message=error_message)

# Metrics Dashboard
@app.route('/metrics')
def metrics():
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    
    # Get ownership distribution
    c.execute("""
        SELECT storage_owner, 
               COUNT(*) as total_items,
               SUM(quantity) as total_quantity,
               SUM(CASE WHEN item_type = 'Pendrive' THEN quantity ELSE 0 END) as pendrive_count,
               SUM(CASE WHEN item_type = 'HDD' THEN quantity ELSE 0 END) as hdd_count,
               SUM(CASE WHEN item_type = 'SSD' THEN quantity ELSE 0 END) as ssd_count
        FROM stock 
        WHERE quantity > 0 
        GROUP BY storage_owner
        ORDER BY total_quantity DESC
    """)
    ownership_data = c.fetchall()
    
    # Get item type distribution by ownership
    c.execute("""
        SELECT storage_owner, item_type, SUM(quantity) as total_quantity
        FROM stock 
        WHERE quantity > 0 
        GROUP BY storage_owner, item_type
        ORDER BY storage_owner, total_quantity DESC
    """)
    item_type_by_owner = c.fetchall()
    
    # Get capacity distribution by ownership
    c.execute("""
        SELECT storage_owner, capacity, SUM(quantity) as total_quantity
        FROM stock 
        WHERE quantity > 0 
        GROUP BY storage_owner, capacity
        ORDER BY storage_owner, total_quantity DESC
    """)
    capacity_by_owner = c.fetchall()
    
    # Get recent orders by ownership
    c.execute("""
        SELECT o.storage_owner, o.disk_name, o.order_reason, o.storage_sent_to, o.item_type, o.capacity, o.quantity, o.sent_by, o.order_date, o.created_at
        FROM orders o
        ORDER BY o.created_at DESC
        LIMIT 20
    """)
    recent_orders = c.fetchall()
    
    # Get total statistics
    c.execute("""
        SELECT 
            COUNT(DISTINCT storage_owner) as total_owners,
            SUM(quantity) as total_items,
            COUNT(DISTINCT item_type) as total_item_types,
            COUNT(DISTINCT capacity) as total_capacities
        FROM stock 
        WHERE quantity > 0
    """)
    total_stats = c.fetchone()
    
    conn.close()
    
    return render_template('metrics.html', 
                         ownership_data=ownership_data,
                         item_type_by_owner=item_type_by_owner,
                         capacity_by_owner=capacity_by_owner,
                         recent_orders=recent_orders,
                         total_stats=total_stats)

# API endpoint to get capacities and serial numbers
@app.route('/api/serial_numbers')
def get_serial_numbers():
    item_type = request.args.get('item_type')
    capacity = request.args.get('capacity')
    
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    
    if not item_type:
        # Return all available item types
        c.execute("SELECT DISTINCT item_type FROM stock WHERE quantity > 0")
        item_types = [{'item_type': row[0]} for row in c.fetchall()]
        conn.close()
        return jsonify(item_types)
    
    if not capacity:
        # Return capacities for the selected item type
        c.execute("SELECT DISTINCT capacity FROM stock WHERE item_type = ? AND quantity > 0", (item_type,))
        capacities = [{'capacity': row[0]} for row in c.fetchall()]
        conn.close()
        return jsonify(capacities)
    else:
        # Return serial numbers for the selected item type and capacity
        c.execute("SELECT serial_number, SUM(quantity) as total_quantity, storage_owner, disk_name FROM stock WHERE item_type = ? AND capacity = ? AND quantity > 0 GROUP BY serial_number, storage_owner, disk_name", 
                  (item_type, capacity))
        serial_numbers = [{'serial_number': row[0], 'quantity': row[1], 'storage_owner': row[2], 'disk_name': row[3]} for row in c.fetchall()]
        conn.close()
        return jsonify(serial_numbers)

@app.route('/work', methods=['GET', 'POST'])
def work():
    if request.method == 'POST':
        # Handle work project submission
        client_name = sentence_case(request.form.get('client_name', ''))
        religion = sentence_case(request.form.get('religion', ''))
        custom_religion = sentence_case(request.form.get('custom_religion', ''))
        christian_subcategory = sentence_case(request.form.get('christian_subcategory', ''))
        requirements = request.form.getlist('requirements')
        requirements_str = sentence_case(','.join(requirements))
        sides = sentence_case(request.form.get('sides', ''))
        maduaram_veypu_type = sentence_case(request.form.get('maduaram_veypu_type', ''))
        maduaram_veypu_date = request.form.get('maduaram_veypu_date', '')
        save_the_date = request.form.get('save_the_date', '')
        print('DEBUG: Requirements received:', requirements)
        print('DEBUG: Sides received:', sides)
        referred_by = sentence_case(request.form.get('referred_by', ''))
        wedding_date = request.form.get('wedding_date', '')
        engagement_date = request.form.get('engagement_date', '')
        services = ','.join(request.form.getlist('services'))
        notes = sentence_case(request.form.get('notes', ''))
        try:
            conn = sqlite3.connect('inventory.db')
            c = conn.cursor()
            c.execute('''INSERT INTO work_projects 
                (client_name, referred_by, wedding_date, engagement_date, services, notes, religion, custom_religion, christian_subcategory, requirements, sides, maduaram_veypu_type, maduaram_veypu_date, save_the_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (client_name, referred_by, wedding_date, engagement_date, services, notes, religion, custom_religion, christian_subcategory, requirements_str, sides, maduaram_veypu_type, maduaram_veypu_date, save_the_date))
            conn.commit()
            conn.close()
            # If AJAX/JSON request, return JSON
            if request.accept_mimetypes['application/json'] or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': True, 'message': 'Work project created successfully.'})
            return redirect(url_for('work'))
        except Exception as e:
            if request.accept_mimetypes['application/json'] or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': f'Error: {str(e)}'})
            return redirect(url_for('work', error=f'Error: {str(e)}'))
    # GET request - display work projects
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    c.execute('''SELECT * FROM work_projects ORDER BY created_at DESC''')
    work_projects = c.fetchall()
    today = datetime.today().date()
    wedding_count = sum(1 for project in work_projects if project[3] and project[3].strip())
    engagement_count = sum(1 for project in work_projects if project[4] and project[4].strip())
    def is_upcoming(date_str):
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').date() >= today
        except Exception:
            return False
    upcoming_count = sum(
        1 for project in work_projects
        if (project[3] and is_upcoming(project[3])) or (project[4] and is_upcoming(project[4]))
    )
    active_count = sum(1 for project in work_projects if project[8] == 'Active')
    active_wedding_count = sum(
        1 for project in work_projects
        if project[8] == 'Active' and project[3] and project[3].strip()
    )
    conn.close()
    return render_template('work.html', 
                         work_projects=work_projects,
                         wedding_count=wedding_count,
                         engagement_count=engagement_count,
                         upcoming_count=upcoming_count,
                         active_count=active_count,
                         active_wedding_count=active_wedding_count)

# View work project profile
@app.route('/work/profile/<int:project_id>')
def work_profile(project_id):
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    
    # Get project details
    c.execute('''SELECT * FROM work_projects WHERE id = ?''', (project_id,))
    project = c.fetchone()
    
    if not project:
        conn.close()
        return "Project not found", 404
    
    # Get project statistics
    c.execute('''SELECT COUNT(*) FROM work_projects WHERE wedding_date IS NOT NULL''')
    similar_projects = c.fetchone()[0]
    
    c.execute('''SELECT COUNT(*) FROM work_projects WHERE status = ?''', (project[8],))
    status_count = c.fetchone()[0]
    
    # Get recent projects for comparison
    c.execute('''SELECT * FROM work_projects WHERE id != ? ORDER BY created_at DESC LIMIT 5''', (project_id,))
    recent_projects = c.fetchall()
    
    # Fetch payment details
    c.execute('SELECT quoted_amount, discount, advance_amount, remaining_amount FROM payment_details WHERE project_id = ?', (project_id,))
    payment = c.fetchone()
    if payment:
        payment = {
            'quoted_amount': payment[0],
            'discount': payment[1],
            'advance_amount': payment[2],
            'remaining_amount': payment[3]
        }
    else:
        payment = {'quoted_amount': 0, 'discount': 0, 'advance_amount': 0, 'remaining_amount': 0}
    conn.close()

    # Fetch employees for dropdown
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    c.execute('SELECT id, name, role FROM employees')
    employees = c.fetchall()

    # Fetch all rework log entries for this project
    c.execute('SELECT section, event_type, event_date, user, details FROM work_logs WHERE project_id = ? ORDER BY event_date', (project_id,))
    work_logs = c.fetchall()
    conn.close()

    # Group logs by section for easier template rendering
    logs_by_section = {'reel': [], 'album': [], 'highlight': [], 'fullwork': []}
    for section, event_type, event_date, user, details in work_logs:
        if section in logs_by_section:
            logs_by_section[section].append({'date': event_date, 'user': user, 'details': details})

    return render_template('work_profile.html', 
                         project=project,
                         similar_projects=similar_projects,
                         status_count=status_count,
                         recent_projects=recent_projects,
                         employees=employees,
                         payment=payment,
                         work_logs=logs_by_section)

# Delete work project
@app.route('/work/delete/<int:project_id>', methods=['DELETE'])
def delete_work_project(project_id):
    try:
        conn = sqlite3.connect('inventory.db')
        c = conn.cursor()
        
        # Check if project exists
        c.execute('SELECT client_name FROM work_projects WHERE id = ?', (project_id,))
        project = c.fetchone()
        
        if not project:
            conn.close()
            return jsonify({'success': False, 'message': 'Project not found'}), 404
        
        # Delete the project
        c.execute('DELETE FROM work_projects WHERE id = ?', (project_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': f'Project for {project[0]} deleted successfully'})
        
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': f'Error deleting project: {str(e)}'}), 500

# Edit work project
@app.route('/work/edit/<int:project_id>', methods=['GET', 'POST'])
def edit_work_project(project_id):
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    if request.method == 'POST':
        client_name = sentence_case(request.form.get('client_name', ''))
        religion = sentence_case(request.form.get('religion', ''))
        custom_religion = sentence_case(request.form.get('custom_religion', ''))
        christian_subcategory = sentence_case(request.form.get('christian_subcategory', ''))
        requirements = request.form.getlist('requirements')
        requirements_str = sentence_case(','.join(requirements))
        sides = sentence_case(request.form.get('sides', ''))
        maduaram_veypu_type = sentence_case(request.form.get('maduaram_veypu_type', ''))
        maduaram_veypu_date = request.form.get('maduaram_veypu_date', '')
        save_the_date = request.form.get('save_the_date', '')
        referred_by = sentence_case(request.form.get('referred_by', ''))
        wedding_date = request.form.get('wedding_date', '')
        engagement_date = request.form.get('engagement_date', '')
        services = ','.join(request.form.getlist('services'))
        notes = sentence_case(request.form.get('notes', ''))
        status = request.form.get('status', 'Active')
        c.execute('''UPDATE work_projects SET client_name=?, referred_by=?, wedding_date=?, engagement_date=?, services=?, notes=?, religion=?, custom_religion=?, christian_subcategory=?, requirements=?, sides=?, maduaram_veypu_type=?, maduaram_veypu_date=?, save_the_date=?, status=? WHERE id=?''',
            (client_name, referred_by, wedding_date, engagement_date, services, notes, religion, custom_religion, christian_subcategory, requirements_str, sides, maduaram_veypu_type, maduaram_veypu_date, save_the_date, status, project_id))
        conn.commit()
        conn.close()
        return redirect(url_for('work_profile', project_id=project_id))
    # GET request
    c.execute('SELECT * FROM work_projects WHERE id = ?', (project_id,))
    project = c.fetchone()
    conn.close()
    if not project:
        return "Project not found", 404
    return render_template('edit_work.html', project=project)

@app.route('/work/edit_assignment_section/<int:project_id>/<section>', methods=['POST'])
def edit_assignment_section(project_id, section):
    # Map section to DB columns
    section_map = {
        'reel': {
            'assigned_to': 'reel_assigned_to',
            'date': 'reel_date_assigned',
            'status': 'reel_status',
            'completed_date': 'reel_completed_date',
            'rework_date': 'reel_rework_date',
        },
        'album': {
            'assigned_to': 'album_assigned_to',
            'date': 'album_date_assigned',
            'status': 'album_status',
            'completed_date': 'album_completed_date',
            'rework_date': 'album_rework_date',
        },
        'highlight': {
            'assigned_to': 'highlight_assigned_to',
            'date': 'highlight_date_assigned',
            'status': 'highlight_status',
            'completed_date': 'highlight_completed_date',
            'rework_date': 'highlight_rework_date',
        },
        'fullwork': {
            'assigned_to': 'fullwork_assigned_to',
            'date': 'fullwork_date_assigned',
            'status': 'fullwork_status',
            'completed_date': 'fullwork_completed_date',
            'rework_date': 'fullwork_rework_date',
        },
    }
    if section not in section_map:
        return jsonify({'success': False, 'message': 'Invalid section'}), 400
    data = section_map[section]
    is_admin = session.get('role') == 'Admin Access'
    assigned_to = request.form.get(data['assigned_to'])
    date_assigned = request.form.get(data['date'])
    status = request.form.get(data['status'])
    completed_date = request.form.get('completed_date') if status == 'Completed' else None
    rework_date = request.form.get('rework_date') if status == 'Rework' else None
    # Always create conn/c at the top
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    # For non-admins, preserve assigned_to and date_assigned if not present in form
    if not is_admin:
        c.execute(f'SELECT {data["assigned_to"]}, {data["date"]} FROM work_projects WHERE id = ?', (project_id,))
        row = c.fetchone()
        if assigned_to is None:
            assigned_to = row[0]
        if date_assigned is None:
            date_assigned = row[1]
    # Build SQL
    sql = f"UPDATE work_projects SET {data['assigned_to']}=?, {data['date']}=?, {data['status']}=?"
    params = [assigned_to, date_assigned, status]
    if status == 'Completed':
        sql += f", {data['completed_date']}=?"
        params.append(completed_date)
        sql += f", {data['rework_date']}=NULL"
        user = session.get('user_name', 'Unknown')
        details = f"Status changed to Completed"
        c.execute('''INSERT INTO work_logs (project_id, section, event_type, event_date, user, details) VALUES (?, ?, ?, ?, ?, ?)''',
                 (project_id, section, 'completed', completed_date, user, details))
    elif status == 'Rework':
        sql += f", {data['rework_date']}=?"
        params.append(rework_date)
        sql += f", {data['completed_date']}=NULL"
        user = session.get('user_name', 'Unknown')
        details = f"Status changed to Rework"
        c.execute('''INSERT INTO work_logs (project_id, section, event_type, event_date, user, details) VALUES (?, ?, ?, ?, ?, ?)''',
                 (project_id, section, 'rework', rework_date, user, details))
    elif status == 'In Progress':
        from datetime import datetime
        today = datetime.today().strftime('%Y-%m-%d')
        user = session.get('user_name', 'Unknown')
        details = f"Status changed to In Progress"
        c.execute('''INSERT INTO work_logs (project_id, section, event_type, event_date, user, details) VALUES (?, ?, ?, ?, ?, ?)''',
                 (project_id, section, 'in_progress', today, user, details))
        sql += f", {data['completed_date']}=NULL, {data['rework_date']}=NULL"
    else:
        sql += f", {data['completed_date']}=NULL, {data['rework_date']}=NULL"
    sql += " WHERE id=?"
    params.append(project_id)
    c.execute(sql, params)
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/edit_order', methods=['POST'])
def edit_order():
    try:
        data = request.get_json()
        order_id = data.get('id')
        item_type = data.get('item_type', '').strip()
        capacity = data.get('capacity', '').strip()
        quantity = int(data.get('quantity', 0))
        storage_owner = data.get('storage_owner', '').strip()
        disk_name = data.get('disk_name', '').strip()
        order_reason = data.get('order_reason', '').strip()
        storage_sent_to = data.get('storage_sent_to', '').strip()
        sent_by = data.get('sent_by', '').strip()
        order_date = data.get('order_date', '').strip()

        if not order_id:
            return jsonify({'success': False, 'error': 'Order ID is required.'}), 400

        conn = sqlite3.connect('inventory.db')
        c = conn.cursor()
        c.execute('''
            UPDATE orders SET
                item_type = ?,
                capacity = ?,
                quantity = ?,
                storage_owner = ?,
                disk_name = ?,
                order_reason = ?,
                storage_sent_to = ?,
                sent_by = ?,
                order_date = ?
            WHERE id = ?
        ''', (item_type, capacity, quantity, storage_owner, disk_name, order_reason, storage_sent_to, sent_by, order_date, order_id))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Order updated successfully.'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Ensure employees table exists
with sqlite3.connect('inventory.db') as conn:
    conn.execute('''CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        role TEXT NOT NULL,
        password TEXT
    )''')

# --- LOGIN/LOGOUT ROUTES ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']
        remember = request.form.get('remember')
        conn = sqlite3.connect('inventory.db')
        c = conn.cursor()
        c.execute('SELECT id, name, role, password FROM employees WHERE name = ?', (name,))
        user = c.fetchone()
        conn.close()
        if user and user[3] and check_password_hash(user[3], password):
            session['user_id'] = user[0]
            session['user_name'] = user[1]
            session['role'] = user[2]
            if remember:
                session.permanent = True
            else:
                session.permanent = False
            flash('Logged in successfully!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out.', 'info')
    return redirect(url_for('login'))

# --- EMPLOYEE REGISTRATION (ADMIN ONLY) ---
@app.route('/employees/add', methods=['GET', 'POST'])
def add_employee():
    if 'role' not in session or session['role'] != 'Admin Access':
        flash('Access denied.', 'danger')
        return redirect(url_for('login'))
    if request.method == 'POST':
        name = request.form.get('name')
        role = request.form.get('role')
        password = request.form.get('password')
        if name and role and password:
            hashed_pw = generate_password_hash(password)
            conn = sqlite3.connect('inventory.db')
            c = conn.cursor()
            c.execute('INSERT INTO employees (name, role, password) VALUES (?, ?, ?)', (name, role, hashed_pw))
            conn.commit()
            conn.close()
            flash('Employee added!', 'success')
            return redirect(url_for('employees'))
        else:
            flash('All fields required.', 'danger')
    return render_template('add_employee.html')

# --- ROLE-BASED ACCESS DECORATOR ---
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'role' not in session or session['role'] != 'Admin Access':
            flash('Admin access required.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- PROTECT ADMIN ROUTES ---
@app.route('/accounts')
@admin_required
def accounts():
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    c.execute('''
        SELECT wp.id, wp.client_name, pd.quoted_amount, pd.discount, pd.advance_amount, pd.remaining_amount
        FROM work_projects wp
        LEFT JOIN payment_details pd ON wp.id = pd.project_id
        ORDER BY wp.client_name COLLATE NOCASE
    ''')
    accounts = c.fetchall()
    conn.close()
    return render_template('accounts.html', accounts=accounts)

@app.route('/employees', methods=['GET'])
@admin_required
def employees():
    show_inactive = request.args.get('show_inactive') == '1'
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    if show_inactive:
        c.execute('SELECT id, name, role, active FROM employees')
    else:
        c.execute('SELECT id, name, role, active FROM employees WHERE active=1')
    employees = c.fetchall()
    conn.close()
    return render_template('employees.html', employees=employees, show_inactive=show_inactive)

@app.route('/employees/data', methods=['GET'])
def employees_data():
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    c.execute('SELECT id, name, role FROM employees')
    employees = c.fetchall()
    conn.close()
    return jsonify({'employees': employees})

@app.route('/employees/list')
@admin_required
def employees_list():
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    c.execute('SELECT id, name, role FROM employees')
    employees = c.fetchall()
    conn.close()
    return jsonify([
        {'id': emp[0], 'name': emp[1], 'role': emp[2]} for emp in employees
    ])

@app.route('/employees/delete/<int:emp_id>', methods=['POST'])
@admin_required
def delete_employee(emp_id):
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    c.execute('UPDATE employees SET active=0 WHERE id = ?', (emp_id,))
    conn.commit()
    conn.close()
    flash('Employee archived (soft deleted).', 'success')
    return redirect(url_for('employees'))

@app.route('/employees/restore/<int:emp_id>', methods=['POST'])
@admin_required
def restore_employee(emp_id):
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    c.execute('UPDATE employees SET active=1 WHERE id = ?', (emp_id,))
    conn.commit()
    conn.close()
    flash('Employee restored.', 'success')
    return redirect(url_for('employees'))

@app.route('/employees/edit/<int:emp_id>', methods=['GET', 'POST'])
@admin_required
def edit_employee(emp_id):
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    if request.method == 'POST':
        name = request.form.get('name')
        role = request.form.get('role')
        password = request.form.get('password')
        if name and role:
            if password:
                from werkzeug.security import generate_password_hash
                hashed_pw = generate_password_hash(password)
                c.execute('UPDATE employees SET name=?, role=?, password=? WHERE id=?', (name, role, hashed_pw, emp_id))
            else:
                c.execute('UPDATE employees SET name=?, role=? WHERE id=?', (name, role, emp_id))
            conn.commit()
            conn.close()
            flash('Employee updated.', 'success')
            return redirect(url_for('employees'))
        else:
            flash('Name and role are required.', 'danger')
    else:
        c.execute('SELECT id, name, role FROM employees WHERE id=?', (emp_id,))
        emp = c.fetchone()
        conn.close()
        if not emp:
            flash('Employee not found.', 'danger')
            return redirect(url_for('employees'))
        return render_template('edit_employee.html', emp=emp)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        password = request.form.get('password')
        if name and password:
            from werkzeug.security import generate_password_hash
            hashed_pw = generate_password_hash(password)
            conn = sqlite3.connect('inventory.db')
            c = conn.cursor()
            # Check if user already exists
            c.execute('SELECT id FROM employees WHERE name = ?', (name,))
            if c.fetchone():
                conn.close()
                flash('Username already exists.', 'danger')
                return render_template('register.html')
            c.execute('INSERT INTO employees (name, role, password, active) VALUES (?, ?, ?, 1)', (name, 'Basic Access', hashed_pw))
            conn.commit()
            conn.close()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        else:
            flash('All fields are required.', 'danger')
    return render_template('register.html')

@app.route('/work/save_payment/<int:project_id>', methods=['POST'])
def save_payment_details(project_id):
    quoted_amount = float(request.form.get('quoted_amount', 0))
    discount = float(request.form.get('discount', 0))
    advance_amount = float(request.form.get('advance_amount', 0))

    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    # Upsert logic: try update, if not updated then insert
    c.execute('''
        UPDATE payment_details
        SET quoted_amount=?, discount=?, advance_amount=?
        WHERE project_id=?
    ''', (quoted_amount, discount, advance_amount, project_id))
    if c.rowcount == 0:
        c.execute('''
            INSERT INTO payment_details (project_id, quoted_amount, discount, advance_amount)
            VALUES (?, ?, ?, ?)
        ''', (project_id, quoted_amount, discount, advance_amount))
    conn.commit()
    conn.close()
    return redirect(url_for('work_profile', project_id=project_id))

@app.route('/work/save_copied_location/<int:project_id>', methods=['POST'])
def save_copied_location(project_id):
    photo = request.form.get('photo_copied_location')
    video = request.form.get('video_copied_location')
    photo_by = request.form.get('photo_copied_by')
    video_by = request.form.get('video_copied_by')
    photo_pc = request.form.get('photo_pc_name')
    video_pc = request.form.get('video_pc_name')
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    if photo is not None:
        c.execute('UPDATE work_projects SET photo_copied_location=? WHERE id=?', (photo, project_id))
    if video is not None:
        c.execute('UPDATE work_projects SET video_copied_location=? WHERE id=?', (video, project_id))
    if photo_by is not None:
        c.execute('UPDATE work_projects SET photo_copied_by=? WHERE id=?', (photo_by, project_id))
    if video_by is not None:
        c.execute('UPDATE work_projects SET video_copied_by=? WHERE id=?', (video_by, project_id))
    if photo_pc is not None:
        c.execute('UPDATE work_projects SET photo_pc_name=? WHERE id=?', (photo_pc, project_id))
    if video_pc is not None:
        c.execute('UPDATE work_projects SET video_pc_name=? WHERE id=?', (video_pc, project_id))
    conn.commit()
    conn.close()
    return redirect(url_for('work_profile', project_id=project_id))

@app.route('/mywork')
def mywork():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_name = session.get('user_name')
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    # Find projects where this user is assigned to any assignment field
    c.execute('''SELECT * FROM work_projects WHERE \
        reel_assigned_to = ? OR album_assigned_to = ? OR highlight_assigned_to = ? OR fullwork_assigned_to = ?
        ORDER BY created_at DESC''', (user_name, user_name, user_name, user_name))
    assigned_projects = c.fetchall()
    conn.close()
    return render_template('mywork.html', work_projects=assigned_projects, user_name=user_name)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=False)