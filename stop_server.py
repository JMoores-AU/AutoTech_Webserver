"""Stop Flask server running on a given port."""
import socket
import subprocess
import sys
import time

port = int(sys.argv[1]) if len(sys.argv) > 1 else 8889

# Use netstat to find PID on the port
try:
    result = subprocess.run(
        ['powershell', '-Command',
         f"Get-NetTCPConnection -LocalPort {port} -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess"],
        capture_output=True, text=True, timeout=10
    )
    pids = [p.strip() for p in result.stdout.strip().split('\n') if p.strip()]
    for pid in pids:
        subprocess.run(['powershell', '-Command', f'Stop-Process -Id {pid} -Force -ErrorAction SilentlyContinue'],
                       capture_output=True, timeout=10)
    time.sleep(2)
except Exception as e:
    sys.stderr.write(f"Error: {e}\n")

# Verify server is stopped
try:
    s = socket.create_connection(('127.0.0.1', port), timeout=2)
    s.close()
    sys.stderr.write(f"WARNING: Port {port} still in use\n")
    sys.exit(1)
except (ConnectionRefusedError, OSError):
    sys.exit(0)
