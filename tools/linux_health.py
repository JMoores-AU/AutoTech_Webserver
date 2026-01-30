# tools/linux_health.py
import paramiko
import os
from datetime import datetime
from pathlib import Path
from tools.app_logger import log_tool

GATEWAY_HOST = "10.110.19.107"
GATEWAY_USER = "mms"
HEALTH_CHECK_SCRIPT = "/home/mms/bin/remote_check/Random/LinuxCheck/For_Support/Check_Exe.sh"

def run(password=None, offline_mode=True):
    """
    Linux Health Check - Performance and Usage Check for PTX/Servers/ESTOP_Machines
    Based on the batch script: Linux_Health_Check
    """
    if offline_mode:
        log_tool('info', 'linux_health', "Linux health check offline mode")
        return """Linux Performance and Usage Check (Demo Mode)

=== SYSTEM HEALTH SUMMARY ===
Timestamp: 2024-01-15 14:32:15

SERVER STATUS:
┌─────────────────┬──────────┬─────────┬──────────────┬─────────┐
│ Server Name     │ Status   │ CPU %   │ Memory %     │ Disk %  │
├─────────────────┼──────────┼─────────┼──────────────┼─────────┤
│ FrontRunner     │ Online   │ 15.2%   │ 67.8%        │ 42.1%   │
│ Dispatch        │ Online   │ 8.7%    │ 34.5%        │ 28.9%   │
│ Base Station    │ Online   │ 22.1%   │ 81.2%        │ 55.7%   │
│ Monitor         │ Online   │ 12.4%   │ 45.6%        │ 33.2%   │
└─────────────────┴──────────┴─────────┴──────────────┴─────────┘

PTX EQUIPMENT STATUS:
- RD001: CPU: 8.5%, RAM: 456MB/2GB, Temp: 45°C
- RD002: CPU: 12.1%, RAM: 612MB/2GB, Temp: 52°C
- RD003: CPU: 6.8%, RAM: 389MB/2GB, Temp: 41°C

ALERTS:
⚠️  Base Station: High memory usage (81.2%)
⚠️  RD002: Temperature above normal (52°C)

Note: This is demonstration data. Enable online mode for live health monitoring."""

    if not password:
        log_tool('warning', 'linux_health', "Linux health check missing password")
        return "Error: Password required for live Linux health check"

    try:
        # Log the activity
        log_activity("Linux_Health_Check", "Linux Health Check script")
        log_tool('info', 'ssh', f"Linux health check connect to {GATEWAY_HOST}")
        
        result = f"""Linux Performance and Usage Check
Connected to: {GATEWAY_HOST}
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Executing health check script...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""
        
        # Connect to gateway and run health check
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(GATEWAY_HOST, username=GATEWAY_USER, password=password, timeout=10)
        
        # Execute the health check script
        stdin, stdout, stderr = ssh.exec_command(HEALTH_CHECK_SCRIPT, get_pty=True)
        
        # Read output in real-time
        output_lines = []
        for line in stdout:
            line = line.strip()
            if line:
                output_lines.append(line)
        
        # Also capture any errors
        error_output = stderr.read().decode('utf-8', errors='ignore').strip()
        
        ssh.close()
        
        if output_lines:
            result += "\n".join(output_lines)
        else:
            result += "No output received from health check script."
            
        if error_output:
            result += f"\n\nERRORS:\n{error_output}"
            
        result += "\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        result += f"\nHealth check completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return result
        
    except paramiko.AuthenticationException:
        log_tool('warning', 'ssh', f"Linux health auth failed for {GATEWAY_HOST}")
        return "Error: Authentication failed. Please check your password."
    except paramiko.SSHException as e:
        log_tool('error', 'ssh', f"Linux health SSH error for {GATEWAY_HOST}: {e}")
        return f"Error: SSH connection failed: {str(e)}"
    except Exception as e:
        log_tool('error', 'linux_health', f"Linux health error: {e}")
        return f"Error executing health check: {str(e)}\n\nPlease check your network connection."

def log_activity(script_name, description):
    """Log script activity like the original batch scripts"""
    try:
        current_date = datetime.now().strftime("%Y-%m-%d")
        current_time = datetime.now().strftime("%H:%M")
        computer_name = os.getenv("COMPUTERNAME", "PythonWebApp")
        username = os.getenv("USERNAME", "WebUser")
        
        log_entry = f"Date: {current_date} {current_time}, Computer Name: {computer_name}, Username: {username} - Ran {description}.\n"
        
        # Try to write to local log (if directory exists)
        log_dir = Path("C:/Komatsu_Tier1/T1_Tools/logs")
        if log_dir.exists():
            log_file = log_dir / "scripts_logfile.txt"
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(log_entry)
                
            # Try to copy to network location  
            network_path = Path("//10.110.19.105/c$/Master_T1_Tools/logs")
            if network_path.exists():
                network_log = network_path / "scripts_logfile.txt"
                with open(network_log, "a", encoding="utf-8") as f:
                    f.write(log_entry)
    except Exception:
        pass  # Logging is best effort
