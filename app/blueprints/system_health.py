"""
app/blueprints/system_health.py
=================================
System health, network status, and core API routes:
  /api/mode, /api/remote-stats, /api/health, /api/network_status,
  /api/system/status, /api/linux_health_check
"""

import logging
import os
import platform
import socket
import subprocess
import time
from datetime import datetime

from flask import Blueprint, jsonify, request

import app.state as state
from app.config import BASE_DIR, GATEWAY_IP, MOCK_EQUIPMENT_DB, PROBE_PORT, SERVERS
from app.utils import check_network_connectivity, is_online_network

logger = logging.getLogger(__name__)

try:
    import ping3
except ImportError:
    ping3 = None

bp = Blueprint('system_health', __name__, url_prefix='')


# ==============================================================================
# HELPERS
# ==============================================================================

def get_remote_stats():
    """Fetch latency/status for each configured server."""
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
                latency = ping3.ping(server["ip"], timeout=3)
                if latency is not None:
                    server_stat["status"] = "online"
                    server_stat["latency"] = round(latency * 1000, 2)
                else:
                    start = time.time()
                    with socket.create_connection((server["ip"], server["port"]), timeout=3):
                        server_stat["status"] = "online"
                        server_stat["latency"] = round((time.time() - start) * 1000, 2)
            else:
                start = time.time()
                with socket.create_connection((server["ip"], server["port"]), timeout=3):
                    server_stat["status"] = "online"
                    server_stat["latency"] = round((time.time() - start) * 1000, 2)
        except Exception as e:
            logger.debug(f"Server {server['name']} check failed: {e}")
        stats.append(server_stat)
    return stats


# ==============================================================================
# ROUTES
# ==============================================================================

@bp.get("/api/mode")
def api_mode():
    """Network mode detection API."""
    return jsonify({"online": is_online_network()})


@bp.route("/api/remote-stats")
def api_remote_stats():
    """Server health monitoring API."""
    try:
        return jsonify(get_remote_stats())
    except Exception as e:
        logger.error(f"Error getting remote stats: {e}")
        return jsonify([]), 500


@bp.route('/api/health')
def api_health():
    """Health check endpoint — reports server and database status."""
    import sqlite3 as _sqlite3

    databases = {}
    all_connected = True

    EQUIPMENT_DB_PATH = state.EQUIPMENT_DB_PATH
    PTX_UPTIME_DB_PATH = state.PTX_UPTIME_DB_PATH

    # Equipment cache database
    try:
        if EQUIPMENT_DB_PATH and os.path.exists(EQUIPMENT_DB_PATH):
            conn = _sqlite3.connect(EQUIPMENT_DB_PATH, timeout=2)
            conn.execute('SELECT 1')
            conn.close()
            databases['equipment_cache'] = {'status': 'connected', 'path': EQUIPMENT_DB_PATH, 'exists': True}
        else:
            databases['equipment_cache'] = {'status': 'not_initialized', 'path': str(EQUIPMENT_DB_PATH), 'exists': False}
            all_connected = False
    except Exception as e:
        databases['equipment_cache'] = {'status': 'error', 'error': str(e),
                                         'exists': EQUIPMENT_DB_PATH is not None and os.path.exists(str(EQUIPMENT_DB_PATH))}
        all_connected = False

    # PTX uptime database
    try:
        if PTX_UPTIME_DB_PATH and os.path.exists(PTX_UPTIME_DB_PATH):
            conn = _sqlite3.connect(PTX_UPTIME_DB_PATH, timeout=2)
            conn.execute('SELECT 1')
            conn.close()
            databases['ptx_uptime'] = {'status': 'connected', 'path': PTX_UPTIME_DB_PATH, 'exists': True}
        else:
            databases['ptx_uptime'] = {'status': 'not_initialized', 'path': str(PTX_UPTIME_DB_PATH), 'exists': False}
            all_connected = False
    except Exception as e:
        databases['ptx_uptime'] = {'status': 'error', 'error': str(e),
                                    'exists': PTX_UPTIME_DB_PATH is not None and os.path.exists(str(PTX_UPTIME_DB_PATH))}
        all_connected = False

    # FrontRunner events database
    try:
        from tools import frontrunner_event_db as _fr_db
        fr_db_path = _fr_db.get_database_path(BASE_DIR)
        if fr_db_path and os.path.exists(fr_db_path):
            conn = _sqlite3.connect(fr_db_path, timeout=2)
            conn.execute('SELECT 1')
            conn.close()
            databases['frontrunner_events'] = {'status': 'connected', 'path': fr_db_path, 'exists': True}
        else:
            databases['frontrunner_events'] = {'status': 'not_initialized', 'path': str(fr_db_path), 'exists': False}
            all_connected = False
    except Exception as e:
        databases['frontrunner_events'] = {'status': 'error', 'error': str(e), 'exists': False}
        all_connected = False

    version_path = os.path.join(BASE_DIR, 'VERSION')
    try:
        with open(version_path, 'r') as vf:
            version = vf.read().strip()
    except Exception:
        version = 'unknown'

    return jsonify({
        'status': 'healthy',
        'database_status': 'connected' if all_connected else 'degraded',
        'databases': databases,
        'server': {
            'version': version,
            'platform': platform.system(),
            'python_version': platform.python_version()
        },
        'timestamp': datetime.now().isoformat()
    })


