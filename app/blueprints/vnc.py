"""
app/blueprints/vnc.py
======================
VNC and TRU remote access API routes:
  /api/vnc/connect, /api/vnc/start, /api/vnc/workstation, /api/tru_setup
"""

import logging
import os
import platform
import subprocess
import time
from datetime import datetime

from flask import Blueprint, jsonify, request

import app.state as state
from app.config import MMS_SERVER, TOOLS_DIR, VNC_VIEWER_PATH
from app.utils import is_online_network, resolve_plink_path

logger = logging.getLogger(__name__)

bp = Blueprint('vnc', __name__, url_prefix='')

# Workstation VNC targets
VNC_WORKSTATIONS = {
    'WS1': {'ip': '10.110.22.56', 'user': 'dlog', 'password': 'gold'},
    'WS2': {'ip': '10.110.22.57', 'user': 'dlog', 'password': 'gold'}
}


@bp.route('/api/vnc/connect', methods=['POST'])
def api_vnc_connect():
    """VNC Connection API - launches VNC viewer"""
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


@bp.route('/api/vnc/start', methods=['POST'])
def api_vnc_start():
    """
    Start VNC session using plink.exe exactly like Start_VNC.bat.
    Uses plink to run MMS script, then launches VNC viewer.
    """
    try:
        data = request.get_json()
        ptx_ip = data.get('ptx_ip')
        equipment_name = data.get('equipment_name', 'Unknown')
        client_ready = data.get('client_ready', False)

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

        mms_server = MMS_SERVER['ip']
        mms_user = MMS_SERVER['user']
        mms_password = MMS_SERVER['password']
        vnc_script = '/home/mms/bin/remote_check/TempTool/VNC/Check_Exe.sh'

        try:
            plink_cmd = [
                plink_path,
                '-batch', '-t',
                f'{mms_user}@{mms_server}',
                '-pw', mms_password,
                f'{vnc_script} {ptx_ip}'
            ]

            logger.info(f"VNC: Executing plink with auto-confirmation")

            if platform.system() == 'Windows':
                result = subprocess.run(
                    plink_cmd,
                    input="Y\n",
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

            ptx_type = 'Unknown'
            output_text = result.stdout + result.stderr
            if 'PTXC' in output_text:
                ptx_type = 'PTXC'
            elif 'PTX10' in output_text:
                ptx_type = 'PTX10'

            vnc_target = f'{ptx_ip}:0'

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

            vnc_viewer_path = None
            possible_vnc_paths = [VNC_VIEWER_PATH]
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

            if platform.system() == 'Windows':
                subprocess.Popen(
                    [vnc_viewer_path, '-WarnUnencrypted=0', f'{ptx_ip}:0'],
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
            else:
                subprocess.Popen([
                    vnc_viewer_path,
                    '-WarnUnencrypted=0',
                    '-SecurityNotificationTimeout=0',
                    '-FullScreen=0',
                    '-ViewOnly=0',
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

        # Always kill any existing tunnel first — only 1 can run
        _kill_tru_connections()

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
            return jsonify({'success': False, 'message': 'plink.exe not found — check tool directory'})

        # Probe PTX type before opening the long-lived tunnel
        ptx_type, ssh_user, ssh_pass = _detect_ptx_type(plink_path, equipment_ip)
        logger.info(f"TRU: {equipment_name} ({equipment_ip}) is {ptx_type}")

        # One plink process, three port forwards
        flags = subprocess.CREATE_NO_WINDOW if platform.system() == 'Windows' else 0
        tunnel_cmd = [
            plink_path, '-v', '-batch', '-N',
            '-l', ssh_user, '-pw', ssh_pass,
            '-L', '5001:192.168.0.101:8002',
            '-L', '5002:192.168.0.102:8002',
            '-L', '5003:192.168.0.103:8002',
            equipment_ip,
        ]
        proc = subprocess.Popen(tunnel_cmd,
                                creationflags=flags,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)

        time.sleep(2)  # Allow tunnel to bind

        if proc.poll() is not None:
            err = proc.stderr.read().decode('utf-8', errors='replace')
            return jsonify({'success': False, 'message': f'Tunnel exited immediately: {err[:200]}'})

        state.active_tru_connections[equipment_name] = {
            'process': proc,
            'equipment_name': equipment_name,
            'ip': equipment_ip,
            'ptx_type': ptx_type,
            'ports': {'gnss1': 5001, 'gnss2': 5002, 'test_gnss': 5003},
            'started_at': datetime.now().isoformat(),
        }

        tru_launched = _launch_tru_exe()
        if tru_launched:
            msg = f'Tunnels open for {equipment_name} ({ptx_type}) — TRU launched'
        else:
            msg = f'Tunnels open for {equipment_name} ({ptx_type}) — launch TRU manually'

        return jsonify({
            'success': True,
            'message': msg,
            'equipment_name': equipment_name,
            'ip_address': equipment_ip,
            'ports': {'gnss1': 5001, 'gnss2': 5002, 'test_gnss': 5003},
            'ptx_type': ptx_type,
            'tru_launched': tru_launched,
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
    """Return current TRU tunnel connection state."""
    try:
        connections = {}
        for name, conn in state.active_tru_connections.items():
            proc = conn.get('process')
            connections[name] = {
                'equipment_name': conn.get('equipment_name'),
                'ip': conn.get('ip'),
                'ptx_type': conn.get('ptx_type'),
                'ports': conn.get('ports'),
                'started_at': conn.get('started_at'),
                'alive': proc is not None and proc.poll() is None,
            }
        return jsonify({'success': True, 'connections': connections, 'count': len(connections)})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _detect_ptx_type(plink_path: str, ip: str):
    """
    Try connecting as dlog/gold (PTXC).  Falls back to mms/modular.
    For mms connections, runs 'uname -m' to distinguish PTXC (New OS) from PTX10.
    Returns (ptx_type, ssh_user, ssh_pass).

    ptx_type is one of:
      'PTXC'          - old PTXC (dlog/gold login)
      'PTXC (New OS)' - new PTXC OS (mms/modular, ARM architecture)
      'PTX10'         - PTX10 (mms/modular, x86_64 architecture)
    """
    flags = subprocess.CREATE_NO_WINDOW if platform.system() == 'Windows' else 0
    try:
        probe = subprocess.run(
            [plink_path, '-v', '-batch', '-l', 'dlog', '-pw', 'gold', ip, 'echo ptxc_ok'],
            capture_output=True, text=True, timeout=8, creationflags=flags,
        )
        if probe.returncode == 0 and 'ptxc_ok' in probe.stdout:
            return 'PTXC', 'dlog', 'gold'
    except Exception:
        pass
    # mms/modular — check architecture to tell PTXC (New OS) apart from PTX10
    try:
        probe = subprocess.run(
            [plink_path, '-batch', '-l', 'mms', '-pw', 'modular', ip, 'uname -m'],
            capture_output=True, text=True, timeout=8, creationflags=flags,
        )
        if probe.returncode == 0 and 'arm' in probe.stdout.lower():
            return 'PTXC (New OS)', 'mms', 'modular'
    except Exception:
        pass
    return 'PTX10', 'mms', 'modular'


def _kill_tru_connections():
    """Terminate every tracked TRU plink process and clear the state dict."""
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
    """Launch TRU.exe from TOOLS_DIR/Topcon/. Returns True if launched."""
    try:
        tru_path = os.path.join(TOOLS_DIR, 'Topcon', 'TRU.exe')
        if os.path.exists(tru_path):
            flags = subprocess.CREATE_NEW_CONSOLE if platform.system() == 'Windows' else 0
            subprocess.Popen([tru_path], creationflags=flags)
            logger.info(f"TRU: Launched TRU.exe from {tru_path}")
            return True
        logger.warning(f"TRU: TRU.exe not found at {tru_path}")
        return False
    except Exception as e:
        logger.error(f"TRU: Failed to launch TRU.exe: {e}")
        return False


@bp.route('/api/vnc/workstation', methods=['POST'])
def api_vnc_workstation():
    """VNC Workstation Access using plink.exe"""
    try:
        data = request.get_json()
        workstation = data.get('workstation', '').upper()

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

        mms_server = MMS_SERVER['ip']
        mms_user = MMS_SERVER['user']
        mms_password = MMS_SERVER['password']
        vnc_script = '/home/mms/bin/remote_check/TempTool/VNC/Check_Exe.sh'

        try:
            plink_cmd = [
                plink_path,
                '-batch', '-t',
                f'{mms_user}@{mms_server}',
                '-pw', mms_password,
                f'{vnc_script} {ws_ip}'
            ]

            logger.info(f"VNC WS{workstation}: Executing plink with auto-confirmation")

            if platform.system() == 'Windows':
                result = subprocess.run(
                    plink_cmd,
                    input="Y\n",
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

            logger.info(f"VNC WS{workstation}: Script output: {result.stdout[:200]}")

            vnc_viewer_path = VNC_VIEWER_PATH
            if not os.path.exists(vnc_viewer_path):
                return jsonify({
                    'success': True,
                    'message': f'VNC server started. Connect manually to {ws_ip}:0',
                    'manual_connect': True,
                    'ip': ws_ip,
                    'note': f'VNC viewer not found at: {vnc_viewer_path}'
                })

            logger.info(f"VNC WS{workstation}: Launching viewer: {vnc_viewer_path}")
            if platform.system() == 'Windows':
                subprocess.Popen(
                    [vnc_viewer_path, '-WarnUnencrypted=0', f'{ws_ip}:0'],
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
