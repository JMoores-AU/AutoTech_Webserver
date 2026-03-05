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
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta

import app.state as state
import app.config as config # Import app.config as config
from app.utils import (
    check_ptx_reachable,
    get_ptx_uptime,
    connect_to_equipment,
    is_online_network as is_online_network_func, # Alias to avoid name conflict
    search_equipment as _search_equipment,       # Private alias — avoids parameter name collision
    _resolve_tool_executable_path # Import directly from app.utils
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

# Scale: SSH thread concurrency drops as online count rises to protect PTX SSH daemons.
# Tiers drop in steps of 50 online equipment.
_WORKER_SCALE = [
    (500, 5),
    (450, 6),
    (400, 7),
    (350, 8),
    (300, 10),
    (250, 12),
    (200, 14),
    (150, 16),
    (100, 18),
    (0,   20),
]

def _get_max_workers(online_count):
    """Return SSH thread pool size based on how many units are online."""
    for threshold, workers in _WORKER_SCALE:
        if online_count >= threshold:
            return workers
    return 20


def _ping_equipment(equipment):
    """Ping a single unit. Returns (equipment_id, ip, reachable)."""
    equipment_id = equipment.get('equipment_id')
    ip = equipment.get('ip')
    if not equipment_id or not ip:
        return (equipment_id, ip, False)
    reachable = check_ptx_reachable(ip, timeout=2.0)
    return (equipment_id, ip, reachable)


def _ssh_check_equipment(equipment_id, ip, ptx_db):
    """SSH to one unit, read uptime, write to DB. Returns status string."""
    result = get_ptx_uptime(ip)
    if result['success']:
        ptx_type = result.get('ptx_type') or 'PTX'
        ptx_db.upsert_uptime(
            equipment_id=equipment_id,
            ip_address=ip,
            uptime_hours=result['uptime_hours'],
            last_check=datetime.now().strftime('%a %b %d %H:%M:%S AEST %Y'),
            last_check_timestamp=int(time.time()),
            ptx_type=ptx_type,
        )
        ptx_db.update_status(equipment_id, 'online', ptx_type)
        return 'online'
    else:
        ptx_db.update_status(equipment_id, 'unknown')
        logger.debug(f"PTX checker SSH error {equipment_id}: {result.get('error')}")
        return 'error'


def _wait_for_interval():
    """Wait for the configured interval, checking stop event every 10 seconds."""
    checker = state.ptx_uptime_checker
    interval_seconds = checker['interval_minutes'] * 60
    checker['next_cycle'] = (
        datetime.now() + timedelta(seconds=interval_seconds)
    ).isoformat()
    checker['status'] = 'waiting'
    for _ in range(interval_seconds // 10):
        if checker['stop_event'].is_set():
            break
        time.sleep(10)
    remaining = interval_seconds % 10
    if remaining > 0 and not checker['stop_event'].is_set():
        time.sleep(remaining)


def ptx_uptime_checker_worker():
    """
    Background worker — hourly PTX uptime sweep.

    Cycle:
      Phase 1 — Parallel ping all equipment (50 threads, ICMP only, fast).
      Phase 2 — Scale SSH concurrency from online count using _WORKER_SCALE.
      Phase 3 — ThreadPoolExecutor SSH checks on reachable units only.
      Phase 4 — Sleep until next 1hr cycle.
    """
    checker = state.ptx_uptime_checker
    ptx_db = state.ptx_uptime_db

    set_request_id('bg-ptx-checker')
    logger.info("PTX Uptime Checker started (threaded, 1hr cycle)")
    log_background('info', 'ptx_checker',
                   f'PTX Uptime Checker started (interval: {checker["interval_minutes"]} min)')

    while not checker['stop_event'].is_set():
        try:
            equipment_list = ptx_db.get_all_uptime(min_hours=0)

            if not equipment_list:
                logger.warning("PTX Uptime Checker: No equipment in database — waiting")
                checker['status'] = 'waiting'
                _wait_for_interval()
                continue

            total = len(equipment_list)
            checker['total_equipment'] = total
            checker['checked_count'] = 0
            checker['online_count'] = 0
            checker['offline_count'] = 0
            checker['error_count'] = 0
            checker['last_cycle_start'] = datetime.now().isoformat()
            checker['status'] = 'pinging'

            logger.info(f"PTX checker: Phase 1 — pinging {total} units")

            # --- Phase 1: parallel ping ---
            online_units = []   # [(equipment_id, ip)]
            with ThreadPoolExecutor(max_workers=50) as ping_pool:
                futures = {ping_pool.submit(_ping_equipment, eq): eq for eq in equipment_list}
                for future in as_completed(futures):
                    if checker['stop_event'].is_set():
                        break
                    equipment_id, ip, reachable = future.result()
                    if reachable:
                        online_units.append((equipment_id, ip))
                    else:
                        checker['offline_count'] += 1
                        checker['checked_count'] += 1
                        if equipment_id:
                            ptx_db.update_status(equipment_id, 'offline')

            online_count = len(online_units)
            max_workers = _get_max_workers(online_count)
            checker['online_count'] = 0  # reset — incremented during SSH phase
            checker['ssh_workers'] = max_workers
            checker['status'] = 'checking'

            logger.info(
                f"PTX checker: Phase 2 — {online_count}/{total} online, "
                f"using {max_workers} SSH threads"
            )
            log_background('info', 'ptx_checker',
                           f'Ping complete: {online_count} online, {checker["offline_count"]} offline, '
                           f'SSH workers={max_workers}')

            # --- Phase 2: threaded SSH ---
            with ThreadPoolExecutor(max_workers=max_workers) as ssh_pool:
                futures = {
                    ssh_pool.submit(_ssh_check_equipment, eid, ip, ptx_db): eid
                    for eid, ip in online_units
                }
                for future in as_completed(futures):
                    if checker['stop_event'].is_set():
                        break
                    status = future.result()
                    checker['checked_count'] += 1
                    if status == 'online':
                        checker['online_count'] += 1
                    else:
                        checker['error_count'] += 1

            checker['last_cycle_end'] = datetime.now().isoformat()
            checker['current_equipment'] = None

            summary = (
                f"Cycle complete: total={total}, online={checker['online_count']}, "
                f"offline={checker['offline_count']}, errors={checker['error_count']}, "
                f"ssh_workers={max_workers}"
            )
            logger.info(f"PTX checker: {summary}")
            log_background('info', 'ptx_checker', summary)

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

def _ssh_health_probe(ssh) -> dict:
    """
    Run uptime and free -m on an open SSH connection.
    Returns dict with uptime_hours (float) and mem_usage (int %) or raises on failure.
    """
    import re

    # Uptime
    _, stdout, _ = ssh.exec_command("uptime", timeout=10)
    uptime_raw = stdout.read().decode('utf-8', errors='ignore').strip()

    uptime_hours = 0.0
    m = re.search(r'up\s+(\d+)\s+days?,\s+(\d+):(\d+)', uptime_raw)
    if m:
        uptime_hours = int(m.group(1)) * 24 + int(m.group(2)) + int(m.group(3)) / 60
    else:
        m = re.search(r'up\s+(\d+):(\d+)', uptime_raw)
        if m:
            uptime_hours = int(m.group(1)) + int(m.group(2)) / 60
        else:
            m = re.search(r'up\s+(\d+)\s+min', uptime_raw)
            if m:
                uptime_hours = int(m.group(1)) / 60

    # Memory — free -m gives plain integers
    _, stdout, _ = ssh.exec_command("free -m", timeout=10)
    mem_raw = stdout.read().decode('utf-8', errors='ignore')

    mem_usage = 0
    for line in mem_raw.splitlines():
        if line.lower().startswith('mem:'):
            parts = line.split()
            if len(parts) >= 3:
                total = int(parts[1])
                used = int(parts[2])
                if total > 0:
                    mem_usage = round((used / total) * 100)
            break

    return {'uptime_hours': round(uptime_hours, 2), 'mem_usage': mem_usage}


def probe_equipment_health(equipment_id, mock_equipment_db: dict = None,
                           mms_server_config: dict = None,
                           equipment_profiles: dict = None,
                           is_online_func: callable = None,
                           search_equipment_func: callable = None):
    """
    Health probe for Dig Fleet Monitor.

    IP lookup order (no MMS involved by default):
      1. equipment_info cache in fleet_monitor.db (populated from IP_list.dat on startup)
      2. MMS server SSH — only if equipment not in cache and MMS is reachable (fallback)

    Once the PTX IP is known, this server SSHes directly to the unit,
    runs uptime + free -m in a single connection, and stores the result.
    The detected PTX model (PTXC / PTXC (New OS) / PTX10) is cached so
    credential detection only happens once per unit.
    """
    import random

    if mock_equipment_db is None:     mock_equipment_db   = config.MOCK_EQUIPMENT_DB
    if mms_server_config is None:     mms_server_config   = config.MMS_SERVER
    if is_online_func is None:        is_online_func      = is_online_network_func
    if search_equipment_func is None: search_equipment_func = _search_equipment

    fleet_db = state.fleet_monitor_db

    # ----------------------------------------------------------------
    # DEV/OFFICE MODE — no route to the mining network
    # ----------------------------------------------------------------
    if not is_online_func(config.GATEWAY_IP, config.PROBE_PORT):
        states = ['green', 'yellow', 'red']
        state_name = states[sum(ord(c) for c in equipment_id) % 3]
        if state_name == 'green':
            uptime, mem = random.uniform(1, 23), random.randint(20, 69)
        elif state_name == 'yellow':
            uptime, mem = random.uniform(24, 35), random.randint(70, 79)
        else:
            uptime, mem = random.uniform(37, 200), random.randint(81, 95)
        fleet_db.update_health(equipment_id, uptime, mem)
        return

    # ----------------------------------------------------------------
    # PRODUCTION MODE — SSH directly to the PTX
    # ----------------------------------------------------------------
    if not paramiko:
        logger.error("Fleet Monitor: paramiko not available")
        return

    try:
        # 1. Resolve PTX IP from equipment_cache.db (kept current by IP Finder searches)
        from tools.equipment_db import get_equipment, save_equipment
        eq_db_path = state.EQUIPMENT_DB_PATH
        cached = get_equipment(eq_db_path, equipment_id) if eq_db_path else None
        ptx_ip = cached.get('network_ip') if cached else None
        avi_ip = cached.get('avi_ip') if cached else None
        cached_model = cached.get('ptx_model') if cached else None

        if not ptx_ip:
            # Fallback: query MMS to discover the IP, saves result to equipment_cache.db
            logger.info(f"Fleet Monitor: {equipment_id} not in equipment_cache, querying MMS")
            info = search_equipment_func(equipment_id, mock_equipment_db, mms_server_config, is_online_func)
            ptx_ip = info.get('ptx_ip')
            if not ptx_ip:
                logger.warning(f"Fleet Monitor: No IP found for {equipment_id}")
                return
            avi_ip = info.get('avi_ip')
            cached_model = info.get('ptx_model')
            # MMS result is already saved to equipment_cache.db by search_equipment()

        # 2. Connect directly to the PTX — auto-detects PTXC / PTXC (New OS) / PTX10
        ssh, detected_model = connect_to_equipment(ptx_ip)
        if not ssh:
            logger.warning(f"Fleet Monitor: Cannot connect to {equipment_id} ({ptx_ip}): {detected_model}")
            return

        # Update equipment_cache.db with detected model if it changed or wasn't set
        if detected_model and detected_model != cached_model and eq_db_path:
            save_equipment(eq_db_path, equipment_name=equipment_id, ptx_model=detected_model)

        # 3. Run health commands on the same open connection
        try:
            result = _ssh_health_probe(ssh)
        finally:
            try:
                ssh.close()
            except Exception:
                pass

        fleet_db.update_health(equipment_id, result['uptime_hours'], result['mem_usage'])
        logger.info(
            f"Fleet Monitor: {equipment_id} ({detected_model}) "
            f"-> {result['uptime_hours']}h uptime, {result['mem_usage']}% mem"
        )

    except Exception as e:
        logger.error(f"Fleet Monitor: Error probing {equipment_id}: {e}")


def fleet_monitor_worker(fleet_data_path: str, gateway_ip: str, probe_port: int, mock_equipment_db: dict, mms_server_config: dict, equipment_profiles: dict):
    """Background worker for Dig Fleet Monitor - runs every 30 mins."""
    updater = state.fleet_monitor_updater

    set_request_id('bg-fleet-monitor')
    logger.info("Fleet Monitor background worker started")
    log_background('info', 'fleet_monitor', 'Fleet Monitor background worker started')


    while not updater['stop_event'].is_set():
        try:
            if os.path.exists(fleet_data_path):
                with open(fleet_data_path, 'r') as f:
                    data = json.load(f)

                all_ids = []
                for col in data['columns']:
                    all_ids.extend(col['equipment'])

                if all_ids:
                    logger.info(f"Fleet Monitor: Updating {len(all_ids)} units...")
                    for eq_id in all_ids:
                        if updater['stop_event'].is_set():
                            break
                        probe_equipment_health(
                            eq_id, mock_equipment_db, mms_server_config,
                            equipment_profiles, is_online_network_func, _search_equipment
                        )
                        if is_online_network_func(gateway_ip, probe_port):
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
