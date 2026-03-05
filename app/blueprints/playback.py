"""
app/blueprints/playback.py
===========================
Playback server API routes:
  /api/playback/monitor/start, /api/playback/monitor/stop,
  /api/playback/monitor/status, /api/playback/server-check,
  /api/playback/open-winscp, /api/playback/local-files,
  /api/playback/server-files, /api/playback/find-file,
  /api/playback/download-file, /api/playback/download-progress/<filename>,
  /api/playback/predict-next-file, /api/playback/detect-log-files,
  /api/playback/find-files, /api/playback/delete-file,
  /download/playback/<filename>
"""

import logging
import os
import platform
import shutil
import socket
import subprocess
import tempfile
import threading
import time
from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path

from flask import Blueprint, jsonify, request, send_file

import app.state as state
from app.background_tasks import playback_monitor_worker
from app.config import PLAYBACK_SERVER
from app.utils import is_online_network

try:
    import paramiko
except ImportError:
    paramiko = None

try:
    import ping3
except ImportError:
    ping3 = None

logger = logging.getLogger(__name__)

bp = Blueprint('playback', __name__, url_prefix='')

# 60-second cache for predict-next-file (avoids SSH on every 2-second frontend poll)
_predict_cache: dict = {'result': None, 'ts': 0.0}
_PREDICT_CACHE_TTL = 60  # seconds


# ========================================
# PLAYBACK MONITOR CONTROL
# ========================================

