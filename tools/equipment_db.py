# tools/equipment_db.py
"""
Equipment Database - SQLite database for caching IP Finder results
Stores equipment details for offline reference
"""
import os
import sqlite3
from datetime import datetime
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)

# Database configuration
DB_FOLDER_NAME = "database"
DB_FILE_NAME = "equipment_cache.db"

# Current schema version - increment when schema changes
SCHEMA_VERSION = 2


def get_database_path(base_dir: str) -> str:
    """
    Get the path to the database file.
    Creates the database folder if it doesn't exist.

    Structure:
    - USB: E:\AutoTech\database\equipment_cache.db
    - Dev: project\AutoTech\database\equipment_cache.db
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

        # Create or migrate equipment cache table
        if current_version < SCHEMA_VERSION:
            # Drop old table if exists (for clean migration)
            cursor.execute('DROP TABLE IF EXISTS equipment_cache')

            # Create equipment cache table with full schema
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS equipment_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    equipment_name TEXT UNIQUE NOT NULL,
                    oid TEXT,
                    cid TEXT,
                    profile TEXT,
                    network_ip TEXT,
                    avi_ip TEXT,
                    ptx_model TEXT,
                    last_status TEXT,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Create index on equipment_name for faster lookups
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_equipment_name
                ON equipment_cache(equipment_name)
            ''')

            # Update schema version
            cursor.execute('DELETE FROM schema_version')
            cursor.execute('INSERT INTO schema_version (version) VALUES (?)', (SCHEMA_VERSION,))

            logger.info(f"Database schema upgraded to version {SCHEMA_VERSION}")

        # Create lookup history table (optional - for tracking queries)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lookup_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                equipment_name TEXT NOT NULL,
                lookup_source TEXT,
                success INTEGER,
                lookup_time DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()
        logger.info(f"Database initialized at: {db_path}")
        return True

    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return False


def save_equipment(db_path: str, equipment_name: str,
                   oid: Optional[str] = None,
                   cid: Optional[str] = None,
                   profile: Optional[str] = None,
                   network_ip: Optional[str] = None,
                   avi_ip: Optional[str] = None,
                   ptx_model: Optional[str] = None,
                   status: Optional[str] = None) -> bool:
    """
    Save or update equipment details in the database.
    Uses INSERT OR REPLACE to handle both new and existing records.

    Fields:
    - equipment_name: Equipment ID (e.g., "AHG69")
    - oid: Object ID
    - cid: Component ID
    - profile: Equipment profile/type
    - network_ip: PTX/Network IP address
    - avi_ip: AVI IP address
    - ptx_model: PTX model (PTXC or PTX10)
    - status: Online/Offline status
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Normalize equipment name to uppercase
        equipment_name = equipment_name.upper().strip()

        # Check if record exists
        cursor.execute(
            'SELECT id FROM equipment_cache WHERE equipment_name = ?',
            (equipment_name,)
        )
        existing = cursor.fetchone()

        if existing:
            # Update existing record - only update non-null values
            cursor.execute('''
                UPDATE equipment_cache
                SET oid = COALESCE(?, oid),
                    cid = COALESCE(?, cid),
                    profile = COALESCE(?, profile),
                    network_ip = COALESCE(?, network_ip),
                    avi_ip = COALESCE(?, avi_ip),
                    ptx_model = COALESCE(?, ptx_model),
                    last_status = COALESCE(?, last_status),
                    last_updated = CURRENT_TIMESTAMP
                WHERE equipment_name = ?
            ''', (oid, cid, profile, network_ip, avi_ip, ptx_model, status, equipment_name))
        else:
            # Insert new record
            cursor.execute('''
                INSERT INTO equipment_cache
                (equipment_name, oid, cid, profile, network_ip, avi_ip, ptx_model, last_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (equipment_name, oid, cid, profile, network_ip, avi_ip, ptx_model, status))

        conn.commit()
        conn.close()
        logger.info(f"Saved equipment {equipment_name} to database")
        return True

    except Exception as e:
        logger.error(f"Failed to save equipment {equipment_name}: {e}")
        return False


def get_equipment(db_path: str, equipment_name: str) -> Optional[Dict]:
    """
    Retrieve equipment details from the database.
    Returns None if not found.
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Normalize equipment name
        equipment_name = equipment_name.upper().strip()

        cursor.execute('''
            SELECT equipment_name, oid, cid, profile, network_ip, avi_ip,
                   ptx_model, last_status, last_updated, created_at
            FROM equipment_cache
            WHERE equipment_name = ?
        ''', (equipment_name,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                'equipment_name': row['equipment_name'],
                'oid': row['oid'],
                'cid': row['cid'],
                'profile': row['profile'],
                'network_ip': row['network_ip'],
                'avi_ip': row['avi_ip'],
                'ptx_model': row['ptx_model'],
                'last_status': row['last_status'],
                'last_updated': row['last_updated'],
                'created_at': row['created_at'],
                'from_cache': True
            }
        return None

    except Exception as e:
        logger.error(f"Failed to get equipment {equipment_name}: {e}")
        return None


def log_lookup(db_path: str, equipment_name: str, source: str, success: bool) -> bool:
    """
    Log a lookup attempt to the history table.
    Source can be: 'network', 'cache', 'test'
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO lookup_history (equipment_name, lookup_source, success)
            VALUES (?, ?, ?)
        ''', (equipment_name.upper().strip(), source, 1 if success else 0))

        conn.commit()
        conn.close()
        return True

    except Exception as e:
        logger.error(f"Failed to log lookup: {e}")
        return False


