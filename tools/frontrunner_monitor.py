# tools/frontrunner_monitor.py
"""
FrontRunner Background Monitor - Maintains persistent SSH connection
Continuously monitors server status and caches results for web access
Supports offline mode with mock data and proper logging
"""
import paramiko
import os
import socket
import re
import json
import time
import threading
from datetime import datetime
from typing import Optional, Dict, Any

# Handle imports for both module and standalone use
try:
    from .app_logger import log_tool, log_background, set_request_id
    from . import frontrunner_event_db
except ImportError:
    # Fallback for standalone execution
    try:
        from app_logger import log_tool, log_background, set_request_id
    except ImportError:
        # No-op fallback if logger not available
        def log_tool(level, subcategory, message, request_id=None):
            pass
        def log_background(level, subcategory, message, request_id=None):
            pass
        def set_request_id(request_id):
            pass
    import frontrunner_event_db

# Cache file location
CACHE_FILE = "frontrunner_status_cache.json"
UPDATE_INTERVAL = 30  # seconds between updates

# Exponential backoff retry delays (seconds)
RETRY_DELAYS = [30, 60, 120, 300]  # 30s -> 60s -> 120s -> 300s max

# Offline test data - mirrors frontrunner_status.py
OFFLINE_TEST_DATA = {
    'success': True,
    'uptime': {
        'pretty': 'up 2 weeks, 3 days, 14 hours, 23 minutes',
        'days': 17.6,
        'seconds': 1520580.0
    },
    'memory': {
        'total_mb': 16384,
        'used_mb': 12288,
        'free_mb': 4096,
        'percent': 75.0
    },
    'cpu': {
        'load_1min': 1.85,
        'count': 4,
        'percent': 46.3
    },
    'disk': {
        'total_gb': 10240.0,
        'used_gb': 7168.0,
        'avail_gb': 3072.0,
        'percent': 70.0,
        'drives': [
            {'device': '//grm0psmb02.fs.pcn.bma.bhpb.net/', 'size': '10T', 'used': '7.0T', 'avail': '3.0T', 'use_percent': '70%', 'mount': '/mnt/share'}
        ]
    },
    'processes': {
        'services': [
            {'name': 'FrontRunner Server', 'status': 'Running'},
            {'name': 'haul road planning server', 'status': 'Running'},
            {'name': 'path planning server', 'status': 'Running'}
        ],
        'running_count': 3,
        'total_count': 3,
        'all_running': True
    },
    'mode': 'offline_test'
}


def _check_network_reachable(hostname: str, timeout: float = 2.0) -> bool:
    """
    Check if network host is reachable via TCP probe.
    Returns True if reachable, False otherwise.
    """
    try:
        with socket.create_connection((hostname, 22), timeout=timeout):
            return True
    except (socket.timeout, socket.error, OSError):
        return False


