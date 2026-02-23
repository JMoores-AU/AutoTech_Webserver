"""
app/blueprints/legacy_terminal.py
===================================
T1 Legacy Tools terminal and script routes:
  /api/legacy/terminal/start, /api/legacy/terminal/command,
  /api/legacy/terminal/output, /api/legacy/terminal/stop,
  /api/legacy/equipment-list, /api/legacy/grm-script,
  /api/legacy/download-file, /api/legacy/execute
"""

import logging
import os
import platform
import queue
import string
import subprocess
import sys
import threading
import uuid
from typing import Optional

from flask import Blueprint, jsonify, request, send_file
from flask import session as flask_session

import app.state as state
from app.config import BASE_DIR, MMS_SERVER, TOOLS_DIR
from app.utils import is_online_network, resolve_plink_path
from tools.equipment_db import get_equipment, log_lookup, save_equipment

logger = logging.getLogger(__name__)

bp = Blueprint('legacy_terminal', __name__, url_prefix='')


# ========================================
# TERMINAL SESSION CLASS
# ========================================

class TerminalSession:
    """Manages a T1_Tools.bat terminal session (legacy tool)"""
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.process: Optional[subprocess.Popen] = None
        self.output_queue: queue.Queue = queue.Queue()
        self.running = False
        self.offline_mode = False

    def start(self) -> tuple:
        """Start T1_Tools.bat process or offline simulation"""

        # Search in multiple locations including all drives
        possible_paths = [
            os.path.join(BASE_DIR, 'T1_Tools_Legacy', 'bin', 'T1_Tools.bat'),
            os.path.join(BASE_DIR, 'T1_Tools.bat'),
            os.path.join(TOOLS_DIR, '..', 'T1_Tools_Legacy', 'bin', 'T1_Tools.bat')
        ]

        # Also search all removable drives (D: through Z:)
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


# ========================================
# HELPER FUNCTIONS
# ========================================

