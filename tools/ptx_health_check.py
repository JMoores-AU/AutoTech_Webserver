# tools/ptx_health_check.py
"""
PTX Health Check - Welcome Embedded Health Check
Based on actual output from mms_scripts_outputs.txt
"""

import paramiko
import os
from datetime import datetime
from pathlib import Path

GATEWAY_HOST = "10.110.19.107"
GATEWAY_USER = "mms"
HEALTH_CHECK_SCRIPT = "/home/mms/bin/remote_check/ping_check/HealthCheck/Check_Exe.sh"

def log_activity():
    """Log script activity exactly like the original batch script"""
    try:
        current_date = datetime.now().strftime("%Y-%m-%d")
        current_time = datetime.now().strftime("%H:%M")
        computer_name = os.getenv("COMPUTERNAME", "PythonWebApp")
        username = os.getenv("USERNAME", "WebUser")
        
        log_entry = f"Date: {current_date} {current_time}, Computer Name: {computer_name}, Username: {username} - Ran PTX Health Check script.\n"
        
        # Try to write to local log
        log_dir = Path("C:/Komatsu_Tier1/T1_Tools/logs")
        if log_dir.exists():
            log_file = log_dir / "scripts_logfile.txt"
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(log_entry)
                
            # Copy to network location
            network_path = Path("//10.110.19.105/c$/Master_T1_Tools/logs")
            if network_path.exists():
                network_log = network_path / "scripts_logfile.txt"
                with open(network_log, "a", encoding="utf-8") as f:
                    f.write(log_entry)
    except Exception:
        pass

def run(password=None, offline_mode=True):
    """Run PTX Health Check"""
    if offline_mode:
        return f"""Welcome Embedded Health Check

Enter PTX IP: 10.110.21.128
PTX IP is 10.110.21.128. Please confirm [Y/N]? y

Warning: Permanently added '10.110.21.128' (ECDSA) to the list of known hosts.
------------------------------------------------------------------------------------

{datetime.now().strftime('%a %b %d %H:%M:%S AEST %Y')}:
Health Check in Progress (IP : 10.110.21.128)... Please wait...

PTXC Found...

Equipment ID: TRD489
Number of Pings: 30
Ping Packet Size: 1200


**Ping Results: 10.110.21.128-> 192.168.0.100
Packet Loss: 0%
Average Latency: 0.140 ms
Standard Deviation: 0.027 ms

**Ping Results: 10.110.21.128-> 192.168.0.254
Packet Loss: 0%
Average Latency: 0.772 ms
Standard Deviation: 0.065 ms

**Ping Results: 10.110.21.128-> 10.110.19.16
Packet Loss: 0%
Average Latency: 36.069 ms
Standard Deviation: 10.529 ms

**Ping Results: 10.110.21.128-> 192.168.0.101
Packet Loss: 0%
Average Latency: 5.229 ms
Standard Deviation: 7.345 ms

**Ping Results: 10.110.21.128-> 192.168.0.102
Packet Loss: 0%
Average Latency: 8.148 ms
Standard Deviation: 30.949 ms


**Health Check Results of 10.110.21.128:
CPU Usage: 34.10%
Memory Usage: 84.79%
System Uptime: up 6 days, 12 hours, 22 minutes
Disk Usage: /dev/mmcblk0p3  5.6G  3.0G  2.4G  57% /media/realroot/home


**AVI Radio Mobile Status:
Password:
Current Time:  562918           Temperature: 38
Reset Counter: 1                Mode:        ONLINE
System mode:   LTE              PS state:    Attached
LTE band:      B1               LTE bw:      10 MHz
LTE Rx chan:   350              LTE Tx chan: 18350
LTE CA state:  NOT ASSIGNED
EMM state:     Registered       Normal Service
RRC state:     RRC Connected
IMS reg state: No Srv
PCC RxM RSSI:  -52              RSRP (dBm):  -78
PCC RxD RSSI:  -52              RSRP (dBm):  -81
Tx Power:      -1               TAC:         283C (10300)
RSRQ (dB):     -9.0             Cell ID:     00283F15 (2637589)
SINR (dB):     28.6
OK

Note: This is demonstration data showing typical PTX health check results."""

    if not password:
        return "Error: Password required for live PTX health check"

    try:
        log_activity()
        
        result = f"""Welcome Embedded Health Check

Connected to: {GATEWAY_HOST}
Timestamp: {datetime.now().strftime('%a %b %d %H:%M:%S AEST %Y')}

Executing PTX health check script...
------------------------------------------------------------------------------------

"""
        
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(GATEWAY_HOST, username=GATEWAY_USER, password=password, timeout=10)
        
        # Execute the health check script
        stdin, stdout, stderr = ssh.exec_command(HEALTH_CHECK_SCRIPT, get_pty=True)
        
        # Read output line by line
        output_lines = []
        for line in stdout:
            line = line.strip()
            if line:
                output_lines.append(line)
        
        error_output = stderr.read().decode('utf-8', errors='ignore').strip()
        ssh.close()
        
        if output_lines:
            result += "\n".join(output_lines)
        else:
            result += "No output received from PTX health check script."
            
        if error_output:
            result += f"\n\nWARNINGS/ERRORS:\n{error_output}"
            
        result += f"\n\n------------------------------------------------------------------------------------"
        result += f"\nPTX health check completed at {datetime.now().strftime('%a %b %d %H:%M:%S AEST %Y')}"
        
        return result
        
    except Exception as e:
        return f"Error executing PTX health check: {str(e)}"