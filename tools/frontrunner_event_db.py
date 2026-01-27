# tools/frontrunner_event_db.py
"""
FrontRunner Event Database - SQLite database for logging critical events
Tracks process failures and disk space warnings with timestamps and durations
"""
import os
import sqlite3
from datetime import datetime
from typing import Optional, Dict, List, Tuple

# Database configuration
DB_FOLDER_NAME = "database"
DB_FILE_NAME = "frontrunner_events.db"

# Current schema version
SCHEMA_VERSION = 1


def get_database_path(base_dir: str) -> str:
    """
    Get the path to the database file.
    Creates the database folder if it doesn't exist.
    """
    # Try USB structure first (E:\AutoTech\database)
    usb_db_folder = os.path.join(base_dir, "AutoTech", DB_FOLDER_NAME)
    if os.path.exists(os.path.join(base_dir, "AutoTech")):
        os.makedirs(usb_db_folder, exist_ok=True)
        return os.path.join(usb_db_folder, DB_FILE_NAME)

    # Fallback to dev structure (project\database)
    dev_db_folder = os.path.join(base_dir, DB_FOLDER_NAME)
    os.makedirs(dev_db_folder, exist_ok=True)
    return os.path.join(dev_db_folder, DB_FILE_NAME)


def init_database(db_path: str) -> bool:
    """
    Initialize the database with required tables.
    Returns True if successful.
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA busy_timeout=5000')
        cursor = conn.cursor()

        # Create schema version table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY
            )
        ''')

        # Check current version
        cursor.execute('SELECT version FROM schema_version LIMIT 1')
        row = cursor.fetchone()
        current_version = row[0] if row else 0

        # Create or migrate tables
        if current_version < SCHEMA_VERSION:
            # Process failure log - tracks when services go down/up
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS process_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    service_name TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    start_timestamp INTEGER NOT NULL,
                    end_time TEXT,
                    end_timestamp INTEGER,
                    duration_seconds INTEGER,
                    is_active INTEGER DEFAULT 1
                )
            ''')

            # Disk space warning log - tracks when disk exceeds 90%
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS disk_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    disk_percent REAL NOT NULL,
                    disk_used_gb REAL NOT NULL,
                    disk_total_gb REAL NOT NULL,
                    start_time TEXT NOT NULL,
                    start_timestamp INTEGER NOT NULL,
                    end_time TEXT,
                    end_timestamp INTEGER,
                    duration_seconds INTEGER,
                    is_active INTEGER DEFAULT 1
                )
            ''')

            # Create indexes for faster queries
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_process_service
                ON process_events(service_name, is_active)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_disk_active
                ON disk_events(is_active)
            ''')

            # Update schema version
            cursor.execute('DELETE FROM schema_version')
            cursor.execute('INSERT INTO schema_version VALUES (?)', (SCHEMA_VERSION,))

        conn.commit()
        conn.close()
        return True

    except Exception as e:
        print(f"Database init error: {e}")
        return False


def log_process_event(db_path: str, service_name: str, status: str) -> None:
    """
    Log a process status change event.

    Args:
        db_path: Path to database
        service_name: Name of the service (e.g., "FrontRunner Server")
        status: Current status ("Running" or "Stopped")
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA busy_timeout=5000')
        cursor = conn.cursor()

        now = datetime.now()
        timestamp = int(now.timestamp())
        time_str = now.strftime('%Y-%m-%d %H:%M:%S')

        if status == "Running":
            # Service is running - close any active "stopped" events
            cursor.execute('''
                SELECT id, start_timestamp FROM process_events
                WHERE service_name = ? AND event_type = 'stopped' AND is_active = 1
                ORDER BY start_timestamp DESC LIMIT 1
            ''', (service_name,))

            row = cursor.fetchone()
            if row:
                event_id, start_ts = row
                duration = timestamp - start_ts
                cursor.execute('''
                    UPDATE process_events
                    SET end_time = ?, end_timestamp = ?, duration_seconds = ?, is_active = 0
                    WHERE id = ?
                ''', (time_str, timestamp, duration, event_id))

        else:  # status == "Stopped"
            # Service is stopped - check if we already have an active stopped event
            cursor.execute('''
                SELECT id FROM process_events
                WHERE service_name = ? AND event_type = 'stopped' AND is_active = 1
            ''', (service_name,))

            if not cursor.fetchone():
                # No active stopped event - create new one
                cursor.execute('''
                    INSERT INTO process_events
                    (service_name, event_type, start_time, start_timestamp, is_active)
                    VALUES (?, 'stopped', ?, ?, 1)
                ''', (service_name, time_str, timestamp))

        conn.commit()
        conn.close()

    except Exception as e:
        print(f"Error logging process event: {e}")


