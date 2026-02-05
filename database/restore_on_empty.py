"""
One-time database restoration script for Railway
Restores from backup.sql if the database is empty or doesn't exist.
"""
import os
import sys
import sqlite3
from pathlib import Path

# Configuration
BASE_DIR = os.getenv('BASE_DIR', '/app')
DATA_DIR = os.path.join(BASE_DIR, 'data')
DATABASE_PATH = os.path.join(DATA_DIR, 'breaktime.db')
BACKUP_SQL_PATH = os.path.join(BASE_DIR, 'database', 'backup.sql')

def log(msg):
    """Print and flush to ensure visibility in logs."""
    print(msg, flush=True)

def check_database_empty():
    """Check if database exists and has data."""
    log(f"[Restore] Checking database at: {DATABASE_PATH}")
    log(f"[Restore] Database exists: {os.path.exists(DATABASE_PATH)}")

    if not os.path.exists(DATABASE_PATH):
        return True

    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM break_logs")
        count = cursor.fetchone()[0]
        conn.close()
        log(f"[Restore] Found {count} records in break_logs")
        return count == 0
    except Exception as e:
        log(f"[Restore] Error checking database: {e}")
        return True

def restore_from_backup():
    """Restore database from backup.sql."""
    log(f"[Restore] Looking for backup at: {BACKUP_SQL_PATH}")
    log(f"[Restore] Backup file exists: {os.path.exists(BACKUP_SQL_PATH)}")

    if not os.path.exists(BACKUP_SQL_PATH):
        log(f"[Restore] Backup file not found: {BACKUP_SQL_PATH}")
        # List contents of database directory for debugging
        db_dir = os.path.join(BASE_DIR, 'database')
        if os.path.exists(db_dir):
            log(f"[Restore] Contents of {db_dir}: {os.listdir(db_dir)}")
        return False

    try:
        # Ensure data directory exists
        Path(DATA_DIR).mkdir(parents=True, exist_ok=True)

        # Delete existing database file if it exists (backup.sql has CREATE TABLE statements)
        if os.path.exists(DATABASE_PATH):
            log(f"[Restore] Removing existing database to restore from backup...")
            os.remove(DATABASE_PATH)

        # Read backup SQL
        with open(BACKUP_SQL_PATH, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        log(f"[Restore] Read backup SQL ({len(sql_script)} bytes)")

        # Create/restore database from scratch
        conn = sqlite3.connect(DATABASE_PATH)
        conn.executescript(sql_script)
        conn.commit()

        # Verify restoration
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM break_logs")
        count = cursor.fetchone()[0]
        conn.close()

        log(f"[Restore] Database restored successfully with {count} break_logs records")
        return True

    except Exception as e:
        log(f"[Restore] Failed to restore database: {e}")
        import traceback
        log(f"[Restore] Traceback: {traceback.format_exc()}")
        return False

def run_restore_if_needed():
    """Main function - restore if database is empty."""
    log("[Restore] ========== RESTORE CHECK STARTED ==========")
    log(f"[Restore] BASE_DIR: {BASE_DIR}")
    log(f"[Restore] DATA_DIR: {DATA_DIR}")
    log(f"[Restore] DATABASE_PATH: {DATABASE_PATH}")
    log(f"[Restore] BACKUP_SQL_PATH: {BACKUP_SQL_PATH}")

    if check_database_empty():
        log("[Restore] Database is empty or missing, attempting restoration...")
        if restore_from_backup():
            log("[Restore] Restoration complete!")
        else:
            log("[Restore] Restoration failed - database will start fresh")
    else:
        log("[Restore] Database already has data, skipping restoration")

    log("[Restore] ========== RESTORE CHECK FINISHED ==========")

if __name__ == '__main__':
    run_restore_if_needed()
