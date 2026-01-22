#!/usr/bin/env python3
"""
AUTOTECH WEB DASHBOARD - ENHANCED MAIN APPLICATION
================================================================
Mining equipment remote access system for Komatsu equipment
Enhanced version combining new design with full functionality
================================================================
"""

# Standard Library Imports
import csv
import json
import logging
import os
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
from datetime import datetime, timedelta
from functools import lru_cache, wraps
from io import StringIO
from pathlib import Path
from typing import Optional
from tools.log_cleanup import cleanup_logs


# Third-Party Imports
try:
    import paramiko
except ImportError:
    paramiko = None

try:
    import ping3
except ImportError:
    ping3 = None

try:
    import requests
except ImportError:
    requests = None

from flask import Flask, render_template, request, session, redirect, url_for, jsonify, flash, Response, make_response, send_file
from flask_cors import CORS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========================================
# APPLICATION BASE DIRECTORY
# ========================================
if getattr(sys, 'frozen', False):
    # Running as PyInstaller executable
    BASE_DIR = os.path.dirname(sys.executable)
    # PyInstaller extracts to temp folder, but we bundled templates/static
    # sys._MEIPASS is added by PyInstaller at runtime (not available during linting)
    meipass = getattr(sys, '_MEIPASS', BASE_DIR)  # type: ignore
    template_folder = os.path.join(meipass, 'templates')
    static_folder = os.path.join(meipass, 'static')
else:
    # Running as Python script
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    template_folder = os.path.join(BASE_DIR, 'templates')
    static_folder = os.path.join(BASE_DIR, 'static')

TOOLS_DIR = os.path.join(BASE_DIR, 'AutoTech', 'tools')
PLINK_PATH = os.path.join(TOOLS_DIR, 'plink.exe')
VNC_VIEWER_PATH = os.path.join(TOOLS_DIR, 'vncviewer_5.3.2.exe')

# AutoTech Client tools path (for T1 Legacy scripts)
# USB: E:\AutoTech\autotech_client\tools  |  Dev: project\autotech_client\tools
CLIENT_TOOLS_DIR = os.path.join(BASE_DIR, 'AutoTech', 'autotech_client', 'tools')
if not os.path.exists(CLIENT_TOOLS_DIR):
    # Fallback to dev structure
    CLIENT_TOOLS_DIR = os.path.join(BASE_DIR, 'autotech_client', 'tools')
CLIENT_PLINK_PATH = os.path.join(CLIENT_TOOLS_DIR, 'plink.exe')

logger.info(f"Application Base Directory: {BASE_DIR}")
logger.info(f"Tools Directory: {TOOLS_DIR}")
logger.info(f"Client Tools Directory: {CLIENT_TOOLS_DIR}")
logger.info(f"Template Folder: {template_folder}")
logger.info(f"Static Folder: {static_folder}")

# NOW we can create the Flask app
app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)
app.secret_key = "komatsu-t1-tools-secret-key-change-in-production"
CORS(app)

