#!/usr/bin/env python3
"""
Convex Studio Inventory - Upgrade Implementation Script
This script provides the foundation for future upgrades and maintenance.
"""

import sqlite3
import os
import shutil
import json
import logging
from datetime import datetime
from pathlib import Path

class InventoryUpgradeManager:
    def __init__(self, db_path='inventory.db'):
        self.db_path = db_path
        self.backup_dir = Path('backups')
        self.logs_dir = Path('logs')
        self.setup_directories()
        self.setup_logging()
        
    def setup_directories(self):
        """Create necessary directories for backups and logs"""
        self.backup_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        
    def setup_logging(self):
        """Setup logging for upgrade operations"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.logs_dir / 'upgrade.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def get_db_version(self):
        """Get current database schema version"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        try:
            # Check if schema_version table exists
            c.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='schema_version'
            """)
            
            if not c.fetchone():
                # Create schema_version table if it doesn't exist
                c.execute('''
                    CREATE TABLE schema_version (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        version INTEGER NOT NULL,
                        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        description TEXT
                    )
                ''')
                c.execute("INSERT INTO schema_version (version, description) VALUES (1, 'Initial version')")
                conn.commit()
                return 1
            
            # Get latest version
            c.execute("SELECT version FROM schema_version ORDER BY id DESC LIMIT 1")
            version = c.fetchone()[0]
            return version
            
        except Exception as e:
            self.logger.error(f"Error getting database version: {e}")
            return 0
        finally:
            conn.close()
            
    def backup_database(self):
        """Create a backup of the current database"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"inventory_backup_{timestamp}.db"
            backup_path = self.backup_dir / backup_name
            
            shutil.copy2(self.db_path, backup_path)
            self.logger.info(f"Database backed up to: {backup_path}")
            return backup_path
            
        except Exception as e:
            self.logger.error(f"Backup failed: {e}")
            return None
            
    def run_migration(self, version, description, migration_func):
        """Run a database migration"""
        try:
            self.logger.info(f"Running migration to version {version}: {description}")
            
            # Run the migration
            migration_func()
            
            # Record the migration
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute(
                "INSERT INTO schema_version (version, description) VALUES (?, ?)",
                (version, description)
            )
            conn.commit()
            conn.close()
            
            self.logger.info(f"Migration to version {version} completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Migration to version {version} failed: {e}")
            return False
            
    def health_check(self):
        """Perform a health check on the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            # Check if all required tables exist
            required_tables = ['stock', 'orders', 'work_projects', 'schema_version']
            existing_tables = []
            
            for table in required_tables:
                c.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name=?
                """, (table,))
                if c.fetchone():
                    existing_tables.append(table)
                    
            # Check table row counts
            table_counts = {}
            for table in existing_tables:
                c.execute(f"SELECT COUNT(*) FROM {table}")
                count = c.fetchone()[0]
                table_counts[table] = count
                
            conn.close()
            
            health_status = {
                'status': 'healthy' if len(existing_tables) == len(required_tables) else 'degraded',
                'database_version': self.get_db_version(),
                'tables_found': existing_tables,
                'missing_tables': [t for t in required_tables if t not in existing_tables],
                'table_counts': table_counts,
                'timestamp': datetime.now().isoformat()
            }
            
            self.logger.info(f"Health check completed: {health_status['status']}")
            return health_status
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            
    def list_backups(self):
        """List all available database backups"""
        backups = []
        for backup_file in self.backup_dir.glob("inventory_backup_*.db"):
            stat = backup_file.stat()
            backups.append({
                'filename': backup_file.name,
                'size_mb': round(stat.st_size / (1024 * 1024), 2),
                'created': datetime.fromtimestamp(stat.st_ctime).isoformat()
            })
        
        return sorted(backups, key=lambda x: x['created'], reverse=True)
        
    def restore_backup(self, backup_filename):
        """Restore database from a backup"""
        try:
            backup_path = self.backup_dir / backup_filename
            
            if not backup_path.exists():
                raise FileNotFoundError(f"Backup file not found: {backup_filename}")
                
            # Create a backup of current database before restore
            current_backup = self.backup_database()
            
            # Restore the backup
            shutil.copy2(backup_path, self.db_path)
            
            self.logger.info(f"Database restored from: {backup_filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"Restore failed: {e}")
            return False

# Example migration functions
def migration_2_add_audit_trail():
    """Migration 2: Add audit trail table"""
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS audit_trail (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            table_name TEXT NOT NULL,
            record_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            old_values TEXT,
            new_values TEXT,
            user_id TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def migration_3_add_user_management():
    """Migration 3: Add user management tables"""
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'staff',
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS user_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            session_token TEXT UNIQUE NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def add_completed_date_columns():
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    # Add columns if they do not exist
    for col in ['reel_completed_date', 'album_completed_date', 'highlight_completed_date', 'fullwork_completed_date']:
        c.execute(f"PRAGMA table_info(work_projects)")
        columns = [row[1] for row in c.fetchall()]
        if col not in columns:
            c.execute(f"ALTER TABLE work_projects ADD COLUMN {col} TEXT")
    conn.commit()
    conn.close()

def add_reel_completed_date_column():
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    c.execute("PRAGMA table_info(work_projects)")
    columns = [row[1] for row in c.fetchall()]
    if 'reel_completed_date' not in columns:
        c.execute("ALTER TABLE work_projects ADD COLUMN reel_completed_date TEXT")
    conn.commit()
    conn.close()

def add_assignment_completed_date_columns():
    conn = sqlite3.connect('inventory.db')
    c = conn.cursor()
    c.execute("PRAGMA table_info(work_projects)")
    columns = [row[1] for row in c.fetchall()]
    for col in ['album_completed_date', 'highlight_completed_date', 'fullwork_completed_date']:
        if col not in columns:
            c.execute(f"ALTER TABLE work_projects ADD COLUMN {col} TEXT")
    conn.commit()
    conn.close()

def migrate_add_payment_details_table():
    db = sqlite3.connect('inventory.db')
    db.execute("""
    CREATE TABLE IF NOT EXISTS payment_details (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL UNIQUE,
        quoted_amount REAL NOT NULL,
        discount REAL DEFAULT 0,
        advance_amount REAL DEFAULT 0,
        remaining_amount REAL,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES work_projects(id)
    )
    """)
    db.commit()
    db.close()

def main():
    """Main function to demonstrate upgrade functionality"""
    upgrade_manager = InventoryUpgradeManager()
    
    print("=== Convex Studio Inventory - Upgrade Manager ===\n")
    
    # Health check
    print("1. Performing health check...")
    health = upgrade_manager.health_check()
    print(f"Status: {health['status']}")
    print(f"Database Version: {health['database_version']}")
    print(f"Tables: {', '.join(health['tables_found'])}")
    
    # List backups
    print("\n2. Available backups:")
    backups = upgrade_manager.list_backups()
    if backups:
        for backup in backups[:5]:  # Show last 5 backups
            print(f"  - {backup['filename']} ({backup['size_mb']}MB, {backup['created']})")
    else:
        print("  No backups found")
    
    # Create backup
    print("\n3. Creating backup...")
    backup_path = upgrade_manager.backup_database()
    if backup_path:
        print(f"  Backup created: {backup_path}")
    
    # Example of running a migration
    current_version = upgrade_manager.get_db_version()
    print(f"\n4. Current database version: {current_version}")
    
    if current_version < 2:
        print("  Running migration to version 2 (audit trail)...")
        success = upgrade_manager.run_migration(
            2, 
            "Add audit trail table", 
            migration_2_add_audit_trail
        )
        if success:
            print("  Migration completed successfully")
        else:
            print("  Migration failed")
    
    if current_version < 3:
        print("  Running migration to version 3 (user management)...")
        success = upgrade_manager.run_migration(
            3, 
            "Add user management tables", 
            migration_3_add_user_management
        )
        if success:
            print("  Migration completed successfully")
        else:
            print("  Migration failed")
    
    print("\n=== Upgrade Manager Complete ===")

if __name__ == "__main__":
    main() 