def get_all_equipment(db_path: str, limit: int = 100) -> List[Dict]:
    """
    Retrieve all cached equipment records.
    Returns list of equipment dicts, ordered by last_updated.
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT equipment_name, oid, cid, profile, network_ip, avi_ip,
                   ptx_model, last_status, last_updated
            FROM equipment_cache
            WHERE last_status != 'not_found' OR last_status IS NULL
            ORDER BY last_updated DESC
            LIMIT ?
        ''', (limit,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    except Exception as e:
        logger.error(f"Failed to get all equipment: {e}")
        return []


def get_database_stats(db_path: str) -> Dict:
    """
    Get statistics about the database.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Count total equipment (excluding not_found)
        cursor.execute(
            "SELECT COUNT(*) FROM equipment_cache WHERE last_status != 'not_found' OR last_status IS NULL"
        )
        total_equipment = cursor.fetchone()[0]

        # Count online/offline
        cursor.execute(
            'SELECT COUNT(*) FROM equipment_cache WHERE last_status = ?',
            ('online',)
        )
        online_count = cursor.fetchone()[0]

        cursor.execute(
            'SELECT COUNT(*) FROM equipment_cache WHERE last_status = ?',
            ('offline',)
        )
        offline_count = cursor.fetchone()[0]

        # Count not_found (hidden from display but tracked)
        cursor.execute(
            'SELECT COUNT(*) FROM equipment_cache WHERE last_status = ?',
            ('not_found',)
        )
        not_found_count = cursor.fetchone()[0]

        # Get most recent update
        cursor.execute(
            'SELECT MAX(last_updated) FROM equipment_cache'
        )
        last_update = cursor.fetchone()[0]

        # Count lookups today
        cursor.execute('''
            SELECT COUNT(*) FROM lookup_history
            WHERE DATE(lookup_time) = DATE('now')
        ''')
        lookups_today = cursor.fetchone()[0]

        conn.close()

        return {
            'total_equipment': total_equipment,
            'online_count': online_count,
            'offline_count': offline_count,
            'unknown_count': total_equipment - online_count - offline_count,
            'not_found_count': not_found_count,
            'last_update': last_update,
            'lookups_today': lookups_today
        }

    except Exception as e:
        logger.error(f"Failed to get database stats: {e}")
        return {
            'total_equipment': 0,
            'online_count': 0,
            'offline_count': 0,
            'unknown_count': 0,
            'last_update': None,
            'lookups_today': 0
        }


