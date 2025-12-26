# tools/mineview_sessions.py
import paramiko
import os
from datetime import datetime
from pathlib import Path

GATEWAY_HOST = "10.110.19.107"
GATEWAY_USER = "mms"
MINEVIEW_SCRIPT = "/home/mms/bin/MineView-Session.sh"

def run(password=None, offline_mode=True):
    """
    MineView Sessions - Live session monitoring and reporting
    Based on the batch script: MineView_Session
    """
    if offline_mode:
        return """Live MineView Sessions (Demo Mode)

=== MINEVIEW SESSION REPORT ===
Generated: 2024-01-15 14:35:42

ACTIVE SESSIONS:
┌────────────────┬─────────────────────┬──────────────┬──────────────┬─────────────┐
│ Session ID     │ User                │ Equipment    │ Duration     │ Status      │
├────────────────┼─────────────────────┼──────────────┼──────────────┼─────────────┤
│ MV-001-2024    │ operator1@mine.com  │ RD001        │ 2h 15m       │ Active      │
│ MV-002-2024    │ supervisor@mine.com │ RD002        │ 45m          │ Active      │
│ MV-003-2024    │ mechanic1@mine.com  │ RD003        │ 1h 32m       │ Active      │
│ MV-004-2024    │ admin@mine.com      │ ALL          │ 4h 22m       │ Active      │
└────────────────┴─────────────────────┴──────────────┴──────────────┴─────────────┘

RECENT DISCONNECTIONS:
- MV-005-2024: operator2@mine.com (RD004) - Disconnected 15 minutes ago
- MV-006-2024: trainee@mine.com (RD001) - Disconnected 1 hour ago

SESSION STATISTICS:
• Total Active Sessions: 4
• Average Session Duration: 2h 3m
• Peak Concurrent Sessions Today: 8
• Total Sessions Today: 23

EQUIPMENT USAGE:
• RD001: 2 sessions (6h 45m total)
• RD002: 1 session (45m total) 
• RD003: 1 session (1h 32m total)
• Global View: 1 session (4h 22m total)

Note: This is demonstration data. Enable online mode for live session monitoring."""

    if not password:
        return "Error: Password required for live MineView session monitoring"

    try:
        # Log the activity
        log_activity("MineView_Session", "MineView Session script")
        
        result = f"""Live MineView Sessions
Connected to: {GATEWAY_HOST}
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Retrieving active MineView sessions...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""
        
        # Connect to gateway and run MineView session script
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(GATEWAY_HOST, username=GATEWAY_USER, password=password, timeout=10)
        
        # Execute the MineView session script
        stdin, stdout, stderr = ssh.exec_command(MINEVIEW_SCRIPT, get_pty=True)
        
        # Read output
        output_lines = []
        for line in stdout:
            line = line.strip()
            if line:
                output_lines.append(line)
        
        # Capture any errors
        error_output = stderr.read().decode('utf-8', errors='ignore').strip()
        
        ssh.close()
        
        if output_lines:
            result += "\n".join(output_lines)
            
            # Add some formatting to make it more readable
            result += "\n\n" + "="*80
            result += f"\nSession report generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            result += "\nFor detailed session logs, check the MineView server logs."
        else:
            result += "No active MineView sessions found or script returned no output."
            
        if error_output:
            result += f"\n\nWARNINGS/ERRORS:\n{error_output}"
            
        return result
        
    except paramiko.AuthenticationException:
        return "Error: Authentication failed. Please check your password."
    except paramiko.SSHException as e:
        return f"Error: SSH connection failed: {str(e)}"
    except Exception as e:
        return f"Error retrieving MineView sessions: {str(e)}\n\nPlease check your network connection."

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