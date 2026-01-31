# tools/autotech_db.py
"""
AutoTech Main Database - SQLite database for core application tables.
Manages users, sessions, equipment master, activity logs, VNC sessions,
screenshots, site config, credentials, alerts, and component history.

These tables complement the domain-specific databases:
  - equipment_cache.db (equipment_db.py) - IP finder cache
  - ptx_uptime.db (ptx_uptime_db.py) - PTX uptime tracking
  - frontrunner_events.db (frontrunner_event_db.py) - FrontRunner process/disk events
"""
import os
import sqlite3
from datetime import datetime
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)

# Database configuration
DB_FOLDER_NAME = "database"
DB_FILE_NAME = "autotech.db"

# Current schema version - increment when schema changes
SCHEMA_VERSION = 1


def get_database_path(base_dir: str) -> str:
    """
    Get the path to the main autotech database file.
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


def get_connection(db_path: str) -> sqlite3.Connection:
    """Get a database connection with WAL mode and foreign keys enabled."""
    conn = sqlite3.connect(db_path)
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA busy_timeout=5000')
    conn.execute('PRAGMA foreign_keys=ON')
    conn.row_factory = sqlite3.Row
    return conn


def init_database(db_path: str) -> bool:
    """
    Initialize the main AutoTech database with all required tables.
    Returns True if successful.
    """
    try:
        conn = get_connection(db_path)
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

        if current_version < SCHEMA_VERSION:
            # ==========================================
            # USERS TABLE
            # ==========================================
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    display_name TEXT,
                    role TEXT NOT NULL DEFAULT 'technician' CHECK(role IN ('technician', 'admin')),
                    contact_number TEXT,
                    shift TEXT,
                    theme_preference TEXT DEFAULT 'dark',
                    dashboard_layout TEXT,
                    settings_json TEXT,
                    last_login DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    is_active INTEGER DEFAULT 1
                )
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_users_username
                ON users(username)
            ''')

            # ==========================================
            # SESSIONS TABLE
            # ==========================================
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    session_token TEXT UNIQUE NOT NULL,
                    ip_address TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    expires_at DATETIME,
                    is_active INTEGER DEFAULT 1,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_sessions_token
                ON sessions(session_token)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_sessions_user
                ON sessions(user_id)
            ''')

            # ==========================================
            # EQUIPMENT TABLE (master equipment registry)
            # ==========================================
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS equipment (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    oid TEXT,
                    cid TEXT,
                    profile_type TEXT,
                    equipment_type TEXT CHECK(equipment_type IN ('AHT', 'backhoe', 'dozer', 'grader', 'excavator', 'water_cart', 'EMV', 'other')),
                    model TEXT,
                    network_ip TEXT,
                    ptx_ip TEXT,
                    avi_ip TEXT,
                    status TEXT DEFAULT 'unknown' CHECK(status IN ('online', 'offline', 'unknown')),
                    smr REAL,
                    last_contact DATETIME,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    notes TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_equipment_oid
                ON equipment(oid)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_equipment_status
                ON equipment(status)
            ''')

            # ==========================================
            # ACTIVITY LOG TABLE
            # ==========================================
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS activity_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    action_type TEXT NOT NULL CHECK(action_type IN (
                        'tool_execution', 'vnc_session', 'health_check',
                        'reboot', 'login', 'logout', 'config_change'
                    )),
                    equipment_id INTEGER,
                    tool_name TEXT,
                    parameters_json TEXT,
                    result_status TEXT CHECK(result_status IN ('success', 'failure', 'error')),
                    result_summary TEXT,
                    duration_ms INTEGER,
                    ip_address TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
                    FOREIGN KEY (equipment_id) REFERENCES equipment(id) ON DELETE SET NULL
                )
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_activity_log_user
                ON activity_log(user_id)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_activity_log_timestamp
                ON activity_log(timestamp)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_activity_log_action
                ON activity_log(action_type)
            ''')

            # ==========================================
            # COMPONENT HISTORY TABLE
            # ==========================================
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS component_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    equipment_id INTEGER NOT NULL,
                    component_type TEXT NOT NULL,
                    part_number TEXT,
                    serial_old TEXT,
                    serial_new TEXT,
                    changed_by TEXT,
                    changed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    work_order TEXT,
                    notes TEXT,
                    FOREIGN KEY (equipment_id) REFERENCES equipment(id) ON DELETE CASCADE
                )
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_component_history_equipment
                ON component_history(equipment_id)
            ''')

            # ==========================================
            # VNC SESSIONS TABLE
            # ==========================================
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS vnc_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    equipment_id INTEGER,
                    equipment_ip TEXT,
                    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    ended_at DATETIME,
                    duration_seconds INTEGER,
                    screenshots_count INTEGER DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
                    FOREIGN KEY (equipment_id) REFERENCES equipment(id) ON DELETE SET NULL
                )
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_vnc_sessions_user
                ON vnc_sessions(user_id)
            ''')

            # ==========================================
            # SCREENSHOTS TABLE
            # ==========================================
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS screenshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    vnc_session_id INTEGER,
                    equipment_id INTEGER,
                    file_path TEXT NOT NULL,
                    thumbnail_path TEXT,
                    captured_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    captured_by TEXT,
                    FOREIGN KEY (vnc_session_id) REFERENCES vnc_sessions(id) ON DELETE CASCADE,
                    FOREIGN KEY (equipment_id) REFERENCES equipment(id) ON DELETE SET NULL
                )
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_screenshots_session
                ON screenshots(vnc_session_id)
            ''')

            # ==========================================
            # SITE CONFIG TABLE
            # ==========================================
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS site_config (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    site_name TEXT NOT NULL,
                    config_key TEXT NOT NULL,
                    config_value TEXT,
                    config_type TEXT DEFAULT 'string' CHECK(config_type IN ('string', 'int', 'bool', 'json')),
                    description TEXT,
                    updated_by TEXT,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(site_name, config_key)
                )
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_site_config_key
                ON site_config(site_name, config_key)
            ''')

            # ==========================================
            # CREDENTIALS TABLE
            # ==========================================
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS credentials (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    credential_name TEXT NOT NULL,
                    credential_type TEXT NOT NULL CHECK(credential_type IN ('ssh', 'service')),
                    username TEXT NOT NULL,
                    encrypted_password TEXT,
                    equipment_type TEXT DEFAULT 'all' CHECK(equipment_type IN ('PTXC', 'PTX10', 'server', 'all')),
                    site_id INTEGER,
                    created_by TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_credentials_name
                ON credentials(credential_name)
            ''')

            # ==========================================
            # ALERTS TABLE
            # ==========================================
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_type TEXT NOT NULL CHECK(alert_type IN (
                        'disk_space', 'service_down', 'equipment_offline', 'high_uptime'
                    )),
                    severity TEXT NOT NULL DEFAULT 'info' CHECK(severity IN ('info', 'warning', 'critical')),
                    message TEXT NOT NULL,
                    equipment_id INTEGER,
                    acknowledged_by TEXT,
                    acknowledged_at DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    resolved_at DATETIME,
                    FOREIGN KEY (equipment_id) REFERENCES equipment(id) ON DELETE SET NULL
                )
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_alerts_type
                ON alerts(alert_type)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_alerts_severity
                ON alerts(severity)
            ''')

            # Update schema version
            cursor.execute('DELETE FROM schema_version')
            cursor.execute('INSERT INTO schema_version (version) VALUES (?)',
                           (SCHEMA_VERSION,))

            conn.commit()
            logger.info(f"AutoTech main database initialized (schema v{SCHEMA_VERSION})")

        conn.close()
        return True

    except Exception as e:
        logger.error(f"Failed to initialize AutoTech database: {e}")
        return False


def get_database_stats(db_path: str) -> Dict:
    """Get statistics about all tables in the main database."""
    stats = {}
    try:
        conn = get_connection(db_path)
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name != 'schema_version' AND name != 'sqlite_sequence'"
        ).fetchall()
        for t in tables:
            tname = t[0]
            count = conn.execute(f'SELECT COUNT(*) FROM "{tname}"').fetchone()[0]
            stats[tname] = count
        conn.close()
    except Exception as e:
        logger.error(f"Failed to get database stats: {e}")
    return stats
