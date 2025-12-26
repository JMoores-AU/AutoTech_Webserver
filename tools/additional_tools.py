# tools/additional_tools.py
"""
Additional tools based on the batch scripts from mms_Scripts.txt
These can be integrated into the main application as needed.
"""

import paramiko
import os
import subprocess
import tempfile
import webbrowser
from datetime import datetime
from pathlib import Path

GATEWAY_HOST = "10.110.19.107"
GATEWAY_USER = "mms"

def component_tracking(equipment_name, password, offline_mode=True):
    """
    Component Tracking - Field Component Info Utility
    Based on: ComponentTracking batch script
    """
    if offline_mode:
        return f"""Field Component Tracker (Demo Mode)
Equipment: {equipment_name}

=== COMPONENT INFORMATION ===
Equipment ID: {equipment_name}
Site: Demo Mine Site
Date Installed: 2023-08-15

COMPONENT INVENTORY:
┌─────────────────────┬─────────────────┬─────────────────┬──────────────┐
│ Component           │ Part Number     │ Serial Number   │ Status       │
├─────────────────────┼─────────────────┼─────────────────┼──────────────┤
│ Main ECU            │ KOM-ECU-2024    │ ECU123456789    │ Active       │
│ Display Unit        │ KOM-DSP-2024    │ DSP987654321    │ Active       │
│ Radio Module        │ KOM-RAD-2024    │ RAD456789123    │ Active       │
│ GPS Antenna         │ KOM-GPS-2024    │ GPS789123456    │ Active       │
└─────────────────────┴─────────────────┴─────────────────┴──────────────┘

RECENT MAINTENANCE:
- 2024-01-10: Radio module firmware update
- 2024-01-05: Display calibration
- 2023-12-20: GPS antenna alignment

Note: This is demonstration data."""

    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(GATEWAY_HOST, username=GATEWAY_USER, password=password, timeout=10)
        
        cmd = f"/home/mms/bin/remote_check/Random/MySQL/Component/site_export.sh {equipment_name}"
        stdin, stdout, stderr = ssh.exec_command(cmd, get_pty=True)
        
        output = stdout.read().decode('utf-8', errors='ignore')
        error = stderr.read().decode('utf-8', errors='ignore')
        
        ssh.close()
        
        result = f"Field Component Tracker - {equipment_name}\n"
        result += "="*60 + "\n"
        result += output if output else "No component data found"
        
        if error:
            result += f"\n\nErrors:\n{error}"
            
        return result
        
    except Exception as e:
        return f"Error retrieving component tracking data: {str(e)}"

def avi_mm2_reboot(ptx_ip, password, offline_mode=True):
    """
    AVI/MM2 Reboot utility
    Based on: AVI_MM2_Reboot batch script
    """
    if offline_mode:
        return f"""AVI/MM2 Reboot Utility (Demo Mode)
Target IP: {ptx_ip}

⚠️  WARNING: This operation will reboot AVI Radio and MM2 components!

REBOOT SEQUENCE (SIMULATED):
1. Connecting to PTX at {ptx_ip}...
2. Stopping AVI radio services...
3. Stopping MM2 services...
4. Performing hardware reset...
5. Starting MM2 services...
6. Starting AVI radio services...

✅ Reboot completed successfully!

Equipment should be back online within 2-3 minutes.
Monitor equipment status to confirm successful restart.

Note: This is demonstration mode - no actual reboot was performed."""

    try:
        # Log the reboot request
        computer_name = os.getenv("COMPUTERNAME", "PythonWebApp")
        username = os.getenv("USERNAME", "WebUser")
        
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(GATEWAY_HOST, username=GATEWAY_USER, password=password, timeout=10)
        
        # Log the reboot initiation
        log_cmd = f'echo "$(date): Initiated from {computer_name} by {username} for {ptx_ip}." >> /home/mms/bin/remote_check/TempTool/MM2/Report.txt'
        ssh.exec_command(log_cmd)
        
        # Execute reboot script
        reboot_cmd = f"/home/mms/bin/remote_check/TempTool/MM2/Check_Exe.sh {ptx_ip}"
        stdin, stdout, stderr = ssh.exec_command(reboot_cmd, get_pty=True)
        
        output = stdout.read().decode('utf-8', errors='ignore')
        error = stderr.read().decode('utf-8', errors='ignore')
        
        ssh.close()
        
        result = f"AVI/MM2 Reboot - {ptx_ip}\n"
        result += "="*50 + "\n"
        result += f"Initiated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        result += output if output else "Reboot command executed"
        
        if error:
            result += f"\n\nWarnings/Errors:\n{error}"
            
        return result
        
    except Exception as e:
        return f"Error executing AVI/MM2 reboot: {str(e)}"