@bp.route('/api/network_status')
def network_status():
    """Network connectivity status API."""
    try:
        online = check_network_connectivity()
        return jsonify({
            'online': online,
            'gateway_ip': GATEWAY_IP,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/api/system/status')
def system_status():
    """System status — service state, active connections, uptime."""
    running_as_service = False
    try:
        result = subprocess.run(
            ['sc', 'query', 'AutoTech'],
            capture_output=True, text=True, timeout=2,
            creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == 'Windows' else 0
        )
        running_as_service = 'RUNNING' in result.stdout
    except Exception:
        pass

    active_connections = 0
    try:
        result = subprocess.run(
            ['netstat', '-an'],
            capture_output=True, text=True, timeout=2,
            creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == 'Windows' else 0
        )
        for line in result.stdout.splitlines():
            if ':8888' in line and 'ESTABLISHED' in line:
                active_connections += 1
    except Exception:
        pass

    import app.state as state
    return jsonify({
        'running_as_service': running_as_service,
        'active_connections': active_connections,
        'server_start_time': state.SERVER_START_TIME.isoformat(),
        'timestamp': datetime.now().isoformat()
    })


@bp.route('/api/comms_ping', methods=['POST'])
def api_comms_ping():
    """
    Comms Info: ping AVI from server, then ping PTX/GNSS from AVI via SSH.
    POST body: { "avi_ip": "10.x.x.x" }
    """
    try:
        from tools.ip_finder import check_avi_status

        data = request.get_json()
        avi_ip = data.get('avi_ip', '').strip()

        if not avi_ip:
            return jsonify({'success': False, 'error': 'AVI IP required'}), 400

        result = check_avi_status(avi_ip)

        # Flatten into a simpler shape for the frontend
        devices = result.get('internal_devices', {})
        return jsonify({
            'success': True,
            'avi': {
                'ip': avi_ip,
                'status': result.get('status', 'Unknown'),
                'ping_time': result.get('response_time')
            },
            'ptx':    devices.get('ptx',    {'ip': '192.168.0.100', 'status': 'Unknown', 'ping_time': None}),
            'gnss_1': devices.get('gnss_1', {'ip': '192.168.0.101', 'status': 'Unknown', 'ping_time': None}),
            'gnss_2': devices.get('gnss_2', {'ip': '192.168.0.102', 'status': 'Unknown', 'ping_time': None}),
        })

    except Exception as e:
        logger.error(f"Comms ping error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/linux_health_check', methods=['POST'])
def api_linux_health_check():
    """Linux Health Check — CPU, Memory, Uptime, Disk via SSH."""
    try:
        from tools.ip_finder import check_linux_health

        data = request.get_json()
        ptx_ip = data.get('ptx_ip', '').strip()
        ptx_model = data.get('ptx_model', 'PTX10').strip().upper()

        if not ptx_ip:
            return jsonify({'success': False, 'error': 'PTX IP required'}), 400

        for equipment_data in MOCK_EQUIPMENT_DB.values():
            if equipment_data.get('ptx_ip') == ptx_ip and 'health' in equipment_data:
                mock_health = equipment_data['health'].copy()
                mock_health['success'] = True
                return jsonify(mock_health)

        ssh_user = 'dlog' if ptx_model == 'PTXC' else 'mms'
        ssh_password = 'gold' if ptx_model == 'PTXC' else 'modular'

        return jsonify(check_linux_health(ptx_ip, ssh_user, ssh_password))

    except Exception as e:
        logger.error(f"Linux health check error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
