# tools/speed_limit_data.py
"""
Live Speed Limit Data Check (LASL Report)
Based on actual output from mms_scripts_outputs.txt
"""

import paramiko
import os
from datetime import datetime
from pathlib import Path

GATEWAY_HOST = "10.110.19.107"
GATEWAY_USER = "mms"
SPEED_LIMIT_SCRIPT = "/home/mms/bin/remote_check/Random/MySQL/LASL_export.sh"

def log_activity():
    """Log script activity exactly like the original batch script"""
    try:
        current_date = datetime.now().strftime("%Y-%m-%d")
        current_time = datetime.now().strftime("%H:%M")
        computer_name = os.getenv("COMPUTERNAME", "PythonWebApp")
        username = os.getenv("USERNAME", "WebUser")
        
        log_entry = f"Date: {current_date} {current_time}, Computer Name: {computer_name}, Username: {username} - Ran Speed Limit data check script.\n"
        
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
    """Run Speed Limit Data Check"""
    if offline_mode:
        return f"""SpeedLimit Data at {datetime.now().strftime('%a %m/%d/%Y %H:%M:%S.%f')[:-4]}

+---------------------+---------------------+---------------------+---------+----------+-----------------+
| Area_Type           | Created_Date        | LastCheck_Date      | X       | Y        | SpeedLimit_kmhr |
+---------------------+---------------------+---------------------+---------+----------+-----------------+
| LocalSpeedLimitArea | 2024-11-26 06:50:38 | 2025-08-10 22:49:06 | -494111 |  6014143 |              12 |
| LocalSpeedLimitArea | 2025-04-01 10:47:55 | 2025-08-10 22:49:06 | -485226 |  5467097 |              12 |
| LocalSpeedLimitArea | 2025-04-01 10:48:43 | 2025-08-10 22:49:06 | -327520 |  4067689 |              12 |
| LocalSpeedLimitArea | 2025-05-05 19:44:53 | 2025-08-10 22:49:06 | 2172645 |  8281664 |              12 |
| LocalSpeedLimitArea | 2025-05-11 11:21:17 | 2025-08-10 22:49:06 |  -67507 |  3440080 |              12 |
| LocalSpeedLimitArea | 2025-06-10 07:18:38 | 2025-08-10 22:49:06 | 1031907 |  8375143 |              13 |
| LocalSpeedLimitArea | 2025-06-10 07:21:02 | 2025-08-10 22:49:06 |  491159 |  7811410 |              12 |
| LocalSpeedLimitArea | 2025-07-02 06:30:25 | 2025-08-10 22:49:06 | 2266384 | 11628496 |              20 |
| LocalSpeedLimitArea | 2025-07-14 01:18:06 | 2025-08-10 22:49:06 | 2441515 |  9963964 |              20 |
| LocalSpeedLimitArea | 2025-07-21 18:49:34 | 2025-08-10 22:49:06 |  390006 | 11211182 |              12 |
| LocalSpeedLimitArea | 2025-07-22 10:05:03 | 2025-08-10 22:49:06 | 2490603 |  6704420 |              50 |
| LocalSpeedLimitArea | 2025-07-22 10:06:48 | 2025-08-10 22:49:06 | 1636713 |  7483947 |              50 |
| LocalSpeedLimitArea | 2025-07-22 10:09:27 | 2025-08-10 22:49:06 | 2108575 | 10032292 |              20 |
| LocalSpeedLimitArea | 2025-07-22 10:12:22 | 2025-08-10 22:49:06 | 3029410 | 10084644 |              20 |
| LocalSpeedLimitArea | 2025-07-22 10:21:05 | 2025-08-10 22:49:06 | -530853 |  9093082 |              20 |
| LocalSpeedLimitArea | 2025-08-10 22:15:16 | 2025-08-10 22:49:06 |  -13944 | 11006204 |              20 |
+---------------------+---------------------+---------------------+---------+----------+-----------------+

+------------------+
| Total_SpeedLimit |
+------------------+
|              104 |
+------------------+

SPEED LIMIT SUMMARY:
• Total Speed Limit Areas: 104
• Speed Ranges: 12-50 km/h
• Most Recent Update: {datetime.now().strftime('%Y-%m-%d %H:%M')}
• Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Note: This is demonstration data showing typical speed limit area data."""

    if not password:
        return "Error: Password required for live speed limit data check"

    try:
        log_activity()
        
        result = f"""SpeedLimit Data at {datetime.now().strftime('%a %m/%d/%Y %H:%M:%S.%f')[:-4]}

Connected to: {GATEWAY_HOST}
Retrieving speed limit data...

"""
        
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(GATEWAY_HOST, username=GATEWAY_USER, password=password, timeout=10)
        
        # Execute the speed limit data export script
        stdin, stdout, stderr = ssh.exec_command(SPEED_LIMIT_SCRIPT, get_pty=True)
        
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
            
            # Extract total count if available
            total_line = [line for line in output_lines if "Total_SpeedLimit" in line or line.strip().isdigit()]
            if total_line:
                result += f"\n\nSPEED LIMIT SUMMARY:"
                result += f"\n• Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                result += f"\n• Data retrieved from live database"
        else:
            result += "No speed limit data available or script returned no output."
            
        if error_output:
            result += f"\n\nERRORS:\n{error_output}"
            
        return result
        
    except Exception as e:
        return f"Error retrieving speed limit data: {str(e)}"