def search_equipment(db_path: str, search_term: str, limit: int = 20) -> List[Dict]:
    """
    Search for equipment by partial name match.
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        search_pattern = f"%{search_term.upper().strip()}%"

        cursor.execute('''
            SELECT equipment_name, oid, cid, profile, network_ip, avi_ip,
                   ptx_model, last_status, last_updated
            FROM equipment_cache
            WHERE equipment_name LIKE ?
              AND (last_status != 'not_found' OR last_status IS NULL)
            ORDER BY equipment_name
            LIMIT ?
        ''', (search_pattern, limit))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    except Exception as e:
        logger.error(f"Failed to search equipment: {e}")
        return []


def parse_ip_list_file(db_path: str, ip_list_path: str) -> Dict:
    """
    Parse IP_list.dat file and import equipment into the database.

    File format (space-delimited):
    Name IP AVI
    RD13 10.110.20.42 10.111.218.148

    Returns dict with import stats.
    """
    result = {
        'success': False,
        'total_lines': 0,
        'imported': 0,
        'updated': 0,
        'skipped': 0,
        'errors': []
    }

    try:
        if not os.path.exists(ip_list_path):
            result['errors'].append(f"File not found: {ip_list_path}")
            return result

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        with open(ip_list_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

        result['total_lines'] = len(lines)

        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            # Skip header line
            if line.lower().startswith('name') and 'ip' in line.lower():
                result['skipped'] += 1
                continue

            # Parse space-delimited fields
            parts = line.split()
            if len(parts) < 2:
                result['skipped'] += 1
                continue

            equipment_name = parts[0].upper().strip()
            network_ip = parts[1].strip() if len(parts) > 1 else None
            avi_ip = parts[2].strip() if len(parts) > 2 else None

            # Check if record exists
            cursor.execute(
                'SELECT id FROM equipment_cache WHERE equipment_name = ?',
                (equipment_name,)
            )
            existing = cursor.fetchone()

            if existing:
                # Update existing - only update IP fields if they have values
                cursor.execute('''
                    UPDATE equipment_cache
                    SET network_ip = COALESCE(?, network_ip),
                        avi_ip = COALESCE(?, avi_ip),
                        last_updated = CURRENT_TIMESTAMP
                    WHERE equipment_name = ?
                ''', (network_ip, avi_ip, equipment_name))
                result['updated'] += 1
            else:
                # Insert new record with just the IP info
                cursor.execute('''
                    INSERT INTO equipment_cache
                    (equipment_name, network_ip, avi_ip, last_status)
                    VALUES (?, ?, ?, ?)
                ''', (equipment_name, network_ip, avi_ip, 'unknown'))
                result['imported'] += 1

        conn.commit()
        conn.close()
        result['success'] = True
        logger.info(f"IP list import complete: {result['imported']} new, {result['updated']} updated")

    except Exception as e:
        result['errors'].append(str(e))
        logger.error(f"Failed to parse IP list: {e}")

    return result


def get_equipment_needing_update(db_path: str, limit: int = 1, max_age_days: int = 7) -> List[Dict]:
    """
    Get equipment records that need live data updates.

    Selection criteria:
    1. Must have network_ip (required to query MMS)
    2. Either missing data (CID, profile, ptx_model) OR not updated in max_age_days
    3. Prioritizes missing data first, then oldest updates

    Args:
        db_path: Path to database
        limit: Max records to return
        max_age_days: Only update records older than this (default 7 days)

    Returns:
        List of equipment records needing update
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get equipment that either:
        # 1. Has missing data (CID, profile, or ptx_model is NULL)
        # 2. OR hasn't been updated in max_age_days
        # Prioritize missing data first, then oldest updates
        cursor.execute('''
            SELECT equipment_name, oid, cid, profile, network_ip, avi_ip,
                   ptx_model, last_status, last_updated
            FROM equipment_cache
            WHERE network_ip IS NOT NULL
            AND (
                -- Missing required data
                cid IS NULL OR profile IS NULL OR ptx_model IS NULL
                -- OR not updated in the last N days
                OR last_updated < datetime('now', '-' || ? || ' days')
            )
            ORDER BY
                CASE
                    WHEN cid IS NULL OR profile IS NULL OR ptx_model IS NULL
                    THEN 0
                    ELSE 1
                END,
                last_updated ASC
            LIMIT ?
        ''', (max_age_days, limit))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    except Exception as e:
        logger.error(f"Failed to get equipment needing update: {e}")
        return []


def get_update_progress(db_path: str, max_age_days: int = 7) -> Dict:
    """
    Get progress statistics for the background update process.

    Args:
        db_path: Path to database
        max_age_days: Consider records "needing update" if older than this
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Total equipment count
        cursor.execute('SELECT COUNT(*) FROM equipment_cache')
        total = cursor.fetchone()[0]

        # Equipment with complete data AND updated within max_age_days
        cursor.execute('''
            SELECT COUNT(*) FROM equipment_cache
            WHERE cid IS NOT NULL
            AND profile IS NOT NULL
            AND ptx_model IS NOT NULL
            AND last_updated >= datetime('now', '-' || ? || ' days')
        ''', (max_age_days,))
        up_to_date = cursor.fetchone()[0]

        # Equipment missing data (needs update regardless of age)
        cursor.execute('''
            SELECT COUNT(*) FROM equipment_cache
            WHERE network_ip IS NOT NULL
            AND (cid IS NULL OR profile IS NULL OR ptx_model IS NULL)
        ''')
        missing_data = cursor.fetchone()[0]

        # Equipment with complete data but stale (older than max_age_days)
        cursor.execute('''
            SELECT COUNT(*) FROM equipment_cache
            WHERE network_ip IS NOT NULL
            AND cid IS NOT NULL
            AND profile IS NOT NULL
            AND ptx_model IS NOT NULL
            AND last_updated < datetime('now', '-' || ? || ' days')
        ''', (max_age_days,))
        stale = cursor.fetchone()[0]

        # Equipment without network_ip (can't update)
        cursor.execute('''
            SELECT COUNT(*) FROM equipment_cache
            WHERE network_ip IS NULL
        ''')
        no_ip = cursor.fetchone()[0]

        # Pending = missing data + stale
        pending = missing_data + stale

        conn.close()

        return {
            'total': total,
            'up_to_date': up_to_date,
            'missing_data': missing_data,
            'stale': stale,
            'pending': pending,
            'no_ip': no_ip,
            'percent_complete': round((up_to_date / total * 100), 1) if total > 0 else 0
        }

    except Exception as e:
        logger.error(f"Failed to get update progress: {e}")
        return {
            'total': 0,
            'up_to_date': 0,
            'missing_data': 0,
            'stale': 0,
            'pending': 0,
            'no_ip': 0,
            'percent_complete': 0
        }
