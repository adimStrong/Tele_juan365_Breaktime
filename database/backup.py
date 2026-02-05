"""
Database Backup Utility for Tele_juan365 Breaktime
Provides automated daily backups with rotation (keeps last 7 days)
"""
import os
import sqlite3
import shutil
import gzip
from datetime import datetime, timedelta
from pathlib import Path
import pytz

# Philippine Timezone
PH_TZ = pytz.timezone('Asia/Manila')

# Configuration
BASE_DIR = os.getenv('BASE_DIR', '/app')
DATA_DIR = os.path.join(BASE_DIR, 'data')
BACKUP_DIR = os.path.join(BASE_DIR, 'backups')
DATABASE_PATH = os.path.join(DATA_DIR, 'breaktime.db')
MAX_BACKUPS = 7  # Keep last 7 backups

def ensure_backup_dir():
    """Ensure backup directory exists"""
    Path(BACKUP_DIR).mkdir(parents=True, exist_ok=True)
    return BACKUP_DIR

def get_backup_filename(timestamp=None):
    """Generate backup filename with timestamp"""
    if timestamp is None:
        timestamp = datetime.now(PH_TZ)
    date_str = timestamp.strftime('%Y%m%d_%H%M%S')
    return f"breaktime_backup_{date_str}.db"

