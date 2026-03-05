"""
app/blueprints/tru.py
=====================
TRU (GNSS Tunnel) access routes:
  /api/tru_setup, /api/tru_disconnect, /api/tru_status
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
from app.config import TOOLS_DIR
from app.utils import is_online_network, resolve_plink_path

logger = logging.getLogger(__name__)

bp = Blueprint('tru', __name__, url_prefix='')


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _check_port(port: int, timeout: float = 1.0) -> bool:
    """Return True if localhost:port is accepting connections."""
    try:
        with socket.create_connection(('localhost', port), timeout=timeout):
            return True
    except Exception:
        return False


def _detect_ptx_type(plink_path: str, ip: str):
    """
    Probe the PTX to determine its type via plink SSH.
    Returns (ptx_type, ssh_user, ssh_pass).

    ptx_type is one of:
      'PTXC'          - old PTXC (dlog/gold login)
      'PTXC (New OS)' - new PTXC OS (mms/modular, ARM architecture)
      'PTX10'         - PTX10 (mms/modular, x86_64 architecture)
    """
    flags = subprocess.CREATE_NO_WINDOW if platform.system() == 'Windows' else 0

    # Try PTXC (dlog/gold) first — fastest probe
    try:
        probe = subprocess.run(
            [plink_path, '-v', '-batch', '-l', 'dlog', '-pw', 'gold', ip, 'echo ptxc_ok'],
            capture_output=True, text=True, timeout=8, creationflags=flags,
        )
        if probe.returncode == 0 and 'ptxc_ok' in probe.stdout:
            return 'PTXC', 'dlog', 'gold'
    except Exception:
        pass

    # Try mms/modular — check architecture to distinguish PTXC (New OS) from PTX10
    try:
        probe = subprocess.run(
            [plink_path, '-batch', '-l', 'mms', '-pw', 'modular', ip, 'uname -m'],
            capture_output=True, text=True, timeout=8, creationflags=flags,
        )
        if probe.returncode == 0:
            if 'arm' in probe.stdout.lower():
                return 'PTXC (New OS)', 'mms', 'modular'
            return 'PTX10', 'mms', 'modular'
    except Exception:
        pass

    # Default fallback
    return 'PTX10', 'mms', 'modular'


def _kill_tru_connections():
    """Terminate every tracked TRU plink process and clear state."""
    for name, conn in list(state.active_tru_connections.items()):
        proc = conn.get('process')
        if proc and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
    state.active_tru_connections.clear()


def _launch_tru_exe() -> bool:
    """Launch TRU.exe from TOOLS_DIR/Topcon/. Returns True if found and launched."""
    try:
        tru_path = os.path.join(TOOLS_DIR, 'Topcon', 'TRU.exe')
        if os.path.exists(tru_path):
            flags = subprocess.CREATE_NEW_CONSOLE if platform.system() == 'Windows' else 0
            subprocess.Popen([tru_path], creationflags=flags)
            logger.info(f"TRU: Launched TRU.exe from {tru_path}")
            return True
    except Exception as e:
        logger.warning(f"TRU: Could not launch TRU.exe: {e}")
    return False


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@bp.route('/api/tru_setup', methods=['POST'])
def api_tru_setup():
    """
    TRU Access Setup — opens SSH port-forward tunnels for GNSS access then
    launches TRU.exe.  Only one tunnel session may be active at a time; any
    existing session is killed before starting the new one.

    Tunnel layout (mirrors the legacy T1_Tools batch script):
      localhost:5001  →  192.168.0.101:8002   (GNSS 1)
      localhost:5002  →  192.168.0.102:8002   (GNSS 2)
      localhost:5003  →  192.168.0.103:8002   (Test GNSS)
    """
    try:
        data = request.get_json()
        equipment_ip = data.get('equipment_ip')
        equipment_name = data.get('equipment_name', 'Unknown')

        if not equipment_ip:
            return jsonify({'success': False, 'message': 'Equipment IP required'})

        # Kill any existing tunnel before starting a new one
        _kill_tru_connections()

        # Offline / dev mode — simulate tunnels
        if not is_online_network():
            return jsonify({
                'success': True,
                'message': f'TRU access simulated for {equipment_name} (offline mode)',
                'equipment_name': equipment_name,
                'ip_address': equipment_ip,
                'ports': {'gnss1': 5001, 'gnss2': 5002, 'test_gnss': 5003},
                'ptx_type': 'PTXC (simulated)',
                'tru_launched': False,
                'simulated': True,
            })

        plink_path = resolve_plink_path()
        if not plink_path:
            return jsonify({
                'success': False,
                'message': (
                    'plink.exe not found. '
                    'Ensure the AutoTech client is installed or USB is connected.'
                )
            })

        logger.info(f"TRU: Using plink at {plink_path}")

        # Prefer AVI as SSH gateway — gives access to GNSS even when PTX is offline.
        # Fall back to PTX direct if no AVI IP is provided.
        avi_ip = data.get('avi_ip', '').strip()
        if avi_ip:
            tunnel_host = avi_ip
            ssh_user    = 'root'
            ssh_pass    = 'root'
            ptx_type    = f'via AVI ({avi_ip})'
            logger.info(f"TRU: Tunnelling through AVI {avi_ip} for {equipment_name}")
        else:
            tunnel_host = equipment_ip
            ptx_type, ssh_user, ssh_pass = _detect_ptx_type(plink_path, equipment_ip)
            logger.info(f"TRU: Tunnelling direct to PTX {equipment_ip} ({ptx_type}) — no AVI IP")

        # One plink process, three port forwards into the AVI/PTX internal subnet
        flags = subprocess.CREATE_NO_WINDOW if platform.system() == 'Windows' else 0
        tunnel_cmd = [
            plink_path, '-v', '-batch', '-N',
            '-l', ssh_user, '-pw', ssh_pass,
            '-L', '5001:192.168.0.101:8002',
            '-L', '5002:192.168.0.102:8002',
            '-L', '5003:192.168.0.103:8002',
            tunnel_host,
        ]

        proc = subprocess.Popen(
            tunnel_cmd,
            creationflags=flags,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Give plink time to bind ports
        time.sleep(2)

        if proc.poll() is not None:
            err = proc.stderr.read().decode('utf-8', errors='replace')
            logger.error(f"TRU: plink exited immediately: {err}")
            return jsonify({
                'success': False,
                'message': f'Tunnel failed to start: {err[:300] or "plink exited immediately"}'
            })

        ports = {'gnss1': 5001, 'gnss2': 5002, 'test_gnss': 5003}

        # Verify at least one port is listening
        listening = [_check_port(p) for p in ports.values()]
        if not any(listening):
            proc.terminate()
            return jsonify({
                'success': False,
                'message': 'Tunnel process started but no ports are listening — check PTX connectivity'
            })

        state.active_tru_connections[equipment_name] = {
            'process': proc,
            'equipment_name': equipment_name,
            'ip': equipment_ip,
            'tunnel_host': tunnel_host,
            'avi_ip': avi_ip or None,
            'ptx_type': ptx_type,
            'ports': ports,
            'started_at': datetime.now().isoformat(),
        }

        tru_launched = _launch_tru_exe()
        msg = (
            f'Tunnels open for {equipment_name} ({ptx_type}) — TRU launched'
            if tru_launched
            else f'Tunnels open for {equipment_name} ({ptx_type}) — launch TRU manually'
        )

        return jsonify({
            'success': True,
            'message': msg,
            'equipment_name': equipment_name,
            'ip_address': equipment_ip,
            'ports': ports,
            'ptx_type': ptx_type,
            'tru_launched': tru_launched,
            'simulated': False,
        })

    except Exception as e:
        logger.error(f"TRU setup error: {e}")
        return jsonify({'success': False, 'message': str(e)})


@bp.route('/api/tru_disconnect', methods=['POST'])
def api_tru_disconnect():
    """Terminate all active TRU SSH tunnel processes."""
    try:
        count = len(state.active_tru_connections)
        _kill_tru_connections()
        return jsonify({'success': True, 'message': f'Disconnected {count} TRU tunnel(s)'})
    except Exception as e:
        logger.error(f"TRU disconnect error: {e}")
        return jsonify({'success': False, 'message': str(e)})


@bp.route('/api/tru_status', methods=['GET'])
def api_tru_status():
    """
    Return current TRU tunnel state including per-port connectivity check.
    Frontend should poll this every 5 seconds while the modal is open.
    """
    try:
        connections = {}
        for name, conn in state.active_tru_connections.items():
            proc = conn.get('process')
            ports = conn.get('ports', {})
            alive = proc is not None and proc.poll() is None

            ports_status = {}
            for port_name, port_num in ports.items():
                ports_status[port_name] = {
                    'port': port_num,
                    'listening': _check_port(port_num) if alive else False,
                }

            connections[name] = {
                'equipment_name': conn.get('equipment_name'),
                'ip': conn.get('ip'),
                'tunnel_host': conn.get('tunnel_host'),
                'avi_ip': conn.get('avi_ip'),
                'ptx_type': conn.get('ptx_type'),
                'ports': ports,
                'ports_status': ports_status,
                'started_at': conn.get('started_at'),
                'alive': alive,
            }

        return jsonify({
            'success': True,
            'connections': connections,
            'count': len(connections),
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