# Extended tool list with all functionality
TOOL_LIST = [
    "IP Finder", 
    "Playback Tools",
    "PTX Uptime", 
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

# Network configuration - FIXED: Use consistent IP reference
GATEWAY_IP = "10.110.19.107"  # CORRECTED from 10.110.19.1
PTX_BASE_IP = "10.110.19.107"
PROBE_PORT = 22

# Mock equipment database for testing
MOCK_EQUIPMENT_DB = {
    'RD111': {
        'OID': 'RD111',
        'profile': 'K930E',
        'ptx_model': 'PTX10',
        'ptx_ip': '10.110.20.110',
        'avi_ip': '10.111.21.112',
        'flight_recorder_ip': '10.110.20.111',
        'vehicle_status': 'Online',
        'ptxc_found': False,
        'ssh_status': 'Connected'
    },
    'RD190': {
        'OID': 'RD190',
        'profile': 'K830E',
        'ptx_model': 'PTXC',
        'ptx_ip': '10.110.19.190',
        'avi_ip': '10.111.19.191',
        'flight_recorder_ip': '10.110.19.191',
        'vehicle_status': 'Online',
        'ptxc_found': True,
        'ssh_status': 'Connected'
    },
    'AHG135': {
        'OID': 'AHG135',
        'profile': 'PTX10',
        'ptx_model': 'PTX10',
        'ptx_ip': '10.110.19.135',
        'avi_ip': None,
        'flight_recorder_ip': None,
        'vehicle_status': 'Online',
        'ptxc_found': False,
        'ssh_status': 'Connected'
    }
}

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

# Global variable to track active TRU connections
active_tru_connections = {}

# ========================================
# AUTHENTICATION AND UTILITY FUNCTIONS
# ========================================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

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

@lru_cache(maxsize=1)
def is_online_network() -> bool:
    """True on closed network; False on laptop/dev."""
    if os.getenv("T1_OFFLINE", "").strip() == "1":
        print("[MODE] Forced OFFLINE via T1_OFFLINE")
        return False
    if os.getenv("T1_FORCE_ONLINE", "").strip() == "1":
        print("[MODE] Forced ONLINE via T1_FORCE_ONLINE")
        return True

    try:
        with socket.create_connection((GATEWAY_IP, PROBE_PORT), timeout=1.5):
            print(f"[MODE] ONLINE tcp {GATEWAY_IP}:{PROBE_PORT}")
            return True
    except Exception as e:
        print(f"[MODE] TCP probe failed: {e}")

    if ping3:
        try:
            rtt = ping3.ping(GATEWAY_IP, timeout=1)
            ok = rtt is not None
            print(f"[MODE] ICMP {'ONLINE' if ok else 'OFFLINE'} rtt={rtt}")
            return ok
        except Exception as e:
            print(f"[MODE] ICMP error: {e}")
            return False
    
    return False

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

def search_equipment(query):
    """
    Search for equipment by name or IP via SSH to MMS server.
    In offline mode, returns mock/simulated data.
    """
    query = query.strip().upper()
    
    # Check if query is in mock database first (for testing)
    if query in MOCK_EQUIPMENT_DB:
        equipment = MOCK_EQUIPMENT_DB[query].copy()
        equipment['found'] = True
        equipment['search_method'] = 'database'
        return equipment
    
    # If offline, return simulated data
    if not is_online_network():
        return {
            'OID': query,
            'profile': 'Simulated',
            'ptx_model': 'PTX10',
            'ptx_ip': f'10.110.19.{len(query) * 10 % 255}',
            'avi_ip': None,
            'flight_recorder_ip': None,
            'vehicle_status': 'Simulated',
            'ptxc_found': False,
            'ssh_status': 'Simulated',
            'found': True,
            'search_method': 'simulation'
        }
    
    # Online mode - query MMS server via SSH
    if not paramiko:
        return {'found': False, 'error': 'SSH library not available'}
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        ssh.connect(
            MMS_SERVER['ip'],
            port=MMS_SERVER['port'],
            username=MMS_SERVER['user'],
            password=MMS_SERVER['password'],
            timeout=10
        )
        
        # Run the ip_export.sh script
        command = f"{MMS_SERVER['script']} {query}"
        stdin, stdout, stderr = ssh.exec_command(command, timeout=15)
        
        output = stdout.read().decode('utf-8', errors='ignore')
        error = stderr.read().decode('utf-8', errors='ignore')
        
        ssh.close()
        
        if error and 'not found' in error.lower():
            return {'found': False, 'error': f'Equipment not found: {query}'}
        
        # Parse the output
        return parse_ip_finder_output(query, output)
        
    except paramiko.AuthenticationException:
        logger.error("MMS server authentication failed")
        return {'found': False, 'error': 'Authentication failed'}
    except paramiko.SSHException as e:
        logger.error(f"SSH connection error: {e}")
        return {'found': False, 'error': f'Connection failed: {str(e)}'}
    except Exception as e:
        logger.error(f"Equipment search error: {e}")
        return {'found': False, 'error': str(e)}


def parse_ip_finder_output(query, output):
    """
    Parse the output from ip_export.sh script.
    
    Example output:
    +--------+-------------+----------+--------------+
    | _OID_  | _CID_       | _profile | network_ip   |
    +--------+-------------+----------+--------------+
    | GRD155 | eqmt_grader | CAT 24M  | 10.110.21.36 |
    +--------+-------------+----------+--------------+
    
    PTX IP is: 10.110.21.36
    Vehicle is Online.
    
    PTXC Found.
    
    AVI IP is : 10.111.218.82
    """
    result = {
        'OID': query,
        'profile': 'Unknown',
        'ptx_model': 'PTX10',
        'ptx_ip': None,
        'avi_ip': None,
        'vehicle_status': 'Unknown',
        'ptxc_found': False,
        'found': False,
        'search_method': 'mms_server'
    }
    
    if not output or not output.strip():
        return result
    
    lines = output.strip().split('\n')
    
    # Parse table data - look for the data row (not header, not border)
    for line in lines:
        # Skip border lines and header
        if line.startswith('+') or '_OID_' in line:
            continue
        # Data row starts with | and contains actual data
        if line.startswith('|') and '|' in line[1:]:
            parts = [p.strip() for p in line.split('|') if p.strip()]
            if len(parts) >= 4 and parts[0].upper() == query:
                result['OID'] = parts[0]
                result['cid'] = parts[1] if len(parts) > 1 else None
                result['profile'] = parts[2] if len(parts) > 2 else 'Unknown'
                result['network_ip'] = parts[3] if len(parts) > 3 else None
                result['found'] = True
                break
    
    # Parse additional fields from output
    for line in lines:
        line = line.strip()
        
        # PTX IP
        if line.lower().startswith('ptx ip is:'):
            ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
            if ip_match:
                result['ptx_ip'] = ip_match.group(1)
        
        # Vehicle status
        if 'vehicle is' in line.lower():
            if 'online' in line.lower():
                result['vehicle_status'] = 'Online'
            elif 'offline' in line.lower():
                result['vehicle_status'] = 'Offline'
        
        # PTXC Found
        if 'ptxc found' in line.lower():
            result['ptxc_found'] = True
            result['ptx_model'] = 'PTXC'
        
        # AVI IP
        if line.lower().startswith('avi ip'):
            ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
            if ip_match:
                result['avi_ip'] = ip_match.group(1)
    
    # If no PTX IP found in extra lines, use network_ip from table
    if not result['ptx_ip'] and result.get('network_ip'):
        result['ptx_ip'] = result['network_ip']
    
    # Calculate flight recorder IP for supported profiles
    if result['profile'] in ['K830E', 'K930E'] and result['ptx_ip']:
        parts = result['ptx_ip'].split('.')
        if len(parts) == 4:
            result['flight_recorder_ip'] = f"{parts[0]}.{parts[1]}.{parts[2]}.{int(parts[3]) + 1}"
    
    return result

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

def connect_to_equipment(ip_address):
    """
    Try to connect to equipment using both credential sets.
    Returns: (ssh_client, credential_name) or (None, error_message)
    """
    credentials = [
        {"user": "dlog", "password": "gold", "name": "PTXC"},
        {"user": "mms", "password": "modular", "name": "PTX10"}
    ]
    
    for cred in credentials:
        try:
            if paramiko is None:
                return None, "paramiko library not available"
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(
                hostname=ip_address,
                username=cred['user'],
                password=cred['password'],
                timeout=10,
                look_for_keys=False,
                allow_agent=False
            )
            return ssh, cred['name']
        except Exception as e:
            continue
    
    return None, f"Could not connect to {ip_address} with any credentials"


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

# ========================================
# AUTHENTICATION ROUTES
# ========================================

@app.before_request
def require_login():
    """Simple password protection"""
    if request.endpoint in ['static', 'login'] or request.path.startswith('/static/'):
        return
    
    if 'authenticated' not in session and request.endpoint != 'dashboard':
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Simple login form"""
    if request.method == 'POST':
        password = request.form.get('password')
        if password == 'komatsu':
            session['authenticated'] = True
            session['password'] = password
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='Invalid password')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout and clear session"""
    session.clear()
    return redirect(url_for('login'))

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
    
    # CRITICAL: Always use enhanced_index.html, never index.html
    return render_template("enhanced_index.html", **dashboard_data)

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

@app.route('/api/equipment_profiles')
def equipment_profiles():
    """Equipment profiles API"""
    return jsonify(EQUIPMENT_PROFILES)

@app.route('/api/equipment_search', methods=['POST'])
@login_required
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
@login_required
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
        
        # Try to launch VNC viewer (Windows)
        import subprocess
        vnc_path = r"C:\Program Files\RealVNC\VNC Viewer\vncviewer.exe"
        
        try:
            subprocess.Popen([vnc_path, f"{ip}:{port}"], 
                           creationflags=subprocess.CREATE_NEW_CONSOLE)
            return jsonify({
                'success': True,
                'message': f'VNC viewer launched for {ip}:{port}'
            })
        except FileNotFoundError:
            # VNC viewer not installed, return info for browser fallback
            return jsonify({
                'success': False,
                'message': 'VNC viewer not found. Use browser VNC client.',
                'vnc_url': f'vnc://{ip}:{port}'
            })
        
    except Exception as e:
        logger.error(f"VNC connection error: {e}")
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/vnc/start', methods=['POST'])
@login_required
def api_vnc_start():
    """
    Start VNC session using plink.exe exactly like Start_VNC.bat
    
    Uses plink to run MMS script, then launches VNC viewer
    """
    try:
        data = request.get_json()
        ptx_ip = data.get('ptx_ip')
        equipment_name = data.get('equipment_name', 'Unknown')
        
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
        
        # Find plink.exe (on USB drive in tools folder)
        plink_path = PLINK_PATH
        if not os.path.exists(plink_path):
            return jsonify({
                'success': False,
                'message': f'plink.exe not found at: {PLINK_PATH}'
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
            
            # Launch VNC viewer to PTX_IP:0 (exactly like batch file)
            vnc_target = f'{ptx_ip}:0'
            
            # Launch VNC viewer with flags to bypass unencrypted warning
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
            
            logger.info(f"VNC: Launched viewer to {vnc_target}")
            
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
@login_required
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
@login_required
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
        
        # Find plink.exe on USB
        plink_path = PLINK_PATH
        if not os.path.exists(plink_path):
            return jsonify({
                'success': False,
                'message': f'plink.exe not found at: {PLINK_PATH}'
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
        password = session.get("password")
        online = is_online_network()
        
        # Check for offline testing mode parameter
        offline_test = request.args.get('offline_test', 'false').lower() == 'true'
        
        # PTX uptime data would be fetched here
        ptx_data = {
            'tool_name': 'PTX Uptime',
            'online': online,
            'offline_test': offline_test,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'gateway_ip': GATEWAY_IP
        }
        
        return render_template('ptx_uptime.html', **ptx_data)
        
    except Exception as e:
        logger.error(f"PTX Uptime error: {e}")
        flash(f"PTX Uptime failed: {e}", "error")
        return redirect(url_for('dashboard'))

# ========================================
# USB TOOLS API ENDPOINTS
# ========================================

@app.route("/api/usb/scan/<tool_id>")
@login_required
def api_usb_scan(tool_id):
    """
    Scan USB drives for a specific tool.
    tool_id: 'camstudio' or 'playback'
    """
    try:
        if tool_id == 'camstudio':
            from tools.camstudio_usb import scan
            result = scan()
        elif tool_id == 'playback':
            from tools.playback_usb import scan
            result = scan()
        else:
            return jsonify({'error': f'Unknown tool: {tool_id}'}), 400
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"USB scan error for {tool_id}: {e}")
        return jsonify({'error': str(e)}), 500


@app.route("/api/usb/launch/<tool_id>", methods=["POST"])
@login_required
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
@login_required
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


# ========================================
# PLAYBACK SERVER API ENDPOINTS
# ========================================

# Playback server configuration
PLAYBACK_SERVER = {
    'ip': '10.110.19.16',
    'port': 22,
    'user': 'komatsu',
    'password': 'M0dul1r@GRM2',
    'path': '/var/log/frontrunner/frontrunnerV3-3.7.0-076-full/playback/'
}

@app.route("/api/playback/server-check")
@login_required
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
@login_required
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
@login_required
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
@login_required
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
@login_required
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


@app.route("/api/playback/download-file", methods=["POST"])
@login_required
def api_playback_download_file():
    """
    Download a file from the server to the local USB playback folder.
    Uses progress tracking via global dict.
    """
    try:
        data = request.get_json()
        filename = data.get('filename')
        file_size = data.get('size', 0)

        if not filename:
            return jsonify({'success': False, 'message': 'Filename required'})

        # OFFLINE MODE: Simulate successful download
        if not is_online_network():
            return jsonify({
                'success': True,
                'message': f'[OFFLINE MODE] Simulated download of {filename}',
                'local_path': f'USB:/playback/{filename}',
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

        # Connect and download
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
            return jsonify({'success': False, 'message': f'Connection failed: {str(e)}'})
        
        sftp = ssh.open_sftp()
        
        # Get file size if not provided
        if not file_size:
            try:
                file_attr = sftp.stat(remote_path)
                file_size = file_attr.st_size
            except:
                file_size = 0
        
        # Progress tracking
        progress_data = {'transferred': 0, 'total': file_size, 'percent': 0}
        
        def progress_callback(transferred, total):
            progress_data['transferred'] = transferred
            progress_data['total'] = total
            if total > 0:
                progress_data['percent'] = int((transferred / total) * 100)
        
        try:
            sftp.get(remote_path, str(local_path), callback=progress_callback)
        except Exception as e:
            sftp.close()
            ssh.close()
            return jsonify({'success': False, 'message': f'Download failed: {str(e)}'})
        
        sftp.close()
        ssh.close()
        
        # Verify file was downloaded
        if local_path.exists():
            final_size = local_path.stat().st_size
            return jsonify({
                'success': True,
                'message': f'Downloaded {filename}',
                'local_path': str(local_path),
                'size': final_size
            })
        else:
            return jsonify({'success': False, 'message': 'File not found after download'})
        
    except Exception as e:
        logger.error(f"Download file error: {e}")
        return jsonify({'success': False, 'message': str(e)})


@app.route("/api/playback/find-files")
@login_required
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
@login_required
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
# PTX EQUIPMENT MANAGEMENT APIS
# ========================================

@app.route("/api/ptx_reboot", methods=["POST"])
@login_required
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
@login_required
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

terminal_sessions = {}

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


@app.route('/autotech')
@app.route('/legacy')  # Keep legacy route for backwards compatibility
@login_required
def autotech_tools():
    """AutoTech Tools page with IP Finder only"""
    return render_template('t1_legacy.html',
                         online=is_online_network(),
                         gateway_ip=GATEWAY_IP)


def get_autotech_client_folder():
    """
    Find the autotech_client folder - checks multiple locations.
    USB structure: E:/AutoTech/autotech_client (inside AutoTech folder)
    Dev structure: project_root/autotech_client
    Returns (folder_path, error_message) tuple.
    """
    import string

    # Check 1: USB structure - E:\AutoTech\autotech_client (AutoTech.exe is at E:\)
    # When running as EXE, BASE_DIR is E:\ so check E:\AutoTech\autotech_client
    usb_client_folder = os.path.join(BASE_DIR, "AutoTech", "autotech_client")
    if os.path.exists(usb_client_folder):
        return usb_client_folder, None

    # Check 2: Dev environment - autotech_client is inside project folder
    local_client_folder = os.path.join(BASE_DIR, "autotech_client")
    if os.path.exists(local_client_folder):
        return local_client_folder, None

    # Check 3: Search USB drives for AutoTech\autotech_client
    for drive_letter in string.ascii_uppercase[3:12]:  # D: through L:
        drive = f"{drive_letter}:\\"
        if os.path.exists(drive):
            # Check for AutoTech\autotech_client structure
            client_folder = os.path.join(drive, "AutoTech", "autotech_client")
            if os.path.exists(client_folder):
                return client_folder, None

    return None, "AutoTech Client folder not found. Run BUILD_WEBSERVER.bat to deploy the installer package."


@app.route('/download-client-setup')
@login_required
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
@login_required
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
@login_required
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
@login_required
def api_check_client_installed():
    """
    Check if AutoTech Client is installed on the server machine.
    This helps determine if the install info box should be shown.
    Checks for the existence of C:\\AutoTech_Client folder.
    """
    client_install_path = "C:\\AutoTech_Client"
    is_installed = os.path.exists(client_install_path)

    # Also check if key files exist
    if is_installed:
        has_scripts = os.path.exists(os.path.join(client_install_path, "mms_scripts"))
        has_tools = os.path.exists(os.path.join(client_install_path, "plink.exe")) or \
                    os.path.exists(os.path.join(client_install_path, "putty.exe"))
        is_installed = has_scripts or has_tools

    return jsonify({
        'installed': is_installed,
        'path': client_install_path if is_installed else None
    })


@app.route('/api/launch-batch-tool', methods=['POST'])
@login_required
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
@login_required
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


@app.route('/api/legacy/terminal/start', methods=['POST'])
@login_required
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
@login_required
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
@login_required
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
@login_required
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
@login_required
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
@login_required
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

        # OFFLINE MODE: Simulate script execution when network is unavailable
        if not is_online_network():
            mock_equipment_ip = None
            mock_equipment_status = 'offline'

            # Set mock IP for equipment that requires it
            if equipment and script.get('requires_equipment'):
                mock_equipment_ip = '10.110.88.88'
                mock_equipment_status = 'offline'

            # Generic offline simulation
            output_lines = []
            output_lines.append(f"[OFFLINE MODE] {script['name']}")
            output_lines.append(f"Description: {script['description']}")

            if equipment:
                output_lines.append(f"Equipment: {equipment}")
                if mock_equipment_ip:
                    output_lines.append(f"Equipment IP: {mock_equipment_ip}")
                    output_lines.append(f"Status: {mock_equipment_status.upper()}")

            output_lines.extend([
                "",
                "Network offline - connect to MMS network for live data.",
                "TIP: Enter 'TEST' as equipment to see mock data.",
                ""
            ])

            return jsonify({
                'success': True,
                'output': '\n'.join(output_lines),
                'message': f'{script["name"]} (offline mode)',
                'equipment_status': mock_equipment_status,
                'equipment_ip': mock_equipment_ip,
                'avi_ip': None,
                'ptx_model': None
            })

        # ONLINE MODE: Execute via plink
        # Check if plink exists
        plink_path = PLINK_PATH
        if not os.path.exists(plink_path):
            return jsonify({
                'success': False,
                'message': f'plink.exe not found at: {plink_path}'
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

        # Initialize AVI IP and PTX model
        avi_ip = None
        ptx_model = None

        if equipment and script.get('requires_equipment'):
            # Use mock data for TEST equipment
            if is_test_equipment:
                equipment_ip = '10.110.99.99'
                avi_ip = '10.111.219.99'
                ptx_model = 'PTXC'
                equipment_status = 'online'

                # Generate mock script output based on script type
                mock_output = generate_mock_script_output(script_name, equipment, equipment_ip)

                return jsonify({
                    'success': True,
                    'output': mock_output,
                    'message': f'{script["name"]} executed successfully',
                    'equipment_status': equipment_status,
                    'equipment_ip': equipment_ip,
                    'avi_ip': avi_ip,
                    'ptx_model': ptx_model
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
                for line in ip_result.stdout.split('\n'):
                    if 'PTX IP is:' in line:
                        equipment_ip = line.split('PTX IP is:')[1].strip()
                    elif 'AVI IP is:' in line:
                        avi_ip = line.split('AVI IP is:')[1].strip()
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
                        parts = [p.strip() for p in line.split('|') if p.strip()]
                        if len(parts) >= 4:
                            equipment_ip = parts[3]  # 4th column is network_ip

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
                return jsonify({
                    'success': True,
                    'output': full_output,
                    'message': f'{script["name"]} executed successfully',
                    'equipment_status': equipment_status,
                    'equipment_ip': equipment_ip,
                    'avi_ip': avi_ip,
                    'ptx_model': ptx_model
                })
            else:
                return jsonify({
                    'success': False,
                    'output': full_output,
                    'message': f'{script["name"]} failed with code {result.returncode}',
                    'equipment_status': equipment_status,
                    'equipment_ip': equipment_ip,
                    'avi_ip': avi_ip,
                    'ptx_model': ptx_model
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
@login_required
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
@login_required
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
                plink_path = PLINK_PATH
                if not os.path.exists(plink_path):
                    return jsonify({'success': False, 'message': f'plink.exe not found'})
                
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
@login_required
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
@login_required
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
@login_required
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
# ERROR HANDLERS
# ========================================

@app.errorhandler(404)
def not_found(error):
    """404 error handler"""
    return render_template('error.html', 
                         error_code=404,
                         error_message="Page not found"), 404

@app.errorhandler(500)
def internal_error(error):
    """500 error handler"""
    return render_template('error.html',
                         error_code=500,
                         error_message="Internal server error"), 500

# ========================================
# STARTUP AND MAIN
# ========================================

def open_browser():
    """Open browser to the application URL after a short delay"""
    time.sleep(2)  # Wait for Flask to start
    try:
        if platform.system() == "Windows":
            # Try Edge first, fallback to default browser
            edge_paths = [
                r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
            ]
            
            edge_found = False
            for edge_path in edge_paths:
                if os.path.exists(edge_path):
                    subprocess.Popen([edge_path, "http://localhost:8888"])
                    edge_found = True
                    break
            
            if not edge_found:
                # Fallback to default browser
                import webbrowser
                webbrowser.open("http://localhost:8888")
        else:
            import webbrowser
            webbrowser.open("http://localhost:8888")
    except Exception as e:
        print(f"Failed to open browser: {e}")

if __name__ == '__main__':
    # Display startup banner
    print_startup_banner()

    # Start browser in separate thread
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()

    # Development server configuration
    try:
        app.run(
            host='0.0.0.0',  # Listen on all network interfaces (allows remote access)
            port=8888,
            debug=True,
            use_reloader=False,  # Disabled - Windows caching issues. Restart manually after code changes.
            passthrough_errors=False  # Handle errors gracefully
        )
    except KeyboardInterrupt:
        print("\n\n[SHUTDOWN] AutoTech Web Dashboard stopped by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] Startup Error: {e}")
        print("Please check that port 8888 is available and try again.")
        sys.exit(1)