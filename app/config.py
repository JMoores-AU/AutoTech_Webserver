"""
app/config.py
=============
Read-only constants for the AutoTech Web Dashboard.
No Flask imports. No mutable state. Safe to import from any module.

NOTE: BASE_DIR is computed from this file's location (app/config.py),
so we go up TWO directory levels to reach the project root.
"""

import os
import sys

# ========================================
# APPLICATION BASE DIRECTORY
# ========================================
if getattr(sys, 'frozen', False):
    # Running as PyInstaller executable
    BASE_DIR = os.path.dirname(sys.executable)
    meipass = getattr(sys, '_MEIPASS', BASE_DIR)  # type: ignore
    TEMPLATE_FOLDER = os.path.join(meipass, 'templates')
    STATIC_FOLDER = os.path.join(meipass, 'static')
else:
    # Running as Python script.
    # This file is at: <project_root>/app/config.py
    # Go up 2 levels: app/ -> project_root/
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    TEMPLATE_FOLDER = os.path.join(BASE_DIR, 'templates')
    STATIC_FOLDER = os.path.join(BASE_DIR, 'static')


def get_version():
    """Return version from VERSION file, works in frozen and dev modes."""
    if getattr(sys, 'frozen', False):
        version_path = os.path.join(getattr(sys, '_MEIPASS', BASE_DIR), 'VERSION')
    else:
        version_path = os.path.join(BASE_DIR, 'VERSION')
    try:
        with open(version_path, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return 'dev'


APP_VERSION = get_version()

# ========================================
# TOOL PATHS (Will be populated in main.py after app.utils is loaded)
# ========================================
TOOLS_DIR = os.path.join(BASE_DIR, 'T1_Tools_Web', 'tools')
PLINK_PATH = None
VNC_VIEWER_PATH = None
WINSCP_PATH = None
CLIENT_TOOLS_DIR = None # Will be set in main.py or a dedicated init function
CLIENT_PLINK_PATH = None

AUTO_TECH_CLIENT_DIR = os.environ.get('AUTOTECH_CLIENT_DIR', r"C:\AutoTech_Client")
AUTO_TECH_CLIENT_PLINK = os.path.join(AUTO_TECH_CLIENT_DIR, 'plink.exe')

PLINK_CANDIDATES = [
    AUTO_TECH_CLIENT_PLINK,
    # Other candidates can be added here or dynamically resolved
]

# VNC Viewer name for dynamic path resolution in playback blueprint
VNC_VIEWER_NAME = "vncviewer.exe"

# ========================================
# NETWORK CONFIGURATION
# ========================================
GATEWAY_IP = "10.110.19.107"
PTX_BASE_IP = "10.110.19.107"
PROBE_PORT = 22

# Server list for health monitoring
SERVERS = [
    {"name": "FrontRunner", "ip": "10.110.19.16", "port": 22},
    {"name": "Dispatch", "ip": "10.110.19.11", "port": 80},
    {"name": "OMS", "ip": "10.110.19.13", "port": 443},
    {"name": "BaseStation", "ip": "10.110.19.18", "port": 8002},
    {"name": "Monitor", "ip": "10.110.19.19", "port": 8002}
]

# MMS Server for IP Finder queries
MMS_SERVER = {
    'ip': '10.110.19.107',
    'port': 22,
    'user': 'mms',
    'password': 'komatsu',  # Default password
    'script': '/home/mms/bin/remote_check/Random/MySQL/ip_export.sh'
}

# Playback server configuration
PLAYBACK_SERVER = {
    'ip': '10.110.19.16',
    'port': 22,
    'user': 'komatsu',
    'password': 'M0dul1r@GRM2',
    'path': '/var/log/frontrunner/frontrunnerV3-3.7.0-076-full/playback/',
    'winscp_path': None # Will be populated later
}

# ========================================
# EQUIPMENT / TOOL CONFIGURATION
# ========================================
TOOL_LIST = [
    "IP Finder",
    "Playback Tools",
    "PTX Uptime",
    "FrontRunner Status",
    "Mineview Sessions",
    "KOA Data Check",
    "Speed Limit Data",
    "Component Tracking",
    "Watchdog Deploy",
    "Linux Health",
    "PTX Health Check",
    "AVI/MM2 Reboot",
    "VNC Viewer",
    "Flight Recorder",
    "Equipment Monitor",
    "Network Scanner",
    "System Diagnostics",
    "Log Viewer"
]

# Equipment profiles with Flight Recorder support
EQUIPMENT_PROFILES = {
    'K830E': {'has_flight_recorder': True, 'ptx_offset': 1},
    'K930E': {'has_flight_recorder': True, 'ptx_offset': 1},
    'Other': {'has_flight_recorder': False, 'ptx_offset': 0}
}

# Mock equipment database for offline / dev mode testing.
# Covers all meaningful combinations: EMV vs AT, all 3 PTX variants,
# with/without AVI, with/without flight recorder, healthy vs degraded.
MOCK_EQUIPMENT_DB = {
    # --- EMV (AHG) entries — no flight recorder ---
    'DEV_AHG_PTXC': {
        'OID': 'DEV_AHG_PTXC',
        'profile': 'AHG',
        'ptx_model': 'PTXC',        # Old PTXC — dlog/gold credentials
        'ptxc_found': True,
        'ptx_ip': '10.110.20.70',
        'avi_ip': None,             # Some EMVs have no AVI
        'flight_recorder_ip': None,
        'vehicle_status': 'Online',
        'ssh_status': 'Connected',
        'health': {
            'cpu_usage': '42.10%',
            'memory_usage': '58.30%',
            'uptime': '12 days, 4 hours',
            'disk_usage': '/dev/mmcblk0p3  5.6G  2.1G  3.2G  40% /media/realroot/home',
            'disk_percent': '40%',
        },
    },
    'DEV_AHG_PTX10': {
        'OID': 'DEV_AHG_PTX10',
        'profile': 'AHG',
        'ptx_model': 'PTX10',       # PTX10 — mms/modular, x86_64
        'ptxc_found': False,
        'ptx_ip': '10.110.20.95',
        'avi_ip': '10.111.20.96',
        'flight_recorder_ip': None,
        'vehicle_status': 'Online',
        'ssh_status': 'Connected',
        'health': {
            'cpu_usage': '31.50%',
            'memory_usage': '44.20%',
            'uptime': '3 days, 18 hours',
            'disk_usage': '/dev/sda1  20G  7.2G  12G  38% /home',
            'disk_percent': '38%',
        },
    },
    'DEV_AHG_PTXCNEW': {
        'OID': 'DEV_AHG_PTXCNEW',
        'profile': 'AHG',
        'ptx_model': 'PTXC (New OS)',   # New-OS PTXC — mms/modular, ARM
        'ptxc_found': False,
        'ptx_ip': '10.110.20.110',
        'avi_ip': '10.111.20.111',
        'flight_recorder_ip': None,
        'vehicle_status': 'Degraded',   # Critical health — exercises Reboot PTX button
        'ssh_status': 'Connected',
        'health': {
            'cpu_usage': '87.40%',
            'memory_usage': '91.20%',
            'uptime': '0 days, 3 hours',
            'disk_usage': '/dev/mmcblk0p3  5.6G  5.1G  0.3G  95% /media/realroot/home',
            'disk_percent': '95%',
        },
    },
    # --- AT (Autonomous Truck) entries — K830E/K930E, includes flight recorder ---
    'DEV_K830E': {
        'OID': 'DEV_K830E',
        'profile': 'K830E',
        'ptx_model': 'PTXC',        # Old PTXC — dlog/gold credentials
        'ptxc_found': True,
        'ptx_ip': '10.110.19.190',
        'avi_ip': '10.111.19.191',
        'flight_recorder_ip': '10.110.19.191',  # PTX last octet + 1
        'vehicle_status': 'Online',
        'ssh_status': 'Connected',
        'health': {
            'cpu_usage': '55.60%',
            'memory_usage': '72.30%',
            'uptime': '7 days, 22 hours',
            'disk_usage': '/dev/mmcblk0p3  5.6G  3.8G  1.5G  72% /media/realroot/home',
            'disk_percent': '72%',
        },
    },
    'DEV_K930E': {
        'OID': 'DEV_K930E',
        'profile': 'K930E',
        'ptx_model': 'PTX10',       # PTX10 — mms/modular, x86_64
        'ptxc_found': False,
        'ptx_ip': '10.110.21.111',
        'avi_ip': '10.111.21.112',
        'flight_recorder_ip': '10.110.21.112',  # PTX last octet + 1
        'vehicle_status': 'Online',
        'ssh_status': 'Connected',
        'health': {
            'cpu_usage': '28.90%',
            'memory_usage': '51.70%',
            'uptime': '21 days, 9 hours',
            'disk_usage': '/dev/sda1  20G  9.1G  10G  48% /home',
            'disk_percent': '48%',
        },
    },
}

# ========================================
# DATABASE / DATA FILE PATHS
# ========================================

def resolve_data_path(base_dir: str, filename: str) -> str:
    """Centralized path resolver for database and config files."""
    # Try USB structure first (E:\AutoTech\database\filename)
    usb_path = os.path.join(base_dir, "AutoTech", "database", filename)
    if os.path.exists(os.path.join(base_dir, "AutoTech")):
        return usb_path
    # Fallback to dev structure (project\database\filename)
    return os.path.join(base_dir, "database", filename)


FLEET_DATA_PATH = resolve_data_path(BASE_DIR, 'fleet_data.json')

# IP_list.dat path for importing equipment list
# Check multiple locations: USB legacy folder first, then local database folder
_ip_list_candidates = [
    os.path.join(BASE_DIR, 'T1_Tools_Legacy', 'bin', 'IP_list.dat'),  # USB: X:\T1_Tools_Legacy\bin\
    os.path.join(BASE_DIR, 'AutoTech', 'database', 'IP_list.dat'),    # USB frozen: X:\AutoTech\database\
    os.path.join(BASE_DIR, 'database', 'IP_list.dat'),                 # Local dev: project\database\
]
IP_LIST_PATH = next((p for p in _ip_list_candidates if os.path.exists(p)), _ip_list_candidates[-1])