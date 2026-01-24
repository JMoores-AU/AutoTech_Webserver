# tools/frontrunner_monitor.py
"""
FrontRunner Background Monitor - Maintains persistent SSH connection
Continuously monitors server status and caches results for web access
"""
import paramiko
import os
import re
import json
import time
import threading
from datetime import datetime
from typing import Optional, Dict, Any

# Handle imports for both module and standalone use
try:
    from . import frontrunner_event_db
except ImportError:
    import frontrunner_event_db

# Cache file location
CACHE_FILE = "frontrunner_status_cache.json"
UPDATE_INTERVAL = 30  # seconds between updates


class FrontRunnerMonitor:
    """Background monitor for FrontRunner server status"""

    def __init__(self, hostname: str, username: str, password: str, cache_dir: str):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.cache_path = os.path.join(cache_dir, CACHE_FILE)
        self.running = False
        self.thread = None
        self.ssh = None
        self.db_path = None

        # Initialize event database
        try:
            self.db_path = frontrunner_event_db.get_database_path(cache_dir)
            frontrunner_event_db.init_database(self.db_path)
        except Exception as e:
            print(f"Warning: Could not initialize event database: {e}")

    def start(self):
        """Start the background monitoring thread"""
        if self.running:
            print("Monitor already running")
            return

        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        print(f"FrontRunner monitor started for {self.hostname}")

    def stop(self):
        """Stop the background monitoring thread"""
        self.running = False
        if self.ssh:
            try:
                self.ssh.close()
            except:
                pass
        if self.thread:
            self.thread.join(timeout=5)
        print("FrontRunner monitor stopped")

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
            print(f"Error reading cache: {e}")
        return None

    def _save_cache(self, status: Dict[str, Any]):
        """Save status to cache file"""
        try:
            with open(self.cache_path, 'w') as f:
                json.dump(status, f, indent=2)
        except Exception as e:
            print(f"Error writing cache: {e}")

    def _connect_ssh(self) -> bool:
        """Establish SSH connection"""
        try:
            if self.ssh:
                try:
                    self.ssh.close()
                except:
                    pass

            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh.connect(
                hostname=self.hostname,
                username=self.username,
                password=self.password,
                timeout=30
            )
            print(f"SSH connected to {self.hostname}")
            return True
        except Exception as e:
            print(f"SSH connection failed: {e}")
            return False

    def _get_status_snapshot(self) -> Dict[str, Any]:
        """Get a single status snapshot from the server"""
        try:
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
                    print(f"Warning: Could not log events: {e}")

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

    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                # Connect if not connected
                if not self.ssh or not self.ssh.get_transport() or not self.ssh.get_transport().is_active():
                    if not self._connect_ssh():
                        print("Waiting 30 seconds before retry...")
                        time.sleep(30)
                        continue

                # Get status snapshot
                status = self._get_status_snapshot()

                # Save to cache
                self._save_cache(status)

                if status['success']:
                    print(f"[{status['report_time']}] Status updated: CPU {status['cpu']['percent']}%, Mem {status['memory']['percent']}%, Disk {status['disk']['percent']}%, Processes {status['processes']['running_count']}/{status['processes']['total_count']}")
                else:
                    print(f"[{status['report_time']}] Error: {status.get('error', 'Unknown')}")

                # Wait for next update
                time.sleep(UPDATE_INTERVAL)

            except Exception as e:
                print(f"Monitor loop error: {e}")
                time.sleep(30)


# Global monitor instance
_monitor_instance = None


def start_monitor(hostname: str, username: str, password: str, cache_dir: str):
    """Start the global monitor instance"""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = FrontRunnerMonitor(hostname, username, password, cache_dir)
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
        print(f"Error reading cache: {e}")

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
        cache_dir=base_dir
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