def create_backup(compress=True):
    """
    Create a backup of the database

    Args:
        compress: If True, creates a gzipped backup

    Returns:
        dict with backup info or error
    """
    try:
        ensure_backup_dir()

        if not os.path.exists(DATABASE_PATH):
            return {
                'success': False,
                'error': f'Database not found at {DATABASE_PATH}'
            }

        timestamp = datetime.now(PH_TZ)
        backup_filename = get_backup_filename(timestamp)
        backup_path = os.path.join(BACKUP_DIR, backup_filename)

        # Use SQLite's backup API for safe backup (handles locks)
        source_conn = sqlite3.connect(DATABASE_PATH)
        backup_conn = sqlite3.connect(backup_path)

        source_conn.backup(backup_conn)

        source_conn.close()
        backup_conn.close()

        final_path = backup_path
        file_size = os.path.getsize(backup_path)

        # Compress if requested
        if compress:
            compressed_path = backup_path + '.gz'
            with open(backup_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)

            # Remove uncompressed backup
            os.remove(backup_path)
            final_path = compressed_path
            file_size = os.path.getsize(compressed_path)

        print(f"[OK] Backup created: {os.path.basename(final_path)} ({file_size / 1024:.1f} KB)")

        return {
            'success': True,
            'path': final_path,
            'filename': os.path.basename(final_path),
            'size_bytes': file_size,
            'size_kb': round(file_size / 1024, 1),
            'timestamp': timestamp.isoformat(),
            'compressed': compress
        }

    except Exception as e:
        print(f"[ERROR] Backup failed: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def create_sql_dump():
    """
    Create a SQL dump backup (text format, good for version control)

    Returns:
        dict with backup info or error
    """
    try:
        ensure_backup_dir()

        if not os.path.exists(DATABASE_PATH):
            return {
                'success': False,
                'error': f'Database not found at {DATABASE_PATH}'
            }

        timestamp = datetime.now(PH_TZ)
        date_str = timestamp.strftime('%Y%m%d_%H%M%S')
        dump_filename = f"breaktime_dump_{date_str}.sql"
        dump_path = os.path.join(BACKUP_DIR, dump_filename)

        conn = sqlite3.connect(DATABASE_PATH)

        with open(dump_path, 'w', encoding='utf-8') as f:
            for line in conn.iterdump():
                f.write(f'{line}\n')

        conn.close()

        file_size = os.path.getsize(dump_path)
        print(f"[OK] SQL dump created: {dump_filename} ({file_size / 1024:.1f} KB)")

        return {
            'success': True,
            'path': dump_path,
            'filename': dump_filename,
            'size_bytes': file_size,
            'size_kb': round(file_size / 1024, 1),
            'timestamp': timestamp.isoformat(),
            'format': 'sql'
        }

    except Exception as e:
        print(f"[ERROR] SQL dump failed: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def rotate_backups():
    """
    Remove old backups, keeping only the most recent MAX_BACKUPS

    Returns:
        dict with rotation info
    """
    try:
        ensure_backup_dir()

        # Get all backup files
        backup_files = []
        for f in os.listdir(BACKUP_DIR):
            if f.startswith('breaktime_backup_') and (f.endswith('.db') or f.endswith('.db.gz')):
                full_path = os.path.join(BACKUP_DIR, f)
                backup_files.append({
                    'path': full_path,
                    'filename': f,
                    'mtime': os.path.getmtime(full_path)
                })

        # Sort by modification time (newest first)
        backup_files.sort(key=lambda x: x['mtime'], reverse=True)

        # Remove old backups
        removed = []
        if len(backup_files) > MAX_BACKUPS:
            for old_backup in backup_files[MAX_BACKUPS:]:
                os.remove(old_backup['path'])
                removed.append(old_backup['filename'])
                print(f"[DEL] Removed old backup: {old_backup['filename']}")

        return {
            'success': True,
            'total_backups': len(backup_files),
            'kept': min(len(backup_files), MAX_BACKUPS),
            'removed': removed,
            'removed_count': len(removed)
        }

    except Exception as e:
        print(f"[ERROR] Backup rotation failed: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def list_backups():
    """
    List all available backups

    Returns:
        list of backup info dicts
    """
    try:
        ensure_backup_dir()

        backups = []
        for f in os.listdir(BACKUP_DIR):
            if f.startswith('breaktime_') and (f.endswith('.db') or f.endswith('.db.gz') or f.endswith('.sql')):
                full_path = os.path.join(BACKUP_DIR, f)
                stat = os.stat(full_path)
                backups.append({
                    'filename': f,
                    'path': full_path,
                    'size_bytes': stat.st_size,
                    'size_kb': round(stat.st_size / 1024, 1),
                    'created': datetime.fromtimestamp(stat.st_mtime, PH_TZ).isoformat(),
                    'compressed': f.endswith('.gz'),
                    'format': 'sql' if f.endswith('.sql') else 'sqlite'
                })

        # Sort by creation time (newest first)
        backups.sort(key=lambda x: x['created'], reverse=True)

        return backups

    except Exception as e:
        print(f"[ERROR] Failed to list backups: {e}")
        return []

def restore_backup(backup_filename):
    """
    Restore database from a backup file

    Args:
        backup_filename: Name of backup file to restore

    Returns:
        dict with restore info or error
    """
    try:
        backup_path = os.path.join(BACKUP_DIR, backup_filename)

        if not os.path.exists(backup_path):
            return {
                'success': False,
                'error': f'Backup file not found: {backup_filename}'
            }

        # Create a backup of current database before restore
        pre_restore = create_backup(compress=True)
        if pre_restore['success']:
            print(f"[OK] Pre-restore backup created: {pre_restore['filename']}")

        # Handle compressed backups
        if backup_filename.endswith('.gz'):
            temp_path = backup_path[:-3]  # Remove .gz
            with gzip.open(backup_path, 'rb') as f_in:
                with open(temp_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            restore_source = temp_path
            cleanup_temp = True
        else:
            restore_source = backup_path
            cleanup_temp = False

        # Restore using SQLite backup API
        source_conn = sqlite3.connect(restore_source)
        dest_conn = sqlite3.connect(DATABASE_PATH)

        source_conn.backup(dest_conn)

        source_conn.close()
        dest_conn.close()

        # Cleanup temp file if we decompressed
        if cleanup_temp and os.path.exists(restore_source):
            os.remove(restore_source)

        print(f"[OK] Database restored from: {backup_filename}")

        return {
            'success': True,
            'restored_from': backup_filename,
            'pre_restore_backup': pre_restore.get('filename') if pre_restore['success'] else None
        }

    except Exception as e:
        print(f"[ERROR] Restore failed: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def run_daily_backup():
    """
    Run the daily backup routine (backup + rotation)
    Called by scheduler

    Returns:
        dict with backup and rotation results
    """
    print(f"\n[BACKUP] Running daily backup at {datetime.now(PH_TZ).strftime('%Y-%m-%d %H:%M:%S')} PH Time")

    # Create backup
    backup_result = create_backup(compress=True)

    # Rotate old backups
    rotation_result = rotate_backups()

    return {
        'backup': backup_result,
        'rotation': rotation_result,
        'timestamp': datetime.now(PH_TZ).isoformat()
    }

# Quick test
if __name__ == '__main__':
    print("Testing backup system...")

    # Test backup
    result = create_backup(compress=True)
    print(f"Backup result: {result}")

    # List backups
    backups = list_backups()
    print(f"\nAvailable backups ({len(backups)}):")
    for b in backups:
        print(f"  - {b['filename']} ({b['size_kb']} KB)")

    # Test rotation
    rotation = rotate_backups()
    print(f"\nRotation result: {rotation}")