def get_equipment_ips(equipment_name):
    """Get PTX and AVI IPs for equipment from IP_list.dat"""
    try:
        possible_paths = [
            os.path.join(BASE_DIR, 'T1_Tools_Legacy', 'bin', 'IP_list.dat'),
            os.path.join(BASE_DIR, 'IP_list.dat'),
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


# ========================================
# TERMINAL SESSION ROUTES
# ========================================

@bp.route('/api/legacy/terminal/start', methods=['POST'])
def api_legacy_terminal_start():
    """Start a new terminal session"""
    try:
        session_id = str(uuid.uuid4())
        term_session = TerminalSession(session_id)
        success, message = term_session.start()

        if success:
            state.terminal_sessions[session_id] = term_session
            return jsonify({'success': True, 'session_id': session_id, 'message': 'T1_Tools.bat terminal started'})
        else:
            return jsonify({'success': False, 'message': message})

    except Exception as e:
        logger.error(f"Terminal start error: {e}")
        return jsonify({'success': False, 'message': str(e)})


@bp.route('/api/legacy/terminal/command', methods=['POST'])
def api_legacy_terminal_command():
    """Send command to terminal session"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        command = data.get('command', '')

        if session_id not in state.terminal_sessions:
            return jsonify({'success': False, 'message': 'Terminal session not found'})

        term_session = state.terminal_sessions[session_id]

        if term_session.send_command(command):
            return jsonify({'success': True, 'message': 'Command sent'})
        else:
            return jsonify({'success': False, 'message': 'Failed to send command'})

    except Exception as e:
        logger.error(f"Terminal command error: {e}")
        return jsonify({'success': False, 'message': str(e)})


@bp.route('/api/legacy/terminal/output', methods=['GET'])
def api_legacy_terminal_output():
    """Get terminal output"""
    try:
        session_id = request.args.get('session_id')

        if session_id not in state.terminal_sessions:
            return jsonify({'success': False, 'message': 'Terminal session not found'})

        term_session = state.terminal_sessions[session_id]
        output = term_session.get_output()

        return jsonify({'success': True, 'output': output, 'exited': not term_session.is_running()})

    except Exception as e:
        logger.error(f"Terminal output error: {e}")
        return jsonify({'success': False, 'message': str(e)})


@bp.route('/api/legacy/terminal/stop', methods=['POST'])
def api_legacy_terminal_stop():
    """Stop terminal session"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')

        if session_id in state.terminal_sessions:
            term_session = state.terminal_sessions[session_id]
            term_session.stop()
            del state.terminal_sessions[session_id]

        return jsonify({'success': True, 'message': 'Terminal stopped'})

    except Exception as e:
        logger.error(f"Terminal stop error: {e}")
        return jsonify({'success': False, 'message': str(e)})


@bp.route('/api/legacy/equipment-list', methods=['GET'])
def api_legacy_equipment_list():
    """Get equipment list from IP_list.dat"""
    try:
        possible_paths = [
            os.path.join(BASE_DIR, 'T1_Tools_Legacy', 'bin', 'IP_list.dat'),
            os.path.join(BASE_DIR, 'IP_list.dat'),
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


@bp.route('/api/legacy/grm-script', methods=['POST'])
def api_legacy_grm_script():
    """Execute GRM T1 Scripts via SSH (plink)"""
    try:
        data = request.get_json()
        script_name = data.get('script', '').lower()
        equipment = data.get('equipment')  # Equipment name or IP

        # Script mapping to remote commands on MMS server
        grm_scripts = {
            'ip-finder': {
                'name': 'IP Finder',
                'command': '/home/mms/bin/remote_check/Random/MySQL/ip_export.sh',
                'requires_equipment': True,
                'description': 'Find equipment IP addresses'
            },
            'ptx-uptime': {
                'name': 'PTX Uptime Report',
                'command': 'download_file',
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
                'command': 'launch_local_app',
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
                'command': '/home/mms/bin/remote_check/Random/Linux Check/For_Support/Check_Exe.sh',
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
                'requires_equipment': True,
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

        # TEST MODE: When equipment is "TEST", always return mock data
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

        # OFFLINE MODE: Check database cache first, then simulate
        db_path = state.EQUIPMENT_DB_PATH
        if not is_online_network():
            cached_equipment = None
            cached_ip = None
            cached_avi_ip = None
            cached_model = None
            cached_status = 'offline'
            cached_oid = None
            cached_cid = None
            cached_profile = None

            if equipment and script.get('requires_equipment') and db_path:
                cached_equipment = get_equipment(db_path, equipment)
                if cached_equipment:
                    cached_ip = cached_equipment.get('network_ip')
                    cached_avi_ip = cached_equipment.get('avi_ip')
                    cached_model = cached_equipment.get('ptx_model')
                    cached_status = cached_equipment.get('last_status', 'unknown')
                    cached_oid = cached_equipment.get('oid')
                    cached_cid = cached_equipment.get('cid')
                    cached_profile = cached_equipment.get('profile')
                    log_lookup(db_path, equipment, 'cache', True)

            output_lines = []
            if cached_equipment:
                output_lines.append(f"[CACHED DATA] {script['name']}")
                output_lines.append(f"Equipment: {equipment}")
                if cached_oid:
                    output_lines.append(f"OID: {cached_oid}")
                if cached_cid:
                    output_lines.append(f"CID: {cached_cid}")
                if cached_profile:
                    output_lines.append(f"Profile: {cached_profile}")
                output_lines.append(f"Network IP: {cached_ip or 'Not cached'}")
                output_lines.append(f"AVI IP: {cached_avi_ip or 'Not cached'}")
                output_lines.append(f"PTX Model: {cached_model or 'Unknown'}")
                output_lines.append(f"Last Known Status: {cached_status.upper()}")
                output_lines.append(f"Cached: {cached_equipment.get('last_updated', 'Unknown')}")
                output_lines.extend([
                    "",
                    "Using cached data - connect to network for live status.",
                    ""
                ])
            else:
                output_lines.append(f"[OFFLINE MODE] {script['name']}")
                output_lines.append(f"Description: {script['description']}")
                if equipment:
                    output_lines.append(f"Equipment: {equipment}")
                    output_lines.append("No cached data available for this equipment.")
                output_lines.extend([
                    "",
                    "Network offline - connect to MMS network for live data.",
                    "TIP: Enter 'TEST' as equipment to see mock data.",
                    ""
                ])

            return jsonify({
                'success': True,
                'output': '\n'.join(output_lines),
                'message': f'{script["name"]} ({"cached" if cached_equipment else "offline"} mode)',
                'equipment_status': cached_status,
                'equipment_ip': cached_ip,
                'avi_ip': cached_avi_ip,
                'ptx_model': cached_model,
                'oid': cached_oid if cached_equipment else None,
                'cid': cached_cid if cached_equipment else None,
                'profile': cached_profile if cached_equipment else None,
                'data_source': 'cached' if cached_equipment else 'offline',
                'last_updated': cached_equipment.get('last_updated') if cached_equipment else None
            })

        # ONLINE MODE: Execute via plink
        plink_path = resolve_plink_path()
        if not plink_path:
            return jsonify({
                'success': False,
                'message': 'plink.exe not found in any configured tool directory'
            })

        mms_server = MMS_SERVER['ip']
        mms_user = MMS_SERVER['user']
        mms_password = MMS_SERVER['password']

        # Handle file download scripts (like PTX Uptime Report)
        if script['command'] == 'download_file':
            if script.get('log_command'):
                log_cmd = [
                    plink_path, '-batch',
                    f'{mms_user}@{mms_server}',
                    '-pw', mms_password,
                    script['log_command']
                ]
                try:
                    subprocess.run(
                        log_cmd, capture_output=True, timeout=10,
                        creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == 'Windows' else 0
                    )
                except Exception:
                    pass

            pscp_path = os.path.join(os.path.dirname(plink_path), 'pscp.exe')
            if not os.path.exists(pscp_path):
                return jsonify({
                    'success': False,
                    'message': f'pscp.exe not found at: {pscp_path}'
                })

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
                    pscp_cmd, capture_output=True, text=True, timeout=30,
                    creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == 'Windows' else 0
                )

                if result.returncode == 0 and os.path.exists(local_path):
                    flask_session['download_file'] = local_path
                    flask_session['download_filename'] = local_filename

                    return jsonify({
                        'success': True,
                        'message': 'File ready for download',
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

        # Look up equipment IP if needed
        equipment_ip = None
        equipment_status = None
        avi_ip = None
        ptx_model = None
        oid = None
        cid = None
        profile = None
        data_source = 'live'

        is_test_equipment = equipment and equipment.upper() == 'TEST'

        if equipment and script.get('requires_equipment'):
            if is_test_equipment:
                equipment_ip = '10.110.99.99'
                avi_ip = '10.111.219.99'
                ptx_model = 'PTXC'
                equipment_status = 'online'
                oid = 'OID-12345'
                cid = 'CID-67890'
                profile = 'LV Single Cab'
                data_source = 'test'

                mock_output = generate_mock_script_output(script_name, equipment, equipment_ip)

                return jsonify({
                    'success': True,
                    'output': mock_output,
                    'message': f'{script["name"]} executed successfully',
                    'equipment_status': equipment_status,
                    'equipment_ip': equipment_ip,
                    'avi_ip': avi_ip,
                    'ptx_model': ptx_model,
                    'oid': oid,
                    'cid': cid,
                    'profile': profile,
                    'data_source': data_source
                })

            # Run IP finder to get equipment IP address
            ip_finder_cmd = f"/home/mms/bin/remote_check/Random/MySQL/ip_export.sh {equipment}"

            ip_lookup_plink = [
                plink_path, '-batch', '-t',
                f'{mms_user}@{mms_server}',
                '-pw', mms_password,
                ip_finder_cmd
            ]

            try:
                ip_result = subprocess.run(
                    ip_lookup_plink, capture_output=True, text=True, timeout=30,
                    creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == 'Windows' else 0
                )

                for line in ip_result.stdout.split('\n'):
                    if 'PTX IP is' in line:
                        equipment_ip = line.split('PTX IP is', 1)[1].replace(':', '').strip()
                    elif 'AVI IP is' in line:
                        avi_ip = line.split('AVI IP is', 1)[1].replace(':', '').strip()
                    elif 'OID:' in line or 'Object ID:' in line:
                        oid = line.split(':')[1].strip() if ':' in line else None
                    elif 'CID:' in line or 'Component ID:' in line:
                        cid = line.split(':')[1].strip() if ':' in line else None
                    elif 'Profile:' in line:
                        profile = line.split(':')[1].strip() if ':' in line else None
                    elif 'PTX Model:' in line or 'Model:' in line:
                        model_part = line.split(':')[1].strip() if ':' in line else None
                        if model_part:
                            ptx_model = model_part
                    elif 'PTXC' in line.upper() and not ptx_model:
                        ptx_model = 'PTXC'
                    elif 'PTX10' in line.upper() and not ptx_model:
                        ptx_model = 'PTX10'
                    elif 'network_ip' in line:
                        continue
                    elif line.strip() and '|' in line and not line.startswith('+'):
                        parts = [p.strip() for p in line.split('|') if p.strip()]
                        if len(parts) >= 4:
                            if not cid and parts[1]:
                                cid = parts[1]
                            if not profile and parts[2]:
                                profile = parts[2]
                            equipment_ip = parts[3]

                    if 'Vehicle is Online' in line or 'Equipment is Online' in line:
                        equipment_status = 'online'
                    elif 'Vehicle is Offline' in line or 'Equipment is Offline' in line:
                        equipment_status = 'offline'

                if not equipment_ip:
                    equipment_ip = equipment

            except Exception:
                equipment_ip = equipment

        # Handle local app launch (VNC, PuTTY, WinSCP)
        if script['command'] == 'launch_local_app':
            app_type = script.get('app_type', 'unknown')
            port = script.get('port', '')

            if app_type == 'vnc':
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
                launch_uri = f"autotech-ssh://{mms_user}@{mms_server}:22"
                output_lines = [
                    "SSH Connection Details:",
                    f"Host: {mms_server}",
                    f"User: {mms_user}",
                    "Port: 22",
                    "",
                    "Launching PuTTY on your computer..."
                ]
            elif app_type == 'winscp':
                launch_uri = f"autotech-sftp://{mms_user}:{mms_password}@{mms_server}:22"
                output_lines = [
                    "SFTP Connection Details:",
                    f"Host: {mms_server}",
                    f"User: {mms_user}",
                    "Port: 22",
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
            param = equipment_ip if equipment_ip else equipment
            remote_command = f"{script['command']} {param}"

        if script.get('log_command'):
            log_cmd_str = script['log_command'].replace('{equipment}', equipment if equipment else 'NONE')
            remote_command = f"{log_cmd_str};{remote_command}"

        plink_cmd = [
            plink_path, '-batch', '-t',
            f'{mms_user}@{mms_server}',
            '-pw', mms_password,
            remote_command
        ]

        logger.info(f"GRM Script: Executing {script['name']}")

        try:
            if platform.system() == 'Windows':
                result = subprocess.run(
                    plink_cmd, capture_output=True, text=True, timeout=120,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            else:
                result = subprocess.run(
                    plink_cmd, capture_output=True, text=True, timeout=120
                )

            full_output = result.stdout
            if result.stderr:
                full_output += f"\n[ERRORS]\n{result.stderr}"

            if result.returncode == 0:
                if equipment and equipment_ip and db_path:
                    save_equipment(
                        db_path, equipment,
                        oid=oid, cid=cid, profile=profile,
                        network_ip=equipment_ip, avi_ip=avi_ip,
                        ptx_model=ptx_model, status=equipment_status
                    )
                    log_lookup(db_path, equipment, 'network', True)

                return jsonify({
                    'success': True,
                    'output': full_output,
                    'message': f'{script["name"]} executed successfully',
                    'equipment_status': equipment_status,
                    'equipment_ip': equipment_ip,
                    'avi_ip': avi_ip,
                    'ptx_model': ptx_model,
                    'oid': oid,
                    'cid': cid,
                    'profile': profile,
                    'data_source': 'live'
                })
            else:
                if equipment and db_path:
                    log_lookup(db_path, equipment, 'network', False)

                return jsonify({
                    'success': False,
                    'output': full_output,
                    'message': f'{script["name"]} failed with code {result.returncode}',
                    'equipment_status': equipment_status,
                    'equipment_ip': equipment_ip,
                    'avi_ip': avi_ip,
                    'ptx_model': ptx_model,
                    'oid': oid,
                    'cid': cid,
                    'profile': profile,
                    'data_source': 'live'
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


@bp.route('/api/legacy/download-file', methods=['GET'])
def api_legacy_download_file():
    """Serve downloaded file to client browser"""
    try:
        file_path = flask_session.get('download_file')
        filename = flask_session.get('download_filename', 'download.html')

        if not file_path or not os.path.exists(file_path):
            return jsonify({'success': False, 'message': 'File not found'}), 404

        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype='text/html'
        )

    except Exception as e:
        logger.error(f"File download error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/api/legacy/execute', methods=['POST'])
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
                return jsonify({'success': False, 'message': 'putty.exe not found'})

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
                return jsonify({'success': False, 'message': 'WinSCP.exe not found'})

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
                return jsonify({'success': False, 'message': 'WinSCP.exe not found'})

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
                return jsonify({'success': False, 'message': 'TRU.exe not found'})

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
                plink_path = resolve_plink_path()
                if not plink_path:
                    return jsonify({'success': False, 'message': 'plink.exe not found in any configured tool directory'})

                subprocess.run(
                    [plink_path, '-batch', '-pw', 'gold', f'dlog@{ptx_ip}', 'sudo reboot'],
                    capture_output=True, text=True, timeout=10
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
