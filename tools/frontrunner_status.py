import paramiko
import os
import re
from datetime import datetime
from typing import Optional, Dict, Any
from . import frontrunner_event_db

def run(password: Optional[str] = None, offline_mode: bool = False, enable_logging: bool = True) -> Dict[str, Any]:
    """
    Get FrontRunner server status (uptime, memory, CPU, disk)
    Server: 10.110.19.16, User: komatsu, PW: M0dul1r@GRM2

    Args:
        password: Server password (optional)
        offline_mode: If True, return test data instead of connecting to server
        enable_logging: If True, log critical events to database
    """
    # Initialize database for event logging
    db_path = None
    if enable_logging:
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = frontrunner_event_db.get_database_path(base_dir)
            frontrunner_event_db.init_database(db_path)
        except Exception as e:
            print(f"Warning: Could not initialize event database: {e}")
            db_path = None

    try:
        # Offline test mode - return simulated data
        if offline_mode:
            print("OFFLINE MODE: Using test data...")
            return {
                'success': True,
                'report_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
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

        # Live mode - connect to actual server
        hostname = "10.110.19.16"
        username = "komatsu"

        print(f"Connecting to FrontRunner server {hostname}...")

        # Create SSH client
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Connect to server
        ssh.connect(
            hostname=hostname,
            username=username,
            password=password,
            timeout=30
        )

        print("SSH connection established, gathering system info...")

        # Get uptime
        stdin, stdout, stderr = ssh.exec_command("uptime -p")
        uptime_pretty = stdout.read().decode('utf-8').strip()

        # Get uptime in seconds for calculation
        stdin, stdout, stderr = ssh.exec_command("cat /proc/uptime")
        uptime_seconds = float(stdout.read().decode('utf-8').split()[0])
        uptime_days = round(uptime_seconds / 86400, 1)

        # Get memory usage
        stdin, stdout, stderr = ssh.exec_command("free -m")
        mem_output = stdout.read().decode('utf-8')
        mem_lines = mem_output.split('\n')

        # Parse memory (second line is Mem:)
        mem_data = mem_lines[1].split()
        total_mem = int(mem_data[1])
        used_mem = int(mem_data[2])
        free_mem = int(mem_data[3])
        mem_percent = round((used_mem / total_mem) * 100, 1)

        # Get CPU usage (1 minute average from uptime)
        stdin, stdout, stderr = ssh.exec_command("uptime")
        uptime_output = stdout.read().decode('utf-8').strip()
        # Extract load average (last 3 numbers)
        load_avg = uptime_output.split('load average:')[1].strip()
        load_1min = float(load_avg.split(',')[0])

        # Get CPU count to calculate percentage
        stdin, stdout, stderr = ssh.exec_command("nproc")
        cpu_count = int(stdout.read().decode('utf-8').strip())
        cpu_percent = round((load_1min / cpu_count) * 100, 1)

        # Get disk usage (df -h) - only report the network share
        stdin, stdout, stderr = ssh.exec_command("df -h")
        df_output = stdout.read().decode('utf-8')
        df_lines = df_output.strip().split('\n')

        # Look for the specific network share: //grm0psmb02.fs.pcn.bma.bhpb.net/
        target_share = '//grm0psmb02.fs.pcn.bma.bhpb.net/'
        total_size_gb = 0
        total_used_gb = 0
        total_avail_gb = 0
        disk_percent = 0
        drives = []

        for line in df_lines[1:]:  # Skip header
            if target_share not in line:
                continue

            # Keep the mount path intact even if the filesystem contains spaces
            parts = line.rsplit(maxsplit=5)
            if len(parts) < 6:
                continue

            filesystem, size_token, used_token, avail_token, percent_token, mount_point = parts
            try:
                size_gb = float(size_token[:-1]) if size_token.endswith(('G', 'M', 'T')) else float(size_token)
                used_gb = float(used_token[:-1]) if used_token.endswith(('G', 'M', 'T')) else float(used_token)
                avail_gb = float(avail_token[:-1]) if avail_token.endswith(('G', 'M', 'T')) else float(avail_token)

                # Normalize to GB when units are not already gigabytes
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

        # Get process status via statusFRserver command
        stdin, stdout, stderr = ssh.exec_command("statusFRserver")
        status_output = stdout.read().decode('utf-8')

        # Parse statusFRserver output using more resilient patterns
        services = []
        running_count = 0
        total_count = 0
        all_running = False

        status_pattern = re.compile(r'\[\s*(?P<status>[\w]+)\s*\]\s*(?P<name>.+)', re.IGNORECASE)
        # Allow both "out of" and "/" formats for the process summary line
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

        ssh.close()

        # Log events to database if enabled
        if db_path:
            try:
                # Log process events (stopped services)
                for service in services:
                    frontrunner_event_db.log_process_event(
                        db_path,
                        service['name'],
                        service['status']
                    )

                # Log disk events if over 90%
                frontrunner_event_db.log_disk_event(
                    db_path,
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
            'mode': 'live'
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'report_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'mode': 'error'
        }

# Test function
if __name__ == "__main__":
    print("Testing FrontRunner Status...")
    print("\n=== OFFLINE TEST MODE ===")
    result = run(offline_mode=True)

    if result['success']:
        print(f"Success!")
        print(f"Uptime: {result['uptime']['pretty']} ({result['uptime']['days']} days)")
        print(f"Memory: {result['memory']['used_mb']}MB / {result['memory']['total_mb']}MB ({result['memory']['percent']}%)")
        print(f"CPU: {result['cpu']['percent']}% (Load: {result['cpu']['load_1min']})")
        print(f"Disk: {result['disk']['used_gb']}GB / {result['disk']['total_gb']}GB ({result['disk']['percent']}%)")
        print(f"\nProcesses: {result['processes']['running_count']} / {result['processes']['total_count']}")
        for service in result['processes']['services']:
            print(f"  - {service['name']}: {service['status']}")
    else:
        print(f"Error: {result['error']}")

    print("\n=== LIVE TEST MODE ===")
    result = run(password="M0dul1r@GRM2")

    if result['success']:
        print(f"Success!")
        print(f"Uptime: {result['uptime']['pretty']} ({result['uptime']['days']} days)")
        print(f"Memory: {result['memory']['used_mb']}MB / {result['memory']['total_mb']}MB ({result['memory']['percent']}%)")
        print(f"CPU: {result['cpu']['percent']}% (Load: {result['cpu']['load_1min']})")
        print(f"Disk: {result['disk']['used_gb']}GB / {result['disk']['total_gb']}GB ({result['disk']['percent']}%)")
        print(f"\nProcesses: {result['processes']['running_count']} / {result['processes']['total_count']}")
        for service in result['processes']['services']:
            print(f"  - {service['name']}: {service['status']}")
    else:
        print(f"Error: {result['error']}")
