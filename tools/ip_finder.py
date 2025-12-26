# tools/ip_finder.py
from typing import Optional, Dict
import re, shlex, paramiko

# --- LIVE CONFIG ---
GATEWAY_HOST = "10.110.19.107"
GATEWAY_USER = "mms"
REMOTE_CMD   = "/home/mms/bin/remote_check/Random/MySQL/ip_export.sh"
# -------------------

DUMMY_OUTPUT = """
+-------+----------+----------+---------------+
| _OID_ | _CID_    | _profile | network_ip    |
+-------+----------+----------+---------------+
| RD190 | eqmt_aht | K830E    | 10.110.20.196 |
+-------+----------+----------+---------------+

PTX IP is: 10.110.20.196
Vehicle is Online.

PTXC Found.

AVI IP is : 10.111.219.117
"""

def _live_call(query: str, password: str, timeout: int = 30) -> str:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(GATEWAY_HOST, username=GATEWAY_USER, password=password, timeout=10)
    cmd = f"{REMOTE_CMD} {shlex.quote(query)}"
    stdin, stdout, stderr = ssh.exec_command(cmd, get_pty=True, timeout=timeout)
    rc  = stdout.channel.recv_exit_status()
    out = stdout.read().decode(errors="ignore")
    err = stderr.read().decode(errors="ignore")
    ssh.close()
    if rc != 0:
        raise RuntimeError(f"IP_Finder remote rc={rc}: {err or out}")
    if not out.strip():
        raise RuntimeError("IP_Finder returned no output")
    return out

def run(equipment_or_ip: Optional[str] = None,
        password: Optional[str] = None,
        offline_mode: bool = True) -> str:
    if offline_mode:
        return DUMMY_OUTPUT
    if not password:
        raise ValueError("IP_Finder: password is required for live mode")
    return _live_call(equipment_or_ip or "", password)

def _parse_table_line(line: str):
    # Matches a data row like: | RD190 | eqmt_aht | K830E | 10.110.20.196 |
    m = re.match(r"\|\s*([^\|]+)\|\s*([^\|]+)\|\s*([^\|]+)\|\s*([^\|]+)\|", line)
    if m and not m.group(1).strip().startswith('_'):
        return [g.strip() for g in m.groups()]
    return None

def parse_ip_finder_output(raw: str) -> Dict[str, object]:
    result: Dict[str, object] = {}
    # 1) Table row
    for line in raw.splitlines():
        row = _parse_table_line(line)
        if row:
            result['OID'], result['CID'], result['profile'], result['network_ip'] = row
            break
    # 2) Summary lines
    for line in raw.splitlines():
        if "PTX IP is" in line:
            result['ptx_ip'] = line.split("PTX IP is:")[1].strip()
        elif "AVI IP is" in line:
            result['avi_ip'] = line.split("AVI IP is :")[1].strip()
        elif "Vehicle is" in line:
            result['vehicle_status'] = line.split("Vehicle is")[1].strip().rstrip(".")
        elif "PTXC Found" in line:
            result['ptxc_found'] = True

    # 3) PTX model inference
    result['ptxc_found'] = bool(result.get('ptxc_found', False))
    result['ptx_model']  = "PTXC" if result['ptxc_found'] else "PTX10"
    return result

import os, subprocess, socket, time

# --- local tools (adjust if needed) ---
PLINK = r"C:\Komatsu_Tier1\T1_Tools\tools\plink.exe"
VNC   = r"C:\Komatsu_Tier1\T1_Tools\tools\VNC\vncviewer.exe"
# --------------------------------------

def _free_local_port(start=5901, end=5999):
    for p in range(start, end+1):
        with socket.socket() as s:
            try:
                s.bind(("", p))
                return p
            except OSError:
                continue
    raise RuntimeError("No free local port for VNC tunnel")

def ip_finder_to_vnc(query: str, gateway_password: str, offline_mode: bool) -> Dict[str, object]:
    raw = run(query, gateway_password, offline_mode=offline_mode)
    info = parse_ip_finder_output(raw)

    ptx_ip   = info.get("ptx_ip") or info.get("network_ip")
    model    = info.get("ptx_model", "PTX10")
    if not ptx_ip:
        raise RuntimeError("Couldn’t determine PTX IP from IP_Finder output")

    # Pick creds based on model
    if str(model).upper() == "PTXC":
        ssh_user, ssh_pass = "dlog", "gold"
    else:
        ssh_user, ssh_pass = "mms", "modular"

    # Pick a local port and build tunnel
    lport = _free_local_port()
    tunnel_cmd = [
        PLINK, "-v", "-ssh",
        "-l", ssh_user, "-pw", ssh_pass,
        "-L", f"{lport}:localhost:5900",
        ptx_ip, "-batch", "vncserver && sleep 10"
    ]

    # Start SSH tunnel (detached)
    subprocess.Popen(tunnel_cmd, creationflags=subprocess.DETACHED_PROCESS if os.name == "nt" else 0)

    # small wait so the port is ready
    time.sleep(5)

    # Launch VNC viewer
    subprocess.Popen([VNC, f"127.0.0.1:{lport}"])

    return {
        "ok": True,
        "message": f"Opening VNC to {ptx_ip} via {model} (local port {lport})",
        "ptx_ip": ptx_ip,
        "model": model,
        "local_port": lport,
    }

