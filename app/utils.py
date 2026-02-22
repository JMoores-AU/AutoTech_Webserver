"""
app/utils.py
============
Shared helper functions for the AutoTech Web Dashboard.
No Flask route definitions. No mutable module-level state.

All functions that need shared state access it via `import app.state as state`
so they always read the live value, not a frozen import-time snapshot.
"""

import logging
import os
import re
import socket
import string
import sys
import time
from functools import wraps

import app.state as state
from app.config import (
    AUTO_TECH_CLIENT_DIR, BASE_DIR, EQUIPMENT_PROFILES,
    GATEWAY_IP, MOCK_EQUIPMENT_DB, MMS_SERVER,
    PLINK_CANDIDATES, PROBE_PORT
)

logger = logging.getLogger(__name__)

# Optional third-party imports (same pattern as main.py)
try:
    import paramiko
except ImportError:
    paramiko = None

try:
    import ping3
except ImportError:
    ping3 = None


# ========================================
# AUTHENTICATION
# ========================================

def login_required(f):
    """Decorator that returns 401 if the session is not authenticated."""
    from flask import jsonify, session as flask_session

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not flask_session.get('authenticated'):
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function


# ========================================
# NETWORK MODE DETECTION
# ========================================

def is_online_network(force_refresh: bool = False, ttl_seconds: int = 30) -> bool:
    """
    Live-ish network probe with a short TTL cache so UI and background
    processes can see changes without hammering the gateway.
    Reads/writes state._network_status_cache so the cache is shared across
    all callers (routes, background tasks, blueprints).
    """
    now = time.time()
    cache = state._network_status_cache
    if not force_refresh and (now - cache["ts"]) < ttl_seconds:
        return cache["online"]

    if os.getenv("T1_OFFLINE", "").strip() == "1":
        print("[MODE] Forced OFFLINE via T1_OFFLINE")
        online = False
    elif os.getenv("T1_FORCE_ONLINE", "").strip() == "1":
        print("[MODE] Forced ONLINE via T1_FORCE_ONLINE")
        online = True
    else:
        online = False
        try:
            with socket.create_connection((GATEWAY_IP, PROBE_PORT), timeout=1.5):
                print(f"[MODE] ONLINE tcp {GATEWAY_IP}:{PROBE_PORT}")
                online = True
        except Exception as e:
            print(f"[MODE] TCP probe failed: {e}")

        if not online and ping3:
            try:
                rtt = ping3.ping(GATEWAY_IP, timeout=1)
                online = rtt is not None
                print(f"[MODE] ICMP {'ONLINE' if online else 'OFFLINE'} rtt={rtt}")
            except Exception as e:
                print(f"[MODE] ICMP error: {e}")

    cache["ts"] = now
    cache["online"] = online
    return online


# ========================================
# PATH HELPERS
# ========================================

def resolve_plink_path():
    """Return the first plink.exe that exists from the preferred locations."""
    for candidate in PLINK_CANDIDATES:
        if candidate and os.path.exists(candidate):
            logger.debug(f"Using plink from: {candidate}")
            return candidate
    return None


def get_autotech_client_folder():
    """
    Find the autotech_client folder — checks multiple locations.
    USB structure: option 18 copies autotech_client/ contents to USB root,
      so Install_AutoTech_Client.bat is at X:\\, AutoTech\\ is at X:\\AutoTech\\
    Dev structure: project_root/autotech_client
    Returns (folder_path, error_message) tuple.
    """
    # Check 0: Frozen EXE running from USB root (X:\\AutoTech.exe)
    # Option 18 copies Install_AutoTech_Client.bat directly to USB root (X:\\)
    if getattr(sys, 'frozen', False):
        if os.path.exists(os.path.join(BASE_DIR, 'Install_AutoTech_Client.bat')):
            return BASE_DIR, None

    # Check 1: USB structure - E:\\AutoTech\\autotech_client (AutoTech.exe is at E:\\)
    usb_client_folder = os.path.join(BASE_DIR, "AutoTech", "autotech_client")
    if os.path.exists(usb_client_folder):
        return usb_client_folder, None

    # Check 2: Dev environment - autotech_client is inside project folder
    local_client_folder = os.path.join(BASE_DIR, "autotech_client")
    if os.path.exists(local_client_folder):
        return local_client_folder, None

    # Check 3: Search USB drives for AutoTech\\autotech_client
    for drive_letter in string.ascii_uppercase[3:]:  # D: through Z:
        drive = f"{drive_letter}:\\"
        if os.path.exists(drive):
            client_folder = os.path.join(drive, "AutoTech", "autotech_client")
            if os.path.exists(client_folder):
                return client_folder, None

    return None, "AutoTech Client folder not found. Run BUILD_WEBSERVER.bat to deploy the installer package."


# ========================================
# SSH / EQUIPMENT CONNECTIVITY
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
        except Exception:
            continue

    return None, f"Could not connect to {ip_address} with any credentials"


def check_ptx_reachable(ip_address: str, timeout: float = 3.0) -> bool:
    """
    Quick check if PTX is reachable via ping.
    Returns True if reachable, False otherwise.
    """
    if ping3:
        try:
            result = ping3.ping(ip_address, timeout=int(timeout))
            return result is not None
        except Exception:
            return False
    else:
        # Fallback to socket check on SSH port
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((ip_address, 22))
            sock.close()
            return result == 0
        except Exception:
            return False


