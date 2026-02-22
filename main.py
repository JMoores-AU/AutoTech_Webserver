#!/usr/bin/env python3
"""
AUTOTECH WEB DASHBOARD - ENHANCED MAIN APPLICATION
================================================================
Mining equipment remote access system for Komatsu equipment
Enhanced version combining new design with full functionality
================================================================
"""

import os
import sqlite3

# Standard Library Imports
import csv
import json
import logging
import platform
import re
import shlex
import shutil
import signal
import socket
import subprocess
import sys
import threading
import time
import uuid              
import queue 
from collections import deque
from datetime import datetime, timedelta
from functools import lru_cache, wraps
from io import StringIO
from pathlib import Path
from typing import Optional
from tools.log_cleanup import cleanup_logs
from tools.app_logger import (
    init_logging, log_server, log_client, log_tool,
    log_background, log_security, log_database,
    format_request_log, format_client_registration,
    generate_request_id, set_request_id, get_request_id,
    get_log_directory, LOG_FILES
)
from tools.equipment_db import (
    get_database_path, init_database, save_equipment,
    get_equipment, log_lookup, get_database_stats,
    get_all_equipment, search_equipment as search_equipment_db,
    parse_ip_list_file, get_equipment_needing_update, get_update_progress
)
from tools.ptx_uptime_db import (
    get_database_path as get_ptx_db_path,
    PTXUptimeDB
)
from tools.fleet_monitor_db import FleetMonitorDB
from tools.autotech_db import (
    get_database_path as get_autotech_db_path,
    init_database as init_autotech_db,
    get_database_stats as get_autotech_db_stats
)
try:
    from tools import ptx_uptime as ptx_uptime_tool
except ImportError:
    ptx_uptime_tool = None

try:
    from tools import frontrunner_status as frontrunner_status_tool
except ImportError:
    frontrunner_status_tool = None

# Third-Party Imports
try:
    import paramiko
except ImportError:
    paramiko = None

# System Tray Support (optional - only needed for --tray mode)
try:
    import pystray
    from PIL import Image, ImageDraw
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False
    pystray = None
    Image = None
    ImageDraw = None

try:
    import ping3
except ImportError:
    ping3 = None

try:
    import requests
except ImportError:
    requests = None

from flask import Flask, render_template, request, session, redirect, url_for, jsonify, flash, Response, make_response, send_file, stream_with_context
from flask_cors import CORS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========================================
# PHASE 1: IMPORT FROM APP MODULES
# ========================================
from app.config import (
    BASE_DIR, TEMPLATE_FOLDER, STATIC_FOLDER,
    TOOLS_DIR, PLINK_PATH, VNC_VIEWER_PATH,
    CLIENT_TOOLS_DIR, CLIENT_PLINK_PATH,
    AUTO_TECH_CLIENT_DIR, AUTO_TECH_CLIENT_PLINK, PLINK_CANDIDATES,
    GATEWAY_IP, PTX_BASE_IP, PROBE_PORT,
    SERVERS, MMS_SERVER, PLAYBACK_SERVER,
    TOOL_LIST, EQUIPMENT_PROFILES, MOCK_EQUIPMENT_DB,
    IP_LIST_PATH, FLEET_DATA_PATH, resolve_data_path,
    APP_VERSION, get_version,
)
import app.state as state
from app.utils import (
    login_required, is_online_network, resolve_plink_path,
    get_autotech_client_folder, connect_to_equipment,
    check_ptx_reachable, get_ptx_uptime,
    search_equipment, parse_ip_finder_output,
)
from app.background_tasks import (
    ptx_uptime_checker_worker, playback_monitor_worker,
    background_update_worker, fleet_monitor_worker,
    probe_equipment_health, format_uptime_hours, open_browser,
)

# ========================================
# INITIALIZE LOGGING INFRASTRUCTURE
# ========================================
LOG_DIR = init_logging()
log_server('info', 'startup', f'Application version: {APP_VERSION}')
log_server('info', 'startup', f'Base directory: {BASE_DIR}')
log_server('info', 'startup', f'Log directory: {LOG_DIR}')

LOG_SOURCES = dict(LOG_FILES)
LOG_SOURCE_LABELS = {
    'server': 'Server',
    'clients': 'Clients',
    'tools': 'Tools',
    'background': 'Background',
    'security': 'Security',
    'database': 'Database'
}

logger.info(f"Application Base Directory: {BASE_DIR}")
logger.info(f"Tools Directory: {TOOLS_DIR}")
logger.info(f"Client Tools Directory: {CLIENT_TOOLS_DIR}")
logger.info(f"AutoTech Client Directory: {AUTO_TECH_CLIENT_DIR}")
logger.info(f"Template Folder: {TEMPLATE_FOLDER}")
logger.info(f"Static Folder: {STATIC_FOLDER}")

# ========================================
# EQUIPMENT DATABASE INITIALIZATION
# ========================================
EQUIPMENT_DB_PATH = get_database_path(BASE_DIR)
if init_database(EQUIPMENT_DB_PATH):
    logger.info(f"Equipment Database: {EQUIPMENT_DB_PATH}")
else:
    logger.warning("Failed to initialize equipment database - caching disabled")
    EQUIPMENT_DB_PATH = None
state.EQUIPMENT_DB_PATH = EQUIPMENT_DB_PATH  # Share with blueprints/background tasks

# ========================================
# PTX UPTIME DATABASE INITIALIZATION
# ========================================
logger.info(f"PTX Uptime Database initialized (managed by app.state)")

# ========================================
# AUTOTECH MAIN DATABASE INITIALIZATION
# ========================================
AUTOTECH_DB_PATH = get_autotech_db_path(BASE_DIR)
if init_autotech_db(AUTOTECH_DB_PATH):
    logger.info(f"AutoTech Main Database: {AUTOTECH_DB_PATH}")
else:
    logger.warning("Failed to initialize AutoTech main database")
    AUTOTECH_DB_PATH = None

# ========================================
# FRONTRUNNER EVENTS DATABASE RE-INIT (schema v2 adds frontrunner_events table)
# ========================================
try:
    from tools import frontrunner_event_db as _fr_event_db
    _fr_db_path = _fr_event_db.get_database_path(BASE_DIR)
    if _fr_event_db.init_database(_fr_db_path):
        logger.info(f"FrontRunner Events Database: {_fr_db_path} (schema updated)")
    else:
        logger.warning("Failed to re-initialize FrontRunner events database")
except Exception as _fr_err:
    logger.warning(f"FrontRunner events DB init skipped: {_fr_err}")

# ========================================
# DIG FLEET MONITOR DATABASE
# ========================================
# IP_LIST_PATH, FLEET_DATA_PATH, resolve_data_path imported from app.config
# fleet_monitor_db managed by app.state

def ensure_fleet_config():
    """Ensure the fleet layout config exists with a default if missing."""
    default_layout = {
        "columns": [
            {
                "id": "lh_north", "title": "Load & Haul North",
                "main": "GR17 PreStrip9", "back": "GR18 PreStrip10",
                "phone": "4940 4258", "comms": "Normal Auto Truck | Shovel comms",
                "color": "#f7a224", "equipment": ["EXD69", "EXD99", "SHE33"]
            },
            {
                "id": "lh_central", "title": "Load & Haul Central",
                "main": "GR15 PreStrip7", "back": "GR16 PreStrip8",
                "phone": "4940 4259", "comms": "Normal Auto Truck | Shovel comms",
                "color": "#73c05c", "equipment": ["EXD265", "EXD81", "EXD57"]
            },
            {
                "id": "lh_south", "title": "Load & Haul South",
                "main": "GR13 PreStrip5", "back": "GR14 PreStrip6",
                "phone": "4940 4252", "comms": "Normal Auto Truck | Shovel comms",
                "color": "#f7e127", "equipment": ["EXD82", "EXD66", "EXD67", "EXD68", "SHE32"]
            }
        ]
    }
    
    try:
        # If file exists, try to load it to ensure it's valid JSON
        if os.path.exists(FLEET_DATA_PATH):
            with open(FLEET_DATA_PATH, 'r') as f:
                json.load(f)
            logger.info(f"Fleet config verified at {FLEET_DATA_PATH}")
        else:
            raise FileNotFoundError("Config missing")
    except (FileNotFoundError, json.JSONDecodeError, Exception):
        logger.warning(f"Fleet config missing or invalid at {FLEET_DATA_PATH}, creating default...")
        try:
            os.makedirs(os.path.dirname(FLEET_DATA_PATH), exist_ok=True)
            with open(FLEET_DATA_PATH, 'w') as f:
                json.dump(default_layout, f, indent=2)
            logger.info("Default fleet layout created successfully")
        except Exception as e:
            logger.error(f"CRITICAL: Failed to create fleet config: {e}")

# Initialize config
ensure_fleet_config()

# Auto-import IP_list.dat on startup if database is empty
if EQUIPMENT_DB_PATH and os.path.exists(IP_LIST_PATH):
    _stats = get_database_stats(EQUIPMENT_DB_PATH)
    if _stats['total_equipment'] == 0:
        logger.info("Database empty - auto-importing IP_list.dat...")
        _import_result = parse_ip_list_file(EQUIPMENT_DB_PATH, IP_LIST_PATH)
        if _import_result['success']:
            logger.info(f"Auto-import complete: {_import_result['imported']} equipment records imported")
        else:
            logger.warning(f"Auto-import failed: {_import_result['errors']}")

# ========================================
# LOCAL ALIASES TO SHARED STATE
# ========================================
# These alias the dicts in app.state so routes in main.py still work unchanged.
# Mutable objects — both names point to the same dict in memory.
background_updater = state.background_updater
ptx_uptime_checker = state.ptx_uptime_checker
playback_monitor = state.playback_monitor
fleet_monitor_updater = state.fleet_monitor_updater
download_progress = state.download_progress
active_tru_connections = state.active_tru_connections
terminal_sessions = state.terminal_sessions
ptx_uptime_db = state.ptx_uptime_db
fleet_monitor_db = state.fleet_monitor_db
PTX_UPTIME_DB_PATH = state.PTX_UPTIME_DB_PATH

# NOW we can create the Flask app
app = Flask(__name__, template_folder=TEMPLATE_FOLDER, static_folder=STATIC_FOLDER)
app.secret_key = "komatsu-t1-tools-secret-key-change-in-production"
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.jinja_env.auto_reload = True

CORS(app)

# ========================================
# BLUEPRINT REGISTRATION
# ========================================
from app.blueprints.auth import bp as auth_bp
from app.blueprints.info_pages import bp as info_pages_bp
from app.blueprints.downloads import bp as downloads_bp
app.register_blueprint(auth_bp)
app.register_blueprint(info_pages_bp)
app.register_blueprint(downloads_bp)

# ========================================
# REQUEST/RESPONSE LOGGING MIDDLEWARE
# ========================================
@app.before_request
def log_request_start():
    """Log incoming requests"""
    incoming_id = request.headers.get('X-Request-ID')
    request_id = incoming_id.strip() if incoming_id else generate_request_id()
    set_request_id(request_id)
    request._request_id = request_id

    # Skip logging for static assets and health checks
    if request.path.startswith('/static/') or request.path == '/health':
        return

    request._start_time = time.time()
    log_server(
        'info',
        'request',
        format_request_log(request.method, request.path, request.remote_addr)
    )

@app.after_request
def log_request_end(response):
    """Log request completion with status code and duration"""
    response.headers['X-Request-ID'] = get_request_id()

    # Skip logging for static assets and health checks
    if request.path.startswith('/static/') or request.path == '/health':
        return response

    duration_ms = None
    if hasattr(request, '_start_time'):
        duration_ms = (time.time() - request._start_time) * 1000

    log_server(
        'info',
        'response',
        format_request_log(
            request.method,
            request.path,
            request.remote_addr,
            duration_ms=duration_ms,
            status_code=response.status_code
        )
    )
    return response

# DEBUG: show where Flask is loading templates from
print("TEMPLATE_FOLDER =", os.path.abspath(app.template_folder))
print("JINJA_SEARCHPATH =", [os.path.abspath(p) for p in app.jinja_loader.searchpath])

# Disable caching for HTML responses so template changes always show
@app.after_request
def add_no_cache_headers(resp):
    if resp.content_type and 'text/html' in (resp.content_type or '').lower():
        resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        resp.headers['Pragma'] = 'no-cache'
        resp.headers['Expires'] = '0'
    return resp

# ========================================
# AUTHENTICATION AND UTILITY FUNCTIONS
# ========================================
# login_required, TOOL_LIST, EQUIPMENT_PROFILES, GATEWAY_IP, PTX_BASE_IP,
# PROBE_PORT, MOCK_EQUIPMENT_DB, SERVERS, MMS_SERVER imported from app.config / app.utils
# download_progress, active_tru_connections aliased from app.state above

def print_startup_banner():
    """Display startup information"""
    # Get server IP address
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        server_ip = s.getsockname()[0]
        s.close()
    except:
        server_ip = "Unknown"
    
    print("\n" + "="*60)
    print("AUTOTECH WEB DASHBOARD - ENHANCED VERSION")
    print("="*60)
    print(f"Network Mode: {'ONLINE' if is_online_network() else 'OFFLINE'}")
    print(f"Gateway IP: {GATEWAY_IP}")
    print(f"Server IP: {server_ip}")
    print(f"\nAccess from this PC:     http://localhost:8888")
    print(f"Access from other PCs:   http://{server_ip}:8888")
    print(f"\nLogin Password: komatsu")
    print(f"Python Version: {sys.version}")
    print(f"Flask Version: {getattr(Flask, '__version__', 'Unknown')}")
    print("="*60)
    print("Press Ctrl+C to stop the server")
    print("="*60 + "\n")

# ========================================
# NETWORK MODE DETECTION AND UTILITIES
# ========================================
# is_online_network imported from app.utils above

def check_network_connectivity():
    """Check if we can reach the network"""
    try:
        if ping3:
            result = ping3.ping(GATEWAY_IP, timeout=2)
            return result is not None
        else:
            # Fallback to socket test if ping3 not available
            try:
                with socket.create_connection((GATEWAY_IP, PROBE_PORT), timeout=2):
                    return True
            except:
                return False
    except Exception:
        return False

def get_remote_stats():
    """Fetch remote server statistics."""
    stats = []
    for server in SERVERS:
        server_stat = {
            "name": server["name"],
            "ip": server["ip"],
            "status": "offline",
            "latency": None
        }
        
        try:
            if ping3:
                # Try ping first
                latency = ping3.ping(server["ip"], timeout=3)
                if latency is not None:
                    server_stat["status"] = "online"
                    server_stat["latency"] = round(latency * 1000, 2)  # Convert to ms
                else:
                    # Try socket connection as fallback
                    start_time = time.time()
                    with socket.create_connection((server["ip"], server["port"]), timeout=3):
                        latency = (time.time() - start_time) * 1000
                        server_stat["status"] = "online"
                        server_stat["latency"] = round(latency, 2)
            else:
                # Socket-only approach if ping3 not available
                start_time = time.time()
                with socket.create_connection((server["ip"], server["port"]), timeout=3):
                    latency = (time.time() - start_time) * 1000
                    server_stat["status"] = "online"
                    server_stat["latency"] = round(latency, 2)
        except Exception as e:
            logger.debug(f"Server {server['name']} check failed: {e}")
            
        stats.append(server_stat)
    
    return stats

def find_ip_address(hostname):
    """Find IP address from hostname - CENTRALIZED FUNCTION"""
    try:
        ip_address = socket.gethostbyname(hostname)
        return ip_address
    except socket.gaierror:
        raise Exception(f"Unable to resolve hostname: {hostname}")

# ========================================
# EQUIPMENT SEARCH AND MANAGEMENT
# ========================================
# search_equipment, parse_ip_finder_output imported from app.utils above

def get_flight_recorder_ip(equipment_type):
    """Calculate Flight Recorder IP for supported equipment"""
    profile = EQUIPMENT_PROFILES.get(equipment_type, EQUIPMENT_PROFILES['Other'])
    
    if not profile['has_flight_recorder']:
        return None
    
    # Calculate Flight Recorder IP (PTX IP + offset)
    base_ip_parts = PTX_BASE_IP.split('.')
    last_octet = int(base_ip_parts[-1]) + profile['ptx_offset']
    return '.'.join(base_ip_parts[:-1] + [str(last_octet)])

# ========================================
# PTX LOG CLEANUP
# ========================================
# connect_to_equipment, get_ptx_uptime, check_ptx_reachable imported from app.utils
# ptx_uptime_checker_worker, _wait_for_interval, playback_monitor_worker imported from app.background_tasks

def find_log_directory(ssh):
    """
    Find the log directory path on the remote system.
    Returns: (path, None) or (None, error_message)
    """
    # Strategy 1: Check user's home
    stdin, stdout, stderr = ssh.exec_command("echo $HOME")
    user_home = stdout.read().decode().strip()
    
    if user_home:
        user_path = f"{user_home}/frontrunnerV3/logs"
        stdin, stdout, stderr = ssh.exec_command(f"test -d {user_path} && echo EXISTS")
        if stdout.read().decode().strip() == "EXISTS":
            return user_path, None
    
    # Strategy 2: Common paths
    base_paths = ["/real_home", "/home/dlog", "/home/mms", "/home", "/opt"]
    
    for base in base_paths:
        test_path = f"{base}/frontrunnerV3/logs"
        stdin, stdout, stderr = ssh.exec_command(f"test -d {test_path} && echo EXISTS")
        if stdout.read().decode().strip() == "EXISTS":
            return test_path, None
    
    # Strategy 3: Search filesystem
    stdin, stdout, stderr = ssh.exec_command(
        "find /real_home /home /opt /usr -type d -path '*/frontrunnerV3/logs' 2>/dev/null | head -1"
    )
    found_path = stdout.read().decode().strip()
    
    if found_path:
        return found_path, None
    
    return None, "Could not locate log directory"

def get_folder_list(ssh, log_path):
    """Get list of monthly folders with their age."""
    cmd = f"cd {log_path} && ls -d */ 2>/dev/null | sed 's|/||'"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    output = stdout.read().decode()
    
    folders = []
    current_date = datetime.now()
    
    for line in output.strip().split('\n'):
        folder = line.strip()
        if not folder:
            continue
        
        if len(folder) == 6 and folder.isdigit():
            folder_year_month = int(folder)
            folder_year = folder_year_month // 100
            folder_month = folder_year_month % 100
            
            if 1 <= folder_month <= 12:
                months_diff = (current_date.year - folder_year) * 12 + (current_date.month - folder_month)
                folders.append((folder, months_diff))
            else:
                folders.append((folder, 0))
        else:
            folders.append((folder, 0))
    
    return folders

def get_broken_logs(ssh, log_path):
    """Find 0-byte files in root directory."""
    cmd = f'cd {log_path} && find . -maxdepth 1 -type f -size 0 -printf "%p:%T@\\n"'
    stdin, stdout, stderr = ssh.exec_command(cmd)
    output = stdout.read().decode()
    
    broken_files = []
    current_time = datetime.now().timestamp()
    
    for line in output.strip().split('\n'):
        if not line or ':' not in line:
            continue
        
        try:
            filepath, mtime = line.rsplit(':', 1)
            filepath = filepath.lstrip('./')
            days_old = int((current_time - float(mtime)) / 86400)
            broken_files.append((filepath, days_old))
        except (ValueError, IndexError):
            continue
    
    return broken_files

def get_loose_files(ssh, log_path):
    """Find loose log files in root directory."""
    cmd = f'cd {log_path} && find . -maxdepth 1 -type f ! -size 0 -printf "%p:%T@\\n"'
    stdin, stdout, stderr = ssh.exec_command(cmd)
    output = stdout.read().decode()
    
    loose_files = []
    current_time = datetime.now().timestamp()
    
    for line in output.strip().split('\n'):
        if not line or ':' not in line:
            continue
        
        try:
            filepath, mtime = line.rsplit(':', 1)
            filepath = filepath.lstrip('./')
            days_old = int((current_time - float(mtime)) / 86400)
            loose_files.append((filepath, days_old))
        except (ValueError, IndexError):
            continue
    
    return loose_files

def cleanup_logs(ip_address, folder_retention=2, file_retention=7, dry_run=True):
    """
    Main cleanup function for web interface.
    Returns: dict with results and logs
    """
    results = {
        "success": False,
        "log": [],
        "stats": {
            "folders_deleted": 0,
            "broken_deleted": 0,
            "loose_deleted": 0,
            "total_deleted": 0
        }
    }
    
    def log(msg):
        results["log"].append(msg)
    
    try:
        # Connect
        log(f"Connecting to {ip_address}...")
        ssh, cred_type = connect_to_equipment(ip_address)
        if not ssh:
            results["error"] = cred_type
            return results
        
        log(f"✓ Connected as {cred_type}")
        
        # Find log directory
        log("Searching for log directory...")
        log_path, error = find_log_directory(ssh)
        if not log_path:
            results["error"] = error
            ssh.close()
            return results
        
        log(f"✓ Found logs: {log_path}")
        
        # Get folders
        log("\nScanning folders...")
        folders = get_folder_list(ssh, log_path)
        log(f"Found {len(folders)} folders")
        
        # Get broken logs
        log("Scanning 0-byte files...")
        broken_files = get_broken_logs(ssh, log_path)
        log(f"Found {len(broken_files)} broken files")
        
        # Get loose files
        log("Scanning loose files...")
        loose_files = get_loose_files(ssh, log_path)
        log(f"Found {len(loose_files)} loose files")
        
        # Process folders
        log(f"\n{'='*50}")
        log(f"FOLDER CLEANUP (Keep: current + last {folder_retention} months)")
        log(f"{'='*50}")
        
        kept_folders = []
        for folder, months_old in sorted(folders, key=lambda x: x[1], reverse=True):
            if months_old > folder_retention:
                if dry_run:
                    log(f"WOULD DELETE: {folder} ({months_old} months old)")
                else:
                    log(f"Deleting: {folder} ({months_old} months old)")
                    cmd = f"cd {log_path} && rm -rf '{folder}'"
                    ssh.exec_command(cmd)
                    log(f"  ✓ Deleted")
                results["stats"]["folders_deleted"] += 1
            else:
                log(f"Keeping: {folder} ({months_old} months old)")
                if len(folder) == 6 and folder.isdigit():
                    kept_folders.append(folder)
        
        # Process broken logs
        log(f"\n{'='*50}")
        log(f"0-BYTE FILE CLEANUP (Retention: {file_retention} days)")
        log(f"{'='*50}")
        
        for filepath, days_old in sorted(broken_files, key=lambda x: x[1], reverse=True):
            if days_old > file_retention:
                if dry_run:
                    log(f"WOULD DELETE: {filepath} ({days_old} days old)")
                else:
                    log(f"Deleting: {filepath} ({days_old} days old)")
                    cmd = f"cd {log_path} && rm -f '{filepath}'"
                    ssh.exec_command(cmd)
                    log(f"  ✓ Deleted")
                results["stats"]["broken_deleted"] += 1
        
        # Process loose files
        log(f"\n{'='*50}")
        log(f"LOOSE FILE CLEANUP (Retention: {file_retention} days)")
        log(f"{'='*50}")
        
        for filepath, days_old in sorted(loose_files, key=lambda x: x[1], reverse=True):
            if days_old > file_retention:
                if dry_run:
                    log(f"WOULD DELETE: {filepath} ({days_old} days old)")
                else:
                    log(f"Deleting: {filepath} ({days_old} days old)")
                    cmd = f"cd {log_path} && rm -f '{filepath}'"
                    ssh.exec_command(cmd)
                    log(f"  ✓ Deleted")
                results["stats"]["loose_deleted"] += 1
        
        # Summary
        results["stats"]["total_deleted"] = (
            results["stats"]["folders_deleted"] + 
            results["stats"]["broken_deleted"] + 
            results["stats"]["loose_deleted"]
        )
        
        log(f"\n{'='*50}")
        log(f"{'DRY RUN ' if dry_run else ''}COMPLETE")
        log(f"{'='*50}")
        log(f"Folders: {results['stats']['folders_deleted']}")
        log(f"Broken files: {results['stats']['broken_deleted']}")
        log(f"Loose files: {results['stats']['loose_deleted']}")
        log(f"Total: {results['stats']['total_deleted']}")
        
        if kept_folders:
            log(f"\n✓ Files in kept folders ({', '.join(kept_folders)}) were preserved")
        
        ssh.close()
        results["success"] = True
        
    except Exception as e:
        log(f"\n✗ ERROR: {str(e)}")
        results["error"] = str(e)
    
    return results

# ============================================================================
# OFFLINE MODE: Log Cleanup Test Function
# ============================================================================

