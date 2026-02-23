"""
app/blueprints/tools_launch.py
================================
Tool execution and batch launcher routes:
  /api/launch-legacy, /api/launch-batch-tool
  (run_tool is handled separately as it dispatches to other blueprints)
"""

import logging
import os
import platform
import subprocess
import time

from flask import Blueprint, jsonify, request

from app.config import BASE_DIR, CLIENT_PLINK_PATH

logger = logging.getLogger(__name__)

bp = Blueprint('tools_launch', __name__, url_prefix='')


@bp.route('/api/launch-legacy', methods=['POST'])
def api_launch_legacy():
    """Launch T1_Tools_Legacy from USB drive."""
    try:
        legacy_paths = []

        if platform.system() == 'Windows':
            import ctypes
            drives = []
            bitmask = ctypes.windll.kernel32.GetLogicalDrives()
            for letter in 'DEFGHIJKLMNOPQRSTUVWXYZ':
                if bitmask & 1:
                    drives.append(f"{letter}:")
                bitmask >>= 1

            for drive in drives:
                legacy_path = os.path.join(drive, 'T1_Tools_Legacy', 'bin', 'Run T1 Tools.bat')
                if os.path.exists(legacy_path):
                    legacy_paths.append(legacy_path)

        if not legacy_paths:
            for path in [r"D:\T1_Tools_Legacy\bin\Run T1 Tools.bat",
                         r"E:\T1_Tools_Legacy\bin\Run T1 Tools.bat",
                         r"F:\T1_Tools_Legacy\bin\Run T1 Tools.bat"]:
                if os.path.exists(path):
                    legacy_paths.append(path)

        if not legacy_paths:
            return jsonify({'success': False, 'message': 'T1 Tools Legacy not found. Please insert USB drive.'})

        legacy_bat = legacy_paths[0]

        if platform.system() == 'Windows':
            subprocess.Popen(['cmd', '/c', 'start', '', legacy_bat],
                             shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE)
        else:
            return jsonify({'success': False, 'message': 'Legacy tools only available on Windows'})

        return jsonify({'success': True, 'message': 'T1 Tools Legacy launched', 'path': legacy_bat})

    except Exception as e:
        logger.error(f"Legacy launch error: {e}")
        return jsonify({'success': False, 'message': str(e)})


@bp.route('/api/launch-batch-tool', methods=['POST'])
def api_launch_batch_tool():
    """Launch a batch file in CMD window with password auto-filled."""
    try:
        data = request.get_json()
        tool_name = data.get('tool', '').lower()
        password = data.get('password', '')

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
            return jsonify({'success': False, 'message': f'Unknown tool: {tool_name}'})

        batch_file = os.path.join(BASE_DIR, batch_files[tool_name])
        if not os.path.exists(batch_file):
            return jsonify({'success': False, 'message': f'Batch file not found: {batch_file}'})

        plink_path = CLIENT_PLINK_PATH
        if not os.path.exists(plink_path):
            return jsonify({
                'success': False,
                'message': f'plink.exe not found at: {plink_path}. Install AutoTech Client or check USB connection.'
            })

        temp_dir = os.path.join(BASE_DIR, 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        temp_batch = os.path.join(temp_dir, f'launch_{tool_name}_{int(time.time())}.bat')

        with open(temp_batch, 'w') as f:
            f.write('@echo off\n')
            f.write(f'SET PLINK_PATH="{plink_path}"\n')
            f.write(f'SET PASSWORD={password}\n')
            f.write(f'echo {password}| "{batch_file}"\n')
            f.write('pause\n')

        subprocess.Popen(
            ['cmd', '/c', 'start', 'cmd', '/k', temp_batch],
            creationflags=subprocess.CREATE_NEW_CONSOLE if platform.system() == 'Windows' else 0
        )

        logger.info(f"Launched batch tool: {tool_name}")
        return jsonify({'success': True, 'message': f'Launched {tool_name} in CMD window'})

    except Exception as e:
        logger.error(f"Error launching batch tool: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})
