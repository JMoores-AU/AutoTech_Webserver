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
    login_required, is_online_network, check_network_connectivity,
    resolve_plink_path, get_autotech_client_folder, connect_to_equipment,
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
from app.blueprints.frontrunner import bp as frontrunner_bp
from app.blueprints.log_cleanup import bp as log_cleanup_bp
from app.blueprints.admin_logs import bp as admin_logs_bp
from app.blueprints.ptx_reboot import bp as ptx_reboot_bp
from app.blueprints.vnc import bp as vnc_bp
from app.blueprints.usb_client import bp as usb_client_bp
from app.blueprints.system_health import bp as system_health_bp
from app.blueprints.fleet_monitor import bp as fleet_monitor_bp
from app.blueprints.tools_launch import bp as tools_launch_bp
from app.blueprints.ptx_uptime import bp as ptx_uptime_bp
app.register_blueprint(auth_bp)
app.register_blueprint(info_pages_bp)
app.register_blueprint(downloads_bp)
app.register_blueprint(frontrunner_bp)
app.register_blueprint(log_cleanup_bp)
app.register_blueprint(admin_logs_bp)
app.register_blueprint(ptx_reboot_bp)
app.register_blueprint(vnc_bp)
app.register_blueprint(usb_client_bp)
app.register_blueprint(system_health_bp)
app.register_blueprint(fleet_monitor_bp)
app.register_blueprint(tools_launch_bp)
app.register_blueprint(ptx_uptime_bp)
from app.blueprints.playback import bp as playback_bp
app.register_blueprint(playback_bp)
from app.blueprints.equipment import bp as equipment_bp
app.register_blueprint(equipment_bp)
from app.blueprints.legacy_terminal import bp as legacy_terminal_bp
app.register_blueprint(legacy_terminal_bp)
from app.blueprints.dashboard import bp as dashboard_bp
app.register_blueprint(dashboard_bp)

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
# is_online_network, check_network_connectivity imported from app.utils above

def find_ip_address(hostname):
    """Find IP address from hostname - CENTRALIZED FUNCTION"""
    try:
        ip_address = socket.gethostbyname(hostname)
        return ip_address
    except socket.gaierror:
        raise Exception(f"Unable to resolve hostname: {hostname}")

# All routes have been moved to blueprints under app/blueprints/

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
