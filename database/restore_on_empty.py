"""
Database cleanup script - ONE TIME USE
Removes old CSR data and starts fresh.
"""
import os
import sys

# Configuration
BASE_DIR = os.getenv('BASE_DIR', '/app')
DATA_DIR = os.path.join(BASE_DIR, 'data')
DATABASE_PATH = os.path.join(DATA_DIR, 'breaktime.db')

def log(msg):
    """Print and flush to ensure visibility in logs."""
    print(msg, flush=True)

def run_restore_if_needed():
    """Clear old data - ONE TIME cleanup."""
    log("[Cleanup] ========== DATABASE CLEANUP ==========")
    log(f"[Cleanup] DATABASE_PATH: {DATABASE_PATH}")

    if os.path.exists(DATABASE_PATH):
        log("[Cleanup] Removing old database with CSR data...")
        os.remove(DATABASE_PATH)
        log("[Cleanup] Old database removed - fresh start!")
    else:
        log("[Cleanup] No existing database found")

    log("[Cleanup] ========== CLEANUP COMPLETE ==========")

if __name__ == '__main__':
    run_restore_if_needed()
