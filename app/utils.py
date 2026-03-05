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
import shutil # Import shutil for shutil.which
from functools import wraps
from typing import Optional # Import Optional

import app.state as state
from app.config import (
    BASE_DIR, GATEWAY_IP, PROBE_PORT, PLINK_CANDIDATES,
    MOCK_EQUIPMENT_DB, MMS_SERVER,
)

# AUTO_TECH_CLIENT_DIR defined locally so tests can monkeypatch without touching app.config
AUTO_TECH_CLIENT_DIR = os.environ.get('AUTOTECH_CLIENT_DIR', r"C:\AutoTech_Client")

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


def _resolve_tool_executable_path(tool_name: str, sub_dir: str = "tools") -> Optional[str]:
    """
    Resolves the full path to an executable tool, prioritizing:
    1. Bundled location (e.g., BASE_DIR/AutoTech/tools/tool_name)
    2. Dev location (e.g., BASE_DIR/tools/tool_name)
    3. System PATH
    """
    # 1. Try bundled location (for PyInstaller/USB deployment structure)
    bundled_path = os.path.join(BASE_DIR, "AutoTech", sub_dir, tool_name)
    if os.path.exists(bundled_path):
        logger.debug(f"Found {tool_name} in bundled path: {bundled_path}")
        return bundled_path

    # 2. Fallback to development structure (if not using 'AutoTech' prefix or for dev)
    dev_path = os.path.join(BASE_DIR, sub_dir, tool_name)
    if os.path.exists(dev_path):
        logger.debug(f"Found {tool_name} in dev path: {dev_path}")
        return dev_path
    
    # 3. Check system PATH
    found_in_path = shutil.which(tool_name)
    if found_in_path:
        logger.debug(f"Found {tool_name} in system PATH: {found_in_path}")
        return found_in_path

    logger.warning(f"Executable tool '{tool_name}' not found in any expected location or system PATH.")
    return None


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

def check_network_connectivity(gateway_ip: str = None, probe_port: int = None) -> bool:
    """Fresh (uncached) gateway ping — used by dashboard and status routes."""
    if gateway_ip is None:
        gateway_ip = GATEWAY_IP
    if probe_port is None:
        probe_port = PROBE_PORT
    try:
        if ping3:
            result = ping3.ping(gateway_ip, timeout=2)
            return result is not None
        else:
            try:
                with socket.create_connection((gateway_ip, probe_port), timeout=2):
                    return True
            except Exception:
                return False
    except Exception:
        return False


def is_online_network(gateway_ip: str = None, probe_port: int = None, force_refresh: bool = False, ttl_seconds: int = 30) -> bool:
    """
    Live-ish network probe with a short TTL cache so UI and background
    processes can see changes without hammering the gateway.
    Reads/writes state._network_status_cache so the cache is shared across
    all callers (routes, background tasks, blueprints).
    """
    if gateway_ip is None:
        gateway_ip = GATEWAY_IP
    if probe_port is None:
        probe_port = PROBE_PORT
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
            with socket.create_connection((gateway_ip, probe_port), timeout=1.5):
                print(f"[MODE] ONLINE tcp {gateway_ip}:{probe_port}")
                online = True
        except Exception as e:
            print(f"[MODE] TCP probe failed: {e}")

        if not online and ping3:
            try:
                rtt = ping3.ping(gateway_ip, timeout=1)
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

def resolve_plink_path() -> Optional[str]:
    """
    Return the first plink.exe that exists.
    Checks config.PLINK_PATH first (resolved from USB/dev structure at startup),
    then falls back to static PLINK_CANDIDATES.
    """
    import app.config as _config  # late import to avoid circular dependency at module load
    candidates = []
    if getattr(_config, 'PLINK_PATH', None):
        candidates.append(_config.PLINK_PATH)
    candidates.extend(PLINK_CANDIDATES)
    for candidate in candidates:
        if candidate and os.path.exists(candidate):
            return candidate
    return None


def get_autotech_client_folder():
    """
    Find the autotech_client folder — checks multiple locations.
    USB structure: option 18 copies autotech_client/ contents to USB root,
      so Install_AutoTech_Client.bat is at X:\, AutoTech\ is at X:\AutoTech\\
    Dev structure: project_root/autotech_client
    Returns (folder_path, error_message) tuple.
    """
    # Check 0: Frozen EXE running from USB root (X:\AutoTech.exe)
    # Option 18 copies Install_AutoTech_Client.bat directly to USB root (X:\)
    if getattr(sys, 'frozen', False):
        if os.path.exists(os.path.join(BASE_DIR, 'Install_AutoTech_Client.bat')):
            return BASE_DIR, None

    # Check 1: USB structure - E:\AutoTech\autotech_client (AutoTech.exe is at E:\)
    usb_client_folder = os.path.join(BASE_DIR, "AutoTech", "autotech_client")
    if os.path.exists(usb_client_folder):
        return usb_client_folder, None

    # Check 2: Dev environment - autotech_client is inside project folder
    local_client_folder = os.path.join(BASE_DIR, "autotech_client")
    if os.path.exists(local_client_folder):
        return local_client_folder, None

    # Check 3: Search USB drives for AutoTech\autotech_client
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