def cleanup_logs_test_mode(folder_retention=2, file_retention=7, dry_run=True):
    """
    Offline mode cleanup - uses local test data.
    Auto-called when is_online_network() returns False.
    """
    import os
    import shutil

    # Use test_logs directory in project root (same directory as main.py)
    TEST_PATH = os.path.join(os.path.dirname(__file__), "test_logs")

    results = {
        "success": False,
        "log": [],
        "stats": {"folders_deleted": 0, "broken_deleted": 0, "loose_deleted": 0, "total_deleted": 0}
    }

    def log(msg):
        results["log"].append(msg)

    try:
        print(f"[DEBUG] Looking for test data at: {TEST_PATH}")
        print(f"[DEBUG] __file__ = {__file__}")
        print(f"[DEBUG] Path exists: {os.path.exists(TEST_PATH)}")

        # Auto-generate test data if it doesn't exist
        if not os.path.exists(TEST_PATH):
            log("[OFFLINE MODE] Test data not found - generating now...")
            print("[CLEANUP] Auto-generating test data...")

            import subprocess
            import sys
            generator_path = os.path.join(os.path.dirname(__file__), 'tools', 'test_log_generator.py')

            try:
                result = subprocess.run([sys.executable, generator_path],
                                      capture_output=True, text=True, timeout=60)
                if result.returncode != 0:
                    results["error"] = f"Failed to generate test data: {result.stderr}"
                    return results
                log("[SUCCESS] Test data generated successfully")
                print("[CLEANUP] Test data generation complete")
            except Exception as gen_error:
                results["error"] = f"Failed to generate test data: {str(gen_error)}"
                return results

        log("[OFFLINE MODE] Using local test data")
        log(f"Path: {TEST_PATH}")
        
        current_date = datetime.now()
        current_time = current_date.timestamp()
        
        # Scan folders
        folders = []
        for item in os.listdir(TEST_PATH):
            path = os.path.join(TEST_PATH, item)
            if os.path.isdir(path) and len(item) == 6 and item.isdigit():
                year, month = int(item) // 100, int(item) % 100
                if 1 <= month <= 12:
                    months_diff = (current_date.year - year) * 12 + (current_date.month - month)
                    folders.append((item, months_diff))
        
        # Scan 0-byte files
        broken = [(f, int((current_time - os.path.getmtime(os.path.join(TEST_PATH, f))) / 86400))
                  for f in os.listdir(TEST_PATH)
                  if os.path.isfile(os.path.join(TEST_PATH, f)) and os.path.getsize(os.path.join(TEST_PATH, f)) == 0]
        
        # Scan loose files
        loose = [(f, int((current_time - os.path.getmtime(os.path.join(TEST_PATH, f))) / 86400))
                 for f in os.listdir(TEST_PATH)
                 if os.path.isfile(os.path.join(TEST_PATH, f)) and os.path.getsize(os.path.join(TEST_PATH, f)) > 0]
        
        log(f"\nFound {len(folders)} folders, {len(broken)} 0-byte files, {len(loose)} loose files")
        
        # Process folders
        log(f"\n{'='*50}\nFOLDER CLEANUP (Keep: current + last {folder_retention} months)\n{'='*50}")
        kept = []
        for folder, age in sorted(folders, key=lambda x: x[1], reverse=True):
            if age > folder_retention:
                log(f"{'WOULD DELETE' if dry_run else 'Deleting'}: {folder} ({age} months old)")
                if not dry_run:
                    shutil.rmtree(os.path.join(TEST_PATH, folder))
                results["stats"]["folders_deleted"] += 1
            else:
                log(f"Keeping: {folder} ({age} months old)")
                kept.append(folder)
        
        # Process 0-byte
        log(f"\n{'='*50}\n0-BYTE FILE CLEANUP (Retention: {file_retention} days)\n{'='*50}")
        for file, age in broken:
            if age > file_retention:
                log(f"{'WOULD DELETE' if dry_run else 'Deleting'}: {file} ({age} days old)")
                if not dry_run:
                    os.remove(os.path.join(TEST_PATH, file))
                results["stats"]["broken_deleted"] += 1
        
        # Process loose
        log(f"\n{'='*50}\nLOOSE FILE CLEANUP (Retention: {file_retention} days)\n{'='*50}")
        for file, age in loose:
            if age > file_retention:
                log(f"{'WOULD DELETE' if dry_run else 'Deleting'}: {file} ({age} days old)")
                if not dry_run:
                    os.remove(os.path.join(TEST_PATH, file))
                results["stats"]["loose_deleted"] += 1
        
        results["stats"]["total_deleted"] = sum(results["stats"].values())
        
        log(f"\n{'='*50}\n{'DRY RUN ' if dry_run else ''}COMPLETE\n{'='*50}")
        log(f"Folders: {results['stats']['folders_deleted']}")
        log(f"Broken: {results['stats']['broken_deleted']}")
        log(f"Loose: {results['stats']['loose_deleted']}")
        log(f"Total: {results['stats']['total_deleted']}")
        
        if kept:
            log(f"\n[KEPT] Folders: {', '.join(kept)}")

        results["success"] = True

        # Delete test_logs folder after successful execution (not dry run)
        if not dry_run:
            log(f"\n{'='*50}")
            log("CLEANUP COMPLETE - RESETTING TEST DATA")
            log(f"{'='*50}")

            import shutil
            try:
                shutil.rmtree(TEST_PATH)
                log(f"[RESET] Test data folder deleted: {TEST_PATH}")
                log(f"[NOTE] Fresh test data will be auto-generated on next cleanup")
                print(f"[CLEANUP] Test data folder deleted and reset")
            except Exception as del_error:
                log(f"[WARNING] Could not delete test folder: {str(del_error)}")

    except Exception as e:
        log(f"\n[ERROR] {str(e)}")
        results["error"] = str(e)

    return results

# /login and /logout moved to app/blueprints/auth.py

# ========================================
# MAIN DASHBOARD ROUTES
# ========================================

@app.route("/", methods=["GET", "POST"])
def dashboard():
    """Main dashboard with enhanced functionality"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if request.method == "POST":
        password = request.form.get("password", "").strip().lower()
        if password == "komatsu":
            session["authenticated"] = True
            session["password"] = password
            flash("Login successful!", "success")
        else:
            flash("Incorrect password", "error")
    
    logged_in = session.get("authenticated", False)
    network_online = check_network_connectivity()
    
    # Dashboard data for enhanced template
    dashboard_data = {
        'logged_in': logged_in,
        'current_time': now,
        'tools': TOOL_LIST,
        'online': is_online_network(),
        'network_status': 'Online' if network_online else 'Offline',
        'gateway_ip': GATEWAY_IP,
        'timestamp': now,
        'equipment_count': len(EQUIPMENT_PROFILES)
    }
    
    # CRITICAL: Always use main_dashboard.html, never index.html
    return render_template("main_dashboard.html", **dashboard_data)

# ========================================
# API ROUTES
# ========================================

@app.get("/api/mode")
def api_mode():
    """Network mode detection API"""
    return jsonify({"online": is_online_network()})

@app.route("/api/remote-stats")
def api_remote_stats():
    """Server health monitoring API"""
    try:
        stats = get_remote_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting remote stats: {e}")
        return jsonify([]), 500

@app.route('/api/health')
def api_health():
    """
    Health check endpoint - reports server and database status.
    Used by infrastructure verification to confirm DB connectivity.
    """
    import sqlite3 as _sqlite3

    databases = {}
    all_connected = True

    # Check equipment cache database
    try:
        if EQUIPMENT_DB_PATH and os.path.exists(EQUIPMENT_DB_PATH):
            conn = _sqlite3.connect(EQUIPMENT_DB_PATH, timeout=2)
            conn.execute('SELECT 1')
            conn.close()
            databases['equipment_cache'] = {
                'status': 'connected',
                'path': EQUIPMENT_DB_PATH,
                'exists': True
            }
        else:
            databases['equipment_cache'] = {
                'status': 'not_initialized',
                'path': str(EQUIPMENT_DB_PATH),
                'exists': False
            }
            all_connected = False
    except Exception as e:
        databases['equipment_cache'] = {
            'status': 'error',
            'error': str(e),
            'exists': EQUIPMENT_DB_PATH is not None and os.path.exists(str(EQUIPMENT_DB_PATH))
        }
        all_connected = False

    # Check PTX uptime database
    try:
        if PTX_UPTIME_DB_PATH and os.path.exists(PTX_UPTIME_DB_PATH):
            conn = _sqlite3.connect(PTX_UPTIME_DB_PATH, timeout=2)
            conn.execute('SELECT 1')
            conn.close()
            databases['ptx_uptime'] = {
                'status': 'connected',
                'path': PTX_UPTIME_DB_PATH,
                'exists': True
            }
        else:
            databases['ptx_uptime'] = {
                'status': 'not_initialized',
                'path': str(PTX_UPTIME_DB_PATH),
                'exists': False
            }
            all_connected = False
    except Exception as e:
        databases['ptx_uptime'] = {
            'status': 'error',
            'error': str(e),
            'exists': PTX_UPTIME_DB_PATH is not None and os.path.exists(str(PTX_UPTIME_DB_PATH))
        }
        all_connected = False

    # Check FrontRunner events database
    try:
        from tools import frontrunner_event_db as _fr_db
        fr_db_path = _fr_db.get_database_path(BASE_DIR)
        if fr_db_path and os.path.exists(fr_db_path):
            conn = _sqlite3.connect(fr_db_path, timeout=2)
            conn.execute('SELECT 1')
            conn.close()
            databases['frontrunner_events'] = {
                'status': 'connected',
                'path': fr_db_path,
                'exists': True
            }
        else:
            databases['frontrunner_events'] = {
                'status': 'not_initialized',
                'path': str(fr_db_path),
                'exists': False
            }
            all_connected = False
    except Exception as e:
        databases['frontrunner_events'] = {
            'status': 'error',
            'error': str(e),
            'exists': False
        }
        all_connected = False

    db_status = 'connected' if all_connected else 'degraded'

    # Read version file
    version_path = os.path.join(BASE_DIR, 'VERSION')
    try:
        with open(version_path, 'r') as vf:
            version = vf.read().strip()
    except Exception:
        version = 'unknown'

    return jsonify({
        'status': 'healthy',
        'database_status': db_status,
        'databases': databases,
        'server': {
            'version': version,
            'platform': platform.system(),
            'python_version': platform.python_version()
        },
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/network_status')
def network_status():
    """Network connectivity status API"""
    try:
        online = check_network_connectivity()
        return jsonify({
            'online': online,
            'gateway_ip': GATEWAY_IP,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/system/status')
def system_status():
    """System status API - service status, connected clients, uptime"""
    # Check if running as Windows service
    running_as_service = False
    try:
        result = subprocess.run(
            ['sc', 'query', 'AutoTech'],
            capture_output=True,
            text=True,
            timeout=2,
            creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == 'Windows' else 0
        )
        running_as_service = 'RUNNING' in result.stdout
    except:
        pass  # Not running as service or sc command failed

    # Get active connections count using netstat (Windows built-in)
    active_connections = 0
    try:
        result = subprocess.run(
            ['netstat', '-an'],
            capture_output=True,
            text=True,
            timeout=2,
            creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == 'Windows' else 0
        )
        # Count ESTABLISHED connections on port 8888
        for line in result.stdout.splitlines():
            if ':8888' in line and 'ESTABLISHED' in line:
                active_connections += 1
    except:
        active_connections = 0  # Fallback if netstat fails

    return jsonify({
        'running_as_service': running_as_service,
        'active_connections': active_connections,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/equipment_profiles')
def equipment_profiles():
    """Equipment profiles API"""
    return jsonify(EQUIPMENT_PROFILES)

@app.route('/api/equipment_search', methods=['POST'])

def api_equipment_search():
    """Equipment search API"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()

        if not query:
            return jsonify({'error': 'Search query required'}), 400

        result = search_equipment(query)
        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/equipment_monitor/<equipment_id>')

