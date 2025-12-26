# tools/koa_data_check.py
"""
Live KOA Data Check
Based on actual output from mms_scripts_outputs.txt
"""

import paramiko
import os
from datetime import datetime
from pathlib import Path

GATEWAY_HOST = "10.110.19.107"
GATEWAY_USER = "mms"
KOA_DATA_SCRIPT = "/home/mms/bin/remote_check/Random/MySQL/table_export.sh"

def log_activity():
    """Log script activity exactly like the original batch script"""
    try:
        current_date = datetime.now().strftime("%Y-%m-%d")
        current_time = datetime.now().strftime("%H:%M")
        computer_name = os.getenv("COMPUTERNAME", "PythonWebApp")
        username = os.getenv("USERNAME", "WebUser")
        
        log_entry = f"Date: {current_date} {current_time}, Computer Name: {computer_name}, Username: {username} - Ran Live KOA Data script.\n"
        
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
    """Run KOA Data Check"""
    if offline_mode:
        return f"""KOA Data at {datetime.now().strftime('%a %m/%d/%Y %H:%M:%S.%f')[:-4]}

+---------------+----------+---------+---------+------+-------+----------------------------+--------------------------+
| TravelID      | Location | FromLoc | ToLoc   | Open | Close | Created                    | LastUpdated              |
+---------------+----------+---------+---------+------+-------+----------------------------+--------------------------+
| 1754188419891 | NULL     | INT_42  | INT_78  |    1 |     0 | 2025-08-03 12:33:39.891000 | 2025-08-08 09:47:34.9510 |
| 1754305539442 | INT_43   | NULL    | NULL    |    1 |     0 | 2025-08-04 21:05:39.442000 | 2025-08-09 15:40:28.2730 |
| 1754557026850 | NULL     | INT_121 | INT_22  |    1 |     0 | 2025-08-07 18:57:06.850000 | 2025-08-08 09:47:35.1020 |
| 1754557026934 | NULL     | INT_121 | INT_22  |    1 |     0 | 2025-08-07 18:57:06.934000 | 2025-08-08 09:47:35.1670 |
| 1754560827084 | NULL     | INT_42  | INT_156 |    1 |     0 | 2025-08-07 20:00:27.084000 | 2025-08-08 09:47:35.2360 |
| 1754712687635 | INT_67   | NULL    | NULL    |    1 |     0 | 2025-08-09 14:11:27.635000 | 2025-08-09 21:17:29.0330 |
| 1754712709174 | NULL     | INT_106 | R23_01  |    1 |     0 | 2025-08-09 14:11:49.174000 | 2025-08-09 14:26:04.7050 |
| 1754722607483 | NULL     | R25_01  | INT_41  |    1 |     0 | 2025-08-09 16:56:47.483000 | 2025-08-09 23:06:24.0710 |
| 1754776668804 | NULL     | R12_11  | INT_49  |    1 |     0 | 2025-08-10 07:57:48.804000 | 2025-08-10 07:57:48.8420 |
| 1754776833651 | NULL     | INT_78  | INT_42  |    1 |     0 | 2025-08-10 08:00:33.651000 | 2025-08-10 08:31:28.9310 |
| 1754785311586 | NULL     | INT_34  | INT_126 |    1 |     0 | 2025-08-10 10:21:51.586000 | 2025-08-10 10:45:59.0380 |
| 1754790076807 | NULL     | R12_04  | INT_49  |    1 |     0 | 2025-08-10 11:41:16.807000 | 2025-08-10 11:54:50.8590 |
| 1754796136930 | NULL     | INT_136 | INT_124 |    1 |     0 | 2025-08-10 13:22:16.930000 | 2025-08-10 13:22:16.9570 |
+---------------+----------+---------+---------+------+-------+----------------------------+--------------------------+

TRAVEL DATA SUMMARY:
• Active Travel Records: 13
• Open Travels: 13
• Closed Travels: 0
• Latest Activity: {datetime.now().strftime('%Y-%m-%d %H:%M')}

Note: This is demonstration data showing typical KOA travel records."""

    if not password:
        return "Error: Password required for live KOA data check"

    try:
        log_activity()
        
        result = f"""KOA Data at {datetime.now().strftime('%a %m/%d/%Y %H:%M:%S.%f')[:-4]}

Connected to: {GATEWAY_HOST}
Retrieving KOA data...

"""
        
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(GATEWAY_HOST, username=GATEWAY_USER, password=password, timeout=10)
        
        # Execute the KOA data export script
        stdin, stdout, stderr = ssh.exec_command(KOA_DATA_SCRIPT, get_pty=True)
        
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
            
            # Add summary information
            travel_count = len([line for line in output_lines if line.startswith('| 17')])  # Travel IDs start with 17
            result += f"\n\nKOA DATA SUMMARY:"
            result += f"\n• Travel Records Retrieved: {travel_count}"
            result += f"\n• Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        else:
            result += "No KOA data available or script returned no output."
            
        if error_output:
            result += f"\n\nERRORS:\n{error_output}"
            
        return result
        
    except Exception as e:
        return f"Error retrieving KOA data: {str(e)}"