def _detect_ptx_model_from_arch(ssh) -> str:
    """
    Run 'uname -m' on an active SSH session to distinguish PTXC (New OS) from PTX10.
    Both use mms/modular credentials, but PTXC (New OS) is ARM (armv7l) and PTX10 is x86_64.
    Returns 'PTXC (New OS)' or 'PTX10'.
    """
    try:
        stdin, stdout, stderr = ssh.exec_command("uname -m", timeout=5)
        arch = stdout.read().decode('utf-8', errors='ignore').strip()
        if 'arm' in arch.lower():
            return 'PTXC (New OS)'
    except Exception:
        pass
    return 'PTX10'


def connect_to_equipment(ip_address, mms_server_config: dict = None):
    """
    Try to connect to equipment using both credential sets.
    Returns: (ssh_client, credential_name) or (None, error_message)

    credential_name is one of:
      'PTXC'         - old PTXC (dlog/gold login)
      'PTXC (New OS)'- new PTXC OS (mms/modular login, ARM architecture)
      'PTX10'        - PTX10 (mms/modular login, x86_64 architecture)
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
            if cred['user'] == 'mms':
                return ssh, _detect_ptx_model_from_arch(ssh)
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
    Uses dlog/gold credentials first (PTXC), then mms/modular.
    For mms connections, runs 'uname -m' to distinguish PTXC (New OS) from PTX10.

    Returns dict with:
        - success: bool
        - uptime_hours: float (hours since last reboot)
        - uptime_raw: str (raw uptime output)
        - ptx_type: str — one of 'PTXC', 'PTXC (New OS)', 'PTX10'
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

    # Distinguish PTXC (New OS) from PTX10 — both use mms/modular but differ by CPU architecture
    if ptx_type == 'PTX10':
        ptx_type = _detect_ptx_model_from_arch(ssh)

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


def search_equipment(query, mock_equipment_db: dict = None, mms_server_config: dict = None, is_online_func=None) -> dict:
    """
    Search for equipment by name or IP via SSH to MMS server.
    In offline mode, returns mock/simulated data.
    """
    if mock_equipment_db is None:
        mock_equipment_db = MOCK_EQUIPMENT_DB
    if mms_server_config is None:
        mms_server_config = MMS_SERVER
    if is_online_func is None:
        is_online_func = is_online_network
    query = query.strip().upper()

    # Check if query is in mock database first (for testing)
    if query in mock_equipment_db:
        equipment = mock_equipment_db[query].copy()
        equipment['found'] = True
        equipment['search_method'] = 'database'
        return equipment

    # If offline, return simulated data
    if not is_online_func():
        _seed = len(query)
        return {
            'OID': query,
            'profile': 'Simulated',
            'ptx_model': 'PTX10',
            'ptx_ip': f'10.110.19.{_seed * 10 % 255}',
            'avi_ip': f'10.111.19.{(_seed * 10 + 1) % 255}',
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
            mms_server_config['ip'],
            port=mms_server_config['port'],
            username=mms_server_config['user'],
            password=mms_server_config['password'],
            timeout=10
        )

        command = f"{mms_server_config['script']} {query}"
        stdin, stdout, stderr = ssh.exec_command(command, timeout=15)

        output = stdout.read().decode('utf-8', errors='ignore')
        error = stderr.read().decode('utf-8', errors='ignore')

        ssh.close()

        if error and 'not found' in error.lower():
            return {'found': False, 'error': f'Equipment not found: {query}'}

        result = parse_ip_finder_output(query, output)

        # Refine PTXC detection: MMS script says 'PTXC Found' for both old and new PTXC.
        # SSH directly to the PTX IP to distinguish them by credentials + architecture.
        if result.get('ptxc_found') and result.get('ptx_ip'):
            ptx_ip = result['ptx_ip']
            try:
                # Try old PTXC (dlog) first — short timeout to avoid blocking
                _ptx_ssh = paramiko.SSHClient()
                _ptx_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                _ptx_ssh.connect(ptx_ip, username='dlog', password='gold',
                                 timeout=4, look_for_keys=False, allow_agent=False)
                result['ptx_model'] = 'PTXC'
                _ptx_ssh.close()
            except Exception:
                # dlog failed — try mms/modular and check CPU architecture
                try:
                    _ptx_ssh = paramiko.SSHClient()
                    _ptx_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    _ptx_ssh.connect(ptx_ip, username='mms', password='modular',
                                     timeout=4, look_for_keys=False, allow_agent=False)
                    result['ptx_model'] = _detect_ptx_model_from_arch(_ptx_ssh)
                    _ptx_ssh.close()
                except Exception:
                    pass  # Leave as 'PTXC' if direct SSH unavailable

        return result

    except paramiko.AuthenticationException:
        logger.error("MMS server authentication failed")
        return {'found': False, 'error': 'Authentication failed'}
    except paramiko.SSHException as e:
        logger.error(f"SSH connection error: {e}")
        return {'found': False, 'error': f'Connection failed: {str(e)}'}
    except Exception as e:
        logger.error(f"Equipment search error: {e}")
        return {'found': False, 'error': str(e)}