def get_flight_recorder_ip(ptx_ip):
    """Calculate Flight Recorder IP (PTX IP + 1) for K830E and K930E profiles"""
    if not ptx_ip:
        return None
    
    try:
        parts = ptx_ip.split('.')
        if len(parts) != 4:
            return None
        
        # Increment the last octet by 1
        last_octet = int(parts[3]) + 1
        if last_octet > 255:  # Handle overflow
            return None
            
        return f"{parts[0]}.{parts[1]}.{parts[2]}.{last_octet}"
    except (ValueError, IndexError):
        return None
    
def check_avi_status(avi_ip, timeout=10):
    """
    Check AVI status by SSH connection and internal network pings
    """
    if not avi_ip:
        return {
            "status": "Disconnected", 
            "response_time": None,
            "internal_devices": {},
            "overall_health": "Unknown"
        }
    
    start_time = time.time()
    ssh_client = None
    
    try:
        # Create SSH client
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Connect to AVI
        ssh_client.connect(
            hostname=avi_ip,
            port=22,
            username='root',
            password='root',
            timeout=timeout,
            auth_timeout=timeout
        )
        
        response_time = round((time.time() - start_time) * 1000, 1)
        
        # Define internal devices to ping
        internal_devices = {
            "ptx": {"ip": "192.168.0.100", "name": "PTX"},
            "gnss_1": {"ip": "192.168.0.101", "name": "MM2 GNSS_1"},
            "gnss_2": {"ip": "192.168.0.102", "name": "MM2 GNSS_2"}
        }
        
        device_results = {}
        
        # Ping each internal device from AVI
        for device_key, device_info in internal_devices.items():
            device_ip = device_info["ip"]
            device_name = device_info["name"]
            
            try:
                # Execute ping command (1 ping, 2 second timeout)
                ping_cmd = f"ping -c 1 -W 2 {device_ip}"
                stdin, stdout, stderr = ssh_client.exec_command(ping_cmd)
                
                ping_output = stdout.read().decode('utf-8')
                
                # Parse ping results
                if "1 packets transmitted, 1 received" in ping_output or "1 received" in ping_output:
                    # Extract ping time using regex
                    time_match = re.search(r'time=(\d+\.?\d*)\s*ms', ping_output)
                    ping_time = float(time_match.group(1)) if time_match else None
                    
                    device_results[device_key] = {
                        "ip": device_ip,
                        "name": device_name,
                        "status": "Online",
                        "ping_time": ping_time
                    }
                else:
                    device_results[device_key] = {
                        "ip": device_ip,
                        "name": device_name, 
                        "status": "Offline",
                        "ping_time": None
                    }
                    
            except Exception:
                # Individual device ping failed - mark as Error but continue
                device_results[device_key] = {
                    "ip": device_ip,
                    "name": device_name,
                    "status": "Error",
                    "ping_time": None
                }
        
        # Close SSH connection
        if ssh_client:
            ssh_client.close()
        
        # Calculate overall health
        online_count = sum(1 for device in device_results.values() if device["status"] == "Online")
        total_count = len(device_results)
        
        if online_count == total_count:
            overall_health = "Healthy"
        elif online_count >= total_count / 2:
            overall_health = "Degraded" 
        elif online_count > 0:
            overall_health = "Critical"
        else:
            overall_health = "Critical"
        
        # SSH connection succeeded - return Connected even if some pings failed
        return {
            "status": "Connected",
            "response_time": response_time,
            "internal_devices": device_results,
            "overall_health": overall_health
        }
        
    except paramiko.AuthenticationException:
        if ssh_client:
            ssh_client.close()
        return {
            "status": "Auth Error",
            "response_time": None,
            "internal_devices": {},
            "overall_health": "Unknown"
        }
    except paramiko.SSHException:
        if ssh_client:
            ssh_client.close()
        return {
            "status": "SSH Error", 
            "response_time": None,
            "internal_devices": {},
            "overall_health": "Unknown"
        }
    except socket.timeout:
        if ssh_client:
            ssh_client.close()
        return {
            "status": "Timeout",
            "response_time": None,
            "internal_devices": {},
            "overall_health": "Unknown"
        }
    except Exception as e:
        if ssh_client:
            ssh_client.close()
        print(f"[AVI_STATUS] Unexpected error: {e}")
        return {
            "status": "Error",
            "response_time": None,
            "internal_devices": {},
            "overall_health": "Unknown"
        }

def get_avi_credentials():
    """
    Return AVI SSH credentials - customize based on your setup
    Could read from config file, environment variables, etc.
    """
    return {
        "username": "root",  # or your AVI username
        "password": "root"  # or your AVI password
    }