def speed_limit_data_check(password, offline_mode=True):
    """
    Speed Limit Data Check (LASL Report)
    Based on: Latest_SpeedLimit_DataCheck batch script
    """
    if offline_mode:
        return f"""Live Speed Limit Data Report (Demo Mode)
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

=== SPEED LIMIT ANALYSIS (LASL) ===

CURRENT SPEED ZONES:
┌─────────────────┬─────────────┬─────────────┬──────────────────┐
│ Zone ID         │ Speed Limit │ Equipment   │ Status           │
├─────────────────┼─────────────┼─────────────┼──────────────────┤
│ ZONE-001        │ 15 km/h     │ RD001,RD002 │ Active           │
│ ZONE-002        │ 25 km/h     │ RD003,RD004 │ Active           │
│ ZONE-003        │ 10 km/h     │ ALL         │ Construction     │
│ ZONE-004        │ 30 km/h     │ RD001       │ Active           │
└─────────────────┴─────────────┴─────────────┴──────────────────┘

SPEED VIOLATIONS (Last 24h):
- RD002: Exceeded 15 km/h limit in ZONE-001 (recorded: 18 km/h)
- RD004: Exceeded 25 km/h limit in ZONE-002 (recorded: 28 km/h)

ZONE UPDATES:
- ZONE-003: Temporary 10 km/h limit due to construction (expires: 2024-01-20)

Note: This is demonstration data. Enable online mode for live LASL reporting."""

    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(GATEWAY_HOST, username=GATEWAY_USER, password=password, timeout=10)
        
        cmd = "/home/mms/bin/remote_check/Random/MySQL/LASL_export.sh"
        stdin, stdout, stderr = ssh.exec_command(cmd, get_pty=True)
        
        output = stdout.read().decode('utf-8', errors='ignore')
        error = stderr.read().decode('utf-8', errors='ignore')
        
        ssh.close()
        
        result = f"Speed Limit Data Report\n"
        result += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        result += "="*60 + "\n"
        result += output if output else "No speed limit data available"
        
        if error:
            result += f"\n\nErrors:\n{error}"
            
        return result
        
    except Exception as e:
        return f"Error retrieving speed limit data: {str(e)}"

def koa_data_check(password, offline_mode=True):
    """
    Live KOA Data Check
    Based on: LIVE_KOA_DataCheck batch script
    """
    if offline_mode:
        return f"""Live KOA Data Report (Demo Mode)
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

=== KOA (Komatsu Operations Analytics) DATA ===

OPERATIONAL METRICS:
┌─────────────────┬─────────────┬─────────────┬─────────────┬──────────────┐
│ Equipment       │ Hours Today │ Fuel Usage  │ Efficiency  │ Status       │
├─────────────────┼─────────────┼─────────────┼─────────────┼──────────────┤
│ RD001          │ 8.5h        │ 145L        │ 87%         │ Operating    │
│ RD002          │ 7.2h        │ 132L        │ 91%         │ Operating    │
│ RD003          │ 6.8h        │ 128L        │ 89%         │ Operating    │
│ RD004          │ 9.1h        │ 158L        │ 85%         │ Operating    │
└─────────────────┴─────────────┴─────────────┴─────────────┴──────────────┘

PRODUCTIVITY SUMMARY:
• Total Operating Hours: 31.6h
• Total Fuel Consumed: 563L
• Fleet Average Efficiency: 88%
• Active Equipment: 4/4 (100%)

ALERTS:
⚠️  RD004: Below target efficiency (85% vs 90% target)
✅ All equipment operating within normal parameters

Note: This is demonstration data. Enable online mode for live KOA analytics."""

    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(GATEWAY_HOST, username=GATEWAY_USER, password=password, timeout=10)
        
        cmd = "/home/mms/bin/remote_check/Random/MySQL/table_export.sh"
        stdin, stdout, stderr = ssh.exec_command(cmd, get_pty=True)
        
        output = stdout.read().decode('utf-8', errors='ignore')
        error = stderr.read().decode('utf-8', errors='ignore')
        
        ssh.close()
        
        result = f"Live KOA Data Report\n"
        result += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        result += "="*60 + "\n"
        result += output if output else "No KOA data available"
        
        if error:
            result += f"\n\nErrors:\n{error}"
            
        return result
        
    except Exception as e:
        return f"Error retrieving KOA data: {str(e)}"

