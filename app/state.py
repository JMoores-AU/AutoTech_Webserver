"""
app/state.py
============
Mutable shared state for the AutoTech Web Dashboard.
No Flask imports. Safe to import from blueprints and background tasks.

IMPORTANT: Blueprints must always access state via module reference:
    import app.state as state
    state.EQUIPMENT_DB_PATH          # correct - reads live value
    state.background_updater[...]    # correct - reads live dict

NEVER do:
    from app.state import EQUIPMENT_DB_PATH  # wrong - frozen at import time
"""

import threading

from app.config import BASE_DIR
from tools.ptx_uptime_db import PTXUptimeDB, get_database_path as get_ptx_db_path
from tools.fleet_monitor_db import FleetMonitorDB

# ========================================
# SINGLETON DATABASE INSTANCES
# ========================================
PTX_UPTIME_DB_PATH = get_ptx_db_path(BASE_DIR)
ptx_uptime_db = PTXUptimeDB(PTX_UPTIME_DB_PATH)
fleet_monitor_db = FleetMonitorDB(BASE_DIR)

# Equipment DB path — None until main.py calls init_database() and sets this.
# Blueprints always read this via `state.EQUIPMENT_DB_PATH`.
EQUIPMENT_DB_PATH = None

# ========================================
# BACKGROUND EQUIPMENT UPDATER STATE
# ========================================
# Controls the background process that updates equipment details one at a time
background_updater = {
    'running': False,
    'thread': None,
    'stop_event': threading.Event(),
    'current_equipment': None,
    'processed_count': 0,
    'error_count': 0,
    'last_update': None,
    'delay_seconds': 5,  # Delay between equipment lookups to avoid system load
    'status': 'stopped'
}

# ========================================
# PTX UPTIME CHECKER STATE
# ========================================
# Background process that checks uptime on all PTX equipment every 30 minutes
ptx_uptime_checker = {
    'running': False,
    'thread': None,
    'stop_event': threading.Event(),
    'current_equipment': None,
    'total_equipment': 0,
    'checked_count': 0,
    'online_count': 0,
    'offline_count': 0,
    'error_count': 0,
    'last_cycle_start': None,
    'last_cycle_end': None,
    'next_cycle': None,
    'interval_minutes': 30,  # Check every 30 minutes
    'status': 'stopped'  # stopped, running, waiting, error
}

# ========================================
# PLAYBACK MONITOR STATE
# ========================================
# Persistent SSH connection to playback server for real-time file monitoring
playback_monitor = {
    'running': False,
    'thread': None,
    'stop_event': threading.Event(),
    'ssh_client': None,
    'sftp_client': None,
    'connected': False,
    'last_scan': None,
    'log_files': [],  # Current .log files detected
    'dat_files': [],  # Recent .dat files
    'pending_file': None,  # File being written (from .log files)
    'last_error': None,
    'reconnect_count': 0,
    'status': 'stopped',  # stopped, connecting, connected, monitoring, error
    'scan_interval_seconds': 10  # Scan playback folder every 10 seconds
}

# ========================================
# DIG FLEET MONITOR STATE
# ========================================
fleet_monitor_updater = {
    'running': False,
    'thread': None,
    'stop_event': threading.Event(),
    'interval_minutes': 30,
    'last_run': None
}

# ========================================
# DOWNLOAD PROGRESS TRACKING
# ========================================
# Format: {filename: {'status': 'downloading'|'complete'|'error', 'progress': 0-100,
#                     'local_path': str, 'total_size': int, 'error': str}}
download_progress = {}

# ========================================
# NETWORK STATUS CACHE
# ========================================
_network_status_cache = {"ts": 0.0, "online": False}

# ========================================
# ACTIVE TRU CONNECTIONS
# ========================================
active_tru_connections = {}

# ========================================
# TERMINAL SESSIONS (T1 Legacy)
# ========================================
terminal_sessions = {}
