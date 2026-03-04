# tools/ptx_uptime_db.py
"""
PTX Uptime Database - SQLite database for storing PTX uptime data
Stores uptime records for offline reference and historical tracking
"""
import os
import sqlite3
import re
from datetime import datetime
from typing import Optional, Dict, List, Tuple
import logging
import tools.app_logger as app_logger # Changed to module import

logger = logging.getLogger(__name__)

# Database configuration
DB_FOLDER_NAME = "database"
DB_FILE_NAME = "ptx_uptime.db"

# Current schema version - increment when schema changes
SCHEMA_VERSION = 1


def get_database_path(base_dir: str) -> str:
    r"""
    Get the path to the database file.
    Creates the database folder if it doesn't exist.

    Structure:
    - USB: E:\AutoTech\database\ptx_uptime.db
    - Dev: project\database\ptx_uptime.db
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
            # Drop old tables if exist (for clean migration)
            cursor.execute('DROP TABLE IF EXISTS ptx_uptime')
            cursor.execute('DROP TABLE IF EXISTS uptime_history')
            cursor.execute('DROP TABLE IF EXISTS reboot_log')

            # Create PTX uptime table - current snapshot
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ptx_uptime (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    equipment_id TEXT UNIQUE NOT NULL,
                    ip_address TEXT NOT NULL,
                    uptime_hours REAL NOT NULL,
                    last_check TEXT,
                    last_check_timestamp INTEGER,
                    ptx_type TEXT,
                    last_status TEXT DEFAULT 'unknown',
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Create index on equipment_id for faster lookups
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_ptx_equipment_id
                ON ptx_uptime(equipment_id)
            ''')

            # Create index on uptime for sorting
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_ptx_uptime_hours
                ON ptx_uptime(uptime_hours DESC)
            ''')

            # Create uptime history table - for tracking changes over time
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS uptime_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    equipment_id TEXT NOT NULL,
                    ip_address TEXT NOT NULL,
                    uptime_hours REAL NOT NULL,
                    recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    source TEXT DEFAULT 'report'
                )
            ''')

            # Create index on history for time-based queries
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_history_recorded
                ON uptime_history(recorded_at DESC)
            ''')

            # Create reboot log table - for tracking reboots
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reboot_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    equipment_id TEXT NOT NULL,
                    ip_address TEXT NOT NULL,
                    rebooted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    rebooted_by TEXT DEFAULT 'web_user',
                    uptime_before_reboot REAL,
                    success INTEGER DEFAULT 1,
                    notes TEXT
                )
            ''')

            # Create sync metadata table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sync_metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Update schema version
            cursor.execute('DELETE FROM schema_version')
            cursor.execute('INSERT INTO schema_version (version) VALUES (?)', (SCHEMA_VERSION,))

            logger.info(f"PTX Uptime database schema created (version {SCHEMA_VERSION})")

        conn.commit()
        conn.close()
        logger.info(f"PTX uptime DB initialized: {db_path}")
        return True

    except Exception as e:
        logger.error(f"Failed to initialize PTX uptime database: {e}")
        return False


class PTXUptimeDB:
    """Class for PTX uptime database operations"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        init_database(db_path)
        logger.info(f"PTX Uptime Database initialized at: {db_path}")

    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA busy_timeout=5000')
        conn.row_factory = sqlite3.Row
        return conn

    def upsert_uptime(self, equipment_id: str, ip_address: str, uptime_hours: float,
                      last_check: str = None, last_check_timestamp: int = None,
                      ptx_type: str = None) -> bool:
        """
        Insert or update a PTX uptime record.
        Also records to history if uptime changed significantly.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Check if record exists and get current uptime
            cursor.execute(
                'SELECT uptime_hours FROM ptx_uptime WHERE equipment_id = ?',
                (equipment_id,)
            )
            existing = cursor.fetchone()

            # Upsert the current record
            cursor.execute('''
                INSERT INTO ptx_uptime (equipment_id, ip_address, uptime_hours, last_check,
                                        last_check_timestamp, ptx_type, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(equipment_id) DO UPDATE SET
                    ip_address = excluded.ip_address,
                    uptime_hours = excluded.uptime_hours,
                    last_check = excluded.last_check,
                    last_check_timestamp = excluded.last_check_timestamp,
                    ptx_type = COALESCE(excluded.ptx_type, ptx_uptime.ptx_type),
                    last_updated = CURRENT_TIMESTAMP
            ''', (equipment_id, ip_address, uptime_hours, last_check, last_check_timestamp, ptx_type))

            # Record to history if this is new or uptime changed by more than 1 hour
            should_record_history = True
            if existing:
                old_uptime = existing['uptime_hours']
                # Only record if change is significant (more than 1 hour difference)
                # or if uptime went down (indicates reboot)
                if abs(uptime_hours - old_uptime) < 1 and uptime_hours >= old_uptime:
                    should_record_history = False

            if should_record_history:
                cursor.execute('''
                    INSERT INTO uptime_history (equipment_id, ip_address, uptime_hours, source)
                    VALUES (?, ?, ?, 'report')
                ''', (equipment_id, ip_address, uptime_hours))

            conn.commit()
            conn.close()
            app_logger.log_database('info', 'write', f"PTX uptime upserted: {equipment_id} uptime={uptime_hours}")
            return True

        except Exception as e:
            logger.error(f"Error upserting PTX uptime for {equipment_id}: {e}")
            app_logger.log_database('error', 'write', f"PTX uptime upsert failed: {equipment_id} - {e}")
            return False

    def update_status(self, equipment_id: str, status: str, ptx_type: str = None) -> bool:
        """Update the online status and PTX type for an equipment"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            if ptx_type:
                cursor.execute('''
                    UPDATE ptx_uptime
                    SET last_status = ?, ptx_type = ?, last_updated = CURRENT_TIMESTAMP
                    WHERE equipment_id = ?
                ''', (status, ptx_type, equipment_id))
            else:
                cursor.execute('''
                    UPDATE ptx_uptime
                    SET last_status = ?, last_updated = CURRENT_TIMESTAMP
                    WHERE equipment_id = ?
                ''', (status, equipment_id))

            conn.commit()
            conn.close()
            app_logger.log_database('info', 'write', f"PTX status updated: {equipment_id} status={status}")
            return True

        except Exception as e:
            logger.error(f"Error updating status for {equipment_id}: {e}")
            app_logger.log_database('error', 'write', f"PTX status update failed: {equipment_id} - {e}")
            return False

    def log_reboot(self, equipment_id: str, ip_address: str, uptime_before: float = None,
                   success: bool = True, rebooted_by: str = 'web_user', notes: str = None) -> bool:
        """Log a reboot event"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO reboot_log (equipment_id, ip_address, uptime_before_reboot,
                                        success, rebooted_by, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (equipment_id, ip_address, uptime_before, 1 if success else 0, rebooted_by, notes))

            conn.commit()
            conn.close()
            app_logger.log_database('info', 'write', f"PTX reboot logged: {equipment_id} success={success}")
            return True

        except Exception as e:
            logger.error(f"Error logging reboot for {equipment_id}: {e}")
            app_logger.log_database('error', 'write', f"PTX reboot log failed: {equipment_id} - {e}")
            return False

    def get_all_uptime(self, min_hours: float = 0, order_by: str = 'uptime_hours DESC') -> List[Dict]:
        """
        Get all PTX uptime records.

        Args:
            min_hours: Minimum uptime hours to filter (default 0 = all)
            order_by: SQL order by clause (default: highest uptime first)

        Returns:
            List of equipment dictionaries
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Sanitize order_by to prevent SQL injection
            allowed_orders = {
                'uptime_hours DESC': 'uptime_hours DESC',
                'uptime_hours ASC': 'uptime_hours ASC',
                'equipment_id ASC': 'equipment_id ASC',
                'equipment_id DESC': 'equipment_id DESC',
                'last_updated DESC': 'last_updated DESC',
                'last_updated ASC': 'last_updated ASC'
            }
            safe_order = allowed_orders.get(order_by, 'uptime_hours DESC')

            cursor.execute(f'''
                SELECT equipment_id, ip_address, uptime_hours, last_check,
                       last_check_timestamp, ptx_type, last_status, last_updated
                FROM ptx_uptime
                WHERE uptime_hours >= ?
                ORDER BY {safe_order}
            ''', (min_hours,))

            results = []
            for row in cursor.fetchall():
                results.append({
                    'equipment_id': row['equipment_id'],
                    'ip': row['ip_address'],
                    'uptime_hours': row['uptime_hours'],
                    'uptime_days': round(row['uptime_hours'] / 24, 1),
                    'last_check': row['last_check'],
                    'timestamp': row['last_check_timestamp'],
                    'ptx_type': row['ptx_type'],
                    'last_status': row['last_status'],
                    'last_updated': row['last_updated']
                })

            conn.close()
            app_logger.log_database('info', 'query', f"PTX uptime records fetched: {len(results)}")
            return results

        except Exception as e:
            logger.error(f"Error getting PTX uptime data: {e}")
            app_logger.log_database('error', 'query', f"PTX uptime fetch failed: {e}")
            return []

    def get_high_uptime(self, min_days: float = 3) -> List[Dict]:
        """Get equipment with uptime greater than specified days"""
        min_hours = min_days * 24
        return self.get_all_uptime(min_hours=min_hours)

    def get_equipment_by_id(self, equipment_id: str) -> Optional[Dict]:
        """Get a single equipment record by ID"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT equipment_id, ip_address, uptime_hours, last_check,
                       last_check_timestamp, ptx_type, last_status, last_updated
                FROM ptx_uptime
                WHERE equipment_id = ?
            ''', (equipment_id,))

            row = cursor.fetchone()
            conn.close()

            if row:
                return {
                    'equipment_id': row['equipment_id'],
                    'ip': row['ip_address'],
                    'uptime_hours': row['uptime_hours'],
                    'uptime_days': round(row['uptime_hours'] / 24, 1),
                    'last_check': row['last_check'],
                    'timestamp': row['last_check_timestamp'],
                    'ptx_type': row['ptx_type'],
                    'last_status': row['last_status'],
                    'last_updated': row['last_updated']
                }
            return None

        except Exception as e:
            logger.error(f"Error getting equipment {equipment_id}: {e}")
            return None

    def get_statistics(self) -> Dict:
        """Get summary statistics for all PTX uptime data"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT
                    COUNT(*) as total_equipment,
                    ROUND(AVG(uptime_hours), 1) as avg_uptime,
                    ROUND(MAX(uptime_hours), 1) as max_uptime,
                    ROUND(MIN(uptime_hours), 1) as min_uptime,
                    SUM(CASE WHEN uptime_hours >= 72 THEN 1 ELSE 0 END) as high_uptime_count,
                    SUM(CASE WHEN last_status = 'online' THEN 1 ELSE 0 END) as online_count
                FROM ptx_uptime
            ''')

            row = cursor.fetchone()
            conn.close()

            if row:
                return {
                    'total_equipment': row['total_equipment'] or 0,
                    'avg_uptime': row['avg_uptime'] or 0,
                    'max_uptime': row['max_uptime'] or 0,
                    'min_uptime': row['min_uptime'] or 0,
                    'high_uptime_count': row['high_uptime_count'] or 0,
                    'online_count': row['online_count'] or 0
                }
            return {
                'total_equipment': 0,
                'avg_uptime': 0,
                'max_uptime': 0,
                'min_uptime': 0,
                'high_uptime_count': 0,
                'online_count': 0
            }

        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {
                'total_equipment': 0,
                'avg_uptime': 0,
                'max_uptime': 0,
                'min_uptime': 0,
                'high_uptime_count': 0,
                'online_count': 0
            }

    def get_reboot_history(self, equipment_id: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """Get reboot history, optionally filtered by equipment"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            if equipment_id:
                cursor.execute('''
                    SELECT equipment_id, ip_address, rebooted_at, rebooted_by,
                           uptime_before_reboot, success, notes
                    FROM reboot_log
                    WHERE equipment_id = ?
                    ORDER BY rebooted_at DESC
                    LIMIT ?
                ''', (equipment_id, limit))
            else:
                cursor.execute('''
                    SELECT equipment_id, ip_address, rebooted_at, rebooted_by,
                           uptime_before_reboot, success, notes
                    FROM reboot_log
                    ORDER BY rebooted_at DESC
                    LIMIT ?
                ''', (limit,))

            results = []
            for row in cursor.fetchall():
                results.append({
                    'equipment_id': row['equipment_id'],
                    'ip_address': row['ip_address'],
                    'rebooted_at': row['rebooted_at'],
                    'rebooted_by': row['rebooted_by'],
                    'uptime_before_reboot': row['uptime_before_reboot'],
                    'success': bool(row['success']),
                    'notes': row['notes']
                })

            conn.close()
            return results

        except Exception as e:
            logger.error(f"Error getting reboot history: {e}")
            return []

    def sync_from_html_report(self, html_path: str) -> Tuple[int, int]:
        """
        Sync database from PTX Uptime Report HTML file.

        Args:
            html_path: Path to the PTX_Uptime_Report.html file

        Returns:
            Tuple of (records_updated, records_added)
        """
        try:
            if not os.path.exists(html_path):
                logger.error(f"HTML report not found: {html_path}")
                return (0, 0)

            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()

            # Parse HTML table rows using regex
            row_pattern = r"<tr data-ts='(\d+)'>\s*<td[^>]*>([^<]+)</td>\s*<td[^>]*>([^<]+)</td>\s*<td[^>]*>([^<]+)</td>\s*<td[^>]*>([^<]+)</td>"
            matches = re.findall(row_pattern, html_content, re.DOTALL)

            records_updated = 0
            records_added = 0

            conn = self._get_connection()
            cursor = conn.cursor()

            for match in matches:
                timestamp_str, ip, equipment_id, uptime_hours_str, last_check = match
                try:
                    timestamp = int(timestamp_str)
                    uptime_hours = float(uptime_hours_str.strip())
                    equipment_id = equipment_id.strip().replace(' *', '')  # Remove asterisk markers
                    ip = ip.strip()
                    last_check = last_check.strip()

                    # Check if exists
                    cursor.execute('SELECT id FROM ptx_uptime WHERE equipment_id = ?', (equipment_id,))
                    exists = cursor.fetchone()

                    # Upsert
                    self.upsert_uptime(
                        equipment_id=equipment_id,
                        ip_address=ip,
                        uptime_hours=uptime_hours,
                        last_check=last_check,
                        last_check_timestamp=timestamp
                    )

                    if exists:
                        records_updated += 1
                    else:
                        records_added += 1

                except (ValueError, TypeError) as e:
                    logger.warning(f"Skipping invalid row: {e}")
                    continue

            conn.close()

            # Update sync metadata
            self.set_sync_metadata('last_html_sync', datetime.now().isoformat())
            self.set_sync_metadata('last_html_path', html_path)

            logger.info(f"Synced PTX uptime from HTML: {records_added} added, {records_updated} updated")
            return (records_updated, records_added)

        except Exception as e:
            logger.error(f"Error syncing from HTML report: {e}")
            return (0, 0)

    def set_sync_metadata(self, key: str, value: str) -> bool:
        """Set a sync metadata value"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO sync_metadata (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    updated_at = CURRENT_TIMESTAMP
            ''', (key, value))

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            logger.error(f"Error setting sync metadata: {e}")
            return False

    def get_sync_metadata(self, key: str) -> Optional[str]:
        """Get a sync metadata value"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute('SELECT value FROM sync_metadata WHERE key = ?', (key,))
            row = cursor.fetchone()
            conn.close()

            return row['value'] if row else None

        except Exception as e:
            logger.error(f"Error getting sync metadata: {e}")
            return None

    def get_record_count(self) -> int:
        """Get total number of records in database"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM ptx_uptime')
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except Exception as e:
            logger.error(f"Error getting record count: {e}")
            return 0

    def clear_all_data(self) -> bool:
        """Clear all data from the database (for testing/reset)"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute('DELETE FROM ptx_uptime')
            cursor.execute('DELETE FROM uptime_history')
            cursor.execute('DELETE FROM reboot_log')
            cursor.execute('DELETE FROM sync_metadata')

            conn.commit()
            conn.close()
            logger.info("PTX Uptime database cleared")
            return True

        except Exception as e:
            logger.error(f"Error clearing database: {e}")
            return False