def get_ptx_uptime(ip_address: str) -> dict:
    """
    Connect to PTX equipment via SSH and retrieve uptime.
    Uses dlog/gold credentials first (PTXC), then mms/modular (PTX10).

    Returns dict with:
        - success: bool
        - uptime_hours: float (hours since last reboot)
        - uptime_raw: str (raw uptime output)
        - ptx_type: str (PTXC or PTX10 based on which credential worked)
        - error: str (if failed)
    """
    import re

    if not paramiko:
        return {'success': False, 'error': 'paramiko library not available'}

    credentials = [
        {"user": "dlog", "password": "gold", "name": "PTXC"},
        {"user": "mms", "password": "modular", "name": "PTX10"}
    ]

    ssh = None
    ptx_type = None

    for cred in credentials:
        try:
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
            ptx_type = cred['name']
            logger.debug(f"Connected to {ip_address} with {cred['name']} credentials")
            break
        except Exception:
            if ssh:
                try:
                    ssh.close()
                except Exception:
                    pass
            ssh = None
            continue

    if not ssh:
        return {'success': False, 'error': f'Could not connect to {ip_address}'}

    try:
        stdin, stdout, stderr = ssh.exec_command("uptime", timeout=15)
        uptime_output = stdout.read().decode('utf-8', errors='ignore').strip()
        error_output = stderr.read().decode('utf-8', errors='ignore').strip()
        ssh.close()

        if error_output and not uptime_output:
            return {'success': False, 'error': f'Uptime command error: {error_output}'}

        if not uptime_output:
            return {'success': False, 'error': 'No uptime output received'}

        uptime_hours = 0.0

        # Pattern for "X days, H:MM" or "X day, H:MM"
        days_hours_match = re.search(r'up\s+(\d+)\s+days?,\s+(\d+):(\d+)', uptime_output)
        if days_hours_match:
            days = int(days_hours_match.group(1))
            hours = int(days_hours_match.group(2))
            minutes = int(days_hours_match.group(3))
            uptime_hours = (days * 24) + hours + (minutes / 60)
        else:
            hours_match = re.search(r'up\s+(\d+):(\d+)', uptime_output)
            if hours_match:
                hours = int(hours_match.group(1))
                minutes = int(hours_match.group(2))
                uptime_hours = hours + (minutes / 60)
            else:
                min_match = re.search(r'up\s+(\d+)\s+min', uptime_output)
                if min_match:
                    minutes = int(min_match.group(1))
                    uptime_hours = minutes / 60

        return {
            'success': True,
            'uptime_hours': round(uptime_hours, 2),
            'uptime_raw': uptime_output,
            'ptx_type': ptx_type
        }

    except Exception as e:
        if ssh:
            try:
                ssh.close()
            except Exception:
                pass
        return {'success': False, 'error': str(e)}


# ========================================
# EQUIPMENT SEARCH
# ========================================

def parse_ip_finder_output(query, output):
    """
    Parse the output from ip_export.sh script.
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
        if line.startswith('+') or '_OID_' in line:
            continue
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

        if line.lower().startswith('ptx ip is:'):
            ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
            if ip_match:
                result['ptx_ip'] = ip_match.group(1)

        if 'vehicle is' in line.lower():
            if 'online' in line.lower():
                result['vehicle_status'] = 'Online'
            elif 'offline' in line.lower():
                result['vehicle_status'] = 'Offline'

        if 'ptxc found' in line.lower():
            result['ptxc_found'] = True
            result['ptx_model'] = 'PTXC'

        if 'avi ip' in line.lower() and 'is' in line.lower():
            ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
            if ip_match:
                result['avi_ip'] = ip_match.group(1)

    # If no PTX IP found in extra lines, use network_ip from table
    if not result['ptx_ip'] and result.get('network_ip'):
        result['ptx_ip'] = result['network_ip']

    # If AVI IP not found from MMS, try equipment cache database
    if not result['avi_ip'] and state.EQUIPMENT_DB_PATH:
        try:
            from tools.equipment_db import get_equipment
            cached = get_equipment(state.EQUIPMENT_DB_PATH, query)
            if cached and cached.get('avi_ip'):
                result['avi_ip'] = cached['avi_ip']
        except Exception as e:
            logger.debug(f"Could not get cached AVI IP for {query}: {e}")

    # Calculate flight recorder IP for supported profiles
    if result['profile'] in ['K830E', 'K930E'] and result['ptx_ip']:
        parts = result['ptx_ip'].split('.')
        if len(parts) == 4:
            result['flight_recorder_IP'] = f"{parts[0]}.{parts[1]}.{parts[2]}.{int(parts[3]) + 1}"

    return result


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

        command = f"{MMS_SERVER['script']} {query}"
        stdin, stdout, stderr = ssh.exec_command(command, timeout=15)

        output = stdout.read().decode('utf-8', errors='ignore')
        error = stderr.read().decode('utf-8', errors='ignore')

        ssh.close()

        if error and 'not found' in error.lower():
            return {'found': False, 'error': f'Equipment not found: {query}'}

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
