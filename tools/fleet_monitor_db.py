# tools/fleet_monitor_db.py
"""
Fleet Monitor Database - SQLite database for storing fleet equipment health data.
Stores uptime/memory health snapshots and history.

IP/model lookups are handled by equipment_cache.db (tools/equipment_db.py),
which is kept current by every IP Finder search.
"""
import os
import sqlite3
from typing import Dict
import logging

logger = logging.getLogger(__name__)

DB_FILE_NAME = "fleet_monitor.db"


class FleetMonitorDB:
    def __init__(self, base_dir: str):
        self.db_path = self._get_db_path(base_dir)
        self._init_db()

    def _get_db_path(self, base_dir: str) -> str:
        # Try USB structure first (E:\AutoTech\database)
        usb_db_folder = os.path.join(base_dir, "AutoTech", "database")
        if os.path.exists(os.path.join(base_dir, "AutoTech")):
            os.makedirs(usb_db_folder, exist_ok=True)
            return os.path.join(usb_db_folder, DB_FILE_NAME)

        # Fallback to dev structure (project\database)
        dev_db_folder = os.path.join(base_dir, "database")
        os.makedirs(dev_db_folder, exist_ok=True)
        return os.path.join(dev_db_folder, DB_FILE_NAME)

    def _init_db(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS equipment_health (
                    equipment_id TEXT PRIMARY KEY,
                    uptime_hours REAL,
                    mem_usage_percent INTEGER,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS health_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    equipment_id TEXT,
                    uptime_hours REAL,
                    mem_usage_percent INTEGER,
                    recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
            conn.close()
            logger.info(f"Fleet Monitor DB initialized: {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize Fleet Monitor DB: {e}")

    def update_health(self, equipment_id: str, uptime_hours: float, mem_usage: int):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO equipment_health (equipment_id, uptime_hours, mem_usage_percent, last_updated)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(equipment_id) DO UPDATE SET
                    uptime_hours = excluded.uptime_hours,
                    mem_usage_percent = excluded.mem_usage_percent,
                    last_updated = CURRENT_TIMESTAMP
            ''', (equipment_id, uptime_hours, mem_usage))
            cursor.execute('''
                INSERT INTO health_history (equipment_id, uptime_hours, mem_usage_percent)
                VALUES (?, ?, ?)
            ''', (equipment_id, uptime_hours, mem_usage))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error updating health for {equipment_id}: {e}")
            return False

    def get_latest_health(self) -> Dict[str, Dict]:
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM equipment_health')
            rows = cursor.fetchall()
            conn.close()
            return {row['equipment_id']: {
                'uptime_hours': row['uptime_hours'],
                'mem_usage': row['mem_usage_percent'],
                'last_updated': row['last_updated']
            } for row in rows}
        except Exception as e:
            logger.error(f"Error getting latest health: {e}")
            return {}
