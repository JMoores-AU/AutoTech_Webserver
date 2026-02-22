"""
app/background_tasks.py
=======================
Background worker thread functions for the AutoTech Web Dashboard.
No Flask route definitions.

All shared state is accessed via `import app.state as state` so workers
always read the live module-level dict, not a frozen import-time snapshot.
"""

import json
import logging
import os
import platform
import subprocess
import time
from datetime import datetime, timedelta

import app.state as state
from app.config import FLEET_DATA_PATH, PLAYBACK_SERVER
from app.utils import (
    check_ptx_reachable,
    get_ptx_uptime,
    is_online_network,
    search_equipment,
)

logger = logging.getLogger(__name__)

# Optional third-party imports
try:
    import paramiko
except ImportError:
    paramiko = None

# App logger helpers — imported lazily to avoid circular imports during startup
try:
    from tools.app_logger import log_background, set_request_id
except ImportError:
    def log_background(*args, **kwargs):
        pass
    def set_request_id(*args, **kwargs):
        pass


# ========================================
# FORMAT HELPERS
# ========================================

def format_uptime_hours(total_hours):
    """Format total hours into 'Xd Yh' string."""
    days = int(total_hours // 24)
    hours = int(total_hours % 24)
    return f"{days}d {hours}h"


# ========================================
# PTX UPTIME CHECKER WORKER
# ========================================

def _wait_for_interval():
    """Wait for the configured interval, checking stop event periodically."""
    checker = state.ptx_uptime_checker
    interval_seconds = checker['interval_minutes'] * 60
    checker['next_cycle'] = (
        datetime.now() + timedelta(seconds=interval_seconds)
    ).isoformat()
    checker['status'] = 'waiting'

    # Check stop event every 10 seconds during wait
    for _ in range(interval_seconds // 10):
        if checker['stop_event'].is_set():
            break
        time.sleep(10)

    # Handle remaining seconds
    remaining = interval_seconds % 10
    if remaining > 0 and not checker['stop_event'].is_set():
        time.sleep(remaining)


def ptx_uptime_checker_worker():
    """
    Background worker that checks uptime on all PTX equipment.
    Runs continuously, checking all equipment then waiting for next cycle.
    Skips equipment that is offline (not pingable).
    """
    checker = state.ptx_uptime_checker
    ptx_db = state.ptx_uptime_db

    set_request_id('bg-ptx-checker')
    logger.info("PTX Uptime Checker started")
    log_background('info', 'ptx_checker',
                   f'PTX Uptime Checker started (interval: {checker["interval_minutes"]} minutes)')
    checker['status'] = 'running'

    while not checker['stop_event'].is_set():
        try:
            equipment_list = ptx_db.get_all_uptime(min_hours=0)

            if not equipment_list:
                logger.warning("PTX Uptime Checker: No equipment in database")
                checker['status'] = 'waiting'
                _wait_for_interval()
                continue

            checker['total_equipment'] = len(equipment_list)
            checker['checked_count'] = 0
            checker['online_count'] = 0
            checker['offline_count'] = 0
            checker['error_count'] = 0
            checker['last_cycle_start'] = datetime.now().isoformat()
            checker['status'] = 'running'

            logger.info(f"PTX Uptime Checker: Starting cycle for {len(equipment_list)} equipment")

            for equipment in equipment_list:
                if checker['stop_event'].is_set():
                    break

                equipment_id = equipment.get('equipment_id')
                ip_address = equipment.get('ip')

                if not equipment_id or not ip_address:
                    checker['error_count'] += 1
                    continue

                checker['current_equipment'] = equipment_id

                if not check_ptx_reachable(ip_address, timeout=2.0):
                    logger.debug(f"PTX Uptime Checker: {equipment_id} ({ip_address}) is offline - skipping")
                    checker['offline_count'] += 1
                    checker['checked_count'] += 1
                    ptx_db.update_status(equipment_id, 'offline')
                    continue

                result = get_ptx_uptime(ip_address)

                if result['success']:
                    ptx_type = result.get('ptx_type') or 'PTX'
                    ptx_db.upsert_uptime(
                        equipment_id=equipment_id,
                        ip_address=ip_address,
                        uptime_hours=result['uptime_hours'],
                        last_check=datetime.now().strftime('%a %b %d %H:%M:%S %Z %Y'),
                        last_check_timestamp=int(time.time()),
                        ptx_type=ptx_type
                    )
                    ptx_db.update_status(equipment_id, 'online', ptx_type)
                    checker['online_count'] += 1
                    logger.debug(f"PTX Uptime Checker: {equipment_id} uptime={result['uptime_hours']:.1f}h")
                else:
                    ptx_db.update_status(equipment_id, 'unknown')
                    checker['error_count'] += 1
                    logger.warning(f"PTX Uptime Checker: {equipment_id} SSH error: {result.get('error')}")

                checker['checked_count'] += 1
                time.sleep(0.5)

            checker['last_cycle_end'] = datetime.now().isoformat()
            checker['current_equipment'] = None

            logger.info(
                f"PTX Uptime Checker: Cycle complete - "
                f"Online: {checker['online_count']}, "
                f"Offline: {checker['offline_count']}, "
                f"Errors: {checker['error_count']}"
            )
            log_background(
                'info',
                'ptx_checker',
                f"Cycle complete: Checked={checker['checked_count']}, "
                f"Online={checker['online_count']}, "
                f"Offline={checker['offline_count']}, "
                f"Errors={checker['error_count']}"
            )

            _wait_for_interval()

        except Exception as e:
            logger.error(f"PTX Uptime Checker error: {e}")
            checker['status'] = 'error'
            time.sleep(60)

    checker['running'] = False
    checker['status'] = 'stopped'
    checker['current_equipment'] = None
    logger.info("PTX Uptime Checker stopped")
    log_background('info', 'ptx_checker', 'PTX Uptime Checker stopped')


# ========================================
# PLAYBACK MONITOR WORKER
# ========================================

def playback_monitor_worker():
    """
    Background worker that maintains persistent SSH/SFTP connection to playback server.
    Monitors playback folder for .log files and .dat files in real-time.
    """
    monitor = state.playback_monitor

    set_request_id('bg-playback-monitor')
    logger.info("Playback Monitor started")
    log_background('info', 'playback_monitor',
                   f'Playback monitor started (scan interval: {monitor["scan_interval_seconds"]}s)')
    monitor['status'] = 'connecting'

    while not monitor['stop_event'].is_set():
        try:
            if not is_online_network():
                monitor['status'] = 'offline'
                monitor['connected'] = False
                time.sleep(30)
                continue

            if not paramiko:
                logger.error("Playback Monitor: Paramiko not available")
                monitor['status'] = 'error'
                monitor['last_error'] = 'SSH library not available'
                time.sleep(60)
                continue

            # Establish SSH connection if not connected
            if not monitor['connected'] or not monitor['ssh_client']:
                try:
                    logger.info(f"Playback Monitor: Connecting to {PLAYBACK_SERVER['ip']}...")

                    ssh = paramiko.SSHClient()
                    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

                    ssh.connect(
                        PLAYBACK_SERVER['ip'],
                        port=PLAYBACK_SERVER['port'],
                        username=PLAYBACK_SERVER['user'],
                        password=PLAYBACK_SERVER['password'],
                        timeout=15,
                        banner_timeout=30
                    )

                    sftp = ssh.open_sftp()

                    monitor['ssh_client'] = ssh
                    monitor['sftp_client'] = sftp
                    monitor['connected'] = True
                    monitor['reconnect_count'] += 1
                    monitor['last_error'] = None
                    monitor['status'] = 'monitoring'

                    logger.info(f"Playback Monitor: Connected successfully (reconnect #{monitor['reconnect_count']})")

                except Exception as conn_err:
                    logger.error(f"Playback Monitor: Connection failed: {conn_err}")
                    monitor['status'] = 'error'
                    monitor['last_error'] = str(conn_err)
                    monitor['connected'] = False

                    if monitor['sftp_client']:
                        try:
                            monitor['sftp_client'].close()
                        except Exception:
                            pass
                        monitor['sftp_client'] = None

                    if monitor['ssh_client']:
                        try:
                            monitor['ssh_client'].close()
                        except Exception:
                            pass
                        monitor['ssh_client'] = None

                    time.sleep(30)
                    continue

            # Monitor the playback folder
            sftp = monitor['sftp_client']

            try:
                file_list = sftp.listdir_attr(PLAYBACK_SERVER['path'])
                monitor['last_scan'] = datetime.now().isoformat()

                log_files = []
                dat_files = []

                for f in file_list:
                    fname = f.filename

                    if fname.startswith('AHS_') and fname.endswith('_AEST.log'):
                        if 'EVENTS_' in fname or 'INDEX_' in fname or 'CACHE_' in fname:
                            log_files.append({
                                'name': fname,
                                'mtime': f.st_mtime,
                                'size': f.st_size
                            })

                    elif fname.startswith('AHS_LOG_') and fname.endswith('.dat'):
                        dat_files.append({
                            'name': fname,
                            'mtime': f.st_mtime,
                            'size': f.st_size
                        })

                log_files.sort(key=lambda x: x['mtime'], reverse=True)
                dat_files.sort(key=lambda x: x['mtime'], reverse=True)

                monitor['log_files'] = log_files[:10]
                monitor['dat_files'] = dat_files[:20]

                # Extract pending file info from most recent .log file
                if log_files:
                    most_recent_log = log_files[0]['name']

                    try:
                        parts = most_recent_log.split('_')
                        date_part = None
                        time_part = None

                        for i in range(len(parts) - 2):
                            if len(parts[i]) == 8 and parts[i].isdigit():
                                date_part = parts[i]
                                time_part = parts[i + 1]
                                break

                        if date_part and time_part:
                            predicted_dat = f"AHS_LOG_{date_part}_{time_part}_AEST.dat"

                            dat_exists = False
                            dat_size = 0
                            dat_ready = False

                            for f in dat_files:
                                if f['name'] == predicted_dat:
                                    dat_exists = True
                                    dat_size = f['size']
                                    dat_ready = dat_size > 50 * 1024 * 1024  # >50MB = ready
                                    break

                            try:
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
                            except Exception:
                                elapsed_seconds = 0
                                countdown_seconds = 120

                            monitor['pending_file'] = {
                                'log_file': most_recent_log,
                                'predicted_dat': predicted_dat,
                                'dat_exists': dat_exists,
                                'dat_size': dat_size,
                                'dat_size_mb': round(dat_size / (1024 * 1024), 1),
                                'dat_ready': dat_ready,
                                'timestamp': f"{date_part}_{time_part}",
                                'elapsed_seconds': elapsed_seconds,
                                'countdown_seconds': max(0, countdown_seconds)
                            }
                        else:
                            monitor['pending_file'] = None

                    except Exception as parse_err:
                        logger.warning(f"Playback Monitor: Could not parse log file: {parse_err}")
                        monitor['pending_file'] = None
                else:
                    monitor['pending_file'] = None

                monitor['status'] = 'monitoring'

            except Exception as scan_err:
                logger.error(f"Playback Monitor: Scan error: {scan_err}")
                monitor['status'] = 'error'
                monitor['last_error'] = str(scan_err)
                monitor['connected'] = False

                try:
                    monitor['sftp_client'].close()
                    monitor['ssh_client'].close()
                except Exception:
                    pass

                monitor['sftp_client'] = None
                monitor['ssh_client'] = None

                time.sleep(10)
                continue

            # Wait before next scan (respect stop event)
            scan_interval = monitor['scan_interval_seconds']
            for _ in range(scan_interval):
                if monitor['stop_event'].is_set():
                    break
                time.sleep(1)

        except Exception as e:
            logger.error(f"Playback Monitor: Unexpected error: {e}")
            monitor['status'] = 'error'
            monitor['last_error'] = str(e)
            monitor['connected'] = False
            time.sleep(30)

    # Cleanup on stop
    if monitor['sftp_client']:
        try:
            monitor['sftp_client'].close()
        except Exception:
            pass

    if monitor['ssh_client']:
        try:
            monitor['ssh_client'].close()
        except Exception:
            pass

    monitor['running'] = False
    monitor['connected'] = False
    monitor['status'] = 'stopped'
    logger.info("Playback Monitor stopped")
    log_background('info', 'playback_monitor', 'Playback monitor stopped')


# ========================================
# BACKGROUND EQUIPMENT UPDATER WORKER
# ========================================

def background_update_worker():
    """
    Background worker that updates equipment details one at a time.
    Uses the search_equipment function to query MMS server and updates the database.
    Runs with delays between lookups to avoid bogging down the system.
    """
    from tools.equipment_db import (
        get_equipment_needing_update,
        get_update_progress,
        save_equipment,
    )

    updater = state.background_updater

    set_request_id('bg-equipment-updater')

    # Early exit if database not initialized
    if not state.EQUIPMENT_DB_PATH:
        logger.error("Background updater: Database not initialized")
        updater['status'] = 'error'
        updater['running'] = False
        return

    db_path = state.EQUIPMENT_DB_PATH  # Local variable with guaranteed str type

    logger.info("Background equipment updater started")
    log_background('info', 'equipment_updater', 'Equipment updater started')
    updater['status'] = 'running'
    updater['processed_count'] = 0
    updater['error_count'] = 0

    while not updater['stop_event'].is_set():
        try:
            equipment_list = get_equipment_needing_update(db_path, limit=1)

            if not equipment_list:
                logger.info("Background updater: No more equipment needs updating")
                updater['status'] = 'complete'
                break

            equipment = equipment_list[0]
            equipment_name = equipment['equipment_name']
            updater['current_equipment'] = equipment_name

            logger.info(f"Background updater: Looking up {equipment_name}")

            result = search_equipment(equipment_name)

            if result.get('found'):
                save_equipment(
                    db_path,
                    equipment_name=equipment_name,
                    cid=result.get('cid'),
                    profile=result.get('profile'),
                    network_ip=result.get('ptx_ip') or result.get('network_ip'),
                    avi_ip=result.get('avi_ip'),
                    ptx_model=result.get('ptx_model'),
                    status=result.get('vehicle_status', '').lower() if result.get('vehicle_status') else None
                )
                updater['processed_count'] += 1
                logger.info(f"Background updater: Updated {equipment_name}")
            else:
                # Mark as 'not_found' so we don't keep retrying
                save_equipment(db_path, equipment_name=equipment_name, status='not_found')
                updater['error_count'] += 1
                logger.warning(f"Background updater: Could not find {equipment_name} - marked as not_found")

            updater['last_update'] = datetime.now().isoformat()

            # Delay before next lookup
            delay = updater['delay_seconds']
            for _ in range(delay * 10):  # Check stop event every 100ms
                if updater['stop_event'].is_set():
                    break
                time.sleep(0.1)

        except Exception as e:
            logger.error(f"Background updater error: {e}")
            updater['error_count'] += 1
            time.sleep(5)

    updater['running'] = False
    updater['current_equipment'] = None
    if updater['status'] != 'complete':
        updater['status'] = 'stopped'
    logger.info("Background equipment updater stopped")
    log_background(
        'info',
        'equipment_updater',
        f'Equipment updater stopped. Processed: {updater["processed_count"]}, Errors: {updater["error_count"]}'
    )


# ========================================
# DIG FLEET MONITOR WORKER
# ========================================

def probe_equipment_health(equipment_id):
    """
    Main health probe logic for Dig Fleet Monitor.
    - Field/Prod: Actually SSH to units.
    - Dev/Office: Generate mock data with variety.
    """
    import random
    from tools import ip_finder

    fleet_db = state.fleet_monitor_db

    # DEV/OFFICE MODE: Show all states for demo purposes
    if not is_online_network():
        states = ['green', 'yellow', 'red']
        idx = sum(ord(c) for c in equipment_id) % 3
        state_name = states[idx]

        if state_name == 'green':
            uptime = random.uniform(1, 23)
            mem = random.randint(20, 69)
        elif state_name == 'yellow':
            uptime = random.uniform(24, 35)
            mem = random.randint(70, 79)
        else:
            uptime = random.uniform(37, 200)
            mem = random.randint(81, 95)

        fleet_db.update_health(equipment_id, uptime, mem)
        return

    # PRODUCTION/FIELD MODE: Actual SSH probe
    try:
        info = search_equipment(equipment_id)
        ptx_ip = info.get('ptx_ip')
        ptx_model = info.get('ptx_model', 'PTX10')

        if not ptx_ip:
            logger.warning(f"Fleet Monitor: No IP for {equipment_id}")
            return

        uptime_result = get_ptx_uptime(ptx_ip)

        if ptx_model == 'PTXC':
            user, pw = 'dlog', 'gold'
        else:
            user, pw = 'mms', 'modular'

        health_result = ip_finder.check_linux_health(ptx_ip, user, pw)

        if uptime_result['success'] and health_result['success']:
            uptime_hours = uptime_result['uptime_hours']
            mem_str = health_result['memory_usage'].replace('%', '')
            try:
                mem_usage = int(float(mem_str))
            except Exception:
                mem_usage = 0

            fleet_db.update_health(equipment_id, uptime_hours, mem_usage)
            logger.info(f"Fleet Monitor: Probed {equipment_id} -> {uptime_hours}h, {mem_usage}%")
        else:
            logger.warning(f"Fleet Monitor: Probe failed for {equipment_id}")

    except Exception as e:
        logger.error(f"Error probing {equipment_id}: {e}")


def fleet_monitor_worker():
    """Background worker for Dig Fleet Monitor - runs every 30 mins."""
    updater = state.fleet_monitor_updater

    set_request_id('bg-fleet-monitor')
    logger.info("Fleet Monitor background worker started")
    log_background('info', 'fleet_monitor', 'Fleet Monitor background worker started')

    while not updater['stop_event'].is_set():
        try:
            if os.path.exists(FLEET_DATA_PATH):
                with open(FLEET_DATA_PATH, 'r') as f:
                    data = json.load(f)

                all_ids = []
                for col in data['columns']:
                    all_ids.extend(col['equipment'])

                if all_ids:
                    logger.info(f"Fleet Monitor: Updating {len(all_ids)} units...")
                    for eq_id in all_ids:
                        if updater['stop_event'].is_set():
                            break
                        probe_equipment_health(eq_id)
                        if is_online_network():
                            time.sleep(1)

                    updater['last_run'] = datetime.now().isoformat()
                    log_background('info', 'fleet_monitor', f'Updated health for {len(all_ids)} units')

            # Wait for 30 minutes (check stop event every 10s)
            interval_seconds = updater['interval_minutes'] * 60
            for _ in range(interval_seconds // 10):
                if updater['stop_event'].is_set():
                    break
                time.sleep(10)

        except Exception as e:
            logger.error(f"Fleet Monitor worker error: {e}")
            time.sleep(60)


# ========================================
# BROWSER LAUNCHER
# ========================================

def open_browser():
    """Open browser to the application URL after a short delay."""
    time.sleep(2)
    try:
        if platform.system() == "Windows":
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
                import webbrowser
                webbrowser.open("http://localhost:8888")
        else:
            import webbrowser
            webbrowser.open("http://localhost:8888")
    except Exception as e:
        print(f"Failed to open browser: {e}")