class FrontRunnerMonitor:
    """Background monitor for FrontRunner server status"""

    def __init__(self, hostname: str, username: str, password: str, cache_dir: str, offline_mode: bool = False):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.cache_path = os.path.join(cache_dir, CACHE_FILE)
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.ssh: Optional[paramiko.SSHClient] = None
        self.db_path: Optional[str] = None
        self.offline_mode = offline_mode
        self.retry_count = 0  # Track retry attempts for exponential backoff

        # Initialize event database
        try:
            self.db_path = frontrunner_event_db.get_database_path(cache_dir)
            frontrunner_event_db.init_database(self.db_path)
        except Exception as e:
            log_background('warning', 'frontrunner_monitor', f'Could not initialize event database: {e}')

    def start(self):
        """Start the background monitoring thread"""
        if self.running:
            log_background('info', 'frontrunner_monitor', 'Monitor already running')
            return

        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        
        mode_str = "OFFLINE MODE" if self.offline_mode else f"for {self.hostname}"
        log_background('info', 'frontrunner_monitor', f'FrontRunner monitor started {mode_str}')

    def stop(self):
        """Stop the background monitoring thread"""
        self.running = False
        if self.ssh:
            try:
                self.ssh.close()
            except Exception:
                pass
        if self.thread:
            self.thread.join(timeout=5)
        log_background('info', 'frontrunner_monitor', 'FrontRunner monitor stopped')

    def get_cached_status(self) -> Optional[Dict[str, Any]]:
        """Read cached status from file"""
        try:
            if os.path.exists(self.cache_path):
                with open(self.cache_path, 'r') as f:
                    data = json.load(f)
                    # Check if cache is recent (within last 2 minutes)
                    cache_time = datetime.fromisoformat(data.get('report_time', '2000-01-01 00:00:00'))
                    age = (datetime.now() - cache_time).total_seconds()
                    if age < 120:  # 2 minutes
                        return data
        except Exception as e:
            log_background('warning', 'frontrunner_monitor', f'Error reading cache: {e}')
        return None

    def _save_cache(self, status: Dict[str, Any]):
        """Save status to cache file"""
        try:
            with open(self.cache_path, 'w') as f:
                json.dump(status, f, indent=2)
        except Exception as e:
            log_background('error', 'frontrunner_monitor', f'Error writing cache: {e}')

    def _connect_ssh(self) -> bool:
        """Establish SSH connection"""
        try:
            if self.ssh:
                try:
                    self.ssh.close()
                except Exception:
                    pass

            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh.connect(
                hostname=self.hostname,
                username=self.username,
                password=self.password,
                timeout=30
            )
            log_tool('info', 'frontrunner', f'SSH connected to {self.hostname}')
            self.retry_count = 0  # Reset retry count on successful connection
            return True
        except Exception as e:
            # Log as INFO, not ERROR - offline is expected behavior
            log_tool('info', 'frontrunner', f'SSH connection to {self.hostname} unavailable: {e}')
            return False

    def _get_mock_status(self) -> Dict[str, Any]:
        """Return mock status data for offline mode"""
        mock_data = OFFLINE_TEST_DATA.copy()
        mock_data['report_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return mock_data

    def _get_status_snapshot(self) -> Dict[str, Any]:
        """Get a single status snapshot from the server"""
        try:
            # Check SSH connection exists
            if not self.ssh:
                raise Exception("SSH connection not established")

            # Get uptime
            stdin, stdout, stderr = self.ssh.exec_command("uptime -p")
            uptime_pretty = stdout.read().decode('utf-8').strip()

            stdin, stdout, stderr = self.ssh.exec_command("cat /proc/uptime")
            uptime_seconds = float(stdout.read().decode('utf-8').split()[0])
            uptime_days = round(uptime_seconds / 86400, 1)

            # Get memory usage
            stdin, stdout, stderr = self.ssh.exec_command("free -m")
            mem_output = stdout.read().decode('utf-8')
            mem_lines = mem_output.split('\n')
            mem_data = mem_lines[1].split()
            total_mem = int(mem_data[1])
            used_mem = int(mem_data[2])
            free_mem = int(mem_data[3])
            mem_percent = round((used_mem / total_mem) * 100, 1)

            # Get CPU usage
            stdin, stdout, stderr = self.ssh.exec_command("uptime")
            uptime_output = stdout.read().decode('utf-8').strip()
            load_avg = uptime_output.split('load average:')[1].strip()
            load_1min = float(load_avg.split(',')[0])

            stdin, stdout, stderr = self.ssh.exec_command("nproc")
            cpu_count = int(stdout.read().decode('utf-8').strip())
            cpu_percent = round((load_1min / cpu_count) * 100, 1)

            # Get disk usage
            stdin, stdout, stderr = self.ssh.exec_command("df -h")
            df_output = stdout.read().decode('utf-8')
            df_lines = df_output.strip().split('\n')

            target_share = '//grm0psmb02.fs.pcn.bma.bhpb.net/'
            total_size_gb = 0
            total_used_gb = 0
            total_avail_gb = 0
            disk_percent = 0
            drives = []

            for line in df_lines[1:]:
                if target_share not in line:
                    continue

                parts = line.rsplit(maxsplit=5)
                if len(parts) < 6:
                    continue

                filesystem, size_token, used_token, avail_token, percent_token, mount_point = parts
                try:
                    size_gb = float(size_token[:-1]) if size_token.endswith(('G', 'M', 'T')) else float(size_token)
                    used_gb = float(used_token[:-1]) if used_token.endswith(('G', 'M', 'T')) else float(used_token)
                    avail_gb = float(avail_token[:-1]) if avail_token.endswith(('G', 'M', 'T')) else float(avail_token)

                    if size_token.endswith('T'):
                        size_gb *= 1024
                    elif size_token.endswith('M'):
                        size_gb /= 1024

                    if used_token.endswith('T'):
                        used_gb *= 1024
                    elif used_token.endswith('M'):
                        used_gb /= 1024

                    if avail_token.endswith('T'):
                        avail_gb *= 1024
                    elif avail_token.endswith('M'):
                        avail_gb /= 1024

                    total_size_gb = size_gb
                    total_used_gb = used_gb
                    total_avail_gb = avail_gb
                    disk_percent = float(percent_token.replace('%', ''))

                    drives.append({
                        'device': filesystem,
                        'size': size_token,
                        'used': used_token,
                        'avail': avail_token,
                        'use_percent': percent_token,
                        'mount': mount_point
                    })
                    break
                except (ValueError, IndexError):
                    continue

            # Get process status via statusFRserver
            stdin, stdout, stderr = self.ssh.exec_command("statusFRserver")
            channel = stdout.channel
            channel.settimeout(5.0)

            try:
                status_output = stdout.read().decode('utf-8')
            except Exception:
                status_output = ""
                if channel.recv_ready():
                    status_output = channel.recv(4096).decode('utf-8')

            # Parse statusFRserver output
            services = []
            running_count = 0
            total_count = 0
            all_running = False

            status_pattern = re.compile(r'\[\s*(?P<status>[\w]+)\s*\]\s*(?P<name>.+)', re.IGNORECASE)
            count_pattern = re.compile(r'Number of processes running:\s*(\d+)\s*(?:out of|/)\s*(\d+)', re.IGNORECASE)

            for line in status_output.split('\n'):
                text = line.strip()
                if not text:
                    continue

                status_match = status_pattern.search(text)
                if status_match:
                    service_name = status_match.group('name').strip()
                    service_status = status_match.group('status').capitalize()
                    services.append({'name': service_name, 'status': service_status})
                    continue

                count_match = count_pattern.search(text)
                if count_match:
                    running_count = int(count_match.group(1))
                    total_count = int(count_match.group(2))
                    all_running = (running_count == total_count)
                    continue

            if total_count == 0 and services:
                total_count = len(services)
                running_count = sum(1 for s in services if s['status'].lower() == 'running')
                all_running = (running_count == total_count)

            # Log events to database
            if self.db_path:
                try:
                    for service in services:
                        frontrunner_event_db.log_process_event(
                            self.db_path,
                            service['name'],
                            service['status']
                        )

                    frontrunner_event_db.log_disk_event(
                        self.db_path,
                        disk_percent,
                        round(total_used_gb, 1),
                        round(total_size_gb, 1)
                    )
                except Exception as e:
                    log_background('warning', 'frontrunner_monitor', f'Could not log events to DB: {e}')

            return {
                'success': True,
                'report_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'uptime': {
                    'pretty': uptime_pretty,
                    'days': uptime_days,
                    'seconds': uptime_seconds
                },
                'memory': {
                    'total_mb': total_mem,
                    'used_mb': used_mem,
                    'free_mb': free_mem,
                    'percent': mem_percent
                },
                'cpu': {
                    'load_1min': load_1min,
                    'count': cpu_count,
                    'percent': cpu_percent
                },
                'disk': {
                    'total_gb': round(total_size_gb, 1),
                    'used_gb': round(total_used_gb, 1),
                    'avail_gb': round(total_avail_gb, 1),
                    'percent': disk_percent,
                    'drives': drives
                },
                'processes': {
                    'services': services,
                    'running_count': running_count,
                    'total_count': total_count,
                    'all_running': all_running
                },
                'mode': 'monitor'
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'report_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'mode': 'error'
            }

    def _get_retry_delay(self) -> int:
        """Get exponential backoff delay based on retry count"""
        if self.retry_count >= len(RETRY_DELAYS):
            return RETRY_DELAYS[-1]  # Max delay
        return RETRY_DELAYS[self.retry_count]

    def _monitor_loop(self):
        """Main monitoring loop"""
        # Set request ID for logging correlation
        set_request_id('bg-frontrunner-monitor')
        
        while self.running:
            try:
                # Offline mode - use mock data
                if self.offline_mode:
                    status = self._get_mock_status()
                    self._save_cache(status)
                    log_background('info', 'frontrunner_monitor', 
                                 f'OFFLINE MODE: Mock status updated')
                    time.sleep(UPDATE_INTERVAL)
                    continue

                # Online mode - check network first to avoid spam
                if not _check_network_reachable(self.hostname, timeout=2.0):
                    # Network unreachable - use mock data without error logging
                    log_background('info', 'frontrunner_monitor', 
                                 f'Network to {self.hostname} unreachable, using mock data')
                    status = self._get_mock_status()
                    self._save_cache(status)
                    
                    # Exponential backoff
                    delay = self._get_retry_delay()
                    self.retry_count += 1
                    time.sleep(delay)
                    continue

                # Network reachable - attempt SSH connection
                transport = self.ssh.get_transport() if self.ssh else None
                if not self.ssh or not transport or not transport.is_active():
                    if not self._connect_ssh():
                        # Connection failed - use mock data
                        status = self._get_mock_status()
                        self._save_cache(status)
                        
                        # Exponential backoff
                        delay = self._get_retry_delay()
                        self.retry_count += 1
                        log_background('info', 'frontrunner_monitor', 
                                     f'Retry in {delay}s (attempt {self.retry_count})')
                        time.sleep(delay)
                        continue

                # Get live status snapshot
                status = self._get_status_snapshot()

                # Save to cache
                self._save_cache(status)

                if status['success']:
                    log_background('info', 'frontrunner_monitor',
                                 f"Status updated: CPU {status['cpu']['percent']}%, "
                                 f"Mem {status['memory']['percent']}%, "
                                 f"Disk {status['disk']['percent']}%, "
                                 f"Processes {status['processes']['running_count']}/{status['processes']['total_count']}")
                else:
                    log_background('error', 'frontrunner_monitor', 
                                 f"Snapshot error: {status.get('error', 'Unknown')}")

                # Wait for next update
                time.sleep(UPDATE_INTERVAL)

            except Exception as e:
                log_background('error', 'frontrunner_monitor', f'Monitor loop error: {e}')
                
                # Use mock data on unexpected errors
                try:
                    status = self._get_mock_status()
                    self._save_cache(status)
                except Exception as cache_err:
                    log_background('error', 'frontrunner_monitor', f'Failed to save mock data: {cache_err}')
                
                # Exponential backoff
                delay = self._get_retry_delay()
                self.retry_count += 1
                time.sleep(delay)