def watchdog_deploy(ptx_ip, ptx_model, password, offline_mode=True):
    """
    PTX-AVI Watchdog Deployment
    Based on: PTX-AVI_Watchdog_SingleDeploy batch script
    """
    if offline_mode:
        return f"""AVI-PTX Watchdog Deployment (Demo Mode)
Target: {ptx_ip} ({ptx_model})
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

DEPLOYMENT PROCESS:
1. ✅ Connecting to PTX at {ptx_ip}
2. ✅ Verifying {ptx_model} compatibility
3. ✅ Backing up existing watchdog configuration
4. ✅ Uploading new watchdog scripts
5. ✅ Configuring watchdog parameters
6. ✅ Starting watchdog service
7. ✅ Verifying watchdog functionality

DEPLOYMENT SUMMARY:
• Watchdog Service: Active
• Monitor Interval: 30 seconds
• Restart Threshold: 3 failures
• Log Retention: 7 days
• AVI Monitor: Enabled
• PTX Monitor: Enabled

✅ Watchdog deployment completed successfully!

The watchdog will now monitor AVI and PTX services and automatically
restart them if failures are detected.

Note: This is demonstration mode - no actual deployment was performed."""

    try:
        computer_name = os.getenv("COMPUTERNAME", "PythonWebApp")
        username = os.getenv("USERNAME", "WebUser")
        
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(GATEWAY_HOST, username=GATEWAY_USER, password=password, timeout=10)
        
        # Log the deployment
        log_cmd = f'echo "$(date): Initiated from {computer_name} by {username} for {ptx_ip}." >> /home/mms/bin/remote_check/AVI_Watchdog/Report.txt'
        ssh.exec_command(log_cmd)
        
        # Choose script based on PTX model
        if ptx_model.upper() == "PTXC":
            deploy_cmd = f"/home/mms/bin/remote_check/AVI_Watchdog/watchdog_setup_single.sh {ptx_ip}"
        else:  # PTX10
            deploy_cmd = f"/home/mms/bin/remote_check/AVI_Watchdog/watchdog_setup_single_PTX10.sh {ptx_ip}"
        
        stdin, stdout, stderr = ssh.exec_command(deploy_cmd, get_pty=True)
        
        output = stdout.read().decode('utf-8', errors='ignore')
        error = stderr.read().decode('utf-8', errors='ignore')
        
        ssh.close()
        
        result = f"AVI-PTX Watchdog Deployment - {ptx_ip} ({ptx_model})\n"
        result += "="*60 + "\n"
        result += f"Initiated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        result += output if output else "Deployment script executed"
        
        if error:
            result += f"\n\nWarnings/Errors:\n{error}"
            
        return result
        
    except Exception as e:
        return f"Error deploying watchdog: {str(e)}"

