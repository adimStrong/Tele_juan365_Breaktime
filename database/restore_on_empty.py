"""
One-time database restoration script for Railway
Restores from backup.sql if the database is empty or doesn't exist.
"""
import os
import sqlite3
from pathlib import Path

# Configuration
BASE_DIR = os.getenv('BASE_DIR', '/app')
DATA_DIR = os.path.join(BASE_DIR, 'data')
DATABASE_PATH = os.path.join(DATA_DIR, 'breaktime.db')
BACKUP_SQL_PATH = os.path.join(BASE_DIR, 'database', 'backup.sql')

def check_database_empty():
    """Check if database exists and has data."""
    if not os.path.exists(DATABASE_PATH):
        return True

    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM break_logs")
        count = cursor.fetchone()[0]
        conn.close()
        return count == 0
    except Exception:
        return True

def restore_from_backup():
    """Restore database from backup.sql."""
    if not os.path.exists(BACKUP_SQL_PATH):
        print(f"[Restore] Backup file not found: {BACKUP_SQL_PATH}")
        return False

    try:
        # Ensure data directory exists
        Path(DATA_DIR).mkdir(parents=True, exist_ok=True)

        # Read backup SQL
        with open(BACKUP_SQL_PATH, 'r', encoding='utf-8') as f:
            sql_script = f.read()

        # Create/restore database
        conn = sqlite3.connect(DATABASE_PATH)
        conn.executescript(sql_script)
        conn.commit()

        # Verify restoration
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM break_logs")
        count = cursor.fetchone()[0]
        conn.close()

        print(f"[Restore] Database restored successfully with {count} break_logs records")
        return True

    except Exception as e:
        print(f"[Restore] Failed to restore database: {e}")
        return False

def run_restore_if_needed():
    """Main function - restore if database is empty."""
    print("[Restore] Checking database state...")

    if check_database_empty():
        print("[Restore] Database is empty or missing, attempting restoration...")
        if restore_from_backup():
            print("[Restore] Restoration complete!")
        else:
            print("[Restore] Restoration failed - database will start fresh")
    else:
        print("[Restore] Database already has data, skipping restoration")

if __name__ == '__main__':
    run_restore_if_needed()