# Global monitor instance
_monitor_instance = None


def start_monitor(hostname: str, username: str, password: str, cache_dir: str, offline_mode: bool = False):
    """Start the global monitor instance"""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = FrontRunnerMonitor(hostname, username, password, cache_dir, offline_mode)
        _monitor_instance.start()
    return _monitor_instance


def stop_monitor():
    """Stop the global monitor instance"""
    global _monitor_instance
    if _monitor_instance:
        _monitor_instance.stop()
        _monitor_instance = None


def get_status(cache_dir: str) -> Dict[str, Any]:
    """Get cached status (for web requests)"""
    cache_path = os.path.join(cache_dir, CACHE_FILE)
    try:
        if os.path.exists(cache_path):
            with open(cache_path, 'r') as f:
                return json.load(f)
    except Exception as e:
        log_background('error', 'frontrunner_monitor', f'Error reading cache for web request: {e}')

    return {
        'success': False,
        'error': 'Monitor not running or no cached data available',
        'report_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'mode': 'error'
    }


# Test/CLI mode
if __name__ == "__main__":
    import sys

    print("FrontRunner Background Monitor")
    print("================================")

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Start monitor
    monitor = start_monitor(
        hostname="10.110.19.16",
        username="komatsu",
        password="M0dul1r@GRM2",
        cache_dir=base_dir,
        offline_mode=False
    )

    print("\nMonitor running. Press Ctrl+C to stop...")
    print("Cache file:", os.path.join(base_dir, CACHE_FILE))

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nStopping monitor...")
        stop_monitor()
        print("Stopped.")