def log_downloader(target_ip, username_remote, password, offline_mode=True):
    """
    FrontRunner Logs Downloader
    Based on: Log_Downloader batch script
    """
    if offline_mode:
        return f"""FrontRunner Logs Downloader (Demo Mode)
Target: {target_ip} (User: {username_remote})

AVAILABLE LOGS:
┌─────────────────────────┬─────────────┬──────────────────┬─────────────┐
│ Log File               │ Size        │ Last Modified    │ Type        │
├─────────────────────────┼─────────────┼──────────────────┼─────────────┤
│ frontrunner_2024-01-15  │ 25.3 MB     │ 2024-01-15 14:30│ Application │
│ system_2024-01-15       │ 12.8 MB     │ 2024-01-15 14:25│ System      │
│ error_2024-01-15        │ 2.1 MB      │ 2024-01-15 14:20│ Error       │
│ network_2024-01-15      │ 8.9 MB      │ 2024-01-15 14:15│ Network     │
└─────────────────────────┴─────────────┴──────────────────┴─────────────┘

DOWNLOAD STATUS:
✅ Latest log package created: logs_{target_ip}_2024-01-15.zip
✅ Package size: 49.1 MB
✅ Download location: Downloads folder
✅ Package contains logs from last 6 hours

Note: This is demonstration mode - no actual download was performed.
In live mode, logs would be downloaded to your Downloads folder."""

    try:
        computer_name = os.getenv("COMPUTERNAME", "PythonWebApp")
        username_local = os.getenv("USERNAME", "WebUser")
        
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(GATEWAY_HOST, username=GATEWAY_USER, password=password, timeout=10)
        
        # Log the download request
        log_cmd = f'echo "$(date): Initiated from {computer_name} by {username_local}." >> /home/mms/bin/remote_check/TempTool/DOWNLOAD/Report.txt'
        ssh.exec_command(log_cmd)
        
        # Execute log collection script
        collect_cmd = f"/home/mms/bin/remote_check/TempTool/DOWNLOAD/Log_Get.sh {target_ip} {username_remote}"
        stdin, stdout, stderr = ssh.exec_command(collect_cmd, get_pty=True)
        
        output = stdout.read().decode('utf-8', errors='ignore')
        error = stderr.read().decode('utf-8', errors='ignore')
        
        # Try to find the latest log file
        ls_cmd = f"ls -t /home/mms/bin/remote_check/TempTool/DOWNLOAD/{target_ip}*.zip 2>/dev/null | head -1"
        stdin, stdout, stderr = ssh.exec_command(ls_cmd)
        latest_file = stdout.read().decode('utf-8', errors='ignore').strip()
        
        result = f"FrontRunner Logs Downloader - {target_ip}\n"
        result += "="*60 + "\n"
        result += f"Target Host: {target_ip}\n"
        result += f"Remote User: {username_remote}\n"
        result += f"Collection Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        if output:
            result += "COLLECTION OUTPUT:\n"
            result += output + "\n"
        
        if latest_file:
            result += f"\nLatest log package: {latest_file}\n"
            result += "Use SCP or download functionality to retrieve the log package."
        else:
            result += "\nNo log package found. Check collection output for errors."
        
        if error:
            result += f"\n\nErrors:\n{error}"
        
        ssh.close()
        return result
        
    except Exception as e:
        return f"Error downloading logs: {str(e)}"

def tcp_avi_dump(password, offline_mode=True):
    """
    Start TCPDump on AVI
    Based on: Start_TCP_AVI batch script
    """
    if offline_mode:
        return f"""TCPDump on AVI (Demo Mode)
Initiated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

AVI NETWORK CAPTURE STATUS:
✅ Connected to AVI radio module
✅ TCPDump service started
✅ Capturing on interface: eth0
✅ Filter: All traffic
✅ Duration: Continuous (until stopped)
✅ Output file: /tmp/avi_capture_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pcap

CAPTURE STATISTICS:
• Packets captured: 1,247
• Data size: 2.3 MB
• Duration: 5 minutes
• Average rate: 4.2 packets/sec

To stop the capture, use the AVI management interface or
contact system administrator.

Note: This is demonstration mode - no actual capture was started."""

    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(GATEWAY_HOST, username=GATEWAY_USER, password=password, timeout=10)
        
        cmd = "/home/mms/bin/remote_check/for_equipment/SCP/AVI_TCP.sh"
        stdin, stdout, stderr = ssh.exec_command(cmd, get_pty=True)
        
        output = stdout.read().decode('utf-8', errors='ignore')
        error = stderr.read().decode('utf-8', errors='ignore')
        
        ssh.close()
        
        result = f"TCPDump on AVI\n"
        result += "="*40 + "\n"
        result += f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        result += output if output else "TCPDump command executed"
        
        if error:
            result += f"\n\nErrors:\n{error}"
            
        return result
        
    except Exception as e:
        return f"Error starting AVI TCPDump: {str(e)}"