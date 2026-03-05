"""
app/blueprints/vnc.py
======================
VNC remote access API routes:
  /api/vnc/connect, /api/vnc/start, /api/vnc/workstation

TRU (GNSS tunnel) routes moved to app/blueprints/tru.py
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