@bp.route('/api/playback/monitor/start', methods=['POST'])
def api_start_playback_monitor():
    """
    Start the background playback monitor.
    Maintains persistent SSH connection to playback server for real-time file monitoring.
    """
    try:
        # Check if online mode
        if not is_online_network():
            return jsonify({
                'success': False,
                'error': 'Playback monitor requires online network connection'
            }), 400

        # Check if already running
        if state.playback_monitor['running']:
            return jsonify({
                'success': False,
                'error': 'Playback monitor is already running',
                'status': state.playback_monitor['status']
            }), 400

        # Get optional scan interval from request
        data = request.get_json() or {}
        interval = data.get('scan_interval_seconds', 10)
        state.playback_monitor['scan_interval_seconds'] = max(5, min(60, interval))  # Clamp 5-60 seconds

        # Start the monitor thread
        state.playback_monitor['stop_event'].clear()
        state.playback_monitor['running'] = True
        state.playback_monitor['thread'] = threading.Thread(
            target=playback_monitor_worker,
            daemon=True
        )
        state.playback_monitor['thread'].start()

        return jsonify({
            'success': True,
            'message': 'Playback monitor started',
            'scan_interval_seconds': state.playback_monitor['scan_interval_seconds']
        })

    except Exception as e:
        logger.error(f"Error starting playback monitor: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/playback/monitor/stop', methods=['POST'])
def api_stop_playback_monitor():
    """Stop the background playback monitor."""
    try:
        if not state.playback_monitor['running']:
            return jsonify({
                'success': False,
                'error': 'Playback monitor is not running'
            }), 400

        # Signal the thread to stop
        state.playback_monitor['stop_event'].set()

        return jsonify({
            'success': True,
            'message': 'Stop signal sent to playback monitor'
        })

    except Exception as e:
        logger.error(f"Error stopping playback monitor: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/playback/monitor/status')
def api_playback_monitor_status():
    """Get the current status of the playback monitor and cached file data."""
    try:
        return jsonify({
            'success': True,
            'running': state.playback_monitor['running'],
            'connected': state.playback_monitor['connected'],
            'status': state.playback_monitor['status'],
            'last_scan': state.playback_monitor['last_scan'],
            'log_files': state.playback_monitor['log_files'],
            'dat_files': state.playback_monitor['dat_files'],
            'pending_file': state.playback_monitor['pending_file'],
            'last_error': state.playback_monitor['last_error'],
            'reconnect_count': state.playback_monitor['reconnect_count'],
            'scan_interval_seconds': state.playback_monitor['scan_interval_seconds']
        })

    except Exception as e:
        logger.error(f"Error getting playback monitor status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ========================================
# PLAYBACK SERVER API ENDPOINTS
# ========================================

@bp.route("/api/playback/server-check")
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
            except Exception:
                connected = False

        return jsonify({
            'connected': connected,
            'ip': PLAYBACK_SERVER['ip'],
            'port': PLAYBACK_SERVER['port']
        })

    except Exception as e:
        logger.error(f"Playback server check error: {e}")
        return jsonify({'connected': False, 'error': str(e)})


@bp.route("/api/playback/open-winscp", methods=["POST"])
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
            winscp_exe = shutil.which("WinSCP.exe") or shutil.which("winscp")

        if not winscp_exe:
            return jsonify({
                'success': False,
                'message': 'WinSCP not found. Please install WinSCP or add it to PATH.'
            })

        # Build WinSCP command with SFTP URL
        # Format: sftp://user:password@host/path/
        sftp_url = (
            f"sftp://{PLAYBACK_SERVER['user']}:{PLAYBACK_SERVER['password']}"
            f"@{PLAYBACK_SERVER['ip']}{PLAYBACK_SERVER['path']}"
        )

        # Launch WinSCP
        subprocess.Popen(
            [winscp_exe, sftp_url],
            creationflags=subprocess.CREATE_NEW_CONSOLE if platform.system() == "Windows" else 0
        )

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


@bp.route("/api/playback/local-files")
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


@bp.route("/api/playback/server-files")
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


@bp.route("/api/playback/find-file")
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
                except Exception:
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


# ========================================
# FILE DOWNLOAD (USB transfer)
# ========================================

def _download_file_thread(filename, file_size, local_path, remote_path):
    """Background thread for file download with progress tracking"""
    try:
        # Initialize progress
        state.download_progress[filename] = {
            'status': 'downloading',
            'progress': 0,
            'total_size': file_size,
            'local_path': str(local_path),
            'error': None
        }

        if not paramiko:
            state.download_progress[filename]['status'] = 'error'
            state.download_progress[filename]['error'] = 'SSH library not available'
            return

        # Connect to server
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            PLAYBACK_SERVER['ip'],
            port=PLAYBACK_SERVER['port'],
            username=PLAYBACK_SERVER['user'],
            password=PLAYBACK_SERVER['password'],
            timeout=10
        )

        sftp = ssh.open_sftp()

        # Get actual file size if not provided
        if not file_size:
            try:
                file_attr = sftp.stat(remote_path)
                file_size = file_attr.st_size
                state.download_progress[filename]['total_size'] = file_size
            except Exception:
                pass

        # Download with callback
        def progress_callback(transferred, total):
            if total > 0:
                percent = int((transferred / total) * 100)
                state.download_progress[filename]['progress'] = percent

        sftp.get(remote_path, str(local_path), callback=progress_callback)

        sftp.close()
        ssh.close()

        # Mark as complete
        if local_path.exists():
            state.download_progress[filename]['status'] = 'complete'
            state.download_progress[filename]['progress'] = 100
        else:
            state.download_progress[filename]['status'] = 'error'
            state.download_progress[filename]['error'] = 'File not found after download'

    except Exception as e:
        state.download_progress[filename]['status'] = 'error'
        state.download_progress[filename]['error'] = str(e)


@bp.route("/api/playback/download-file", methods=["POST"])
def api_playback_download_file():
    """
    Start a file download from the server to the local USB playback folder.
    Returns immediately with download ID. Use /api/playback/download-progress to check status.
    """
    try:
        data = request.get_json()
        filename = data.get('filename')
        file_size = data.get('size', 0)

        if not filename:
            return jsonify({'success': False, 'message': 'Filename required'})

        # OFFLINE MODE: Simulate successful download
        if not is_online_network():
            # Simulate with progress tracking
            state.download_progress[filename] = {
                'status': 'complete',
                'progress': 100,
                'total_size': 15728640,
                'local_path': f'USB:/playback/{filename}',
                'error': None
            }
            return jsonify({
                'success': True,
                'message': f'[OFFLINE MODE] Simulated download of {filename}',
                'download_id': filename,
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

        # Check if already downloading
        if (filename in state.download_progress
                and state.download_progress[filename]['status'] == 'downloading'):
            return jsonify({
                'success': True,
                'message': 'Download already in progress',
                'download_id': filename
            })

        # Start download in background thread
        thread = threading.Thread(
            target=_download_file_thread,
            args=(filename, file_size, local_path, remote_path),
            daemon=True
        )
        thread.start()

        return jsonify({
            'success': True,
            'message': 'Download started',
            'download_id': filename
        })

    except Exception as e:
        logger.error(f"Download file error: {e}")
        return jsonify({'success': False, 'message': str(e)})


@bp.route("/api/playback/download-progress/<filename>")
def api_playback_download_progress(filename):
    """Get download progress for a specific file"""
    if filename in state.download_progress:
        return jsonify(state.download_progress[filename])
    else:
        return jsonify({
            'status': 'not_found',
            'progress': 0,
            'error': 'Download not found'
        })


@bp.route("/api/playback/predict-next-file")
def api_playback_predict_next_file():
    """
    Analyze recent playback files and predict when the next file will be available.
    Returns prediction based on file timestamp patterns.
    """
    try:
        # OFFLINE MODE
        if not is_online_network():
            now = datetime.now()
            next_time = now + timedelta(
                minutes=15 - (now.minute % 15),
                seconds=-now.second,
                microseconds=-now.microsecond
            )

            next_file_name = f"AHS_LOG_{next_time.strftime('%Y%m%d_%H%M00')}_AEST.dat"

            # Add 2-minute buffer for .dat file to be fully written after .log files
            next_time_with_buffer = next_time + timedelta(minutes=2)

            return jsonify({
                'success': True,
                'has_prediction': True,
                'last_file_time': None,
                'next_file_time': next_time_with_buffer.isoformat(),
                'predicted_file_time': next_time.isoformat(),
                'last_file_name': None,
                'next_file_name': next_file_name,
                'countdown_seconds': int((next_time_with_buffer - now).total_seconds()),
                'average_interval_minutes': 15,
                'files_analyzed': 10,
                'confidence': 'high',
                'offline_mode': True
            })

        if not paramiko:
            return jsonify({'success': False, 'error': 'SSH library not available'})

        # Return cached result if fresh (avoids SSH on every 2-second frontend poll)
        now_ts = time.monotonic()
        if _predict_cache['result'] and (now_ts - _predict_cache['ts']) < _PREDICT_CACHE_TTL:
            cached = dict(_predict_cache['result'])
            if cached.get('has_prediction') and cached.get('next_file_time'):
                try:
                    next_time = datetime.fromisoformat(cached['next_file_time'])
                    countdown = int((next_time - datetime.now()).total_seconds())
                    cached['countdown_seconds'] = countdown
                    cached['is_overdue'] = countdown < 0
                except Exception:
                    pass
            cached['from_cache'] = True
            return jsonify(cached)

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
            return jsonify({'success': False, 'error': f'Connection failed: {str(e)}'})

        sftp = ssh.open_sftp()

        try:
            file_list = sftp.listdir_attr(PLAYBACK_SERVER['path'])
        except Exception as e:
            sftp.close()
            ssh.close()
            return jsonify({'success': False, 'error': f'Cannot read directory: {str(e)}'})

        sftp.close()
        ssh.close()

        # Parse timestamps + keep filenames
        file_items = []  # list of (dt, filename)

        for f in file_list:
            if f.filename.startswith('AHS_LOG_') and f.filename.endswith('.dat'):
                try:
                    # AHS_LOG_YYYYMMDD_HHMMSS_AEST.dat
                    parts = f.filename.split('_')
                    date_part = parts[2]  # YYYYMMDD
                    time_part = parts[3]  # HHMMSS

                    year = int(date_part[0:4])
                    month = int(date_part[4:6])
                    day = int(date_part[6:8])
                    hour = int(time_part[0:2])
                    minute = int(time_part[2:4])
                    second = int(time_part[4:6])

                    dt = datetime(year, month, day, hour, minute, second)
                    file_items.append((dt, f.filename))
                except Exception:
                    continue

        if len(file_items) < 2:
            return jsonify({
                'success': True,
                'has_prediction': False,
                'error': 'Not enough files to predict pattern (need at least 2)'
            })

        # Sort by time
        file_items.sort(key=lambda x: x[0])
        file_timestamps = [x[0] for x in file_items]

        # Calculate intervals in minutes
        intervals = []
        for i in range(1, len(file_timestamps)):
            interval = (file_timestamps[i] - file_timestamps[i - 1]).total_seconds() / 60.0
            intervals.append(interval)

        recent_intervals = intervals[-20:] if len(intervals) > 20 else intervals
        avg_interval = sum(recent_intervals) / len(recent_intervals)

        # Most recent file info
        last_file_time, last_file_name = file_items[-1]

        # Predict next file time
        predicted_next = last_file_time + timedelta(minutes=avg_interval)

        # Snap seconds to 00 (matches your naming convention / cadence)
        predicted_next = predicted_next.replace(second=0, microsecond=0)

        next_file_name = f"AHS_LOG_{predicted_next.strftime('%Y%m%d_%H%M00')}_AEST.dat"

        # Add buffer time: AHS_EVENTS/INDEX/CACHE .log files are written first,
        # then the .dat file is created. Add 2 minutes to ensure .dat is fully written.
        predicted_next_with_buffer = predicted_next + timedelta(minutes=2)

        # Countdown (allow negative so UI can show overdue)
        now = datetime.now()
        countdown_seconds = int((predicted_next_with_buffer - now).total_seconds())

        # Confidence from variance
        interval_variance = sum((i - avg_interval) ** 2 for i in recent_intervals) / len(recent_intervals)
        if interval_variance < 1:
            confidence = 'high'
        elif interval_variance < 5:
            confidence = 'medium'
        else:
            confidence = 'low'

        result = {
            'success': True,
            'has_prediction': True,
            'last_file_time': last_file_time.isoformat(),
            'next_file_time': predicted_next_with_buffer.isoformat(),
            'predicted_file_time': predicted_next.isoformat(),
            'last_file_name': last_file_name,
            'next_file_name': next_file_name,
            'countdown_seconds': countdown_seconds,
            'average_interval_minutes': round(avg_interval, 1),
            'files_analyzed': len(file_timestamps),
            'confidence': confidence,
            'is_overdue': countdown_seconds < 0
        }
        _predict_cache['result'] = result
        _predict_cache['ts'] = time.monotonic()
        return jsonify(result)

    except Exception as e:
        logger.error(f"Predict next file error: {e}")
        return jsonify({'success': False, 'error': str(e)})


@bp.route("/api/playback/detect-log-files")
def api_playback_detect_log_files():
    """
    Detect auxiliary .log files (EVENTS, INDEX, CACHE) on the server.
    These indicate a .dat file is currently being written with the SAME timestamp.
    Returns the timestamp from the .log files so we can download the matching .dat file.

    If playback monitor is running, uses cached data for instant response.
    Otherwise, creates new SSH connection.
    """
    try:
        # OFFLINE MODE
        if not is_online_network():
            return jsonify({
                'success': False,
                'error': 'Offline mode - cannot detect log files'
            })

        # USE CACHED DATA if monitor is running and connected
        if (state.playback_monitor['running']
                and state.playback_monitor['connected']
                and state.playback_monitor['pending_file']):
            pending = state.playback_monitor['pending_file']

            # Calculate countdown based on timestamp
            try:
                timestamp_str = pending['timestamp']  # Format: YYYYMMDD_HHMMSS
                date_part, time_part = timestamp_str.split('_')

                year = int(date_part[0:4])
                month = int(date_part[4:6])
                day = int(date_part[6:8])
                hour = int(time_part[0:2])
                minute = int(time_part[2:4])
                second = int(time_part[4:6])

                dt = datetime(year, month, day, hour, minute, second)
                now = datetime.now()
                elapsed_seconds = int((now - dt).total_seconds())
                estimated_ready_time = dt + timedelta(minutes=2)
                countdown_seconds = int((estimated_ready_time - now).total_seconds())

                return jsonify({
                    'success': True,
                    'has_log_files': True,
                    'dat_exists': pending['dat_exists'],
                    'log_files_count': len(state.playback_monitor['log_files']),
                    'most_recent_log': pending['log_file'],
                    'timestamp': dt.isoformat(),
                    'predicted_filename': pending['predicted_dat'],
                    'elapsed_seconds': elapsed_seconds,
                    'countdown_seconds': max(0, countdown_seconds),
                    'estimated_ready_time': estimated_ready_time.isoformat(),
                    'is_ready': countdown_seconds <= 0 or pending['dat_exists'],
                    'from_cache': True  # Indicate this came from cached data
                })
            except Exception as cache_err:
                logger.warning(f"Error parsing cached data: {cache_err}")
                # Fall through to SSH connection below

        # FALLBACK: Create new SSH connection if monitor not running
        if not paramiko:
            return jsonify({'success': False, 'error': 'SSH library not available'})

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
            return jsonify({'success': False, 'error': f'Connection failed: {str(e)}'})

        sftp = ssh.open_sftp()

        try:
            file_list = sftp.listdir_attr(PLAYBACK_SERVER['path'])
        except Exception as e:
            sftp.close()
            ssh.close()
            return jsonify({'success': False, 'error': f'Cannot read directory: {str(e)}'})

        sftp.close()
        ssh.close()

        # Look for auxiliary .log files (EVENTS, INDEX, CACHE)
        log_files = []
        for f in file_list:
            fname = f.filename
            if fname.startswith('AHS_') and fname.endswith('_AEST.log'):
                # Check if it's one of the auxiliary files
                if 'EVENTS_' in fname or 'INDEX_' in fname or 'CACHE_' in fname:
                    log_files.append((fname, f.st_mtime))

        if not log_files:
            return jsonify({
                'success': True,
                'has_log_files': False,
                'message': 'No .log files detected'
            })

        # Sort by modification time to get the most recent
        log_files.sort(key=lambda x: x[1], reverse=True)
        most_recent_log = log_files[0][0]

        # Extract timestamp from the most recent log file
        # Format: AHS_EVENTS_YYYYMMDD_HHMMSS_AEST.log
        try:
            parts = most_recent_log.split('_')
            # Find the date and time parts
            date_part = None
            time_part = None

            for i in range(len(parts) - 2):
                if len(parts[i]) == 8 and parts[i].isdigit():  # YYYYMMDD
                    date_part = parts[i]
                    time_part = parts[i + 1]  # HHMMSS
                    break

            if not date_part or not time_part:
                raise ValueError("Could not find date/time in filename")

            year = int(date_part[0:4])
            month = int(date_part[4:6])
            day = int(date_part[6:8])
            hour = int(time_part[0:2])
            minute = int(time_part[2:4])
            second = int(time_part[4:6])

            dt = datetime(year, month, day, hour, minute, second)

        except Exception as parse_err:
            return jsonify({
                'success': False,
                'error': f'Could not parse timestamp from log file: {str(parse_err)}'
            })

        # Construct the expected .dat filename with THE SAME TIMESTAMP
        predicted_dat_filename = f"AHS_LOG_{date_part}_{time_part}_AEST.dat"

        # Check if .dat file already exists
        dat_exists = any(
            f.filename == predicted_dat_filename
            for f in file_list
        )

        # Calculate time until .dat should be ready
        # (typically 2 minutes after .log files appear)
        now = datetime.now()
        elapsed_seconds = int((now - dt).total_seconds())
        estimated_ready_time = dt + timedelta(minutes=2)
        countdown_seconds = int((estimated_ready_time - now).total_seconds())

        return jsonify({
            'success': True,
            'has_log_files': True,
            'dat_exists': dat_exists,
            'log_files_count': len(log_files),
            'most_recent_log': most_recent_log,
            'timestamp': dt.isoformat(),
            'predicted_filename': predicted_dat_filename,
            'elapsed_seconds': elapsed_seconds,
            'countdown_seconds': max(0, countdown_seconds),  # Don't show negative
            'estimated_ready_time': estimated_ready_time.isoformat(),
            'is_ready': countdown_seconds <= 0 or dat_exists
        })

    except Exception as e:
        logger.error(f"Detect log files error: {e}")
        return jsonify({'success': False, 'error': str(e)})


@bp.route("/api/playback/find-files")
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
        except Exception:
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
                except Exception:
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


@bp.route("/api/playback/delete-file", methods=["POST"])
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
# PLAYBACK DIRECT DOWNLOAD (for remote PCs)
# ========================================
# These routes stream files directly to the user's browser for download.
# Remote PCs download files to their local PC, not to USB on the server.
# This replaces the old USB-based workflow where files were stored on server USB.

@bp.route("/download/playback/<filename>")
def download_playback_file(filename):
    """
    Stream playback file directly to remote PC browser.
    Downloads from server via SFTP and streams to user.
    """
    try:
        # Validate filename to prevent path traversal
        if '..' in filename or '/' in filename or '\\' in filename:
            return "Invalid filename", 400

        # Validate it's a playback file
        if not filename.startswith('AHS_LOG_') or not filename.endswith('.dat'):
            return "Invalid playback file", 400

        # OFFLINE MODE: Return dummy file
        if not is_online_network():
            dummy_data = b'OFFLINE MODE - Test playback file data\n' * 100
            return send_file(
                BytesIO(dummy_data),
                as_attachment=True,
                download_name=filename,
                mimetype='application/octet-stream'
            )

        if not paramiko:
            return "SSH library not available", 500

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
            logger.error(f"SSH connection failed: {e}")
            return f"Server connection failed: {str(e)}", 500

        sftp = ssh.open_sftp()
        remote_path = PLAYBACK_SERVER['path'] + filename

        # Check if file exists
        try:
            file_attr = sftp.stat(remote_path)
            file_size = file_attr.st_size  # noqa: F841 — reserved for future use
        except Exception:
            sftp.close()
            ssh.close()
            return "File not found on server", 404

        # Use a temporary file to stream
        with tempfile.NamedTemporaryFile(delete=False, suffix='.dat') as tmp_file:
            temp_path = tmp_file.name

            try:
                # Download to temp file
                sftp.get(remote_path, temp_path)
                sftp.close()
                ssh.close()

                # Send file to user and delete temp file after
                return send_file(
                    temp_path,
                    as_attachment=True,
                    download_name=filename,
                    mimetype='application/octet-stream'
                )
            except Exception as e:
                sftp.close()
                ssh.close()
                # Clean up temp file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                logger.error(f"File download error: {e}")
                return f"Download failed: {str(e)}", 500

    except Exception as e:
        logger.error(f"Playback download error: {e}")
        return str(e), 500