def log_disk_event(db_path: str, disk_percent: float, disk_used_gb: float, disk_total_gb: float) -> None:
    """
    Log disk space event when usage exceeds 90%.

    Args:
        db_path: Path to database
        disk_percent: Current disk usage percentage
        disk_used_gb: Used disk space in GB
        disk_total_gb: Total disk space in GB
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA busy_timeout=5000')
        cursor = conn.cursor()

        now = datetime.now()
        timestamp = int(now.timestamp())
        time_str = now.strftime('%Y-%m-%d %H:%M:%S')

        if disk_percent >= 90:
            # Disk is over 90% - check if we already have an active event
            cursor.execute('''
                SELECT id FROM disk_events
                WHERE event_type = 'high_usage' AND is_active = 1
            ''')

            if not cursor.fetchone():
                # No active event - create new one
                cursor.execute('''
                    INSERT INTO disk_events
                    (event_type, disk_percent, disk_used_gb, disk_total_gb,
                     start_time, start_timestamp, is_active)
                    VALUES ('high_usage', ?, ?, ?, ?, ?, 1)
                ''', (disk_percent, disk_used_gb, disk_total_gb, time_str, timestamp))
            else:
                # Update existing active event with latest values
                cursor.execute('''
                    UPDATE disk_events
                    SET disk_percent = ?, disk_used_gb = ?, disk_total_gb = ?
                    WHERE event_type = 'high_usage' AND is_active = 1
                ''', (disk_percent, disk_used_gb, disk_total_gb))

        else:
            # Disk is below 90% - close any active high_usage events
            cursor.execute('''
                SELECT id, start_timestamp FROM disk_events
                WHERE event_type = 'high_usage' AND is_active = 1
            ''')

            row = cursor.fetchone()
            if row:
                event_id, start_ts = row
                duration = timestamp - start_ts
                cursor.execute('''
                    UPDATE disk_events
                    SET end_time = ?, end_timestamp = ?, duration_seconds = ?, is_active = 0
                    WHERE id = ?
                ''', (time_str, timestamp, duration, event_id))

        conn.commit()
        conn.close()

    except Exception as e:
        print(f"Error logging disk event: {e}")


def get_active_events(db_path: str) -> Dict[str, List[Dict]]:
    """
    Get all currently active events (process failures and disk warnings).

    Returns:
        Dict with 'process_events' and 'disk_events' lists
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA busy_timeout=5000')
        cursor = conn.cursor()

        # Get active process events
        cursor.execute('''
            SELECT service_name, event_type, start_time, start_timestamp
            FROM process_events
            WHERE is_active = 1
            ORDER BY start_timestamp DESC
        ''')

        process_events = []
        for row in cursor.fetchall():
            now_ts = int(datetime.now().timestamp())
            duration = now_ts - row[3]
            process_events.append({
                'service_name': row[0],
                'event_type': row[1],
                'start_time': row[2],
                'duration_seconds': duration,
                'duration_formatted': format_duration(duration)
            })

        # Get active disk events
        cursor.execute('''
            SELECT disk_percent, disk_used_gb, disk_total_gb, start_time, start_timestamp
            FROM disk_events
            WHERE is_active = 1
            ORDER BY start_timestamp DESC
        ''')

        disk_events = []
        for row in cursor.fetchall():
            now_ts = int(datetime.now().timestamp())
            duration = now_ts - row[4]
            disk_events.append({
                'disk_percent': row[0],
                'disk_used_gb': row[1],
                'disk_total_gb': row[2],
                'start_time': row[3],
                'duration_seconds': duration,
                'duration_formatted': format_duration(duration)
            })

        conn.close()

        return {
            'process_events': process_events,
            'disk_events': disk_events
        }

    except Exception as e:
        print(f"Error getting active events: {e}")
        return {'process_events': [], 'disk_events': []}