def equipment_monitor(equipment_id):
    """
    Popout page for monitoring specific equipment
    No search functionality - equipment-specific monitoring only
    """
    return render_template('ip_finder_popout.html',
                         equipment_id=equipment_id,
                         online=is_online_network(),
                         gateway_ip=GATEWAY_IP,
                         timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

@app.route('/api/linux_health_check', methods=['POST'])

def api_linux_health_check():
    """
    Linux Health Check API - Gets CPU, Memory, Uptime, and Disk usage via SSH
    """
    try:
        # Import the health check function
        from tools.ip_finder import check_linux_health

        data = request.get_json()
        ptx_ip = data.get('ptx_ip', '').strip()
        ptx_model = data.get('ptx_model', 'PTX10').strip().upper()

        if not ptx_ip:
            return jsonify({'success': False, 'error': 'PTX IP required'}), 400

        # Check if this is mock equipment with predefined health data
        for equipment_id, equipment_data in MOCK_EQUIPMENT_DB.items():
            if equipment_data.get('ptx_ip') == ptx_ip and 'health' in equipment_data:
                # Return the mock health data
                mock_health = equipment_data['health'].copy()
                mock_health['success'] = True
                return jsonify(mock_health)

        # Determine SSH credentials based on PTX model
        if ptx_model == 'PTXC':
            ssh_user = 'dlog'
            ssh_password = 'gold'
        else:
            ssh_user = 'mms'
            ssh_password = 'modular'

        # Run health check
        result = check_linux_health(ptx_ip, ssh_user, ssh_password)

        return jsonify(result)

    except Exception as e:
        logger.error(f"Linux health check error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/flight_recorder_ip/<equipment_type>')
def api_get_flight_recorder_ip(equipment_type):
    """
    Flight Recorder IP calculation API
    CRITICAL: Only works for K830E and K930E profiles
    """
    try:
        profile = EQUIPMENT_PROFILES.get(equipment_type, EQUIPMENT_PROFILES['Other'])
        
        if not profile['has_flight_recorder']:
            return jsonify({
                'error': f'Flight Recorder not available for {equipment_type}',
                'has_flight_recorder': False
            })
        
        # Calculate Flight Recorder IP (PTX IP + offset)
        base_ip_parts = PTX_BASE_IP.split('.')
        last_octet = int(base_ip_parts[-1]) + profile['ptx_offset']
        flight_recorder_ip = '.'.join(base_ip_parts[:-1] + [str(last_octet)])
        
        return jsonify({
            'equipment_type': equipment_type,
            'ptx_ip': PTX_BASE_IP,
            'flight_recorder_ip': flight_recorder_ip,
            'has_flight_recorder': True,
            'offset': profile['ptx_offset']
        })
        
    except Exception as e:
        logger.error(f"Error calculating Flight Recorder IP for {equipment_type}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/vnc/connect', methods=['POST'])

def api_vnc_connect():
    """
    VNC Connection API - launches VNC viewer
    """
    try:
        data = request.get_json()
        ip = data.get('ip')
        port = data.get('port', 5900)
        
        if not ip:
            return jsonify({'success': False, 'message': 'IP address required'})
        
        # In offline mode, simulate the connection
        if not is_online_network():
            return jsonify({
                'success': True,
                'message': f'VNC connection simulated to {ip}:{port}',
                'simulated': True
            })
        
        # Try to launch VNC viewer from USB tools directory
        import subprocess
        vnc_path = VNC_VIEWER_PATH

        if not os.path.exists(vnc_path):
            return jsonify({
                'success': False,
                'message': f'VNC viewer not found at {vnc_path}. Ensure USB is connected with AutoTech tools.',
                'vnc_url': f'vnc://{ip}:{port}'
            })

        try:
            subprocess.Popen([vnc_path, '-WarnUnencrypted=0', f"{ip}:{port}"],
                           creationflags=subprocess.CREATE_NEW_CONSOLE)
            return jsonify({
                'success': True,
                'message': f'VNC viewer launched for {ip}:{port}'
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Failed to launch VNC viewer: {e}',
                'vnc_url': f'vnc://{ip}:{port}'
            })
        
    except Exception as e:
        logger.error(f"VNC connection error: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/vnc/start', methods=['POST'])

def api_vnc_start():
    """
    Start VNC session using plink.exe exactly like Start_VNC.bat
    
    Uses plink to run MMS script, then launches VNC viewer
    """
    try:
        data = request.get_json()
        ptx_ip = data.get('ptx_ip')
        equipment_name = data.get('equipment_name', 'Unknown')
        client_ready = data.get('client_ready', False)  # Check if client will launch VNC

        if not ptx_ip:
            return jsonify({'success': False, 'message': 'PTX IP address required'})
        
        # Simulate in offline mode
        if not is_online_network():
            return jsonify({
                'success': True,
                'message': f'VNC simulated for {equipment_name}',
                'simulated': True
            })
        
        logger.info(f"VNC: Starting session for {equipment_name} ({ptx_ip})")
        
        plink_path = resolve_plink_path()
        if not plink_path:
            return jsonify({
                'success': False,
                'message': 'plink.exe not found in any configured tool directory'
            })
        
        # MMS server details
        mms_server = MMS_SERVER['ip']
        mms_user = MMS_SERVER['user']
        mms_password = MMS_SERVER['password']
        vnc_script = '/home/mms/bin/remote_check/TempTool/VNC/Check_Exe.sh'
        
        try:
            # Build plink command exactly like Start_VNC.bat
            # plink.exe -batch -t mms@10.110.19.107 -pw password "script ip"
            plink_cmd = [
                plink_path,
                '-batch', '-t',
                f'{mms_user}@{mms_server}',
                '-pw', mms_password,
                f'{vnc_script} {ptx_ip}'  # NO QUOTES!
            ]

            logger.info(f"VNC: Executing plink with auto-confirmation")

            if platform.system() == 'Windows':
                result = subprocess.run(
                    plink_cmd,
                    input="Y\n",  # AUTO-CONFIRM
                    capture_output=True,
                    text=True,
                    timeout=45,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            else:
                result = subprocess.run(
                    plink_cmd,
                    input="Y\n",
                    capture_output=True,
                    text=True,
                    timeout=45
                )
            
            logger.info(f"VNC: Script output: {result.stdout[:300]}")
            if result.stderr:
                logger.info(f"VNC: Script stderr: {result.stderr[:300]}")
            
            # Parse output to determine PTX type
            ptx_type = 'Unknown'
            output_text = result.stdout + result.stderr
            if 'PTXC' in output_text:
                ptx_type = 'PTXC'
            elif 'PTX10' in output_text:
                ptx_type = 'PTX10'
            
            # VNC server started successfully, now determine how to launch viewer
            vnc_target = f'{ptx_ip}:0'

            # If client is ready, let client launch VNC viewer via protocol handler
            if client_ready:
                logger.info(f"VNC: Server started, client will launch viewer to {vnc_target}")
                return jsonify({
                    'success': True,
                    'message': f'VNC server started for {equipment_name}',
                    'equipment_name': equipment_name,
                    'ptx_type': ptx_type,
                    'ptx_ip': ptx_ip,
                    'vnc_display': vnc_target,
                    'script_output': result.stdout[:200],
                    'manual_connect': False
                })

            # Client not ready - try to launch VNC viewer from server
            # Find VNC viewer (check USB location first, then system locations)
            possible_vnc_paths = [
                VNC_VIEWER_PATH,  # USB location
            ]

            for path in possible_vnc_paths:
                if os.path.exists(path):
                    vnc_viewer_path = path
                    break

            if not vnc_viewer_path:
                return jsonify({
                    'success': True,
                    'message': f'VNC server started. Connect manually to {ptx_ip}:0 (VNC Viewer not found)',
                    'ptx_type': ptx_type,
                    'vnc_display': f'{ptx_ip}:0',
                    'manual_connect': True,
                    'script_output': result.stdout[:200]
                })

            # Launch VNC viewer from server with flags to bypass unencrypted warning
            if platform.system() == 'Windows':
                subprocess.Popen(
                    [vnc_viewer_path,
                    '-WarnUnencrypted=0',  # Bypass unencrypted connection prompt
                    f'{ptx_ip}:0'],
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
            else:
                subprocess.Popen([
                vnc_viewer_path,
                '-WarnUnencrypted=0',           # No unencrypted warning
                '-SecurityNotificationTimeout=0', # No security notification timeout
                '-FullScreen=0',                # Don't start fullscreen
                '-ViewOnly=0',                  # Not view-only (allow interaction)
                f'{ptx_ip}:0'
            ])

            logger.info(f"VNC: Launched viewer from server to {vnc_target}")

            return jsonify({
                'success': True,
                'message': f'VNC session started for {equipment_name}',
                'equipment_name': equipment_name,
                'ptx_type': ptx_type,
                'ptx_ip': ptx_ip,
                'vnc_display': vnc_target,
                'script_output': result.stdout[:200]
            })
            
        except subprocess.TimeoutExpired:
            return jsonify({
                'success': False,
                'message': 'VNC setup script timed out (45s). Try again or run manually.'
            })
        except FileNotFoundError:
            return jsonify({
                'success': False,
                'message': f'plink.exe not found at {plink_path}'
            })
        except Exception as e:
            logger.error(f"VNC: Command execution error: {e}")
            return jsonify({
                'success': False,
                'message': f'Failed to execute VNC setup: {str(e)}'
            })
        
    except Exception as e:
        logger.error(f"VNC start error: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/tru_setup', methods=['POST'])

def api_tru_setup():
    """
    TRU Access Setup API - establishes SSH tunnels for GNSS access
    """
    try:
        data = request.get_json()
        equipment_ip = data.get('equipment_ip')
        equipment_name = data.get('equipment_name', 'Unknown')
        
        if not equipment_ip:
            return jsonify({'success': False, 'message': 'Equipment IP required'})
        
        # In offline mode, simulate the TRU setup
        if not is_online_network():
            return jsonify({
                'success': True,
                'message': f'TRU access simulated for {equipment_name}',
                'equipment_name': equipment_name,
                'ip_address': equipment_ip,
                'local_ports': [5001, 5002],
                'simulated': True
            })
        
        # In online mode, this would establish actual SSH tunnels
        # For now, return simulated ports
        local_port_1 = 5001
        local_port_2 = 5002
        
        # TODO: Implement actual SSH tunnel setup with paramiko
        # ssh = paramiko.SSHClient()
        # ssh.connect(equipment_ip, username='root', password='...')
        # transport = ssh.get_transport()
        # channel = transport.open_channel(...)
        
        return jsonify({
            'success': True,
            'message': f'TRU access established for {equipment_name}',
            'equipment_name': equipment_name,
            'ip_address': equipment_ip,
            'local_ports': [local_port_1, local_port_2],
            'ptx_type': 'PTX10'
        })
        
    except Exception as e:
        logger.error(f"TRU setup error: {e}")
        return jsonify({'success': False, 'message': str(e)})

# VNC Workstation configuration
VNC_WORKSTATIONS = {
    'WS1': {'ip': '10.110.22.56', 'user': 'dlog', 'password': 'gold'},
    'WS2': {'ip': '10.110.22.57', 'user': 'dlog', 'password': 'gold'}
}

@app.route('/api/vnc/workstation', methods=['POST'])
def api_vnc_workstation():
    """
    VNC Workstation Access using plink.exe
    Mimics the batch file: echo Y | plink.exe ...
    """
    try:
        data = request.get_json()
        workstation = data.get('workstation', '').upper()
        
        # Hardcoded workstation IPs
        WORKSTATION_IPS = {
            'WS1': '10.110.22.56',
            'WS2': '10.110.22.57'
        }
        
        if workstation not in WORKSTATION_IPS:
            return jsonify({
                'success': False, 
                'message': f'Unknown workstation: {workstation}'
            })
        
        ws_ip = WORKSTATION_IPS[workstation]
        
        # In offline mode, simulate
        if not is_online_network():
            return jsonify({
                'success': True,
                'message': f'VNC {workstation} session simulated',
                'simulated': True
            })
        
        plink_path = resolve_plink_path()
        if not plink_path:
            return jsonify({
                'success': False,
                'message': 'plink.exe not found in any configured tool directory'
            })
        
        # MMS server details
        mms_server = MMS_SERVER['ip']
        mms_user = MMS_SERVER['user']
        mms_password = MMS_SERVER['password']
        vnc_script = '/home/mms/bin/remote_check/TempTool/VNC/Check_Exe.sh'
        
        try:
            # Use plink to run VNC script for workstation
            plink_cmd = [
                plink_path,
                '-batch',
                '-t',
                f'{mms_user}@{mms_server}',
                '-pw', mms_password,
                f'{vnc_script} {ws_ip}'  # NO quotes!
            ]
            
            logger.info(f"VNC WS{workstation}: Executing plink with auto-confirmation")
            
            # Run plink with auto-confirmation (mimics: echo Y | plink.exe)
            if platform.system() == 'Windows':
                result = subprocess.run(
                    plink_cmd,
                    input="Y\n",  # Auto-confirm "Start VNC manually? [Y/N]"
                    capture_output=True,
                    text=True,
                    timeout=45,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            else:
                result = subprocess.run(
                    plink_cmd,
                    input="Y\n",  # Auto-confirm
                    capture_output=True,
                    text=True,
                    timeout=45
                )
            
            logger.info(f"VNC WS{workstation}: Script output: {result.stdout[:200]}")
            
            # Find VNC viewer on USB
            vnc_viewer_path = VNC_VIEWER_PATH
            if not os.path.exists(vnc_viewer_path):
                return jsonify({
                    'success': True,
                    'message': f'VNC server started. Connect manually to {ws_ip}:0',
                    'manual_connect': True,
                    'ip': ws_ip,
                    'note': f'VNC viewer not found at: {vnc_viewer_path}'
                })
            
            # Launch VNC viewer
            logger.info(f"VNC WS{workstation}: Launching viewer: {vnc_viewer_path}")
            if platform.system() == 'Windows':
                subprocess.Popen(
                    [vnc_viewer_path, 
                    '-WarnUnencrypted=0',  # Bypass unencrypted connection prompt
                    f'{ws_ip}:0'],
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
            else:
                subprocess.Popen([vnc_viewer_path, '-WarnUnencrypted=0', f'{ws_ip}:0'])
            
            return jsonify({
                'success': True,
                'message': f'VNC {workstation} session started',
                'workstation': workstation,
                'ip': ws_ip
            })
            
        except subprocess.TimeoutExpired:
            return jsonify({
                'success': False,
                'message': 'VNC setup timed out (45s). Try again.'
            })
        except Exception as e:
            logger.error(f"VNC workstation error: {e}")
            return jsonify({
                'success': False,
                'message': f'Failed to start VNC: {str(e)}'
            })
        
    except Exception as e:
        logger.error(f"VNC workstation error: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/launch-legacy', methods=['POST'])
def api_launch_legacy():
    """
    Launch T1_Tools_Legacy from USB drive (legacy tool suite)
    Path: T1_Tools_Legacy\\bin\\Run T1 Tools.bat
    """
    try:
        # Find USB drive with T1_Tools_Legacy
        legacy_paths = []
        
        if platform.system() == 'Windows':
            import ctypes
            
            # Get available drives
            drives = []
            bitmask = ctypes.windll.kernel32.GetLogicalDrives()
            for letter in 'DEFGHIJKLMNOPQRSTUVWXYZ':
                if bitmask & 1:
                    drives.append(f"{letter}:")
                bitmask >>= 1
            
            # Look for T1_Tools_Legacy folder on each drive
            for drive in drives:
                legacy_path = os.path.join(drive, 'T1_Tools_Legacy', 'bin', 'Run T1 Tools.bat')
                if os.path.exists(legacy_path):
                    legacy_paths.append(legacy_path)
        
        if not legacy_paths:
            # Check common paths
            common_paths = [
                r"D:\T1_Tools_Legacy\bin\Run T1 Tools.bat",
                r"E:\T1_Tools_Legacy\bin\Run T1 Tools.bat",
                r"F:\T1_Tools_Legacy\bin\Run T1 Tools.bat",
            ]
            for path in common_paths:
                if os.path.exists(path):
                    legacy_paths.append(path)
        
        if not legacy_paths:
            return jsonify({
                'success': False,
                'message': 'T1 Tools Legacy not found. Please insert USB drive.'
            })
        
        # Use the first found path
        legacy_bat = legacy_paths[0]
        
        # Launch the batch file
        if platform.system() == 'Windows':
            # Run batch file in new console
            subprocess.Popen(
                ['cmd', '/c', 'start', '', legacy_bat],
                shell=True,
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
        else:
            return jsonify({
                'success': False,
                'message': 'Legacy tools only available on Windows'
            })
        
        return jsonify({
            'success': True,
            'message': 'T1 Tools Legacy launched',
            'path': legacy_bat
        })
        
    except Exception as e:
        logger.error(f"Legacy launch error: {e}")
        return jsonify({'success': False, 'message': str(e)})

# ========================================
# TOOL EXECUTION ROUTES
# ========================================

@app.route("/run/<tool_name>")
def run_tool(tool_name):
    """
    Tool execution route with special handling for IP Finder
    CRITICAL: IP Finder uses dedicated page, NOT inline
    """
    if not session.get("authenticated"):
        return redirect(url_for("dashboard"))
    
    try:
        # CRITICAL: IP Finder gets its own dedicated page
        if tool_name == "IP Finder":
            return render_template('ip_finder.html',
                                 online=is_online_network(),
                                 gateway_ip=GATEWAY_IP,
                                 timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

        # Handle PTX Uptime with enhanced functionality
        if tool_name == "PTX Uptime":
            return handle_ptx_uptime()

        # Handle FrontRunner Status
        if tool_name == "FrontRunner Status":
            return handle_frontrunner_status()

        # Handle CamStudio USB
        if tool_name == "CamStudio USB":
            return render_template('usb_tool.html',
                                 tool_name=tool_name,
                                 tool_id='camstudio',
                                 tool_icon='🎬',
                                 tool_display_name='CamStudio Portable',
                                 tool_description='Screen recording and capture tool',
                                 tool_folder='CamStudio_USB',
                                 tool_file='CamStudioPortable.exe',
                                 online=is_online_network(),
                                 gateway_ip=GATEWAY_IP,
                                 timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        # Handle Playback USB
        if tool_name == "Playback USB":
            return render_template('usb_tool.html',
                                 tool_name=tool_name,
                                 tool_id='playback',
                                 tool_icon='▶️',
                                 tool_display_name='Playback Tool V3.7.0',
                                 tool_description='Video playback and review tool',
                                 tool_folder='frontrunnerV3-3.7.0-076-full',
                                 tool_file='V3.7.0 Playback Tool.bat',
                                 online=is_online_network(),
                                 gateway_ip=GATEWAY_IP,
                                 timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        # Handle combined Playback Tools page
        if tool_name == "Playback Tools":
            return render_template('playback_tools.html',
                                 tool_name=tool_name,
                                 online=is_online_network(),
                                 gateway_ip=GATEWAY_IP,
                                 timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        # For other tools, use generic tool template or specific handling
        tool_data = {
            'tool_name': tool_name,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'online': is_online_network(),
            'gateway_ip': GATEWAY_IP
        }
        
        return render_template('tool_generic.html', **tool_data)
        
    except Exception as e:
        logger.error(f"Error running tool {tool_name}: {e}")
        flash(f"Tool Error: {e}", "error")
        return redirect(url_for('dashboard'))

def handle_ptx_uptime():
    """Handle PTX Uptime tool with enhanced functionality"""
    try:
        online = is_online_network()
        force_sync = request.args.get('sync', 'false').lower() == 'true' or 'refresh' in request.args

        # Check if database needs initial sync from live server
        db_count = ptx_uptime_db.get_record_count()

        last_live_sync = ptx_uptime_db.get_sync_metadata('last_live_sync')
        needs_live_sync = online and (force_sync or db_count == 0)
        if online and last_live_sync and not force_sync:
            try:
                last_sync_dt = datetime.fromisoformat(last_live_sync)
                needs_live_sync = needs_live_sync or (datetime.now() - last_sync_dt) > timedelta(minutes=10)
            except ValueError:
                needs_live_sync = True

        if needs_live_sync and ptx_uptime_tool:
            logger.info("Syncing PTX uptime database from live report")
            result = ptx_uptime_tool.run(password=MMS_SERVER['password'])
            if result.get('success'):
                existing_ids = {row['equipment_id'] for row in ptx_uptime_db.get_all_uptime(min_hours=0)}
                added = 0
                updated = 0
                for equipment in result.get('equipment_list', []):
                    equipment_id = equipment.get('equipment_id')
                    ip_address = equipment.get('ip')
                    if not equipment_id or not ip_address:
                        continue
                    if equipment_id in existing_ids:
                        updated += 1
                    else:
                        added += 1
                        existing_ids.add(equipment_id)

                    ts = equipment.get('timestamp') or 0
                    if not ts and ptx_uptime_tool:
                        ts = ptx_uptime_tool.parse_last_check_timestamp(equipment.get('last_check'))
                    if not ts:
                        ts = int(time.time())

                    ptx_uptime_db.upsert_uptime(
                        equipment_id=equipment_id,
                        ip_address=ip_address,
                        uptime_hours=equipment.get('uptime_hours', 0),
                        last_check=equipment.get('last_check'),
                        last_check_timestamp=ts
                    )
                ptx_uptime_db.set_sync_metadata('last_live_sync', datetime.now().isoformat())
                ptx_uptime_db.set_sync_metadata('last_live_path', result.get('file_path', ''))
                if force_sync:
                    flash(f"Database synced: {added} added, {updated} updated", "success")
            else:
                logger.warning(f"Live PTX uptime sync failed: {result.get('error')}")

        # Get data from database
        high_uptime_equipment = ptx_uptime_db.get_high_uptime(min_days=3)
        statistics = ptx_uptime_db.get_statistics()

        # If database is still empty, use sample data for testing
        if not high_uptime_equipment:
            logger.info("Using sample PTX uptime data for testing")
            high_uptime_equipment = [
                {'timestamp': 1769006409, 'ip': '10.110.20.10', 'equipment_id': 'ROM1', 'uptime_hours': 151.05, 'uptime_days': 6.3, 'last_check': 'Thu Jan 22 00:40:09 AEST 2026'},
                {'timestamp': 1769004985, 'ip': '10.110.20.11', 'equipment_id': 'ROM2', 'uptime_hours': 150.65, 'uptime_days': 6.3, 'last_check': 'Thu Jan 22 00:16:25 AEST 2026'},
                {'timestamp': 1768977869, 'ip': '10.110.21.151', 'equipment_id': 'TRD410', 'uptime_hours': 195.80, 'uptime_days': 8.2, 'last_check': 'Wed Jan 21 16:44:29 AEST 2026'},
                {'timestamp': 1769001329, 'ip': '10.110.21.157', 'equipment_id': 'TRD498', 'uptime_hours': 169.65, 'uptime_days': 7.1, 'last_check': 'Wed Jan 21 23:15:29 AEST 2026'},
                {'timestamp': 1768992242, 'ip': '10.110.21.130', 'equipment_id': 'TRD409', 'uptime_hours': 162.27, 'uptime_days': 6.8, 'last_check': 'Wed Jan 21 20:44:02 AEST 2026'},
                {'timestamp': 1768973183, 'ip': '10.110.21.229', 'equipment_id': 'EL20', 'uptime_hours': 115.22, 'uptime_days': 4.8, 'last_check': 'Wed Jan 21 15:26:23 AEST 2026'},
                {'timestamp': 1768966923, 'ip': '10.110.21.185', 'equipment_id': 'EXD265', 'uptime_hours': 109.48, 'uptime_days': 4.6, 'last_check': 'Wed Jan 21 13:42:03 AEST 2026'},
                {'timestamp': 1768948919, 'ip': '10.110.21.196', 'equipment_id': 'DZ32NPE', 'uptime_hours': 137.42, 'uptime_days': 5.7, 'last_check': 'Wed Jan 21 08:41:59 AEST 2026'},
            ]
            statistics = {
                'total_equipment': len(high_uptime_equipment),
                'avg_uptime': 140,
                'max_uptime': 195.80,
                'high_uptime_count': len(high_uptime_equipment)
            }

        def ensure_display_timestamp(row: dict) -> dict:
            ts = row.get('timestamp') or 0
            if not ts and ptx_uptime_tool:
                ts = ptx_uptime_tool.parse_last_check_timestamp(row.get('last_check'))
            if not ts and row.get('last_updated'):
                try:
                    ts = int(datetime.fromisoformat(row['last_updated']).timestamp())
                except ValueError:
                    ts = 0
            if not ts:
                ts = int(time.time())
            row['display_ts'] = ts
            return row

        high_uptime_equipment = [ensure_display_timestamp(dict(eq)) for eq in high_uptime_equipment]

        # Get last sync time
        last_sync = ptx_uptime_db.get_sync_metadata('last_html_sync')

        ptx_data = {
            'tool_name': 'PTX Uptime',
            'online': online,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'gateway_ip': GATEWAY_IP,
            'high_uptime_equipment': high_uptime_equipment,
            'statistics': statistics,
            'last_sync': last_sync,
            'mode': 'reference' if not online else 'live'
        }

        return render_template('ptx_uptime.html', **ptx_data)

    except Exception as e:
        logger.error(f"PTX Uptime error: {e}")
        flash(f"PTX Uptime failed: {e}", "error")
        return redirect(url_for('dashboard'))

def handle_frontrunner_status():
    """Handle FrontRunner Status tool"""
    try:
        # Check if we're in online mode
        online = is_online_network()

        # Try to get cached status from background monitor first
        result = None
        if online:
            try:
                from tools import frontrunner_monitor
                base_dir = os.path.dirname(os.path.abspath(__file__))
                result = frontrunner_monitor.get_status(base_dir)

                # If cache is stale or monitor not running, fall back to direct call
                if not result or not result.get('success'):
                    logger.warning("Background monitor cache unavailable, using direct connection")
                    result = None
            except Exception as e:
                logger.warning(f"Could not read monitor cache: {e}")
                result = None

        # Fallback: Use direct SSH connection if monitor cache unavailable
        if result is None:
            FR_PASSWORD = "M0dul1r@GRM2"
            if frontrunner_status_tool:
                result = frontrunner_status_tool.run(password=FR_PASSWORD, offline_mode=not online, enable_logging=False)
                if online and not result.get('success'):
                    logger.warning("FrontRunner live status failed (%s); falling back to offline snapshot", result.get('error'))
                    fallback = frontrunner_status_tool.run(password=FR_PASSWORD, offline_mode=True, enable_logging=False)
                    fallback['mode'] = 'offline_fallback'
                    fallback['fallback_reason'] = result.get('error')
                    result = fallback
            else:
                result = {
                    'success': False,
                    'error': 'FrontRunner Status tool not available',
                    'report_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'mode': 'error'
                }

        return render_template('frontrunner_status.html', result=result, online=online)

    except Exception as e:
        logger.error(f"FrontRunner Status error: {e}")
        flash(f"FrontRunner Status failed: {e}", "error")
        return redirect(url_for('dashboard'))

@app.route('/api/frontrunner/events')
def api_frontrunner_events():
    """API endpoint to get FrontRunner event logs (process failures and disk warnings)"""
    try:
        from tools import frontrunner_event_db

        # Get database path
        base_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = frontrunner_event_db.get_database_path(base_dir)

        # Get event history
        history = frontrunner_event_db.get_event_history(db_path, limit=100)

        return jsonify({
            'success': True,
            'process_events': history['process_events'],
            'disk_events': history['disk_events']
        })

    except Exception as e:
        logger.error(f"Error fetching FrontRunner events: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'process_events': [],
            'disk_events': []
        }), 500

@app.route('/api/frontrunner/active-events')
def api_frontrunner_active_events():
    """API endpoint to get currently active FrontRunner events"""
    try:
        from tools import frontrunner_event_db

        # Get database path
        base_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = frontrunner_event_db.get_database_path(base_dir)

        # Get active events
        active = frontrunner_event_db.get_active_events(db_path)

        return jsonify({
            'success': True,
            'process_events': active['process_events'],
            'disk_events': active['disk_events']
        })

    except Exception as e:
        logger.error(f"Error fetching active FrontRunner events: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'process_events': [],
            'disk_events': []
        }), 500

@app.route('/ptx-uptime-csv')
def ptx_uptime_csv():
    """Download PTX Uptime data as CSV"""
    try:
        import csv
        import io

        # Get all data from database
        equipment_data = ptx_uptime_db.get_all_uptime(min_hours=0)

        if not equipment_data:
            flash("No PTX uptime data available. Please sync the database first.", "warning")
            return redirect(url_for('run_tool', tool_name='PTX Uptime'))

        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow(['Equipment ID', 'IP Address', 'Uptime (Hours)', 'Uptime (Days)', 'Last Check', 'Timestamp', 'PTX Type', 'Status'])

        # Write data rows (already sorted by uptime descending from database)
        for eq in equipment_data:
            writer.writerow([
                eq.get('equipment_id', ''),
                eq.get('ip', ''),
                eq.get('uptime_hours', 0),
                eq.get('uptime_days', 0),
                eq.get('last_check', ''),
                eq.get('timestamp', ''),
                eq.get('ptx_type', ''),
                eq.get('last_status', '')
            ])

        # Create response
        output.seek(0)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=PTX_Uptime_Report_{timestamp}.csv'}
        )

    except Exception as e:
        logger.error(f"PTX Uptime CSV error: {e}")
        flash(f"CSV download failed: {e}", "error") 
        return redirect(url_for('run_tool', tool_name='PTX Uptime'))

# ========================================
# PTX UPTIME DATABASE API ENDPOINTS
# ========================================

@app.route('/api/ptx/db/sync', methods=['POST'])
def api_ptx_db_sync():
    """Sync PTX uptime database from HTML report"""
    try:
        if is_online_network() and ptx_uptime_tool:
            result = ptx_uptime_tool.run(password=MMS_SERVER['password'])
            if not result.get('success'):
                return jsonify({'success': False, 'error': result.get('error', 'Live sync failed')}), 500

            existing_ids = {row['equipment_id'] for row in ptx_uptime_db.get_all_uptime(min_hours=0)}
            added = 0
            updated = 0
            for equipment in result.get('equipment_list', []):
                equipment_id = equipment.get('equipment_id')
                ip_address = equipment.get('ip')
                if not equipment_id or not ip_address:
                    continue
                if equipment_id in existing_ids:
                    updated += 1
                else:
                    added += 1
                    existing_ids.add(equipment_id)
                ptx_uptime_db.upsert_uptime(
                    equipment_id=equipment_id,
                    ip_address=ip_address,
                    uptime_hours=equipment.get('uptime_hours', 0),
                    last_check=equipment.get('last_check'),
                    last_check_timestamp=0
                )
            ptx_uptime_db.set_sync_metadata('last_live_sync', datetime.now().isoformat())
            ptx_uptime_db.set_sync_metadata('last_live_path', result.get('file_path', ''))
        else:
            report_path = os.path.join(os.path.dirname(__file__), 'backups', 'PTX_Uptime_Report.html')
            if not os.path.exists(report_path):
                return jsonify({
                    'success': False,
                    'error': 'PTX Uptime Report HTML not found',
                    'path': report_path
                }), 404
            updated, added = ptx_uptime_db.sync_from_html_report(report_path)

        return jsonify({
            'success': True,
            'records_added': added,
            'records_updated': updated,
            'total_records': ptx_uptime_db.get_record_count(),
            'sync_time': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"PTX DB sync error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ptx/db/stats')
def api_ptx_db_stats():
    """Get PTX uptime database statistics"""
    try:
        stats = ptx_uptime_db.get_statistics()
        stats['last_sync'] = ptx_uptime_db.get_sync_metadata('last_html_sync')
        stats['total_records'] = ptx_uptime_db.get_record_count()

        return jsonify({
            'success': True,
            'statistics': stats
        })

    except Exception as e:
        logger.error(f"PTX DB stats error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ptx/db/reboot-log', methods=['POST'])
def api_ptx_log_reboot():
    """Log a PTX reboot event to the database"""
    try:
        data = request.get_json()
        equipment_id = data.get('equipment_id')
        ip_address = data.get('ip_address')
        uptime_before = data.get('uptime_before')
        success = data.get('success', True)
        notes = data.get('notes', '')

        if not equipment_id or not ip_address:
            return jsonify({'success': False, 'error': 'Missing equipment_id or ip_address'}), 400

        result = ptx_uptime_db.log_reboot(
            equipment_id=equipment_id,
            ip_address=ip_address,
            uptime_before=uptime_before,
            success=success,
            rebooted_by=session.get('username', 'web_user'),
            notes=notes
        )

        return jsonify({'success': result})

    except Exception as e:
        logger.error(f"PTX reboot log error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ptx/db/reboot-history')
def api_ptx_reboot_history():
    """Get PTX reboot history"""
    try:
        equipment_id = request.args.get('equipment_id', None)
        limit = int(request.args.get('limit', 50))

        history = ptx_uptime_db.get_reboot_history(equipment_id=equipment_id if equipment_id else None, limit=limit)

        return jsonify({
            'success': True,
            'history': history,
            'count': len(history)
        })

    except Exception as e:
        logger.error(f"PTX reboot history error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ptx/db/update-status', methods=['POST'])
def api_ptx_update_status():
    """Update PTX equipment status in database"""
    try:
        data = request.get_json()
        equipment_id = data.get('equipment_id')
        status = data.get('status')
        ptx_type = data.get('ptx_type')

        if not equipment_id or not status:
            return jsonify({'success': False, 'error': 'Missing equipment_id or status'}), 400

        result = ptx_uptime_db.update_status(
            equipment_id=equipment_id,
            status=status,
            ptx_type=ptx_type
        )

        return jsonify({'success': result})

    except Exception as e:
        logger.error(f"PTX update status error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ========================================
# PTX UPTIME CHECKER API ENDPOINTS
# ========================================

@app.route('/api/ptx/uptime-checker/start', methods=['POST'])
def api_start_ptx_uptime_checker():
    """
    Start the background PTX uptime checker.
    Checks all equipment in database every 30 minutes (configurable).
    """
    global ptx_uptime_checker

    try:
        # Check if online mode
        if not is_online_network():
            return jsonify({
                'success': False,
                'error': 'PTX uptime checker requires online network connection'
            }), 400

        # Check if already running
        if ptx_uptime_checker['running']:
            return jsonify({
                'success': False,
                'error': 'PTX uptime checker is already running',
                'status': ptx_uptime_checker['status']
            }), 400

        # Get optional interval from request
        data = request.get_json() or {}
        interval = data.get('interval_minutes', 30)
        ptx_uptime_checker['interval_minutes'] = max(5, min(120, interval))  # Clamp 5-120 minutes

        # Start the checker thread
        ptx_uptime_checker['stop_event'].clear()
        ptx_uptime_checker['running'] = True
        ptx_uptime_checker['thread'] = threading.Thread(
            target=ptx_uptime_checker_worker,
            daemon=True
        )
        ptx_uptime_checker['thread'].start()

        return jsonify({
            'success': True,
            'message': 'PTX uptime checker started',
            'interval_minutes': ptx_uptime_checker['interval_minutes']
        })

    except Exception as e:
        logger.error(f"Error starting PTX uptime checker: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ptx/uptime-checker/stop', methods=['POST'])
def api_stop_ptx_uptime_checker():
    """Stop the background PTX uptime checker."""
    global ptx_uptime_checker

    try:
        if not ptx_uptime_checker['running']:
            return jsonify({
                'success': False,
                'error': 'PTX uptime checker is not running'
            }), 400

        # Signal the thread to stop
        ptx_uptime_checker['stop_event'].set()

        return jsonify({
            'success': True,
            'message': 'Stop signal sent to PTX uptime checker'
        })

    except Exception as e:
        logger.error(f"Error stopping PTX uptime checker: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ptx/uptime-checker/status')
def api_ptx_uptime_checker_status():
    """Get the current status of the PTX uptime checker."""
    try:
        return jsonify({
            'success': True,
            'running': ptx_uptime_checker['running'],
            'status': ptx_uptime_checker['status'],
            'current_equipment': ptx_uptime_checker['current_equipment'],
            'total_equipment': ptx_uptime_checker['total_equipment'],
            'checked_count': ptx_uptime_checker['checked_count'],
            'online_count': ptx_uptime_checker['online_count'],
            'offline_count': ptx_uptime_checker['offline_count'],
            'error_count': ptx_uptime_checker['error_count'],
            'last_cycle_start': ptx_uptime_checker['last_cycle_start'],
            'last_cycle_end': ptx_uptime_checker['last_cycle_end'],
            'next_cycle': ptx_uptime_checker['next_cycle'],
            'interval_minutes': ptx_uptime_checker['interval_minutes']
        })

    except Exception as e:
        logger.error(f"Error getting PTX uptime checker status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/playback/monitor/start', methods=['POST'])
def api_start_playback_monitor():
    """
    Start the background playback monitor.
    Maintains persistent SSH connection to playback server for real-time file monitoring.
    """
    global playback_monitor

    try:
        # Check if online mode
        if not is_online_network():
            return jsonify({
                'success': False,
                'error': 'Playback monitor requires online network connection'
            }), 400

        # Check if already running
        if playback_monitor['running']:
            return jsonify({
                'success': False,
                'error': 'Playback monitor is already running',
                'status': playback_monitor['status']
            }), 400

        # Get optional scan interval from request
        data = request.get_json() or {}
        interval = data.get('scan_interval_seconds', 10)
        playback_monitor['scan_interval_seconds'] = max(5, min(60, interval))  # Clamp 5-60 seconds

        # Start the monitor thread
        playback_monitor['stop_event'].clear()
        playback_monitor['running'] = True
        playback_monitor['thread'] = threading.Thread(
            target=playback_monitor_worker,
            daemon=True
        )
        playback_monitor['thread'].start()

        return jsonify({
            'success': True,
            'message': 'Playback monitor started',
            'scan_interval_seconds': playback_monitor['scan_interval_seconds']
        })

    except Exception as e:
        logger.error(f"Error starting playback monitor: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/playback/monitor/stop', methods=['POST'])
def api_stop_playback_monitor():
    """Stop the background playback monitor."""
    global playback_monitor

    try:
        if not playback_monitor['running']:
            return jsonify({
                'success': False,
                'error': 'Playback monitor is not running'
            }), 400

        # Signal the thread to stop
        playback_monitor['stop_event'].set()

        return jsonify({
            'success': True,
            'message': 'Stop signal sent to playback monitor'
        })

    except Exception as e:
        logger.error(f"Error stopping playback monitor: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/playback/monitor/status')
def api_playback_monitor_status():
    """Get the current status of the playback monitor and cached file data."""
    try:
        return jsonify({
            'success': True,
            'running': playback_monitor['running'],
            'connected': playback_monitor['connected'],
            'status': playback_monitor['status'],
            'last_scan': playback_monitor['last_scan'],
            'log_files': playback_monitor['log_files'],
            'dat_files': playback_monitor['dat_files'],
            'pending_file': playback_monitor['pending_file'],
            'last_error': playback_monitor['last_error'],
            'reconnect_count': playback_monitor['reconnect_count'],
            'scan_interval_seconds': playback_monitor['scan_interval_seconds']
        })

    except Exception as e:
        logger.error(f"Error getting playback monitor status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ptx/uptime-checker/check-single', methods=['POST'])
def api_check_single_ptx_uptime():
    """
    Check uptime for a single PTX equipment.
    Useful for manual refresh of individual equipment.
    """
    try:
        if not is_online_network():
            return jsonify({
                'success': False,
                'error': 'Online network connection required'
            }), 400

        data = request.get_json()
        ip_address = data.get('ip_address')
        equipment_id = data.get('equipment_id')

        if not ip_address:
            return jsonify({'success': False, 'error': 'IP address required'}), 400

        # Check if reachable
        if not check_ptx_reachable(ip_address, timeout=3.0):
            if equipment_id:
                ptx_uptime_db.update_status(equipment_id, 'offline')
            return jsonify({
                'success': True,
                'reachable': False,
                'status': 'offline',
                'message': f'{ip_address} is not reachable'
            })

        # Get uptime
        result = get_ptx_uptime(ip_address)

        if result['success']:
            # Update database if equipment_id provided
            if equipment_id:
                ptx_type = result.get('ptx_type') or 'PTX'
                ptx_uptime_db.upsert_uptime(
                    equipment_id=equipment_id,
                    ip_address=ip_address,
                    uptime_hours=result['uptime_hours'],
                    last_check=datetime.now().strftime('%a %b %d %H:%M:%S %Z %Y'),
                    last_check_timestamp=int(time.time()),
                    ptx_type=ptx_type
                )
                ptx_uptime_db.update_status(equipment_id, 'online', ptx_type)

            return jsonify({
                'success': True,
                'reachable': True,
                'status': 'online',
                'uptime_hours': result['uptime_hours'],
                'uptime_days': round(result['uptime_hours'] / 24, 1),
                'uptime_raw': result['uptime_raw'],
                'ptx_type': result.get('ptx_type')
            })
        else:
            if equipment_id:
                ptx_uptime_db.update_status(equipment_id, 'unknown')
            return jsonify({
                'success': True,
                'reachable': True,
                'status': 'error',
                'error': result.get('error', 'Unknown error')
            })

    except Exception as e:
        logger.error(f"Error checking single PTX uptime: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ========================================
# USB TOOLS API ENDPOINTS
# ========================================

@app.route("/api/usb/scan/<tool_id>")
@login_required
def api_usb_scan(tool_id):
    """
    Scan USB drives for a specific tool.
    tool_id: 'camstudio' or 'playback'
    Normalizes scan() output to match playback_tools.html expectations:
      - found: bool
      - details.drive.letter: "E"
      - drives: [...]
    """
    def _normalize_scan_result(result: dict) -> dict:
        if not isinstance(result, dict):
            return {'found': False, 'error': 'Invalid scan result type', 'details': {}, 'drives': []}

        # Determine drive letter from common patterns
        letter = None

        # 1) Already in the expected shape
        try:
            letter = result.get('details', {}).get('drive', {}).get('letter')
        except Exception:
            letter = None

        # 2) Common alternative keys
        if not letter:
            letter = result.get('drive_letter') or result.get('letter')

        # 3) drive may be "E:" or "E"
        if not letter and isinstance(result.get('drive'), str):
            d = result['drive'].strip()
            letter = d[0].upper() if d else None

        # 4) Some tools return a list of drives
        drives = result.get('drives')
        if not drives:
            drives = result.get('usb_drives') or result.get('available_drives') or []

        # Infer letter from drives list if possible
        if not letter and isinstance(drives, list) and drives:
            first = drives[0]
            if isinstance(first, dict):
                d = first.get('letter') or first.get('drive_letter') or first.get('drive')
                if isinstance(d, str) and d:
                    letter = d.strip()[0].upper()

        # Determine found flag
        found = result.get('found')
        if found is None:
            # Sometimes scan() returns success + path
            found = bool(result.get('success')) and bool(letter)

        # Build normalized response
        normalized = {
            'found': bool(found),
            'details': {
                'drive': {
                    'letter': letter
                }
            },
            'drives': drives if isinstance(drives, list) else [],
        }

        # Preserve helpful fields from original
        if 'error' in result and result['error']:
            normalized['error'] = result['error']
        if 'message' in result and result['message']:
            normalized['message'] = result['message']
        if 'path' in result and result['path']:
            normalized['path'] = result['path']

        return normalized

    try:
        if tool_id == 'camstudio':
            from tools.camstudio_usb import scan
            raw = scan()
        elif tool_id == 'playback':
            from tools.playback_usb import scan
            raw = scan()
        else:
            return jsonify({'found': False, 'error': f'Unknown tool: {tool_id}', 'details': {}, 'drives': []}), 400

        return jsonify(_normalize_scan_result(raw))

    except Exception as e:
        logger.error(f"USB scan error for {tool_id}: {e}")
        return jsonify({'found': False, 'error': str(e), 'details': {}, 'drives': []}), 500

@app.route("/api/usb/launch/<tool_id>", methods=["POST"])
def api_usb_launch(tool_id):
    """
    Launch a USB tool.
    tool_id: 'camstudio' or 'playback'
    """
    try:
        if tool_id == 'camstudio':
            from tools.camstudio_usb import launch
            success, message = launch()
        elif tool_id == 'playback':
            from tools.playback_usb import launch
            success, message = launch()
        else:
            return jsonify({'success': False, 'message': f'Unknown tool: {tool_id}'}), 400
        
        return jsonify({'success': success, 'message': message})
        
    except Exception as e:
        logger.error(f"USB launch error for {tool_id}: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route("/api/usb/status")
def api_usb_status():
    """
    Get status of all USB drives and tools.
    """
    try:
        from tools.usb_tools import scan_usb_status
        status = scan_usb_status()
        return jsonify(status)

    except Exception as e:
        logger.error(f"USB status error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/usb_tool')
def usb_tool_page():
    """AutoTech Client USB management page."""
    return render_template('usb_tool.html',
                         tool_name='AutoTech Client USB',
                         tool_id='client',
                         tool_icon='💾',
                         tool_display_name='AutoTech Client Package',
                         tool_description='USB installer and client management tools',
                         tool_folder='autotech_client',
                         tool_file='Install_AutoTech_Client.bat',
                         online=is_online_network(),
                         gateway_ip=GATEWAY_IP,
                         timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

@app.route('/api/usb/scan')
def api_usb_scan_all():
    """
    Scan all USB drives for AutoTech client package (no specific tool required).
    Returns USB drive status from usb_tools.scan_usb_status().
    """
    try:
        from tools.usb_tools import scan_usb_status
        status = scan_usb_status()
        return jsonify(status)
    except Exception as e:
        logger.error(f"USB scan error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/client/installer')
def api_client_installer():
    """
    Download AutoTech Client installer batch file.
    Serves Install_AutoTech_Client.bat from the autotech_client folder.
    """
    client_folder, error = get_autotech_client_folder()
    if error or not client_folder:
        return jsonify({'error': error or 'AutoTech Client folder not found'}), 404
    installer_path = os.path.join(client_folder, 'Install_AutoTech_Client.bat')
    if not os.path.exists(installer_path):
        return jsonify({'error': 'Install_AutoTech_Client.bat not found in client folder'}), 404
    return send_file(installer_path, as_attachment=True, download_name='Install_AutoTech_Client.bat')

@app.route('/api/client/test')
def api_client_test():
    """
    Test AutoTech Client installation status.
    Checks Windows registry for URI handler registrations and
    C:\\AutoTech_Client\\scripts\\ for launcher files.
    """
    try:
        import winreg
    except ImportError:
        return jsonify({'error': 'winreg not available (Windows only)'}), 500

    protocols = ['autotech-ssh', 'autotech-sftp', 'autotech-vnc', 'autotech-script']
    handlers = {}
    for protocol in protocols:
        try:
            key = winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, protocol)
            winreg.CloseKey(key)
            handlers[protocol] = True
        except (FileNotFoundError, OSError):
            handlers[protocol] = False

    install_dir = r'C:\AutoTech_Client\scripts'
    launchers = {}
    for script in ['launch_putty.bat', 'launch_winscp.bat', 'launch_vnc.bat', 'launch_script.bat']:
        launchers[script] = os.path.exists(os.path.join(install_dir, script))

    all_installed = all(handlers.values()) and all(launchers.values())
    return jsonify({
        'handlers': handlers,
        'launchers': launchers,
        'install_dir': install_dir,
        'all_installed': all_installed
    })

# ========================================
# PLAYBACK SERVER API ENDPOINTS
# ========================================

# PLAYBACK_SERVER imported from app.config above

@app.route("/api/playback/server-check")
def api_playback_server_check():
    """
    Check if playback server is reachable.
    """
    try:
        # OFFLINE MODE: Return disconnected status
        if not is_online_network():
            return jsonify({
                'connected': False,
                'ip': PLAYBACK_SERVER['ip'],
                'port': PLAYBACK_SERVER['port'],
                'offline_mode': True,
                'message': 'Server unavailable in offline mode'
            })

        # Try ping first
        connected = False

        if ping3:
            result = ping3.ping(PLAYBACK_SERVER['ip'], timeout=3)
            connected = result is not None
        else:
            # Fallback to socket test
            try:
                with socket.create_connection(
                    (PLAYBACK_SERVER['ip'], PLAYBACK_SERVER['port']),
                    timeout=3
                ):
                    connected = True
            except:
                connected = False

        return jsonify({
            'connected': connected,
            'ip': PLAYBACK_SERVER['ip'],
            'port': PLAYBACK_SERVER['port']
        })
        
    except Exception as e:
        logger.error(f"Playback server check error: {e}")
        return jsonify({'connected': False, 'error': str(e)})

@app.route("/api/playback/open-winscp", methods=["POST"])
def api_playback_open_winscp():
    """
    Open WinSCP to the playback server.
    """
    try:
        # Common WinSCP locations
        winscp_paths = [
            r"C:\Program Files (x86)\WinSCP\WinSCP.exe",
            r"C:\Program Files\WinSCP\WinSCP.exe",
            os.path.expanduser(r"~\AppData\Local\Programs\WinSCP\WinSCP.exe"),
        ]
        
        # Also check PATH
        winscp_exe = None
        
        # Check common locations
        for path in winscp_paths:
            if os.path.exists(path):
                winscp_exe = path
                break
        
        # Try to find in PATH if not found
        if not winscp_exe:
            import shutil
            winscp_exe = shutil.which("WinSCP.exe") or shutil.which("winscp")
        
        if not winscp_exe:
            return jsonify({
                'success': False,
                'message': 'WinSCP not found. Please install WinSCP or add it to PATH.'
            })
        
        # Build WinSCP command with SFTP URL
        # Format: sftp://user:password@host/path/
        sftp_url = f"sftp://{PLAYBACK_SERVER['user']}:{PLAYBACK_SERVER['password']}@{PLAYBACK_SERVER['ip']}{PLAYBACK_SERVER['path']}"
        
        # Launch WinSCP
        subprocess.Popen([winscp_exe, sftp_url], 
                        creationflags=subprocess.CREATE_NEW_CONSOLE if platform.system() == "Windows" else 0)
        
        return jsonify({
            'success': True,
            'message': 'WinSCP opened successfully'
        })
        
    except Exception as e:
        logger.error(f"WinSCP launch error: {e}")
        return jsonify({
            'success': False,
            'message': f'Error launching WinSCP: {str(e)}'
        })

@app.route("/api/playback/local-files")
def api_playback_local_files():
    """
    List playback files on local USB drive.
    """
    try:
        # Import the USB tools module
        try:
            from tools.usb_tools import find_tool_on_usb
        except ImportError as e:
            logger.error(f"USB tools import error: {e}")
            return jsonify({'error': 'USB tools module not available', 'files': []})
        
        # Find the playback tool to get the USB drive path
        result = find_tool_on_usb("frontrunnerV3-3.7.0-076-full", "V3.7.0 Playback Tool.bat")
        
        if not result:
            return jsonify({'error': 'Playback USB not detected', 'files': []})
        
        # Build path to playback folder
        playback_path = Path(result['folder_path']) / 'playback'
        
        if not playback_path.exists():
            # Try to create it if it doesn't exist
            try:
                playback_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created playback folder: {playback_path}")
            except Exception as mkdir_e:
                logger.error(f"Could not create playback folder: {mkdir_e}")
                return jsonify({'error': 'Playback folder not found', 'files': [], 'path': str(playback_path)})
        
        # List .dat files
        files = []
        for f in playback_path.glob('AHS_LOG_*.dat'):
            try:
                stat = f.stat()
                files.append({
                    'name': f.name,
                    'size': stat.st_size,
                    'modified': stat.st_mtime
                })
            except Exception as file_e:
                logger.warning(f"Could not read file {f}: {file_e}")
                continue
        
        # Sort by name descending (newest first based on filename)
        files.sort(key=lambda x: x['name'], reverse=True)
        
        return jsonify({
            'files': files,
            'path': str(playback_path),
            'count': len(files)
        })
        
    except Exception as e:
        logger.error(f"Local files error: {e}", exc_info=True)
        return jsonify({'error': f'Error: {str(e)}', 'files': []})

@app.route("/api/playback/server-files")
def api_playback_server_files():
    """
    List playback files on the server via SFTP.
    """
    try:
        # OFFLINE MODE: Return mock files
        if not is_online_network():
            mock_files = [
                {'name': 'AHS_LOG_20260108_120000_AEST.dat', 'size': 15728640, 'modified': time.time() - 3600},
                {'name': 'AHS_LOG_20260108_114500_AEST.dat', 'size': 15728640, 'modified': time.time() - 5400},
                {'name': 'AHS_LOG_20260108_113000_AEST.dat', 'size': 15728640, 'modified': time.time() - 7200},
                {'name': 'AHS_LOG_20260107_150000_AEST.dat', 'size': 15728640, 'modified': time.time() - 86400},
            ]
            return jsonify({'files': mock_files, 'count': len(mock_files), 'offline_mode': True})

        if not paramiko:
            return jsonify({'error': 'SSH library not available', 'files': []})

        # Connect via SSH
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            ssh.connect(
                PLAYBACK_SERVER['ip'],
                port=PLAYBACK_SERVER['port'],
                username=PLAYBACK_SERVER['user'],
                password=PLAYBACK_SERVER['password'],
                timeout=10
            )
        except Exception as e:
            return jsonify({'error': f'Connection failed: {str(e)}', 'files': []})
        
        # Use SFTP to list files
        sftp = ssh.open_sftp()
        
        try:
            file_list = sftp.listdir_attr(PLAYBACK_SERVER['path'])
        except Exception as e:
            sftp.close()
            ssh.close()
            return jsonify({'error': f'Cannot read directory: {str(e)}', 'files': []})
        
        # Filter and format files
        files = []
        for f in file_list:
            if f.filename.startswith('AHS_LOG_') and f.filename.endswith('.dat'):
                files.append({
                    'name': f.filename,
                    'size': f.st_size,
                    'modified': f.st_mtime
                })
        
        sftp.close()
        ssh.close()
        
        # Sort by name descending (newest first)
        files.sort(key=lambda x: x['name'], reverse=True)
        
        return jsonify({
            'files': files,
            'count': len(files)
        })
        
    except Exception as e:
        logger.error(f"Server files error: {e}")
        return jsonify({'error': str(e), 'files': []})

@app.route("/api/playback/find-file")
def api_playback_find_file():
    """
    Find the playback file that covers a specific date/time.
    Files are in 15-minute blocks with format: AHS_LOG_YYYYMMDD_HHMMSS_AEST.dat
    """
    try:
        date_str = request.args.get('date')  # YYYY-MM-DD
        time_str = request.args.get('time')  # HH:MM

        if not date_str or not time_str:
            return jsonify({'found': False, 'error': 'Date and time required'})

        # Parse requested datetime
        requested_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")

        # OFFLINE MODE: Return mock file that matches the requested time
        if not is_online_network():
            # Round down to nearest 15-minute block
            minutes = (requested_dt.minute // 15) * 15
            block_start = requested_dt.replace(minute=minutes, second=0, microsecond=0)
            filename = f"AHS_LOG_{block_start.strftime('%Y%m%d_%H%M%S')}_AEST.dat"
            return jsonify({
                'found': True,
                'filename': filename,
                'size': 15728640,
                'time_str': block_start.strftime('%H:%M:%S'),
                'offline_mode': True
            })

        if not paramiko:
            return jsonify({'found': False, 'error': 'SSH library not available'})

        # Connect to server
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            ssh.connect(
                PLAYBACK_SERVER['ip'],
                port=PLAYBACK_SERVER['port'],
                username=PLAYBACK_SERVER['user'],
                password=PLAYBACK_SERVER['password'],
                timeout=10
            )
        except Exception as e:
            return jsonify({'found': False, 'error': f'Connection failed: {str(e)}'})
        
        sftp = ssh.open_sftp()
        file_list = sftp.listdir_attr(PLAYBACK_SERVER['path'])
        
        # Parse and filter files for the requested date
        date_prefix = f"AHS_LOG_{date_str.replace('-', '')}_"
        matching_files = []
        
        for f in file_list:
            if f.filename.startswith(date_prefix) and f.filename.endswith('.dat'):
                # Extract time from filename: AHS_LOG_YYYYMMDD_HHMMSS_AEST.dat
                try:
                    time_part = f.filename.split('_')[3]  # HHMMSS
                    file_hour = int(time_part[0:2])
                    file_minute = int(time_part[2:4])
                    file_second = int(time_part[4:6])
                    
                    file_dt = datetime(
                        requested_dt.year, requested_dt.month, requested_dt.day,
                        file_hour, file_minute, file_second
                    )
                    
                    matching_files.append({
                        'name': f.filename,
                        'size': f.st_size,
                        'datetime': file_dt,
                        'time_str': f"{file_hour:02d}:{file_minute:02d}:{file_second:02d}"
                    })
                except:
                    continue
        
        sftp.close()
        ssh.close()
        
        if not matching_files:
            return jsonify({'found': False, 'error': 'No files found for that date'})
        
        # Sort by datetime
        matching_files.sort(key=lambda x: x['datetime'])
        
        # Find the file that covers the requested time
        # The file timestamp is the START of the recording period
        # So we want the file with timestamp <= requested_time
        selected_file = None
        for i, f in enumerate(matching_files):
            if f['datetime'] <= requested_dt:
                selected_file = f
            else:
                break
        
        # If no file starts before requested time, use the first file
        if not selected_file and matching_files:
            selected_file = matching_files[0]
        
        if selected_file:
            # Calculate the coverage period (approximately 15 minutes)
            covers_from = selected_file['time_str']
            
            # Find next file to determine end time, or add 15 mins
            idx = matching_files.index(selected_file)
            if idx + 1 < len(matching_files):
                covers_to = matching_files[idx + 1]['time_str']
            else:
                # Add approximately 15 minutes
                end_dt = selected_file['datetime'] + timedelta(minutes=15)
                covers_to = end_dt.strftime("%H:%M:%S")
            
            return jsonify({
                'found': True,
                'file': {
                    'name': selected_file['name'],
                    'size': selected_file['size']
                },
                'covers_from': covers_from,
                'covers_to': covers_to
            })
        
        return jsonify({'found': False, 'error': 'Could not find matching file'})
        
    except Exception as e:
        logger.error(f"Find file error: {e}")
        return jsonify({'found': False, 'error': str(e)})

def _download_file_thread(filename, file_size, local_path, remote_path):
    """Background thread for file download with progress tracking"""
    global download_progress

    try:
        # Initialize progress
        download_progress[filename] = {
            'status': 'downloading',
            'progress': 0,
            'total_size': file_size,
            'local_path': str(local_path),
            'error': None
        }

        if not paramiko:
            download_progress[filename]['status'] = 'error'
            download_progress[filename]['error'] = 'SSH library not available'
            return

        # Connect to server
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            PLAYBACK_SERVER['ip'],
            port=PLAYBACK_SERVER['port'],
            username=PLAYBACK_SERVER['user'],
            password=PLAYBACK_SERVER['password'],
            timeout=10
        )

        sftp = ssh.open_sftp()

        # Get actual file size if not provided
        if not file_size:
            try:
                file_attr = sftp.stat(remote_path)
                file_size = file_attr.st_size
                download_progress[filename]['total_size'] = file_size
            except:
                pass

        # Download with callback
        def progress_callback(transferred, total):
            if total > 0:
                percent = int((transferred / total) * 100)
                download_progress[filename]['progress'] = percent

        sftp.get(remote_path, str(local_path), callback=progress_callback)

        sftp.close()
        ssh.close()

        # Mark as complete
        if local_path.exists():
            download_progress[filename]['status'] = 'complete'
            download_progress[filename]['progress'] = 100
        else:
            download_progress[filename]['status'] = 'error'
            download_progress[filename]['error'] = 'File not found after download'

    except Exception as e:
        download_progress[filename]['status'] = 'error'
        download_progress[filename]['error'] = str(e)

@app.route("/api/playback/download-file", methods=["POST"])
def api_playback_download_file():
    """
    Start a file download from the server to the local USB playback folder.
    Returns immediately with download ID. Use /api/playback/download-progress to check status.
    """
    try:
        data = request.get_json()
        filename = data.get('filename')
        file_size = data.get('size', 0)

        if not filename:
            return jsonify({'success': False, 'message': 'Filename required'})

        # OFFLINE MODE: Simulate successful download
        if not is_online_network():
            # Simulate with progress tracking
            global download_progress
            download_progress[filename] = {
                'status': 'complete',
                'progress': 100,
                'total_size': 15728640,
                'local_path': f'USB:/playback/{filename}',
                'error': None
            }
            return jsonify({
                'success': True,
                'message': f'[OFFLINE MODE] Simulated download of {filename}',
                'download_id': filename,
                'offline_mode': True
            })

        # Find local USB path
        from tools.usb_tools import find_tool_on_usb
        result = find_tool_on_usb("frontrunnerV3-3.7.0-076-full", "V3.7.0 Playback Tool.bat")

        if not result:
            return jsonify({'success': False, 'message': 'Playback USB not detected'})

        local_path = Path(result['folder_path']) / 'playback' / filename
        remote_path = PLAYBACK_SERVER['path'] + filename

        # Ensure local directory exists
        local_path.parent.mkdir(parents=True, exist_ok=True)

        if not paramiko:
            return jsonify({'success': False, 'message': 'SSH library not available'})

        # Check if already downloading
        if filename in download_progress and download_progress[filename]['status'] == 'downloading':
            return jsonify({
                'success': True,
                'message': 'Download already in progress',
                'download_id': filename
            })

        # Start download in background thread
        thread = threading.Thread(
            target=_download_file_thread,
            args=(filename, file_size, local_path, remote_path),
            daemon=True
        )
        thread.start()

        return jsonify({
            'success': True,
            'message': 'Download started',
            'download_id': filename
        })

    except Exception as e:
        logger.error(f"Download file error: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route("/api/playback/download-progress/<filename>")
def api_playback_download_progress(filename):
    """Get download progress for a specific file"""
    if filename in download_progress:
        return jsonify(download_progress[filename])
    else:
        return jsonify({
            'status': 'not_found',
            'progress': 0,
            'error': 'Download not found'
        })

@app.route("/api/playback/predict-next-file")
def api_playback_predict_next_file():
    """
    Analyze recent playback files and predict when the next file will be available.
    Returns prediction based on file timestamp patterns.
    """
    try:
        from datetime import datetime, timedelta

        # OFFLINE MODE
        if not is_online_network():
            now = datetime.now()
            next_time = now + timedelta(
                minutes=15 - (now.minute % 15),
                seconds=-now.second,
                microseconds=-now.microsecond
            )

            next_file_name = f"AHS_LOG_{next_time.strftime('%Y%m%d_%H%M00')}_AEST.dat"

            # Add 2-minute buffer for .dat file to be fully written after .log files
            next_time_with_buffer = next_time + timedelta(minutes=2)

            return jsonify({
                'success': True,
                'has_prediction': True,
                'last_file_time': None,
                'next_file_time': next_time_with_buffer.isoformat(),
                'predicted_file_time': next_time.isoformat(),
                'last_file_name': None,
                'next_file_name': next_file_name,
                'countdown_seconds': int((next_time_with_buffer - now).total_seconds()),
                'average_interval_minutes': 15,
                'files_analyzed': 10,
                'confidence': 'high',
                'offline_mode': True
            })

        if not paramiko:
            return jsonify({'success': False, 'error': 'SSH library not available'})

        # Connect to server
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            ssh.connect(
                PLAYBACK_SERVER['ip'],
                port=PLAYBACK_SERVER['port'],
                username=PLAYBACK_SERVER['user'],
                password=PLAYBACK_SERVER['password'],
                timeout=10
            )
        except Exception as e:
            return jsonify({'success': False, 'error': f'Connection failed: {str(e)}'})

        sftp = ssh.open_sftp()

        try:
            file_list = sftp.listdir_attr(PLAYBACK_SERVER['path'])
        except Exception as e:
            sftp.close()
            ssh.close()
            return jsonify({'success': False, 'error': f'Cannot read directory: {str(e)}'})

        sftp.close()
        ssh.close()

        # Parse timestamps + keep filenames
        file_items = []  # list of (dt, filename)

        for f in file_list:
            if f.filename.startswith('AHS_LOG_') and f.filename.endswith('.dat'):
                try:
                    # AHS_LOG_YYYYMMDD_HHMMSS_AEST.dat
                    parts = f.filename.split('_')
                    date_part = parts[2]  # YYYYMMDD
                    time_part = parts[3]  # HHMMSS

                    year = int(date_part[0:4])
                    month = int(date_part[4:6])
                    day = int(date_part[6:8])
                    hour = int(time_part[0:2])
                    minute = int(time_part[2:4])
                    second = int(time_part[4:6])

                    dt = datetime(year, month, day, hour, minute, second)
                    file_items.append((dt, f.filename))
                except Exception:
                    continue

        if len(file_items) < 2:
            return jsonify({
                'success': True,
                'has_prediction': False,
                'error': 'Not enough files to predict pattern (need at least 2)'
            })

        # Sort by time
        file_items.sort(key=lambda x: x[0])
        file_timestamps = [x[0] for x in file_items]

        # Calculate intervals in minutes
        intervals = []
        for i in range(1, len(file_timestamps)):
            interval = (file_timestamps[i] - file_timestamps[i - 1]).total_seconds() / 60.0
            intervals.append(interval)

        recent_intervals = intervals[-20:] if len(intervals) > 20 else intervals
        avg_interval = sum(recent_intervals) / len(recent_intervals)

        # Most recent file info
        last_file_time, last_file_name = file_items[-1]

        # Predict next file time
        predicted_next = last_file_time + timedelta(minutes=avg_interval)

        # Snap seconds to 00 (matches your naming convention / cadence)
        predicted_next = predicted_next.replace(second=0, microsecond=0)

        next_file_name = f"AHS_LOG_{predicted_next.strftime('%Y%m%d_%H%M00')}_AEST.dat"

        # Add buffer time: AHS_EVENTS/INDEX/CACHE .log files are written first,
        # then the .dat file is created. Add 2 minutes to ensure .dat is fully written.
        predicted_next_with_buffer = predicted_next + timedelta(minutes=2)

        # Countdown (allow negative so UI can show overdue)
        now = datetime.now()
        countdown_seconds = int((predicted_next_with_buffer - now).total_seconds())

        # Confidence from variance
        interval_variance = sum((i - avg_interval) ** 2 for i in recent_intervals) / len(recent_intervals)
        if interval_variance < 1:
            confidence = 'high'
        elif interval_variance < 5:
            confidence = 'medium'
        else:
            confidence = 'low'

        return jsonify({
            'success': True,
            'has_prediction': True,
            'last_file_time': last_file_time.isoformat(),
            'next_file_time': predicted_next_with_buffer.isoformat(),  # Return buffered time for UI countdown
            'predicted_file_time': predicted_next.isoformat(),  # Actual file timestamp (for reference)
            'last_file_name': last_file_name,
            'next_file_name': next_file_name,
            'countdown_seconds': countdown_seconds,
            'average_interval_minutes': round(avg_interval, 1),
            'files_analyzed': len(file_timestamps),
            'confidence': confidence,
            'is_overdue': countdown_seconds < 0
        })

    except Exception as e:
        logger.error(f"Predict next file error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route("/api/playback/detect-log-files")
def api_playback_detect_log_files():
    """
    Detect auxiliary .log files (EVENTS, INDEX, CACHE) on the server.
    These indicate a .dat file is currently being written with the SAME timestamp.
    Returns the timestamp from the .log files so we can download the matching .dat file.

    If playback monitor is running, uses cached data for instant response.
    Otherwise, creates new SSH connection.
    """
    try:
        # OFFLINE MODE
        if not is_online_network():
            return jsonify({
                'success': False,
                'error': 'Offline mode - cannot detect log files'
            })

        # USE CACHED DATA if monitor is running and connected
        if playback_monitor['running'] and playback_monitor['connected'] and playback_monitor['pending_file']:
            pending = playback_monitor['pending_file']

            # Calculate countdown based on timestamp
            try:
                timestamp_str = pending['timestamp']  # Format: YYYYMMDD_HHMMSS
                date_part, time_part = timestamp_str.split('_')

                year = int(date_part[0:4])
                month = int(date_part[4:6])
                day = int(date_part[6:8])
                hour = int(time_part[0:2])
                minute = int(time_part[2:4])
                second = int(time_part[4:6])

                dt = datetime(year, month, day, hour, minute, second)
                now = datetime.now()
                elapsed_seconds = int((now - dt).total_seconds())
                estimated_ready_time = dt + timedelta(minutes=2)
                countdown_seconds = int((estimated_ready_time - now).total_seconds())

                return jsonify({
                    'success': True,
                    'has_log_files': True,
                    'dat_exists': pending['dat_exists'],
                    'log_files_count': len(playback_monitor['log_files']),
                    'most_recent_log': pending['log_file'],
                    'timestamp': dt.isoformat(),
                    'predicted_filename': pending['predicted_dat'],
                    'elapsed_seconds': elapsed_seconds,
                    'countdown_seconds': max(0, countdown_seconds),
                    'estimated_ready_time': estimated_ready_time.isoformat(),
                    'is_ready': countdown_seconds <= 0 or pending['dat_exists'],
                    'from_cache': True  # Indicate this came from cached data
                })
            except Exception as cache_err:
                logger.warning(f"Error parsing cached data: {cache_err}")
                # Fall through to SSH connection below

        # FALLBACK: Create new SSH connection if monitor not running
        if not paramiko:
            return jsonify({'success': False, 'error': 'SSH library not available'})

        # Connect to server
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            ssh.connect(
                PLAYBACK_SERVER['ip'],
                port=PLAYBACK_SERVER['port'],
                username=PLAYBACK_SERVER['user'],
                password=PLAYBACK_SERVER['password'],
                timeout=10
            )
        except Exception as e:
            return jsonify({'success': False, 'error': f'Connection failed: {str(e)}'})

        sftp = ssh.open_sftp()

        try:
            file_list = sftp.listdir_attr(PLAYBACK_SERVER['path'])
        except Exception as e:
            sftp.close()
            ssh.close()
            return jsonify({'success': False, 'error': f'Cannot read directory: {str(e)}'})

        sftp.close()
        ssh.close()

        # Look for auxiliary .log files (EVENTS, INDEX, CACHE)
        log_files = []
        for f in file_list:
            fname = f.filename
            if fname.startswith('AHS_') and fname.endswith('_AEST.log'):
                # Check if it's one of the auxiliary files
                if 'EVENTS_' in fname or 'INDEX_' in fname or 'CACHE_' in fname:
                    log_files.append((fname, f.st_mtime))

        if not log_files:
            return jsonify({
                'success': True,
                'has_log_files': False,
                'message': 'No .log files detected'
            })

        # Sort by modification time to get the most recent
        log_files.sort(key=lambda x: x[1], reverse=True)
        most_recent_log = log_files[0][0]

        # Extract timestamp from the most recent log file
        # Format: AHS_EVENTS_YYYYMMDD_HHMMSS_AEST.log
        try:
            parts = most_recent_log.split('_')
            # Find the date and time parts
            date_part = None
            time_part = None

            for i in range(len(parts) - 2):
                if len(parts[i]) == 8 and parts[i].isdigit():  # YYYYMMDD
                    date_part = parts[i]
                    time_part = parts[i + 1]  # HHMMSS
                    break

            if not date_part or not time_part:
                raise ValueError("Could not find date/time in filename")

            year = int(date_part[0:4])
            month = int(date_part[4:6])
            day = int(date_part[6:8])
            hour = int(time_part[0:2])
            minute = int(time_part[2:4])
            second = int(time_part[4:6])

            dt = datetime(year, month, day, hour, minute, second)

        except Exception as parse_err:
            return jsonify({
                'success': False,
                'error': f'Could not parse timestamp from log file: {str(parse_err)}'
            })

        # Construct the expected .dat filename with THE SAME TIMESTAMP
        predicted_dat_filename = f"AHS_LOG_{date_part}_{time_part}_AEST.dat"

        # Check if .dat file already exists
        dat_exists = any(
            f.filename == predicted_dat_filename
            for f in file_list
        )

        # Calculate time until .dat should be ready
        # (typically 2 minutes after .log files appear)
        now = datetime.now()
        elapsed_seconds = int((now - dt).total_seconds())
        estimated_ready_time = dt + timedelta(minutes=2)
        countdown_seconds = int((estimated_ready_time - now).total_seconds())

        return jsonify({
            'success': True,
            'has_log_files': True,
            'dat_exists': dat_exists,
            'log_files_count': len(log_files),
            'most_recent_log': most_recent_log,
            'timestamp': dt.isoformat(),
            'predicted_filename': predicted_dat_filename,
            'elapsed_seconds': elapsed_seconds,
            'countdown_seconds': max(0, countdown_seconds),  # Don't show negative
            'estimated_ready_time': estimated_ready_time.isoformat(),
            'is_ready': countdown_seconds <= 0 or dat_exists
        })

    except Exception as e:
        logger.error(f"Detect log files error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route("/api/playback/find-files")
def api_playback_find_files():
    """
    Find playback files for a date and time range.
    Supports both single time and time range modes.
    """
    try:
        date_str = request.args.get('date')  # YYYY-MM-DD
        time_from = request.args.get('time_from')  # HH:MM
        time_to = request.args.get('time_to')  # HH:MM
        mode = request.args.get('mode', 'single')  # single or range

        if not date_str:
            return jsonify({'files': [], 'error': 'Date required'})

        if not time_from:
            return jsonify({'files': [], 'error': 'Time required'})

        # Parse times
        try:
            from_hour, from_minute = map(int, time_from.split(':'))
            if time_to:
                to_hour, to_minute = map(int, time_to.split(':'))
            else:
                to_hour, to_minute = from_hour, from_minute
        except:
            return jsonify({'files': [], 'error': 'Invalid time format'})

        # OFFLINE MODE: Return mock files in the time range
        if not is_online_network():
            mock_files = []
            current_hour = from_hour
            current_minute = (from_minute // 15) * 15  # Round to 15-min block

            while (current_hour < to_hour) or (current_hour == to_hour and current_minute <= to_minute):
                filename = f"AHS_LOG_{date_str.replace('-', '')}_{current_hour:02d}{current_minute:02d}00_AEST.dat"
                mock_files.append({
                    'name': filename,
                    'size': 15728640,
                    'time_str': f"{current_hour:02d}:{current_minute:02d}:00"
                })
                # Increment by 15 minutes
                current_minute += 15
                if current_minute >= 60:
                    current_minute = 0
                    current_hour += 1

            return jsonify({'files': mock_files, 'count': len(mock_files), 'offline_mode': True})

        if not paramiko:
            return jsonify({'files': [], 'error': 'SSH library not available'})

        # Connect to server
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            ssh.connect(
                PLAYBACK_SERVER['ip'],
                port=PLAYBACK_SERVER['port'],
                username=PLAYBACK_SERVER['user'],
                password=PLAYBACK_SERVER['password'],
                timeout=10
            )
        except Exception as e:
            return jsonify({'files': [], 'error': f'Connection failed: {str(e)}'})
        
        sftp = ssh.open_sftp()
        
        try:
            file_list = sftp.listdir_attr(PLAYBACK_SERVER['path'])
        except Exception as e:
            sftp.close()
            ssh.close()
            return jsonify({'files': [], 'error': f'Cannot read directory: {str(e)}'})
        
        # Filter files for the requested date
        date_prefix = f"AHS_LOG_{date_str.replace('-', '')}_"
        matching_files = []
        
        for f in file_list:
            if f.filename.startswith(date_prefix) and f.filename.endswith('.dat'):
                try:
                    # Extract time from filename: AHS_LOG_YYYYMMDD_HHMMSS_AEST.dat
                    time_part = f.filename.split('_')[3]  # HHMMSS
                    file_hour = int(time_part[0:2])
                    file_minute = int(time_part[2:4])
                    
                    # Convert to minutes for easy comparison
                    file_mins = file_hour * 60 + file_minute
                    from_mins = from_hour * 60 + from_minute
                    to_mins = to_hour * 60 + to_minute
                    
                    # For single mode, find the file that covers the requested time
                    # The file timestamp is the START of the recording period (~15 min blocks)
                    if mode == 'single':
                        # File should start at or before requested time, and end after it
                        # Assuming 15-minute blocks, the file covers file_mins to file_mins + 15
                        if file_mins <= from_mins < file_mins + 20:  # 20 min window to be safe
                            matching_files.append({
                                'name': f.filename,
                                'size': f.st_size,
                                'time_mins': file_mins
                            })
                    else:
                        # Range mode - include all files within the time range
                        # Include file if it overlaps with the requested range
                        file_end_mins = file_mins + 15
                        if file_mins <= to_mins and file_end_mins >= from_mins:
                            matching_files.append({
                                'name': f.filename,
                                'size': f.st_size,
                                'time_mins': file_mins
                            })
                except:
                    continue
        
        sftp.close()
        ssh.close()
        
        # Sort by time
        matching_files.sort(key=lambda x: x['time_mins'])
        
        # For single mode, just return the best match (closest to requested time)
        if mode == 'single' and matching_files:
            # Find the file that best covers the requested time
            from_mins = from_hour * 60 + from_minute
            best_file = min(matching_files, key=lambda x: abs(x['time_mins'] - from_mins))
            matching_files = [best_file]
        
        # Remove time_mins from response
        result_files = [{'name': f['name'], 'size': f['size']} for f in matching_files]
        
        return jsonify({
            'files': result_files,
            'count': len(result_files)
        })
        
    except Exception as e:
        logger.error(f"Find files error: {e}")
        return jsonify({'files': [], 'error': str(e)})

@app.route("/api/playback/delete-file", methods=["POST"])
def api_playback_delete_file():
    """
    Delete a playback file from the local USB drive.
    """
    try:
        data = request.get_json()
        filename = data.get('filename')
        
        if not filename:
            return jsonify({'success': False, 'message': 'Filename required'})
        
        # Validate filename to prevent path traversal
        if '..' in filename or '/' in filename or '\\' in filename:
            return jsonify({'success': False, 'message': 'Invalid filename'})
        
        # Find local USB path
        from tools.usb_tools import find_tool_on_usb
        result = find_tool_on_usb("frontrunnerV3-3.7.0-076-full", "V3.7.0 Playback Tool.bat")
        
        if not result:
            return jsonify({'success': False, 'message': 'Playback USB not detected'})
        
        file_path = Path(result['folder_path']) / 'playback' / filename
        
        if not file_path.exists():
            return jsonify({'success': False, 'message': 'File not found'})
        
        # Delete the file
        file_path.unlink()
        
        return jsonify({
            'success': True,
            'message': f'Deleted {filename}'
        })
        
    except Exception as e:
        logger.error(f"Delete file error: {e}")
        return jsonify({'success': False, 'message': str(e)})

# ========================================
# PLAYBACK DIRECT DOWNLOAD (for remote PCs)
# ========================================
# These routes stream files directly to the user's browser for download.
# Remote PCs download files to their local PC, not to USB on the server.
# This replaces the old USB-based workflow where files were stored on server USB.

@app.route("/download/playback/<filename>")
def download_playback_file(filename):
    """
    Stream playback file directly to remote PC browser.
    Downloads from server via SFTP and streams to user.
    """
    try:
        # Validate filename to prevent path traversal
        if '..' in filename or '/' in filename or '\\' in filename:
            return "Invalid filename", 400

        # Validate it's a playback file
        if not filename.startswith('AHS_LOG_') or not filename.endswith('.dat'):
            return "Invalid playback file", 400

        # OFFLINE MODE: Return dummy file
        if not is_online_network():
            from io import BytesIO
            dummy_data = b'OFFLINE MODE - Test playback file data\n' * 100
            return send_file(
                BytesIO(dummy_data),
                as_attachment=True,
                download_name=filename,
                mimetype='application/octet-stream'
            )

        if not paramiko:
            return "SSH library not available", 500

        # Connect to server
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            ssh.connect(
                PLAYBACK_SERVER['ip'],
                port=PLAYBACK_SERVER['port'],
                username=PLAYBACK_SERVER['user'],
                password=PLAYBACK_SERVER['password'],
                timeout=10
            )
        except Exception as e:
            logger.error(f"SSH connection failed: {e}")
            return f"Server connection failed: {str(e)}", 500

        sftp = ssh.open_sftp()
        remote_path = PLAYBACK_SERVER['path'] + filename

        # Check if file exists
        try:
            file_attr = sftp.stat(remote_path)
            file_size = file_attr.st_size
        except:
            sftp.close()
            ssh.close()
            return "File not found on server", 404

        # Use a temporary file to stream
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.dat') as tmp_file:
            temp_path = tmp_file.name

            try:
                # Download to temp file
                sftp.get(remote_path, temp_path)
                sftp.close()
                ssh.close()

                # Send file to user and delete temp file after
                return send_file(
                    temp_path,
                    as_attachment=True,
                    download_name=filename,
                    mimetype='application/octet-stream'
                )
            except Exception as e:
                sftp.close()
                ssh.close()
                # Clean up temp file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                logger.error(f"File download error: {e}")
                return f"Download failed: {str(e)}", 500

    except Exception as e:
        logger.error(f"Playback download error: {e}")
        return str(e), 500

# /download/camstudio, /download/frontrunner moved to app/blueprints/downloads.py

# ========================================
# PTX EQUIPMENT MANAGEMENT APIS
# ========================================

@app.route("/api/ptx_reboot", methods=["POST"])
def api_ptx_reboot():
    """Reboot PTX equipment via SSH"""
    data = request.get_json()
    ip_address = data.get('ip_address')
    equipment_id = data.get('equipment_id', 'Unknown')
    
    if not ip_address:
        return jsonify({'success': False, 'message': 'IP address required'}), 400
    
    try:
        # Simulate reboot in offline mode
        if not is_online_network() or not paramiko:
            return jsonify({
                'success': True,
                'message': f'SIMULATED: Reboot command sent to {equipment_id}',
                'ptx_type': 'Simulated',
                'details': 'Offline testing mode - reboot simulated'
            })
        
        # Real reboot implementation would go here
        return jsonify({
            'success': False,
            'message': 'PTX reboot functionality requires paramiko library',
            'details': 'Install paramiko for SSH functionality'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Reboot failed: {str(e)}'}), 500

@app.route("/api/ptx_status", methods=["POST"])
def api_ptx_status():
    """Check PTX equipment status via ping and SSH"""
    data = request.get_json()
    ip_address = data.get('ip_address')

    if not ip_address:
        return jsonify({'success': False, 'message': 'IP address required'}), 400

    try:
        # OFFLINE MODE: Return simulated online status
        if not is_online_network():
            return jsonify({
                'success': True,
                'ping_status': True,
                'ping_time': 0.025,  # Simulated 25ms ping
                'ssh_status': True,
                'ssh_details': 'SSH available (simulated)',
                'overall_status': 'Online',
                'offline_mode': True
            })

        # Test ping connectivity
        ping_result = None
        ping_status = False

        if ping3:
            ping_result = ping3.ping(ip_address, timeout=3)
            ping_status = ping_result is not None
        else:
            # Fallback for testing
            ping_status = True
            ping_result = 0.05  # Simulated ping time

        # Simulate SSH status for offline mode
        ssh_status = ping_status  # Assume SSH available if ping works
        ssh_details = "SSH status simulated" if not paramiko else "SSH check available"
        
        return jsonify({
            'success': True,
            'ping_status': ping_status,
            'ping_time': ping_result if ping_result else None,
            'ssh_status': ssh_status,
            'ssh_details': ssh_details,
            'overall_status': 'Online' if ping_status and ssh_status else 'Offline' if not ping_status else 'Limited'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Status check failed: {str(e)}'}), 500
    
# ========================================
# T1 LEGACY TOOLS
# ========================================
# terminal_sessions aliased from app.state above

class TerminalSession:
    """Manages a T1_Tools.bat terminal session (legacy tool)"""
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.process: Optional[subprocess.Popen] = None
        self.output_queue: queue.Queue = queue.Queue()
        self.running = False
        self.offline_mode = False
        
    def start(self) -> tuple[bool, str]:
        """Start T1_Tools.bat process or offline simulation"""

        # First, search for T1_Tools.bat (works both online and offline)
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))

        # Search in multiple locations including all drives
        possible_paths = [
            os.path.join(base_dir, 'T1_Tools_Legacy', 'bin', 'T1_Tools.bat'),
            os.path.join(base_dir, 'T1_Tools.bat'),
            os.path.join(TOOLS_DIR, '..', 'T1_Tools_Legacy', 'bin', 'T1_Tools.bat')
        ]

        # Also search all removable drives (D: through Z:)
        import string
        for drive_letter in string.ascii_uppercase[3:]:  # D through Z
            drive_path = f"{drive_letter}:/T1_Tools_Legacy/bin/T1_Tools.bat"
            possible_paths.append(drive_path)
            drive_path2 = f"{drive_letter}:/T1_Tools.bat"
            possible_paths.append(drive_path2)

        bat_file = None
        for path in possible_paths:
            if os.path.exists(path):
                bat_file = path
                print(f"[LEGACY] Found T1_Tools.bat at: {path}")
                break

        # If USB not found, fall back to simulation mode
        if not bat_file:
            self.running = True
            self.offline_mode = True
            self.output_queue.put("[SIMULATION MODE] T1_Tools.bat not found on USB\n")
            self.output_queue.put("Using simulated terminal. Type 'help' for commands.\n")
            return True, "Simulation mode (USB not detected)"
        
        try:
            if platform.system() == 'Windows':
                self.process = subprocess.Popen(
                    [bat_file],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            else:
                return False, "Terminal only supported on Windows"
            
            self.running = True
            output_thread = threading.Thread(target=self._read_output, daemon=True)
            output_thread.start()
            return True, "Terminal started successfully"
            
        except Exception as e:
            return False, str(e)
    
    def _read_output(self) -> None:
        """Read output from process in background thread"""
        try:
            while self.running and self.process and self.process.poll() is None:
                if self.process.stdout is not None:
                    line = self.process.stdout.readline()
                    if line:
                        self.output_queue.put(line.rstrip('\n\r'))
        except Exception as e:
            logger.error(f"Terminal output read error: {e}")
        finally:
            self.running = False
    
    def send_command(self, command: str) -> bool:
        """Send command to terminal or simulate in offline mode"""
        # Offline mode - simulate command responses
        if self.offline_mode:
            self.output_queue.put(f"\n> {command}\n")
            self._simulate_command(command.strip().lower())
            return True

        # Online mode - send to actual process
        if self.process and self.process.poll() is None:
            try:
                if self.process.stdin is not None:
                    self.process.stdin.write(command + '\n')
                    self.process.stdin.flush()
                    return True
            except Exception as e:
                logger.error(f"Terminal command send error: {e}")
                return False
        return False

    def _simulate_command(self, command: str):
        """Simulate command responses in offline mode"""
        if command == 'help':
            self.output_queue.put("Available commands:\n")
            self.output_queue.put("  help     - Show this help message\n")
            self.output_queue.put("  status   - Show system status\n")
            self.output_queue.put("  clear    - Clear terminal\n")
            self.output_queue.put("\n[NOTE] Offline mode - commands are simulated\n")
        elif command == 'status':
            self.output_queue.put("System Status:\n")
            self.output_queue.put("  Mode: OFFLINE (Simulation)\n")
            self.output_queue.put("  Tools: T1_Tools_Legacy (Simulated)\n")
            self.output_queue.put("  Status: Ready\n")
        elif command == 'clear':
            self.output_queue.put("\033[2J\033[H")  # ANSI clear screen
        elif command:
            self.output_queue.put(f"[OFFLINE] Simulated response for: {command}\n")
            self.output_queue.put("Command executed successfully (simulation)\n")
        else:
            self.output_queue.put("\n")
    
    def get_output(self) -> str:
        """Get accumulated output"""
        lines = []
        try:
            while not self.output_queue.empty():
                lines.append(self.output_queue.get_nowait())
        except queue.Empty:
            pass
        return '\n'.join(lines)
    
    def is_running(self) -> bool:
        """Check if process is still running"""
        return self.process is not None and self.process.poll() is None
    
    def stop(self) -> None:
        """Stop the terminal session"""
        self.running = False
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except Exception:
                self.process.kill()

# /autotech, /legacy, /database, /t1-tools-help moved to app/blueprints/info_pages.py

# get_autotech_client_folder imported from app.utils above

@app.route('/download-client-setup')
def download_client_setup():
    """
    Download AutoTech Client installer batch file.
    Pure batch - no Python or dependencies required on target PC.
    Serves the file over the network from the USB drive to any connected PC.
    """
    client_folder, error = get_autotech_client_folder()

    if error or not client_folder:
        return render_template('error.html',
                             error_title="Installer Not Found",
                             error_message=error or "AutoTech Client folder not found.",
                             online=is_online_network(),
                             gateway_ip=GATEWAY_IP), 404

    # Try batch installer first (preferred - no dependencies)
    installer_path = os.path.join(client_folder, "Install_AutoTech_Client.bat")
    download_name = "Install_AutoTech_Client.bat"

    # Fallback to EXE if batch not found
    if not os.path.exists(installer_path):
        installer_path = os.path.join(client_folder, "AutoTech_Client_Installer.exe")
        download_name = "AutoTech_Client_Installer.exe"

    if not os.path.exists(installer_path):
        return render_template('error.html',
                             error_title="Installer Not Found",
                             error_message="Installer not found. Run BUILD_PYTHON_INSTALLER.bat option 5 to deploy.",
                             online=is_online_network(),
                             gateway_ip=GATEWAY_IP), 404

    return send_file(
        installer_path,
        as_attachment=True,
        download_name=download_name
    )

@app.route('/download-client-package')
def download_client_package():
    """
    Download the complete AutoTech Client package as a ZIP file.
    Includes installer EXE + tools + scripts - everything needed to install on any PC.
    Serves over the network from USB - user extracts ZIP and runs installer.
    """
    import zipfile
    from io import BytesIO

    client_folder, error = get_autotech_client_folder()

    if error or not client_folder:
        return render_template('error.html',
                             error_title="Package Not Found",
                             error_message=error or "AutoTech Client folder not found.",
                             online=is_online_network(),
                             gateway_ip=GATEWAY_IP), 404

    # Verify required folders exist
    tools_folder = os.path.join(client_folder, "tools")
    scripts_folder = os.path.join(client_folder, "scripts")

    if not os.path.exists(tools_folder) or not os.path.exists(scripts_folder):
        return render_template('error.html',
                             error_title="Package Incomplete",
                             error_message="The autotech_client folder is missing tools or scripts. Run BUILD_PYTHON_INSTALLER.bat option 5 to deploy the complete package.",
                             online=is_online_network(),
                             gateway_ip=GATEWAY_IP), 404

    # Create ZIP file in memory containing everything
    memory_file = BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(client_folder):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, client_folder)
                zf.write(file_path, arcname)

    memory_file.seek(0)

    return send_file(
        memory_file,
        mimetype='application/zip',
        as_attachment=True,
        download_name='AutoTech_Client_Package.zip'
    )

@app.route('/live-install-client')
def live_install_client():
    """
    Show page with instructions and path for running installer directly from USB.
    User can copy the path and run it, or use file:// link.
    """
    client_folder, error = get_autotech_client_folder()

    if error or not client_folder:
        return render_template('error.html',
                             error_title="Installer Not Found",
                             error_message=error or "AutoTech Client folder not found. Make sure the AUTOTECH USB is connected.",
                             online=is_online_network(),
                             gateway_ip=GATEWAY_IP), 404

    installer_path = os.path.join(client_folder, "Install_AutoTech_Client.bat")

    if not os.path.exists(installer_path):
        return render_template('error.html',
                             error_title="Installer Not Found",
                             error_message=f"Install_AutoTech_Client.bat not found in {client_folder}. Run BUILD_WEBSERVER.bat to rebuild.",
                             online=is_online_network(),
                             gateway_ip=GATEWAY_IP), 404

    # Convert to Windows path format for display
    installer_path_display = installer_path.replace('/', '\\')

    html_content = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Live Install - AutoTech Client</title>
        <link rel="stylesheet" href="/static/style.css">
        <style>
            .install-container {{
                max-width: 700px;
                margin: 40px auto;
                padding: 30px;
                background: var(--theme-card-bg);
                border-radius: 12px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            }}
            .install-container h1 {{
                color: var(--theme-accent);
                margin-bottom: 20px;
            }}
            .path-box {{
                background: #1a1a2e;
                border: 1px solid var(--theme-accent);
                border-radius: 8px;
                padding: 15px;
                font-family: monospace;
                font-size: 14px;
                word-break: break-all;
                margin: 20px 0;
                color: #00ff88;
            }}
            .copy-btn {{
                background: linear-gradient(135deg, var(--theme-accent) 0%, #e67e00 100%);
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                cursor: pointer;
                font-size: 16px;
                margin-right: 10px;
            }}
            .copy-btn:hover {{
                transform: translateY(-2px);
            }}
            .back-btn {{
                background: #555;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                cursor: pointer;
                font-size: 16px;
                text-decoration: none;
            }}
            .steps {{
                background: #2a2a3e;
                border-radius: 8px;
                padding: 20px;
                margin: 20px 0;
            }}
            .steps ol {{
                margin: 0;
                padding-left: 20px;
            }}
            .steps li {{
                margin: 10px 0;
                color: var(--theme-text);
            }}
            .success-msg {{
                color: #00ff88;
                display: none;
                margin-left: 10px;
            }}
        </style>
    </head>
    <body>
        <div class="install-container">
            <h1>⚡ Live Install from USB</h1>
            <p>The installer is available at the following path:</p>

            <div class="path-box" id="installerPath">{installer_path_display}</div>

            <button class="copy-btn" onclick="copyPath()">📋 Copy Path</button>
            <a href="/autotech" class="back-btn">← Back to T1 Legacy</a>
            <span class="success-msg" id="copySuccess">✓ Copied!</span>

            <div class="steps">
                <h3>Installation Steps:</h3>
                <ol>
                    <li>Open <strong>File Explorer</strong> on the target PC</li>
                    <li>Navigate to the USB drive path above (or paste the copied path)</li>
                    <li>Right-click <strong>Install_AutoTech_Client.bat</strong></li>
                    <li>Select <strong>"Run as administrator"</strong></li>
                    <li>Follow the on-screen prompts</li>
                </ol>
            </div>

            <p style="color: var(--theme-text-muted); font-size: 14px;">
                <strong>Note:</strong> The target PC must have network access to this USB drive.
                If not accessible, use the ZIP download option instead.
            </p>
        </div>

        <script>
            function copyPath() {{
                const path = document.getElementById('installerPath').textContent;
                navigator.clipboard.writeText(path).then(() => {{
                    const msg = document.getElementById('copySuccess');
                    msg.style.display = 'inline';
                    setTimeout(() => {{ msg.style.display = 'none'; }}, 2000);
                }});
            }}
        </script>
    </body>
    </html>
    '''
    return html_content

@app.route('/api/check-client-installed')
def api_check_client_installed():
    """
    Returns server version for comparison.
    Also returns client IP for tracking purposes.
    """
    # Get server version - check AutoTech/scripts/VERSION first, then folder root
    server_version = None
    server_version_file, _ = get_autotech_client_folder()
    if server_version_file:
        version_path = os.path.join(server_version_file, "AutoTech", "scripts", "VERSION")
        if not os.path.exists(version_path):
            version_path = os.path.join(server_version_file, "VERSION")
        if os.path.exists(version_path):
            try:
                with open(version_path, 'r') as f:
                    server_version = f.read().strip()
            except:
                pass

    # Get client info
    client_ip = request.remote_addr
    user_agent = request.headers.get('User-Agent', 'Unknown')

    return jsonify({
        'server_version': server_version or "1.1.1",
        'client_ip': client_ip,
        'user_agent': user_agent
    })

@app.route('/api/register-client', methods=['POST'])
def api_register_client():
    """
    Called when client installation test succeeds.
    Registers client with server to track active installations.
    """
    data = request.get_json() or {}
    client_version = data.get('client_version', '1.1.1')
    test_success = data.get('test_success', False)

    # Get client details
    client_ip = request.remote_addr
    user_agent = request.headers.get('User-Agent', 'Unknown')
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Log client registration
    log_client(
        'info',
        'registration',
        format_client_registration(client_ip, client_version, user_agent, test_success)
    )

    # Log to console (could be stored in database later)
    print(f"\n{'='*60}")
    print(f"[CLIENT REGISTERED]")
    print(f"  IP Address: {client_ip}")
    print(f"  Version: v{client_version}")
    print(f"  Timestamp: {timestamp}")
    print(f"  User Agent: {user_agent[:50]}...")
    print(f"  Test Success: {test_success}")
    print(f"{'='*60}\n")

    return jsonify({
        'success': True,
        'message': f'Client registered: {client_ip}',
        'client_ip': client_ip,
        'timestamp': timestamp
    })

@app.route('/api/launch-batch-tool', methods=['POST'])
def api_launch_batch_tool():
    """Launch a batch file in CMD window with password auto-filled"""
    try:
        data = request.get_json()
        tool_name = data.get('tool', '').lower()
        password = data.get('password', '')

        # Map tool names to batch file paths
        batch_files = {
            'ip-finder': 'legacy_batch_scripts/IP_Finder.bat',
            'ptx-uptime': 'legacy_batch_scripts/PTX_Uptime.bat',
            'mineview-sessions': 'legacy_batch_scripts/MineView_Session.bat',
            'start-vnc': 'legacy_batch_scripts/Start_VNC.bat',
            'ptx-health': 'legacy_batch_scripts/PTXC_Health_Check.bat',
            'avi-reboot': 'legacy_batch_scripts/AVI_MM2_Reboot.bat',
            'watchdog': 'legacy_batch_scripts/PTX-AVI_Watchdog_SingleDeploy.bat',
            'koa-data': 'legacy_batch_scripts/LIVE_KOA_DataCheck.bat',
            'speed-limit': 'legacy_batch_scripts/Latest_SpeedLimit_DataCheck.bat',
            'linux-perf': 'legacy_batch_scripts/Linux_Health_Check.bat',
            'component-tracking': 'legacy_batch_scripts/ComponentTracking.bat',
            'log-downloader': 'legacy_batch_scripts/Log_Downloader.bat',
            't1-tools': 'legacy_batch_scripts/T1_Tools_Launch.bat'
        }

        if tool_name not in batch_files:
            return jsonify({
                'success': False,
                'message': f'Unknown tool: {tool_name}'
            })

        batch_file = os.path.join(BASE_DIR, batch_files[tool_name])

        if not os.path.exists(batch_file):
            return jsonify({
                'success': False,
                'message': f'Batch file not found: {batch_file}'
            })

        # Get correct plink path from web server
        plink_path = CLIENT_PLINK_PATH
        if not os.path.exists(plink_path):
            return jsonify({
                'success': False,
                'message': f'plink.exe not found at: {plink_path}. Install AutoTech Client or check USB connection.'
            })

        # Create a temporary wrapper batch file that uses correct plink path and auto-fills password
        temp_dir = os.path.join(BASE_DIR, 'temp')
        os.makedirs(temp_dir, exist_ok=True)

        temp_batch = os.path.join(temp_dir, f'launch_{tool_name}_{int(time.time())}.bat')

        with open(temp_batch, 'w') as f:
            f.write(f'@echo off\n')
            f.write(f'SET PLINK_PATH="{plink_path}"\n')
            f.write(f'SET PASSWORD={password}\n')
            f.write(f'echo {password}| "{batch_file}"\n')
            # Keep window open after script completes
            f.write(f'pause\n')

        # Launch temp batch file in new CMD window
        subprocess.Popen(
            ['cmd', '/c', 'start', 'cmd', '/k', temp_batch],
            creationflags=subprocess.CREATE_NEW_CONSOLE if platform.system() == 'Windows' else 0
        )

        logger.info(f"Launched batch tool: {tool_name} with auto-filled password and correct plink path")

        return jsonify({
            'success': True,
            'message': f'Launched {tool_name} in CMD window'
        })

    except Exception as e:
        logger.error(f"Error launching batch tool: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        })

@app.route('/api/find-equipment-ip', methods=['POST'])
def api_find_equipment_ip():
    """Find equipment IP address for terminal display"""
    try:
        data = request.get_json()
        equipment = data.get('equipment_id', '').strip().upper()

        if not equipment:
            return jsonify({
                'success': False,
                'error': 'Equipment ID is required'
            })

        # Get MMS credentials
        mms_server = '10.110.19.107'
        mms_user = 'mms'
        mms_password = session.get('mms_password', '')

        if not mms_password:
            return jsonify({
                'success': False,
                'error': 'MMS password not found. Please log in again.'
            })

        # Get plink path
        plink_path = CLIENT_PLINK_PATH
        if not os.path.exists(plink_path):
            return jsonify({
                'success': False,
                'error': f'plink.exe not found at: {plink_path}. Install AutoTech Client or check USB connection.'
            })

        # Run IP finder command
        ip_finder_cmd = f"/home/mms/bin/remote_check/Random/MySQL/ip_export.sh {equipment}"

        ip_lookup_plink = [
            plink_path,
            '-batch',
            '-t',
            f'{mms_user}@{mms_server}',
            '-pw', mms_password,
            ip_finder_cmd
        ]

        result = subprocess.run(
            ip_lookup_plink,
            capture_output=True,
            text=True,
            timeout=30,
            creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == 'Windows' else 0
        )

        # Parse the output to extract IP and status
        equipment_ip = None
        equipment_status = 'unknown'
        output_lines = []

        for line in result.stdout.split('\n'):
            if line.strip():
                output_lines.append(line)

                if 'PTX IP is:' in line:
                    equipment_ip = line.split('PTX IP is:')[1].strip()
                elif '|' in line and not line.startswith('+') and 'network_ip' not in line:
                    # Parse table row: | AHG69 | eqmt_lv | LV Single Cab | 10.110.21.87 |
                    parts = [p.strip() for p in line.split('|') if p.strip()]
                    if len(parts) >= 4:
                        equipment_ip = parts[3]  # 4th column is network_ip

                if 'Vehicle is Online' in line or 'Equipment is Online' in line:
                    equipment_status = 'ONLINE'
                elif 'Vehicle is Offline' in line or 'Equipment is Offline' in line:
                    equipment_status = 'OFFLINE'

        # Format output for terminal display
        formatted_output = '\n'.join(output_lines)

        if equipment_ip:
            formatted_output += f'\n\n[RESULT] Equipment: {equipment}\n'
            formatted_output += f'[RESULT] IP Address: {equipment_ip}\n'
            formatted_output += f'[RESULT] Status: {equipment_status}'
        else:
            formatted_output += f'\n\n[ERROR] Could not find IP address for equipment: {equipment}'

        return jsonify({
            'success': True,
            'output': formatted_output,
            'equipment_ip': equipment_ip,
            'status': equipment_status
        })

    except subprocess.TimeoutExpired:
        return jsonify({
            'success': False,
            'error': 'Request timed out. MMS server may be unreachable.'
        })
    except Exception as e:
        logger.error(f"Error finding equipment IP: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Error: {str(e)}'
        })

# ========================================
# EQUIPMENT DATABASE API ENDPOINTS
# ========================================

@app.route('/api/equipment/cache', methods=['GET'])
def api_equipment_cache():
    """
    Get all cached equipment from database.
    Query params:
    - limit: Max records to return (default 100)
    - search: Search term to filter by equipment name
    """
    try:
        if not EQUIPMENT_DB_PATH:
            return jsonify({
                'success': False,
                'error': 'Equipment database not initialized'
            })

        limit = request.args.get('limit', 100, type=int)
        search_term = request.args.get('search', '').strip()

        if search_term:
            # Search by equipment name
            equipment_list = search_equipment_db(EQUIPMENT_DB_PATH, search_term, limit)
        else:
            # Get all equipment
            equipment_list = get_all_equipment(EQUIPMENT_DB_PATH, limit)

        return jsonify({
            'success': True,
            'count': len(equipment_list),
            'equipment': equipment_list
        })

    except Exception as e:
        logger.error(f"Error getting equipment cache: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/equipment/cache/stats', methods=['GET'])
def api_equipment_cache_stats():
    """Get statistics about the equipment cache database."""
    try:
        if not EQUIPMENT_DB_PATH:
            return jsonify({
                'success': False,
                'error': 'Equipment database not initialized'
            })

        stats = get_database_stats(EQUIPMENT_DB_PATH)
        stats['database_path'] = EQUIPMENT_DB_PATH

        return jsonify({
            'success': True,
            'stats': stats
        })

    except Exception as e:
        logger.error(f"Error getting database stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/equipment/cache/<equipment_name>', methods=['GET'])
def api_equipment_cache_single(equipment_name):
    """Get a single equipment record from the cache."""
    try:
        if not EQUIPMENT_DB_PATH:
            return jsonify({
                'success': False,
                'error': 'Equipment database not initialized'
            })

        equipment = get_equipment(EQUIPMENT_DB_PATH, equipment_name)

        if equipment:
            return jsonify({
                'success': True,
                'equipment': equipment
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Equipment {equipment_name} not found in cache'
            })

    except Exception as e:
        logger.error(f"Error getting equipment {equipment_name}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/api/equipment', methods=['POST'])
def api_equipment_create():
    """
    Create or update an equipment record in the database.
    Accepts JSON body with equipment_name (required) and optional fields.
    """
    try:
        if not EQUIPMENT_DB_PATH:
            return jsonify({
                'success': False,
                'error': 'Equipment database not initialized'
            }), 500

        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Request body must be JSON'
            }), 400

        equipment_name = data.get('equipment_name') or data.get('name')
        if not equipment_name:
            return jsonify({
                'success': False,
                'error': 'equipment_name is required'
            }), 400

        result = save_equipment(
            EQUIPMENT_DB_PATH,
            equipment_name=equipment_name,
            oid=data.get('oid'),
            cid=data.get('cid'),
            profile=data.get('profile'),
            network_ip=data.get('network_ip'),
            avi_ip=data.get('avi_ip'),
            ptx_model=data.get('ptx_model'),
            status=data.get('status')
        )

        if result:
            log_database('info', 'equipment_create', f'Equipment created/updated: {equipment_name}')
            return jsonify({
                'success': True,
                'message': f'Equipment {equipment_name} saved successfully',
                'equipment_name': equipment_name.upper().strip()
            }), 201
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to save equipment {equipment_name}'
            }), 500

    except Exception as e:
        logger.error(f"Error creating equipment: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/equipment/<equipment_name>', methods=['DELETE'])
def api_equipment_delete(equipment_name):
    """
    Delete an equipment record from the database by name.
    """
    try:
        if not EQUIPMENT_DB_PATH:
            return jsonify({
                'success': False,
                'error': 'Equipment database not initialized'
            }), 500

        conn = sqlite3.connect(EQUIPMENT_DB_PATH)
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA busy_timeout=5000')
        cursor = conn.cursor()
        equipment_name_upper = equipment_name.upper().strip()
        cursor.execute('DELETE FROM equipment_cache WHERE equipment_name = ?', (equipment_name_upper,))
        deleted = cursor.rowcount
        conn.commit()
        conn.close()

        if deleted > 0:
            log_database('info', 'equipment_delete', f'Equipment deleted: {equipment_name_upper}')
            return jsonify({
                'success': True,
                'message': f'Equipment {equipment_name_upper} deleted'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Equipment {equipment_name_upper} not found'
            }), 404

    except Exception as e:
        logger.error(f"Error deleting equipment {equipment_name}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/equipment', methods=['GET'])
def api_equipment_list():
    """
    Get all equipment from the database.
    Alias for /api/equipment/cache for convenience.
    """
    try:
        if not EQUIPMENT_DB_PATH:
            return jsonify({
                'success': False,
                'error': 'Equipment database not initialized'
            }), 500

        limit = request.args.get('limit', 100, type=int)
        search_term = request.args.get('search', '').strip()

        if search_term:
            equipment_list = search_equipment_db(EQUIPMENT_DB_PATH, search_term, limit)
        else:
            equipment_list = get_all_equipment(EQUIPMENT_DB_PATH, limit)

        return jsonify({
            'success': True,
            'count': len(equipment_list),
            'equipment': equipment_list
        })

    except Exception as e:
        logger.error(f"Error listing equipment: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ========================================
# EQUIPMENT DATABASE IMPORT & UPDATE API
# ========================================

# background_update_worker imported from app.background_tasks above

@app.route('/api/equipment/import-ip-list', methods=['POST'])
def api_import_ip_list():
    """
    Import equipment from IP_list.dat file into the database.
    This populates the database with equipment names and IP addresses.
    """
    try:
        if not EQUIPMENT_DB_PATH:
            return jsonify({
                'success': False,
                'error': 'Equipment database not initialized'
            })

        if not os.path.exists(IP_LIST_PATH):
            return jsonify({
                'success': False,
                'error': f'IP_list.dat not found at {IP_LIST_PATH}'
            })

        result = parse_ip_list_file(EQUIPMENT_DB_PATH, IP_LIST_PATH)

        return jsonify({
            'success': result['success'],
            'imported': result['imported'],
            'updated': result['updated'],
            'skipped': result['skipped'],
            'total_lines': result['total_lines'],
            'errors': result['errors']
        })

    except Exception as e:
        logger.error(f"Error importing IP list: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/equipment/updater/start', methods=['POST'])
def api_start_background_updater():
    """
    Start the background equipment updater.
    This will query MMS server one equipment at a time to fill in missing data.
    """
    global background_updater

    try:
        if not EQUIPMENT_DB_PATH:
            return jsonify({
                'success': False,
                'error': 'Equipment database not initialized'
            })

        if not is_online_network():
            return jsonify({
                'success': False,
                'error': 'Cannot start updater - not on online network'
            })

        if background_updater['running']:
            return jsonify({
                'success': False,
                'error': 'Background updater is already running'
            })

        # Get optional delay from request
        data = request.get_json() or {}
        delay = data.get('delay_seconds', 5)
        background_updater['delay_seconds'] = max(2, min(60, delay))  # Clamp 2-60 seconds

        # Reset state and start thread
        background_updater['stop_event'].clear()
        background_updater['running'] = True
        background_updater['thread'] = threading.Thread(
            target=background_update_worker,
            daemon=True
        )
        background_updater['thread'].start()

        return jsonify({
            'success': True,
            'message': 'Background updater started',
            'delay_seconds': background_updater['delay_seconds']
        })

    except Exception as e:
        logger.error(f"Error starting background updater: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/equipment/updater/stop', methods=['POST'])
def api_stop_background_updater():
    """Stop the background equipment updater."""
    global background_updater

    try:
        if not background_updater['running']:
            return jsonify({
                'success': False,
                'error': 'Background updater is not running'
            })

        background_updater['stop_event'].set()

        return jsonify({
            'success': True,
            'message': 'Stop signal sent to background updater'
        })

    except Exception as e:
        logger.error(f"Error stopping background updater: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/equipment/updater/status', methods=['GET'])
def api_background_updater_status():
    """Get the current status of the background equipment updater."""
    try:
        progress = get_update_progress(EQUIPMENT_DB_PATH) if EQUIPMENT_DB_PATH else {}

        return jsonify({
            'success': True,
            'running': background_updater['running'],
            'status': background_updater['status'],
            'current_equipment': background_updater['current_equipment'],
            'processed_count': background_updater['processed_count'],
            'error_count': background_updater['error_count'],
            'last_update': background_updater['last_update'],
            'delay_seconds': background_updater['delay_seconds'],
            'progress': progress
        })

    except Exception as e:
        logger.error(f"Error getting updater status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/legacy/terminal/start', methods=['POST'])
def api_legacy_terminal_start():
    """Start a new terminal session"""
    try:
        session_id = str(uuid.uuid4())
        session = TerminalSession(session_id)
        success, message = session.start()
        
        if success:
            terminal_sessions[session_id] = session
            return jsonify({'success': True, 'session_id': session_id, 'message': 'T1_Tools.bat terminal started'})
        else:
            return jsonify({'success': False, 'message': message})
            
    except Exception as e:
        logger.error(f"Terminal start error: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/legacy/terminal/command', methods=['POST'])
def api_legacy_terminal_command():
    """Send command to terminal session"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        command = data.get('command', '')
        
        if session_id not in terminal_sessions:
            return jsonify({'success': False, 'message': 'Terminal session not found'})
        
        session = terminal_sessions[session_id]
        
        if session.send_command(command):
            return jsonify({'success': True, 'message': 'Command sent'})
        else:
            return jsonify({'success': False, 'message': 'Failed to send command'})
            
    except Exception as e:
        logger.error(f"Terminal command error: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/legacy/terminal/output', methods=['GET'])
def api_legacy_terminal_output():
    """Get terminal output"""
    try:
        session_id = request.args.get('session_id')
        
        if session_id not in terminal_sessions:
            return jsonify({'success': False, 'message': 'Terminal session not found'})
        
        session = terminal_sessions[session_id]
        output = session.get_output()
        
        return jsonify({'success': True, 'output': output, 'exited': not session.is_running()})
        
    except Exception as e:
        logger.error(f"Terminal output error: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/legacy/terminal/stop', methods=['POST'])
def api_legacy_terminal_stop():
    """Stop terminal session"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        
        if session_id in terminal_sessions:
            session = terminal_sessions[session_id]
            session.stop()
            del terminal_sessions[session_id]
            
        return jsonify({'success': True, 'message': 'Terminal stopped'})
        
    except Exception as e:
        logger.error(f"Terminal stop error: {e}")
        return jsonify({'success': False, 'message': str(e)})

# Keep existing equipment list route
@app.route('/api/legacy/equipment-list', methods=['GET'])
def api_legacy_equipment_list():
    """Get equipment list from IP_list.dat"""
    try:
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        
        possible_paths = [
            os.path.join(base_dir, 'T1_Tools_Legacy', 'bin', 'IP_list.dat'),
            os.path.join(base_dir, 'IP_list.dat'),
            os.path.join(TOOLS_DIR, 'IP_list.dat')
        ]
        
        ip_list_file = None
        for path in possible_paths:
            if os.path.exists(path):
                ip_list_file = path
                break
        
        if not ip_list_file:
            return jsonify({
                'success': False,
                'message': 'IP_list.dat not found'
            })
        
        equipment_list = []
        with open(ip_list_file, 'r') as f:
            lines = f.readlines()
            for line in lines[1:]:  # Skip header
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                parts = line.split()
                if len(parts) >= 3:
                    equipment_list.append({
                        'name': parts[0],
                        'ptx_ip': parts[1],
                        'avi_ip': parts[2]
                    })
        
        return jsonify({
            'success': True,
            'equipment': equipment_list,
            'count': len(equipment_list)
        })
        
    except Exception as e:
        logger.error(f"Equipment list error: {e}")
        return jsonify({'success': False, 'message': str(e)})

# Helper function for equipment IPs
def get_equipment_ips(equipment_name):
    """Get PTX and AVI IPs for equipment"""
    try:
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        
        possible_paths = [
            os.path.join(base_dir, 'T1_Tools_Legacy', 'bin', 'IP_list.dat'),
            os.path.join(base_dir, 'IP_list.dat'),
            os.path.join(TOOLS_DIR, 'IP_list.dat')
        ]
        
        ip_list_file = None
        for path in possible_paths:
            if os.path.exists(path):
                ip_list_file = path
                break
        
        if not ip_list_file:
            return None, None
        
        with open(ip_list_file, 'r') as f:
            lines = f.readlines()
            for line in lines[1:]:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                parts = line.split()
                if len(parts) >= 3:
                    if parts[0].upper() == equipment_name.upper():
                        return parts[1], parts[2]  # ptx_ip, avi_ip
        
        return None, None
        
    except Exception as e:
        logger.error(f"Error reading IP list: {e}")
        return None, None

def generate_mock_script_output(script_name, equipment, equipment_ip):
    """Generate realistic mock output for TEST equipment"""

    mock_outputs = {
        'ip-finder': f"""
+-------+---------+---------------+--------------+
| _OID_ | _CID_   | _profile      | network_ip   |
+-------+---------+---------------+--------------+
| {equipment.upper()} | eqmt_test | Test Equipment | {equipment_ip} |
+-------+---------+---------------+--------------+
PTX IP is: {equipment_ip}
Vehicle is Online.
PTXC Found.
AVI IP is : 10.111.219.99
""",
        'start-vnc': f"""
Starting VNC connection to {equipment_ip}...
VNC session established.
Opening VNC viewer...
""",
        'ptx-health': f"""
PTX IP is {equipment_ip}. Health check starting...
PTXC Found...
Equipment ID: {equipment.upper()}

**Ping Results: {equipment_ip}-> 192.168.0.100
Packet Loss: 0%
Average Latency: 0.125 ms

**Health Check Results of {equipment_ip}:
CPU Usage: 25.30%
Memory Usage: 45.12%
System Uptime: up 5 hours, 23 minutes
Disk Usage: /dev/mmcblk0p3  5.6G  2.8G  2.6G  52% /media/realroot/home

**AVI Radio Mobile Status:
Current Time:  1234             Temperature: 28
Reset Counter: 1                Mode:        ONLINE
System mode:   LTE              PS state:    Attached
RSRP (dBm):    -75              SINR (dB):   22.5
""",
        'avi-reboot': f"""
Rebooting AVI Radio and MM2 for {equipment_ip}...
AVI Radio shutdown initiated...
MM2 controller reset in progress...
Reboot completed successfully.
""",
        'component-tracking': f"""
*************************** 1. row ***************************
                  equipment_name: {equipment.upper()}
                            type: TestVehicle
                           model: Test Equipment
            field_computer_part_name: PTXC
        field_computer_serial_number: TEST123456
          field_computer_mac_address: 00:80:07:01:99:99
          gnss1_hardware_serial_number: 1445-99999
            gnss1_hardware_firmware: 5.4+TEST
""",
        'watchdog': f"""
AVI-PTX Watchdog Deployment for {equipment_ip}...
PTXC IP is {equipment_ip}
Equipment is {equipment.upper()}. Deploying watchdog...
{equipment.upper()} : Connected {equipment_ip} successfully.
{equipment.upper()} : AVI IP is 10.111.219.99.
{equipment.upper()} : Copied er-watchdog.sh successfully.
{equipment.upper()} : Copied er-reset.pl successfully.
Watchdog deployment completed.
""",
        'linux-perf': f"""
Performance and Usage Check Results of {equipment_ip}:

CPU Usage: 25.80%
Memory Usage: 48.06%
System Uptime: up 5 hours, 23 minutes

Disk Usage:
Filesystem      Size  Used Avail Use% Mounted on
/dev/mmcblk0p3  5.6G  2.8G  2.6G  52% /media/realroot/home

Top 5 Processes by CPU Usage:
  PID  CMD                         %CPU %MEM
  540  java -DAPP_NAME=_minemobile  12.5 18.9
  438  /usr/bin/X :0                2.1  1.2
""",
        'log-downloader': f"""
Downloading logs from {equipment_ip}...
Downloading /home/dlog/frontrunnerV3/logs/gc_minemobile.log....
Downloading /home/dlog/frontrunnerV3/logs/management_minemobile.dbg....
Creating archive: {equipment_ip}_TEST_logs.zip
Download completed: {equipment_ip}_TEST_logs.zip (1.2 MB)
File saved to Downloads folder.
""",
        'ptx-uptime': f"""
Downloading PTX Uptime Report from MMS server...
Report file: PTX_Uptime_Report.html
Downloaded to: C:\\Users\\YourUser\\Downloads\\PTX_Uptime_Report.html

Opening in Microsoft Edge...
Report contains uptime data for all PTX systems.
""",
        'mineview-sessions': f"""
Checking active Mineview sessions...

Active Sessions Found:
+-----------------+------------------+----------------------+
| Session ID      | User             | Connected Since      |
+-----------------+------------------+----------------------+
| SESSION_001     | admin            | 2026-01-10 08:00:00 |
| SESSION_002     | operator1        | 2026-01-10 09:15:00 |
| SESSION_003     | support          | 2026-01-10 09:45:00 |
+-----------------+------------------+----------------------+
Total active sessions: 3
""",
        'koa-data': f"""
Retrieving Live KOA Data...

+---------------+----------+---------+---------+------+-------+
| TravelID      | Location | FromLoc | ToLoc   | Open | Close |
+---------------+----------+---------+---------+------+-------+
| 1767644342329 | NULL     | INT_27  | R23_05  |    1 |     0 |
| 1767690576531 | NULL     | INT_34  | INT_48  |    1 |     0 |
| 1767853995047 | NULL     | INT_104 | R06_16  |    1 |     0 |
+---------------+----------+---------+---------+------+-------+
Total KOA records: 3
""",
        'speed-limit': f"""
Retrieving Live Speed Limit Data...

+---------------------+-----------------+
| Area_Type           | SpeedLimit_kmhr |
+---------------------+-----------------+
| LocalSpeedLimitArea |              12 |
| LocalSpeedLimitArea |              20 |
| LocalSpeedLimitArea |              55 |
| LocalSpeedLimitArea |              50 |
| LocalSpeedLimitArea |              15 |
+---------------------+-----------------+
Total speed limit areas: 115
"""
    }

    # Default output for scripts not in the map
    default_output = f"""
Executing {script_name}...
[TEST MODE] Mock output generated.
Script completed successfully.
"""

    return mock_outputs.get(script_name, default_output)

@app.route('/api/legacy/grm-script', methods=['POST'])
def api_legacy_grm_script():
    """Execute GRM T1 Scripts via SSH (plink)"""
    try:
        data = request.get_json()
        script_name = data.get('script', '').lower()
        equipment = data.get('equipment')  # Equipment name or IP

        # Script mapping to remote commands on MMS server
        # Format: plink -t mms@10.110.19.107 -pw password "/full/path/to/script.sh [equipment]"
        grm_scripts = {
            'ip-finder': {
                'name': 'IP Finder',
                'command': '/home/mms/bin/remote_check/Random/MySQL/ip_export.sh',
                'requires_equipment': True,
                'description': 'Find equipment IP addresses'
            },
            'ptx-uptime': {
                'name': 'PTX Uptime Report',
                'command': 'download_file',  # Special command for file download
                'file_path': '/home/mms/Logs/PTX_Uptime_Report.html',
                'log_command': 'echo $(date): PTX_Uptime_Report Download Initiated from WEB_APP. >> /home/mms/Logs/Report_Download.txt',
                'description': 'Download PTX uptime report HTML file'
            },
            'mineview-sessions': {
                'name': 'Mineview Sessions',
                'command': '/home/mms/bin/MineView-Session.sh',
                'description': 'Check active Mineview sessions'
            },
            'start-vnc': {
                'name': 'Start PTX VNC',
                'command': 'launch_local_app',  # Special command for client-side launch
                'app_type': 'vnc',
                'requires_equipment': True,
                'port': 5900,
                'description': 'Start VNC connection to PTX'
            },
            'ptx-health': {
                'name': 'PTX Health Check',
                'command': '/home/mms/bin/remote_check/ping_check/HealthCheck/ip_export_only.sh',
                'requires_equipment': True,
                'description': 'Check PTX system health and network connectivity'
            },
            'avi-reboot': {
                'name': 'MM2 AVI Reboot',
                'command': '/home/mms/bin/remote_check/TempTool/MM2/Check_Exe.sh',
                'requires_equipment': True,
                'log_command': 'echo $(date): Initiated from WEB_APP for {equipment}. >> /home/mms/bin/remote_check/TempTool/MM2/Report.txt',
                'description': 'Reboot AVI radio and MM2'
            },
            'watchdog': {
                'name': 'PTX-AVI Watchdog Deploy',
                'command': '/home/mms/bin/remote_check/AVI_Watchdog/watchdog_setup_single.sh',
                'requires_equipment': True,
                'log_command': 'echo $(date): Initiated from WEB_APP for {equipment}. >> /home/mms/bin/remote_check/AVI_Watchdog/Report.txt',
                'description': 'Deploy watchdog to PTXC (interactive - may timeout)'
            },
            'koa-data': {
                'name': 'Live KOA Data',
                'command': '/home/mms/bin/remote_check/Random/MySQL/table_export.sh',
                'description': 'Check live KOA data'
            },
            'speed-limit': {
                'name': 'Live Speed Limit Data',
                'command': '/home/mms/bin/remote_check/Random/MySQL/LASL_export.sh',
                'description': 'Check speed limit data'
            },
            'linux-perf': {
                'name': 'Linux Perf/Usage Check',
                'command': '/home/mms/bin/remote_check/Random/LinuxCheck/For_Support/Check_Exe.sh',
                'requires_equipment': True,
                'description': 'Check Linux performance (interactive - may timeout)'
            },
            'component-tracking': {
                'name': 'Field Component Tracking',
                'command': '/home/mms/bin/remote_check/Random/MySQL/Component/site_export.sh',
                'requires_equipment': True,
                'description': 'Track field components'
            },
            'log-downloader': {
                'name': 'Linux Logs Downloader',
                'command': '/home/mms/bin/remote_check/TempTool/DOWNLOAD/Log_Get.sh',
                'requires_equipment': True,  # Requires IP and username
                'log_command': 'echo $(date): Initiated from WEB_APP for {equipment}. >> /home/mms/bin/remote_check/TempTool/DOWNLOAD/Report.txt',
                'description': 'Download Linux system logs'
            }
        }

        # Check if script exists
        if script_name not in grm_scripts:
            return jsonify({
                'success': False,
                'message': f'Unknown script: {script_name}'
            })

        script = grm_scripts[script_name]

        # Check if script is available
        if script['command'] is None:
            return jsonify({
                'success': False,
                'message': f'{script["name"]}: {script["description"]}'
            })

        # Check if equipment is required but not provided
        if script.get('requires_equipment') and not equipment:
            return jsonify({
                'success': False,
                'message': f'{script["name"]} requires equipment name or IP address'
            })

        # TEST MODE: When equipment is "TEST", always return mock data (regardless of network)
        is_test_mode = equipment and equipment.upper() == 'TEST'

        if is_test_mode:
            mock_equipment_ip = '10.110.99.99'
            mock_avi_ip = '10.111.219.99'
            mock_ptx_model = 'PTXC'
            mock_equipment_status = 'online'
            mock_script_output = generate_mock_script_output(script_name, equipment, mock_equipment_ip)

            return jsonify({
                'success': True,
                'output': mock_script_output,
                'message': f'{script["name"]} executed successfully (TEST MODE)',
                'equipment_status': mock_equipment_status,
                'equipment_ip': mock_equipment_ip,
                'avi_ip': mock_avi_ip,
                'ptx_model': mock_ptx_model
            })

        # OFFLINE MODE: Check database cache first, then simulate
        if not is_online_network():
            cached_equipment = None
            cached_ip = None
            cached_avi_ip = None
            cached_model = None
            cached_status = 'offline'

            # Try to get cached data from database
            if equipment and script.get('requires_equipment') and EQUIPMENT_DB_PATH:
                cached_equipment = get_equipment(EQUIPMENT_DB_PATH, equipment)
                if cached_equipment:
                    cached_ip = cached_equipment.get('network_ip')
                    cached_avi_ip = cached_equipment.get('avi_ip')
                    cached_model = cached_equipment.get('ptx_model')
                    cached_status = cached_equipment.get('last_status', 'unknown')
                    cached_oid = cached_equipment.get('oid')
                    cached_cid = cached_equipment.get('cid')
                    cached_profile = cached_equipment.get('profile')
                    log_lookup(EQUIPMENT_DB_PATH, equipment, 'cache', True)

            # Build output
            output_lines = []
            if cached_equipment:
                output_lines.append(f"[CACHED DATA] {script['name']}")
                output_lines.append(f"Equipment: {equipment}")
                if cached_oid:
                    output_lines.append(f"OID: {cached_oid}")
                if cached_cid:
                    output_lines.append(f"CID: {cached_cid}")
                if cached_profile:
                    output_lines.append(f"Profile: {cached_profile}")
                output_lines.append(f"Network IP: {cached_ip or 'Not cached'}")
                output_lines.append(f"AVI IP: {cached_avi_ip or 'Not cached'}")
                output_lines.append(f"PTX Model: {cached_model or 'Unknown'}")
                output_lines.append(f"Last Known Status: {cached_status.upper()}")
                output_lines.append(f"Cached: {cached_equipment.get('last_updated', 'Unknown')}")
                output_lines.extend([
                    "",
                    "Using cached data - connect to network for live status.",
                    ""
                ])
            else:
                output_lines.append(f"[OFFLINE MODE] {script['name']}")
                output_lines.append(f"Description: {script['description']}")
                if equipment:
                    output_lines.append(f"Equipment: {equipment}")
                    output_lines.append("No cached data available for this equipment.")
                output_lines.extend([
                    "",
                    "Network offline - connect to MMS network for live data.",
                    "TIP: Enter 'TEST' as equipment to see mock data.",
                    ""
                ])
                # Reset cache variables for response
                cached_ip = None
                cached_avi_ip = None
                cached_model = None
                cached_oid = None
                cached_cid = None
                cached_profile = None

            return jsonify({
                'success': True,
                'output': '\n'.join(output_lines),
                'message': f'{script["name"]} ({"cached" if cached_equipment else "offline"} mode)',
                'equipment_status': cached_status,
                'equipment_ip': cached_ip,
                'avi_ip': cached_avi_ip,
                'ptx_model': cached_model,
                'oid': cached_oid if cached_equipment else None,
                'cid': cached_cid if cached_equipment else None,
                'profile': cached_profile if cached_equipment else None,
                'data_source': 'cached' if cached_equipment else 'offline',
                'last_updated': cached_equipment.get('last_updated') if cached_equipment else None
            })

        # ONLINE MODE: Execute via plink
        plink_path = resolve_plink_path()
        if not plink_path:
            return jsonify({
                'success': False,
                'message': 'plink.exe not found in any configured tool directory'
            })

        # MMS server connection details
        mms_server = MMS_SERVER['ip']
        mms_user = MMS_SERVER['user']
        mms_password = MMS_SERVER['password']

        # Handle file download scripts (like PTX Uptime Report)
        if script['command'] == 'download_file':
            # Log the download
            if script.get('log_command'):
                log_cmd = [
                    plink_path,
                    '-batch',
                    f'{mms_user}@{mms_server}',
                    '-pw', mms_password,
                    script['log_command']
                ]
                try:
                    subprocess.run(log_cmd, capture_output=True, timeout=10, creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == 'Windows' else 0)
                except:
                    pass

            # Use pscp to download file
            pscp_path = os.path.join(os.path.dirname(plink_path), 'pscp.exe')
            if not os.path.exists(pscp_path):
                return jsonify({
                    'success': False,
                    'message': f'pscp.exe not found at: {pscp_path}'
                })

            # Download to Downloads folder
            download_dir = os.path.join(os.path.expanduser('~'), 'Downloads')
            local_filename = os.path.basename(script['file_path'])
            local_path = os.path.join(download_dir, local_filename)

            pscp_cmd = [
                pscp_path,
                '-pw', mms_password,
                f'{mms_user}@{mms_server}:{script["file_path"]}',
                local_path
            ]

            try:
                result = subprocess.run(
                    pscp_cmd,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == 'Windows' else 0
                )

                if result.returncode == 0 and os.path.exists(local_path):
                    # Store file path in session for download endpoint
                    session['download_file'] = local_path
                    session['download_filename'] = local_filename

                    return jsonify({
                        'success': True,
                        'message': f'File ready for download',
                        'output': f'Downloaded: {local_filename}\nPreparing file for your browser...\n\nClick the download link to save to your computer.',
                        'download_ready': True,
                        'download_url': '/api/legacy/download-file',
                        'filename': local_filename
                    })
                else:
                    return jsonify({
                        'success': False,
                        'message': f'File download failed: {result.stderr}'
                    })
            except subprocess.TimeoutExpired:
                return jsonify({
                    'success': False,
                    'message': 'File download timed out after 30 seconds'
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f'File download error: {str(e)}'
                })

        # If equipment is provided and script needs IP, run IP finder first to get actual IP
        equipment_ip = None
        equipment_status = None

        # Check if this is TEST equipment for mock data
        is_test_equipment = equipment and equipment.upper() == 'TEST'

        # Initialize all equipment fields
        avi_ip = None
        ptx_model = None
        oid = None
        cid = None
        profile = None
        data_source = 'live'  # 'live' or 'cached'

        if equipment and script.get('requires_equipment'):
            # Use mock data for TEST equipment
            if is_test_equipment:
                equipment_ip = '10.110.99.99'
                avi_ip = '10.111.219.99'
                ptx_model = 'PTXC'
                equipment_status = 'online'
                oid = 'OID-12345'
                cid = 'CID-67890'
                profile = 'LV Single Cab'
                data_source = 'test'

                # Generate mock script output based on script type
                mock_output = generate_mock_script_output(script_name, equipment, equipment_ip)

                return jsonify({
                    'success': True,
                    'output': mock_output,
                    'message': f'{script["name"]} executed successfully',
                    'equipment_status': equipment_status,
                    'equipment_ip': equipment_ip,
                    'avi_ip': avi_ip,
                    'ptx_model': ptx_model,
                    'oid': oid,
                    'cid': cid,
                    'profile': profile,
                    'data_source': data_source
                })

            # Run IP finder to get equipment IP address
            ip_finder_cmd = f"/home/mms/bin/remote_check/Random/MySQL/ip_export.sh {equipment}"

            ip_lookup_plink = [
                plink_path,
                '-batch',
                '-t',
                f'{mms_user}@{mms_server}',
                '-pw', mms_password,
                ip_finder_cmd
            ]

            try:
                ip_result = subprocess.run(
                    ip_lookup_plink,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == 'Windows' else 0
                )

                # Parse IP from output (looks for "PTX IP is: X.X.X.X" or network_ip column)
                # Also parse OID, CID, profile from output
                for line in ip_result.stdout.split('\n'):
                    # Parse direct field outputs
                    if 'PTX IP is' in line:
                        equipment_ip = line.split('PTX IP is', 1)[1].replace(':', '').strip()
                    elif 'AVI IP is' in line:
                        avi_ip = line.split('AVI IP is', 1)[1].replace(':', '').strip()
                    elif 'OID:' in line or 'Object ID:' in line:
                        oid = line.split(':')[1].strip() if ':' in line else None
                    elif 'CID:' in line or 'Component ID:' in line:
                        cid = line.split(':')[1].strip() if ':' in line else None
                    elif 'Profile:' in line:
                        profile = line.split(':')[1].strip() if ':' in line else None
                    elif 'PTX Model:' in line or 'Model:' in line:
                        model_part = line.split(':')[1].strip() if ':' in line else None
                        if model_part:
                            ptx_model = model_part
                    elif 'PTXC' in line.upper() and not ptx_model:
                        ptx_model = 'PTXC'
                    elif 'PTX10' in line.upper() and not ptx_model:
                        ptx_model = 'PTX10'
                    elif 'network_ip' in line:
                        # Table header, skip
                        continue
                    elif line.strip() and '|' in line and not line.startswith('+'):
                        # Parse table row: | AHG69 | eqmt_lv | LV Single Cab | 10.110.21.87 |
                        # Columns: equipment_name | profile_short | profile | network_ip
                        parts = [p.strip() for p in line.split('|') if p.strip()]
                        if len(parts) >= 4:
                            # Column 1: equipment name (skip, we already have it)
                            # Column 2: profile short code (can use as CID if not set)
                            if not cid and parts[1]:
                                cid = parts[1]
                            # Column 3: profile/description
                            if not profile and parts[2]:
                                profile = parts[2]
                            # Column 4: network_ip
                            equipment_ip = parts[3]

                    if 'Vehicle is Online' in line or 'Equipment is Online' in line:
                        equipment_status = 'online'
                    elif 'Vehicle is Offline' in line or 'Equipment is Offline' in line:
                        equipment_status = 'offline'

                if not equipment_ip:
                    equipment_ip = equipment  # Fallback to using equipment name

            except Exception as e:
                equipment_ip = equipment

        # Handle local app launch (VNC, PuTTY, WinSCP) - after IP lookup
        if script['command'] == 'launch_local_app':
            app_type = script.get('app_type', 'unknown')
            port = script.get('port', '')

            # Build custom URI for client-side launch
            if app_type == 'vnc':
                # Format: autotech-vnc://10.110.21.87:5900
                host = equipment_ip if equipment_ip else equipment
                launch_uri = f"autotech-vnc://{host}:{port}"
                output_lines = [
                    "VNC Connection Details:",
                    f"Host: {host}",
                    f"Port: {port}",
                    "",
                    "Launching VNC Viewer on your computer..."
                ]
            elif app_type == 'putty':
                # Format: autotech-ssh://mms@10.110.19.107:22
                launch_uri = f"autotech-ssh://{mms_user}@{mms_server}:22"
                output_lines = [
                    "SSH Connection Details:",
                    f"Host: {mms_server}",
                    f"User: {mms_user}",
                    f"Port: 22",
                    "",
                    "Launching PuTTY on your computer..."
                ]
            elif app_type == 'winscp':
                # Format: autotech-sftp://mms:password@10.110.19.107:22
                launch_uri = f"autotech-sftp://{mms_user}:{mms_password}@{mms_server}:22"
                output_lines = [
                    "SFTP Connection Details:",
                    f"Host: {mms_server}",
                    f"User: {mms_user}",
                    f"Port: 22",
                    "",
                    "Launching WinSCP on your computer..."
                ]
            else:
                return jsonify({
                    'success': False,
                    'message': f'Unknown app type: {app_type}'
                })

            return jsonify({
                'success': True,
                'output': '\n'.join(output_lines),
                'message': f'{script["name"]} - Launching on your computer',
                'launch_uri': launch_uri,
                'launch_required': True,
                'equipment_ip': equipment_ip,
                'equipment_status': equipment_status,
                'avi_ip': avi_ip,
                'ptx_model': ptx_model
            })

        # Build remote command with equipment IP or name
        remote_command = script['command']
        if equipment:
            # Use IP if we found it, otherwise use equipment name
            param = equipment_ip if equipment_ip else equipment
            remote_command = f"{script['command']} {param}"

        # Add logging command if specified (for scripts that track usage)
        if script.get('log_command'):
            log_cmd = script['log_command'].replace('{equipment}', equipment if equipment else 'NONE')
            remote_command = f"{log_cmd};{remote_command}"

        # Build plink command
        # Format: plink -batch -t mms@10.110.19.107 -pw password "command [equipment]"
        # NOTE: MUST use -batch flag for web interface - scripts must be non-interactive
        plink_cmd = [
            plink_path,
            '-batch',
            '-t',
            f'{mms_user}@{mms_server}',
            '-pw', mms_password,
            remote_command
        ]

        logger.info(f"GRM Script: Executing {script['name']}")

        # Execute plink command
        try:
            if platform.system() == 'Windows':
                result = subprocess.run(
                    plink_cmd,
                    capture_output=True,
                    text=True,
                    timeout=120,  # Increased to 120s for interactive scripts
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            else:
                result = subprocess.run(
                    plink_cmd,
                    capture_output=True,
                    text=True,
                    timeout=120  # Increased to 120s for interactive scripts
                )

            # Combine stdout and stderr
            full_output = result.stdout
            if result.stderr:
                full_output += f"\n[ERRORS]\n{result.stderr}"

            if result.returncode == 0:
                # Save successful IP Finder results to database
                if equipment and equipment_ip and EQUIPMENT_DB_PATH:
                    save_equipment(
                        EQUIPMENT_DB_PATH,
                        equipment,
                        oid=oid,
                        cid=cid,
                        profile=profile,
                        network_ip=equipment_ip,
                        avi_ip=avi_ip,
                        ptx_model=ptx_model,
                        status=equipment_status
                    )
                    log_lookup(EQUIPMENT_DB_PATH, equipment, 'network', True)

                return jsonify({
                    'success': True,
                    'output': full_output,
                    'message': f'{script["name"]} executed successfully',
                    'equipment_status': equipment_status,
                    'equipment_ip': equipment_ip,
                    'avi_ip': avi_ip,
                    'ptx_model': ptx_model,
                    'oid': oid,
                    'cid': cid,
                    'profile': profile,
                    'data_source': 'live'
                })
            else:
                # Log failed lookup
                if equipment and EQUIPMENT_DB_PATH:
                    log_lookup(EQUIPMENT_DB_PATH, equipment, 'network', False)

                return jsonify({
                    'success': False,
                    'output': full_output,
                    'message': f'{script["name"]} failed with code {result.returncode}',
                    'equipment_status': equipment_status,
                    'equipment_ip': equipment_ip,
                    'avi_ip': avi_ip,
                    'ptx_model': ptx_model,
                    'oid': oid,
                    'cid': cid,
                    'profile': profile,
                    'data_source': 'live'
                })

        except subprocess.TimeoutExpired:
            return jsonify({
                'success': False,
                'message': f'{script["name"]} timed out after 120 seconds (script may require interactive input)'
            })
        except Exception as e:
            logger.error(f"GRM Script error: {e}")
            return jsonify({
                'success': False,
                'message': f'Failed to execute {script["name"]}: {str(e)}'
            })

    except Exception as e:
        logger.error(f"GRM Script API error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/legacy/download-file', methods=['GET'])
def api_legacy_download_file():
    """Serve downloaded file to client browser"""
    try:
        file_path = session.get('download_file')
        filename = session.get('download_filename', 'download.html')

        if not file_path or not os.path.exists(file_path):
            return jsonify({'success': False, 'message': 'File not found'}), 404

        # Send file to client browser
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype='text/html'
        )

    except Exception as e:
        logger.error(f"File download error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/legacy/execute', methods=['POST'])
def api_legacy_execute():
    """Execute quick access commands (PuTTY, WinSCP, etc.)"""
    try:
        data = request.get_json()
        command = data.get('command', '').lower()
        equipment = data.get('equipment', '').upper()
        
        # Get equipment IPs
        if command != 'help':
            ptx_ip, avi_ip = get_equipment_ips(equipment)
            if not ptx_ip:
                return jsonify({
                    'success': False,
                    'message': f'Equipment {equipment} not found in IP list'
                })
        
        # VNC
        if command == 'vnc':
            return jsonify({
                'success': True,
                'message': f'Use VNC button in IP Finder for {equipment}',
                'redirect': '/run/IP Finder'
            })
        
        # PUTTY
        elif command == 'putty':
            putty_path = os.path.join(TOOLS_DIR, 'putty.exe')
            if not os.path.exists(putty_path):
                return jsonify({'success': False, 'message': f'putty.exe not found'})
            
            try:
                subprocess.Popen([putty_path, '-ssh', f'dlog@{ptx_ip}', '-pw', 'gold'])
                return jsonify({
                    'success': True,
                    'message': f'PuTTY opened to {equipment} ({ptx_ip})'
                })
            except Exception as e:
                return jsonify({'success': False, 'message': f'Failed to launch PuTTY: {str(e)}'})
        
        # AVI
        elif command == 'avi':
            try:
                if platform.system() == 'Windows':
                    os.startfile(f'http://{avi_ip}')
                else:
                    import webbrowser
                    webbrowser.open(f'http://{avi_ip}')
                
                return jsonify({
                    'success': True,
                    'message': f'Opened AVI for {equipment} ({avi_ip})'
                })
            except Exception as e:
                return jsonify({'success': False, 'message': f'Failed to open AVI: {str(e)}'})
        
        # CACHE
        elif command == 'cache':
            winscp_path = os.path.join(TOOLS_DIR, 'WinSCP', 'WinSCP.exe')
            if not os.path.exists(winscp_path):
                return jsonify({'success': False, 'message': f'WinSCP.exe not found'})
            
            try:
                cache_path = '/usr/local/modular/cache/'
                subprocess.Popen([winscp_path, f'scp://dlog:gold@{ptx_ip}{cache_path}'])
                return jsonify({
                    'success': True,
                    'message': f'Opened cache for {equipment} ({ptx_ip})'
                })
            except Exception as e:
                return jsonify({'success': False, 'message': f'Failed to launch WinSCP: {str(e)}'})
        
        # AVI LOGS
        elif command == 'avilogs':
            winscp_path = os.path.join(TOOLS_DIR, 'WinSCP', 'WinSCP.exe')
            if not os.path.exists(winscp_path):
                return jsonify({'success': False, 'message': f'WinSCP.exe not found'})
            
            try:
                logs_path = '/mnt/bulk/'
                subprocess.Popen([winscp_path, f'scp://root:root@{avi_ip}{logs_path}'])
                return jsonify({
                    'success': True,
                    'message': f'Opened AVI logs for {equipment} ({avi_ip})'
                })
            except Exception as e:
                return jsonify({'success': False, 'message': f'Failed to launch WinSCP: {str(e)}'})
        
        # TRU
        elif command == 'tru':
            tru_path = os.path.join(TOOLS_DIR, 'Topcon', 'TRU.exe')
            if not os.path.exists(tru_path):
                return jsonify({'success': False, 'message': f'TRU.exe not found'})
            
            try:
                subprocess.Popen([tru_path])
                return jsonify({
                    'success': True,
                    'message': f'Launched TRU for {equipment}'
                })
            except Exception as e:
                return jsonify({'success': False, 'message': f'Failed to launch TRU: {str(e)}'})
        
        # PTX REBOOT
        elif command == 'ptxr':
            try:
                plink_path = resolve_plink_path()
                if not plink_path:
                    return jsonify({'success': False, 'message': 'plink.exe not found in any configured tool directory'})
                
                result = subprocess.run(
                    [plink_path, '-batch', '-pw', 'gold', f'dlog@{ptx_ip}', 'sudo reboot'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                return jsonify({
                    'success': True,
                    'message': f'Reboot command sent to {equipment} ({ptx_ip})'
                })
            except Exception as e:
                return jsonify({'success': False, 'message': f'Failed to reboot: {str(e)}'})
        
        # HELP
        elif command == 'help':
            return jsonify({
                'success': True,
                'message': 'Use terminal or quick access buttons'
            })
        
        else:
            return jsonify({
                'success': False,
                'message': f'Command "{command}" not implemented'
            })
        
    except Exception as e:
        logger.error(f"Legacy API error: {e}")
        return jsonify({'success': False, 'message': str(e)})
    
# ========================================
# LOG - CLEANUP TOOL
# ========================================
    
@app.route('/api/cleanup-logs', methods=['POST'])

def api_cleanup_logs():
    """Execute log cleanup - auto-detects online/offline mode."""
    print("[CLEANUP ROUTE] /api/cleanup-logs called")
    try:
        data = request.json
        if data is None:
            return jsonify({"success": False, "error": "No JSON data provided"}), 400
        folder_retention = int(data.get('folder_retention', 2))
        file_retention = int(data.get('file_retention', 7))
        dry_run = data.get('dry_run', True)

        print(f"[CLEANUP] Received: dry_run={dry_run}, folder_retention={folder_retention}, file_retention={file_retention}")

        # AUTO-DETECT OFFLINE MODE
        if not is_online_network():
            print(f"[CLEANUP] OFFLINE MODE - Using test data (dry_run={dry_run})")
            results = cleanup_logs_test_mode(
                folder_retention=folder_retention,
                file_retention=file_retention,
                dry_run=dry_run
            )
            return jsonify(results)
        
        # ONLINE MODE
        print("[CLEANUP] ONLINE MODE - Connecting to equipment")
        ip_address = data.get('ip')
        
        if not ip_address:
            return jsonify({"success": False, "error": "No IP address provided"}), 400
        
        results = cleanup_logs(
            ip_address=ip_address,
            folder_retention=folder_retention,
            file_retention=file_retention,
            dry_run=dry_run
        )
        
        return jsonify(results)
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/cleanup-logs/preview', methods=['POST'])

def api_cleanup_logs_preview():
    """Preview cleanup - auto-detects online/offline mode."""
    print("[CLEANUP ROUTE] /api/cleanup-logs/preview called")
    try:
        data = request.json
        if data is None:
            return jsonify({"success": False, "error": "No JSON data provided"}), 400
        folder_retention = int(data.get('folder_retention', 2))
        file_retention = int(data.get('file_retention', 7))
        
        # AUTO-DETECT OFFLINE MODE
        if not is_online_network():
            print("[CLEANUP] OFFLINE MODE - Preview with test data")
            results = cleanup_logs_test_mode(
                folder_retention=folder_retention,
                file_retention=file_retention,
                dry_run=True
            )
            return jsonify(results)
        
        # ONLINE MODE
        print("[CLEANUP] ONLINE MODE - Preview real equipment")
        ip_address = data.get('ip')
        
        if not ip_address:
            return jsonify({"success": False, "error": "No IP address provided"}), 400
        
        results = cleanup_logs(
            ip_address=ip_address,
            folder_retention=folder_retention,
            file_retention=file_retention,
            dry_run=True
        )
        
        return jsonify(results)

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/cleanup-logs/generate-test-data', methods=['POST'])

def api_generate_test_data():
    """Generate test data for offline mode testing."""
    try:
        # Only works in offline mode
        if is_online_network():
            return jsonify({"success": False, "error": "Test data generation only available in offline mode"}), 400

        print("[TEST DATA] Generating test log files...")

        import subprocess
        import sys

        generator_path = os.path.join(os.path.dirname(__file__), 'tools', 'test_log_generator.py')

        if not os.path.exists(generator_path):
            return jsonify({"success": False, "error": f"Generator not found at {generator_path}"}), 500

        # Run the generator
        result = subprocess.run([sys.executable, generator_path],
                              capture_output=True, text=True, timeout=60)

        if result.returncode == 0:
            print("[TEST DATA] Generation complete")
            return jsonify({
                "success": True,
                "message": "Test data generated successfully"
            })
        else:
            error_msg = result.stderr[:500] if result.stderr else "Unknown error"
            print(f"[TEST DATA] Generation failed: {error_msg}")
            return jsonify({
                "success": False,
                "error": f"Generation failed: {error_msg}"
            }), 500

    except subprocess.TimeoutExpired:
        return jsonify({"success": False, "error": "Test data generation timed out"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ========================================
# ADMIN LOG VIEWER
# ========================================
def _resolve_log_path(source: str) -> Optional[str]:
    if source not in LOG_SOURCES:
        return None
    log_dir = get_log_directory()
    return os.path.join(log_dir, LOG_SOURCES[source])

def _tail_log_lines(filepath: str, max_lines: int = 200) -> list:
    if not os.path.exists(filepath):
        return []
    max_lines = max(1, min(2000, max_lines))
    lines = deque(maxlen=max_lines)
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            lines.append(line.rstrip('\n'))
    return list(lines)

def _stream_log_lines(filepath: str, initial_lines: int = 200):
    def generate():
        try:
            if os.path.exists(filepath):
                if initial_lines > 0:
                    for line in _tail_log_lines(filepath, initial_lines):
                        payload = json.dumps({"line": line})
                        yield f"data: {payload}\n\n"
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    f.seek(0, os.SEEK_END)
                    while True:
                        line = f.readline()
                        if line:
                            payload = json.dumps({"line": line.rstrip('\n')})
                            yield f"data: {payload}\n\n"
                        else:
                            time.sleep(0.5)
            else:
                payload = json.dumps({"error": "Log file not found"})
                yield f"event: error\ndata: {payload}\n\n"
        except GeneratorExit:
            return
        except Exception as e:
            payload = json.dumps({"error": str(e)})
            yield f"event: error\ndata: {payload}\n\n"
    return generate()

@app.route('/admin/logs')
def admin_logs():
    sources = [
        {'key': key, 'label': LOG_SOURCE_LABELS.get(key, key.title())}
        for key in LOG_SOURCES.keys()
    ]
    return render_template('admin_logs.html', sources=sources)

@app.route('/api/logs/<source>', methods=['GET'])
def api_logs_tail(source: str):
    log_path = _resolve_log_path(source)
    if not log_path:
        return jsonify({"error": "Unknown log source", "request_id": get_request_id()}), 404

    try:
        lines = int(request.args.get('lines', 200))
    except ValueError:
        lines = 200

    return jsonify({
        "source": source,
        "lines": _tail_log_lines(log_path, lines),
        "request_id": get_request_id()
    })

@app.route('/api/logs/<source>/stream', methods=['GET'])
def api_logs_stream(source: str):
    log_path = _resolve_log_path(source)
    if not log_path:
        return jsonify({"error": "Unknown log source", "request_id": get_request_id()}), 404

    try:
        lines = int(request.args.get('lines', 200))
    except ValueError:
        lines = 200

    headers = {
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no"
    }
    return Response(
        stream_with_context(_stream_log_lines(log_path, lines)),
        mimetype='text/event-stream',
        headers=headers
    )

@app.route('/api/logs/<source>/download', methods=['GET'])
def api_logs_download(source: str):
    log_path = _resolve_log_path(source)
    if not log_path:
        return jsonify({"error": "Unknown log source", "request_id": get_request_id()}), 404
    if not os.path.exists(log_path):
        return jsonify({"error": "Log file not found", "request_id": get_request_id()}), 404
    return send_file(log_path, as_attachment=True)

# ========================================
# DIG FLEET MONITOR ROUTES
# ========================================

# ========================================
# DIG FLEET MONITOR ROUTES
# ========================================

# format_uptime_hours, probe_equipment_health, fleet_monitor_worker imported from app.background_tasks above

@app.route('/dig_fleet_monitor')
def dig_fleet_monitor():
    """Dig Fleet Monitor page"""
    return render_template('dig_fleet_monitor.html',
                         page_title="Dig Fleet Monitor",
                         online=is_online_network(),
                         gateway_ip=GATEWAY_IP,
                         timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

@app.route('/api/fleet_data')
def api_fleet_data():
    """Get fleet data with health info from SQL DB - Non-blocking & Failure Resilient"""
    try:
        data = None
        # Load layout with a complete fallback if the file is missing/locked
        if os.path.exists(FLEET_DATA_PATH):
            try:
                with open(FLEET_DATA_PATH, 'r') as f:
                    data = json.load(f)
            except Exception as read_err:
                logger.error(f"Fleet Monitor: Error reading layout file: {read_err}")
        
        if not data:
            logger.warning("Fleet Monitor: Using safety fallback layout")
            data = {
                "columns": [
                    {"id": "lh_north", "title": "Load & Haul North", "main": "GR17", "back": "GR18", "phone": "4258", "comms": "Auto Truck", "color": "#f7a224", "equipment": ["EXD69", "EXD99"]},
                    {"id": "lh_central", "title": "Load & Haul Central", "main": "GR15", "back": "GR16", "phone": "4259", "comms": "Auto Truck", "color": "#73c05c", "equipment": ["EXD265", "EXD81"]},
                    {"id": "lh_south", "title": "Load & Haul South", "main": "GR13", "back": "GR14", "phone": "4252", "comms": "Auto Truck", "color": "#f7e127", "equipment": ["EXD82", "EXD66"]}
                ]
            }
            
        # Get latest cached health from SQL
        health_data = {}
        try:
            health_data = fleet_monitor_db.get_latest_health()
        except Exception as db_err:
            logger.error(f"Fleet Monitor: SQL error: {db_err}")
            
        # Merge health data into each equipment
        for column in data['columns']:
            detailed = []
            for eq_id in column['equipment']:
                health = health_data.get(eq_id)
                
                if not health:
                    # Trigger background probe if online
                    if is_online_network():
                        threading.Thread(target=probe_equipment_health, args=(eq_id,), daemon=True).start()
                    
                    detailed.append({
                        'id': eq_id, 'uptime': 'Pending', 'uptime_hours': 0,
                        'mem_usage': '--%', 'mem_usage_raw': 0, 'last_updated': None
                    })
                else:
                    detailed.append({
                        'id': eq_id,
                        'uptime': format_uptime_hours(health['uptime_hours']),
                        'uptime_hours': health['uptime_hours'],
                        'mem_usage': f"{health['mem_usage']}%",
                        'mem_usage_raw': health['mem_usage'],
                        'last_updated': health['last_updated']
                    })
            column['equipment_detailed'] = detailed
            
        return jsonify(data)
    except Exception as e:
        logger.error(f"CRITICAL Fleet Monitor API Failure: {e}")
        # Universal emergency response - MUST return a valid JSON structure to prevent JS crash
        return jsonify({
            "columns": [{"id": "emergency", "title": "SYSTEM ERROR", "main": "-", "back": "-", "phone": "-", "comms": str(e), "color": "#ff0000", "equipment": [], "equipment_detailed": []}]
        })

@app.route('/api/fleet_data/refresh', methods=['POST'])
def api_fleet_data_refresh():
    """Manually trigger a re-probe of all equipment (Non-blocking)"""
    try:
        if not os.path.exists(FLEET_DATA_PATH):
            return jsonify({'success': False, 'error': 'No layout'}), 404
            
        with open(FLEET_DATA_PATH, 'r') as f:
            data = json.load(f)
        
        # Trigger background threads for all units
        for col in data['columns']:
            for eq_id in col['equipment']:
                threading.Thread(target=probe_equipment_health, args=(eq_id,), daemon=True).start()
        
        return jsonify({'success': True, 'message': 'Refresh tasks queued'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/fleet_data/save', methods=['POST'])
def api_fleet_data_save():
    """Save updated fleet layout and trigger immediate probe for new items"""
    try:
        data = request.get_json()
        if not data or 'columns' not in data:
            return jsonify({'success': False, 'error': 'Invalid data'}), 400
            
        save_data = {'columns': []}
        all_ids = []
        for col in data['columns']:
            eq_ids = [eq['id'] if isinstance(eq, dict) else eq for eq in col['equipment']]
            all_ids.extend(eq_ids)
            save_data['columns'].append({
                'id': col['id'],
                'title': col['title'],
                'main': col['main'],
                'back': col['back'],
                'phone': col['phone'],
                'comms': col['comms'],
                'color': col.get('color', '#9e9e9e'),
                'equipment': eq_ids
            })
            
        with open(FLEET_DATA_PATH, 'w') as f:
            json.dump(save_data, f, indent=2)
            
        for eq_id in all_ids:
            probe_equipment_health(eq_id)
            
        log_database('info', 'fleet_data', f'Fleet layout updated and probed by {request.remote_addr}')
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error saving fleet data: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ========================================
# ERROR HANDLERS
# ========================================

@app.errorhandler(404)
def not_found(error):
    """404 error handler"""
    request_id = get_request_id()
    if request.path.startswith('/api/'):
        return jsonify({"error": "Not found", "request_id": request_id}), 404
    return render_template(
        'error.html',
        error_code=404,
        error_message="Page not found",
        request_id=request_id
    ), 404

@app.errorhandler(500)
def internal_error(error):
    """500 error handler"""
    request_id = get_request_id()
    log_server('error', 'exception', f"Unhandled error: {error}", request_id=request_id)
    if request.path.startswith('/api/') or request.accept_mimetypes.accept_json:
        return jsonify({"error": "Internal server error", "request_id": request_id}), 500
    return render_template(
        'error.html',
        error_code=500,
        error_message="Internal server error",
        request_id=request_id
    ), 500

# ========================================
# STARTUP AND MAIN
# ========================================

# open_browser imported from app.background_tasks above

# ========================================
# SYSTEM TRAY MODE
# ========================================
class AutoTechTrayMode:
    """System tray application that runs Flask in background"""

    def __init__(self):
        self.icon = None
        self.flask_thread = None
        self.server_running = False

    def create_icon_image(self, color='green'):
        """Create a simple icon for the system tray"""
        if not TRAY_AVAILABLE or Image is None or ImageDraw is None:
            return None

        # Create 64x64 icon with wrench/tool symbol
        img = Image.new('RGB', (64, 64), color='white')
        draw = ImageDraw.Draw(img)

        # Draw a simple tool/wrench icon
        if color == 'green':
            fill_color = (34, 197, 94)  # Green when running
        elif color == 'red':
            fill_color = (239, 68, 68)  # Red when stopped
        else:
            fill_color = (156, 163, 175)  # Gray

        # Draw wrench shape
        draw.ellipse([20, 15, 44, 39], fill=fill_color)
        draw.rectangle([28, 35, 36, 55], fill=fill_color)
        draw.rectangle([25, 50, 39, 58], fill=fill_color)

        return img

    def start_flask_server(self):
        """Start Flask server in background thread"""
        if self.server_running:
            return "Already running"

        try:
            self.flask_thread = threading.Thread(
                target=lambda: app.run(
                    host='0.0.0.0',
                    port=8888,
                    debug=False,
                    use_reloader=False
                ),
                daemon=True
            )
            self.flask_thread.start()
            time.sleep(2)  # Wait for server to start

            self.server_running = True
            self.update_icon('green')
            return "AutoTech started successfully"
        except Exception as e:
            return f"Error starting AutoTech: {str(e)}"

    def stop_flask_server(self):
        """Stop Flask server (note: Flask doesn't support clean shutdown in threads)"""
        if not self.server_running:
            return "Not running"

        # Flask running in thread can't be easily stopped, so just exit
        self.show_notification("Stopping AutoTech...")
        if self.icon is not None:
            self.icon.stop()
        sys.exit(0)

    def restart_server(self):
        """Restart server (exit and let user restart manually)"""
        self.show_notification("Please restart AutoTech manually")
        if self.icon is not None:
            self.icon.stop()
        sys.exit(0)

    def open_browser(self):
        """Open AutoTech dashboard in default browser"""
        try:
            import webbrowser
            webbrowser.open("http://localhost:8888")
            return "Opening dashboard..."
        except Exception as e:
            return f"Error opening browser: {str(e)}"

    def update_icon(self, color):
        """Update tray icon color"""
        if self.icon:
            self.icon.icon = self.create_icon_image(color)

    def show_notification(self, message):
        """Show system notification"""
        if self.icon:
            self.icon.notify(message, "AutoTech")

    # Menu actions
    def action_open(self, icon, item):
        """Open dashboard"""
        msg = self.open_browser()
        self.show_notification(msg)

    def action_restart(self, icon, item):
        """Restart server"""
        self.restart_server()

    def action_exit(self, icon, item):
        """Exit tray application"""
        self.stop_flask_server()

    def create_menu(self):
        """Create system tray menu"""
        if pystray is None:
            return None
        return pystray.Menu(
            pystray.MenuItem("Open Dashboard", self.action_open, default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Restart Server", self.action_restart),
            pystray.MenuItem("Exit", self.action_exit)
        )

    def run(self):
        """Run the system tray application"""
        if not TRAY_AVAILABLE:
            print("ERROR: System tray mode requires pystray and pillow packages!")
            print("Run: pip install pystray pillow")
            sys.exit(1)

        # Start Flask server in background
        print_startup_banner()
        start_msg = self.start_flask_server()
        print(f"\n{start_msg}")
        print("AutoTech running in system tray (no window)")
        print("Right-click tray icon to access menu\n")

        # Create system tray icon
        icon_image = self.create_icon_image('green' if self.server_running else 'red')
        if pystray is not None:
            self.icon = pystray.Icon(
                "AutoTech",
                icon_image,
                "AutoTech Dashboard",
                menu=self.create_menu()
            )

        # Show startup notification
        if self.icon is not None:
            self.icon.notify(start_msg, "AutoTech")

            # Run the icon (blocking)
            self.icon.run()

if __name__ == '__main__':
    # Check for --tray flag
    if '--tray' in sys.argv:
        # System tray mode (no console window)
        tray_app = AutoTechTrayMode()
        tray_app.run()
    else:
        # Normal mode with console window
        # Display startup banner
        print_startup_banner()

        # Log server startup
        log_server('info', 'startup', f'Server starting on port 8888')
        log_server('info', 'startup', f'Network mode: {"ONLINE" if is_online_network() else "OFFLINE"}')

        # Start FrontRunner background monitor
        try:
            from tools import frontrunner_monitor
            base_dir = os.path.dirname(os.path.abspath(__file__))
            
            frontrunner_monitor.start_monitor(
                hostname="10.110.19.16",
                username="komatsu",
                password="M0dul1r@GRM2",
                cache_dir=base_dir,
                offline_mode=False  # monitor handles reachability each cycle
            )
            log_background('info', 'frontrunner_monitor', 'FrontRunner monitor started (dynamic online/offline)')
        except Exception as e:
            log_background('warning', 'frontrunner_monitor', f'FrontRunner monitor failed to start: {e}')

        # Start browser in separate thread
        browser_thread = threading.Thread(target=open_browser, daemon=True)
        browser_thread.start()

        # Start Dig Fleet Monitor background worker
        fleet_monitor_updater['thread'] = threading.Thread(target=fleet_monitor_worker, daemon=True)
        fleet_monitor_updater['thread'].start()
        fleet_monitor_updater['running'] = True

        # Development server configuration
        server_port = int(os.environ.get('AUTOTECH_PORT', 8888))
        try:
            app.run(
                host='0.0.0.0',  # Listen on all network interfaces (allows remote access)
                port=server_port,
                debug=True,
                use_reloader=False,  # Disabled - Windows caching issues. Restart manually after code changes.
                passthrough_errors=False  # Handle errors gracefully
            )
        except KeyboardInterrupt:
            print("\n\n[SHUTDOWN] AutoTech Web Dashboard stopped by user.")
            # Stop background monitor
            try:
                frontrunner_monitor.stop_monitor()
            except:
                pass
            sys.exit(0)
        except Exception as e:
            print(f"\n[ERROR] Startup Error: {e}")
            print("Please check that port 8888 is available and try again.")
            sys.exit(1)
