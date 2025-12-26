# tools/avi_mm2_reboot.py
"""
AVI/MM2 Reboot - You are about to Reboot AVI Radio and MM2!!!
Based on actual output from mms_scripts_outputs.txt
"""

import paramiko
import os
from datetime import datetime
from pathlib import Path

GATEWAY_HOST = "10.110.19.107"
GATEWAY_USER = "mms"
MM2_REBOOT_SCRIPT = "/home/mms/bin/remote_check/TempTool/MM2/Check_Exe.sh"

def log_activity():
    """Log script activity exactly like the original batch script"""
    try:
        current_date = datetime.now().strftime("%Y-%m-%d")
        current_time = datetime.now().strftime("%H:%M")
        computer_name = os.getenv("COMPUTERNAME", "PythonWebApp")
        username = os.getenv("USERNAME", "WebUser")
        
        log_entry = f"Date: {current_date} {current_time}, Computer Name: {computer_name}, Username: {username} - Ran AVI/MM2 reboot script.\n"
        
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

def run(ptx_ip=None, password=None, offline_mode=True):
    """Run AVI/MM2 Reboot"""
    if offline_mode:
        return f"""You are about to Reboot AVI Radio and MM2!!!

Enter PTXC IP Address: {ptx_ip or '10.110.21.72'}

Machine is Reachable.

PTXC IP is {ptx_ip or '10.110.21.72'}
Equipment Name is AHG54. Please confirm [Y/N]? y
Warning: Permanently added '{ptx_ip or '10.110.21.72'}' (ECDSA) to the list of known hosts.

***Resetting MM2 Master & Slave - In-Progress
   Resetting MM2 Master & Slave - Done!


***Resetting AVI Radio - In-Progress
   Resetting AVI Radio - Done!

REBOOT COMPLETED SUCCESSFULLY!

Equipment should be back online within 2-3 minutes.
Monitor equipment status to confirm successful restart.

Note: This is demonstration mode - no actual reboot was performed."""

    if not password:
        return "Error: Password required for AVI/MM2 reboot"

    if not ptx_ip:
        return "Error: PTX IP address required"

    try:
        log_activity()
        
        computer_name = os.getenv("COMPUTERNAME", "PythonWebApp")
        username = os.getenv("USERNAME", "WebUser")
        
        result = f"""You are about to Reboot AVI Radio and MM2!!!

Target PTXC IP: {ptx_ip}
Initiated by: {username} from {computer_name}
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Connecting to equipment...

"""
        
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(GATEWAY_HOST, username=GATEWAY_USER, password=password, timeout=10)
        
        # Log the reboot initiation (exactly like the batch script)
        log_cmd = f'echo "$(date): Initiated from {computer_name} by {username} for {ptx_ip}." >> /home/mms/bin/remote_check/TempTool/MM2/Report.txt'
        ssh.exec_command(log_cmd)
        
        # Execute the MM2 reboot script
        command = f"{MM2_REBOOT_SCRIPT} {ptx_ip}"
        stdin, stdout, stderr = ssh.exec_command(command, get_pty=True)
        
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
            result += f"AVI/MM2 reboot command executed for {ptx_ip}."
            
        if error_output:
            result += f"\n\nWARNINGS/ERRORS:\n{error_output}"
            
        result += f"\n\nAVI/MM2 reboot completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        result += "\n\n⚠️  IMPORTANT: Monitor equipment status to confirm successful restart."
        result += "\nEquipment should be back online within 2-3 minutes."
        
        return result
        
    except Exception as e:
        return f"Error executing AVI/MM2 reboot: {str(e)}"