def get_event_history(db_path: str, limit: int = 100) -> Dict[str, List[Dict]]:
    """
    Get historical events (both active and resolved).

    Args:
        limit: Maximum number of events per type to return

    Returns:
        Dict with 'process_events' and 'disk_events' lists
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA busy_timeout=5000')
        cursor = conn.cursor()

        # Get process events
        cursor.execute('''
            SELECT service_name, event_type, start_time, end_time,
                   duration_seconds, is_active, start_timestamp
            FROM process_events
            ORDER BY start_timestamp DESC
            LIMIT ?
        ''', (limit,))

        process_events = []
        for row in cursor.fetchall():
            duration = row[4]
            if row[5] == 1:  # is_active
                now_ts = int(datetime.now().timestamp())
                duration = now_ts - row[6]

            process_events.append({
                'service_name': row[0],
                'event_type': row[1],
                'start_time': row[2],
                'end_time': row[3] if row[3] else 'Ongoing',
                'duration_seconds': duration,
                'duration_formatted': format_duration(duration) if duration else 'N/A',
                'is_active': row[5] == 1
            })

        # Get disk events
        cursor.execute('''
            SELECT disk_percent, disk_used_gb, disk_total_gb,
                   start_time, end_time, duration_seconds, is_active, start_timestamp
            FROM disk_events
            ORDER BY start_timestamp DESC
            LIMIT ?
        ''', (limit,))

        disk_events = []
        for row in cursor.fetchall():
            duration = row[5]
            if row[6] == 1:  # is_active
                now_ts = int(datetime.now().timestamp())
                duration = now_ts - row[7]

            disk_events.append({
                'disk_percent': row[0],
                'disk_used_gb': row[1],
                'disk_total_gb': row[2],
                'start_time': row[3],
                'end_time': row[4] if row[4] else 'Ongoing',
                'duration_seconds': duration,
                'duration_formatted': format_duration(duration) if duration else 'N/A',
                'is_active': row[6] == 1
            })

        conn.close()

        return {
            'process_events': process_events,
            'disk_events': disk_events
        }

    except Exception as e:
        print(f"Error getting event history: {e}")
        return {'process_events': [], 'disk_events': []}


def format_duration(seconds: int) -> str:
    """Format duration in seconds to human-readable string."""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}m {secs}s"
    elif seconds < 86400:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"
    else:
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        return f"{days}d {hours}h"


# Test function
if __name__ == "__main__":
    import time

    print("Testing FrontRunner Event Database...")

    # Get database path
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = get_database_path(base_dir)
    print(f"Database: {db_path}")

    # Initialize database
    if init_database(db_path):
        print("[OK] Database initialized")

    # Test process event logging
    print("\n=== Testing Process Events ===")
    log_process_event(db_path, "FrontRunner Server", "Stopped")
    print("[OK] Logged: FrontRunner Server stopped")

    time.sleep(2)

    log_process_event(db_path, "haul road planning server", "Stopped")
    print("[OK] Logged: haul road planning server stopped")

    # Check active events
    active = get_active_events(db_path)
    print(f"\nActive process events: {len(active['process_events'])}")
    for event in active['process_events']:
        print(f"  - {event['service_name']}: {event['event_type']} (Duration: {event['duration_formatted']})")

    # Test disk event logging
    print("\n=== Testing Disk Events ===")
    log_disk_event(db_path, 92.5, 9472.0, 10240.0)
    print("[OK] Logged: Disk space at 92.5%")

    active = get_active_events(db_path)
    print(f"\nActive disk events: {len(active['disk_events'])}")
    for event in active['disk_events']:
        print(f"  - Disk at {event['disk_percent']}% (Duration: {event['duration_formatted']})")

    # Test resolving events
    print("\n=== Testing Event Resolution ===")
    log_process_event(db_path, "FrontRunner Server", "Running")
    print("[OK] Resolved: FrontRunner Server back online")

    log_disk_event(db_path, 85.0, 8704.0, 10240.0)
    print("[OK] Resolved: Disk space back to normal")

    # Get history
    print("\n=== Event History ===")
    history = get_event_history(db_path, limit=10)
    print(f"Process events in history: {len(history['process_events'])}")
    for event in history['process_events'][:3]:
        status = "ACTIVE" if event['is_active'] else "RESOLVED"
        print(f"  [{status}] {event['service_name']}: {event['start_time']} -> {event['end_time']} ({event['duration_formatted']})")

    print(f"\nDisk events in history: {len(history['disk_events'])}")
    for event in history['disk_events'][:3]:
        status = "ACTIVE" if event['is_active'] else "RESOLVED"
        print(f"  [{status}] {event['disk_percent']}%: {event['start_time']} -> {event['end_time']} ({event['duration_formatted']})")
