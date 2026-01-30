"""
PTX Log Cleanup Tool - Web Interface Module
Provides log cleanup functionality for T1 Tools Web Dashboard
"""

import paramiko
from datetime import datetime
import json
from tools.app_logger import log_tool


def connect_to_equipment(ip_address):
    """
    Try to connect to equipment using both credential sets.
    Returns: (ssh_client, credential_name) or (None, error_message)
    """
    credentials = [
        {"user": "dlog", "password": "gold", "name": "PTXC"},
        {"user": "mms", "password": "modular", "name": "PTX10"}
    ]
    
    for cred in credentials:
        try:
            log_tool('info', 'ssh', f"Log cleanup SSH connect to {ip_address} ({cred['name']})")
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(
                hostname=ip_address,
                username=cred['user'],
                password=cred['password'],
                timeout=10,
                look_for_keys=False,
                allow_agent=False
            )
            return ssh, cred['name']
        except Exception as e:
            continue
    
    log_tool('error', 'ssh', f"Log cleanup SSH failed for {ip_address}")
    return None, f"Could not connect to {ip_address} with any credentials"


def find_log_directory(ssh):
    """
    Find the log directory path on the remote system.
    Returns: (path, None) or (None, error_message)
    """
    # Strategy 1: Check user's home
    stdin, stdout, stderr = ssh.exec_command("echo $HOME")
    user_home = stdout.read().decode().strip()
    
    if user_home:
        user_path = f"{user_home}/frontrunnerV3/logs"
        stdin, stdout, stderr = ssh.exec_command(f"test -d {user_path} && echo EXISTS")
        if stdout.read().decode().strip() == "EXISTS":
            return user_path, None
    
    # Strategy 2: Common paths
    base_paths = ["/real_home", "/home/dlog", "/home/mms", "/home", "/opt"]
    
    for base in base_paths:
        test_path = f"{base}/frontrunnerV3/logs"
        stdin, stdout, stderr = ssh.exec_command(f"test -d {test_path} && echo EXISTS")
        if stdout.read().decode().strip() == "EXISTS":
            return test_path, None
    
    # Strategy 3: Search filesystem
    stdin, stdout, stderr = ssh.exec_command(
        "find /real_home /home /opt /usr -type d -path '*/frontrunnerV3/logs' 2>/dev/null | head -1"
    )
    found_path = stdout.read().decode().strip()
    
    if found_path:
        return found_path, None
    
    return None, "Could not locate log directory"


def get_folder_list(ssh, log_path):
    """Get list of monthly folders with their age."""
    cmd = f"cd {log_path} && ls -d */ 2>/dev/null | sed 's|/||'"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    output = stdout.read().decode()
    
    folders = []
    current_date = datetime.now()
    
    for line in output.strip().split('\n'):
        folder = line.strip()
        if not folder:
            continue
        
        if len(folder) == 6 and folder.isdigit():
            folder_year_month = int(folder)
            folder_year = folder_year_month // 100
            folder_month = folder_year_month % 100
            
            if 1 <= folder_month <= 12:
                months_diff = (current_date.year - folder_year) * 12 + (current_date.month - folder_month)
                folders.append((folder, months_diff))
            else:
                folders.append((folder, 0))
        else:
            folders.append((folder, 0))
    
    return folders


def get_broken_logs(ssh, log_path):
    """Find 0-byte files in root directory."""
    cmd = f'cd {log_path} && find . -maxdepth 1 -type f -size 0 -printf "%p:%T@\\n"'
    stdin, stdout, stderr = ssh.exec_command(cmd)
    output = stdout.read().decode()
    
    broken_files = []
    current_time = datetime.now().timestamp()
    
    for line in output.strip().split('\n'):
        if not line or ':' not in line:
            continue
        
        try:
            filepath, mtime = line.rsplit(':', 1)
            filepath = filepath.lstrip('./')
            days_old = int((current_time - float(mtime)) / 86400)
            broken_files.append((filepath, days_old))
        except (ValueError, IndexError):
            continue
    
    return broken_files


def get_loose_files(ssh, log_path):
    """Find loose log files in root directory."""
    cmd = f'cd {log_path} && find . -maxdepth 1 -type f ! -size 0 -printf "%p:%T@\\n"'
    stdin, stdout, stderr = ssh.exec_command(cmd)
    output = stdout.read().decode()
    
    loose_files = []
    current_time = datetime.now().timestamp()
    
    for line in output.strip().split('\n'):
        if not line or ':' not in line:
            continue
        
        try:
            filepath, mtime = line.rsplit(':', 1)
            filepath = filepath.lstrip('./')
            days_old = int((current_time - float(mtime)) / 86400)
            loose_files.append((filepath, days_old))
        except (ValueError, IndexError):
            continue
    
    return loose_files


def cleanup_logs(ip_address, folder_retention=2, file_retention=7, dry_run=True):
    """
    Main cleanup function for web interface.
    Returns: dict with results and logs
    """
    log_tool('info', 'log_cleanup', f"Log cleanup start for {ip_address} dry_run={dry_run}")
    results = {
        "success": False,
        "log": [],
        "stats": {
            "folders_deleted": 0,
            "broken_deleted": 0,
            "loose_deleted": 0,
            "total_deleted": 0
        }
    }
    
    def log(msg):
        results["log"].append(msg)
    
    try:
        # Connect
        log(f"Connecting to {ip_address}...")
        ssh, cred_type = connect_to_equipment(ip_address)
        if not ssh:
            results["error"] = cred_type
            return results
        
        log(f"âœ“ Connected as {cred_type}")
        
        # Find log directory
        log("Searching for log directory...")
        log_path, error = find_log_directory(ssh)
        if not log_path:
            results["error"] = error
            ssh.close()
            return results
        
        log(f"âœ“ Found logs: {log_path}")
        
        # Get folders
        log("\nScanning folders...")
        folders = get_folder_list(ssh, log_path)
        log(f"Found {len(folders)} folders")
        
        # Get broken logs
        log("Scanning 0-byte files...")
        broken_files = get_broken_logs(ssh, log_path)
        log(f"Found {len(broken_files)} broken files")
        
        # Get loose files
        log("Scanning loose files...")
        loose_files = get_loose_files(ssh, log_path)
        log(f"Found {len(loose_files)} loose files")
        
        # Process folders
        log(f"\n{'='*50}")
        log(f"FOLDER CLEANUP (Keep: current + last {folder_retention} months)")
        log(f"{'='*50}")
        
        kept_folders = []
        for folder, months_old in sorted(folders, key=lambda x: x[1], reverse=True):
            if months_old > folder_retention:
                if dry_run:
                    log(f"WOULD DELETE: {folder} ({months_old} months old)")
                else:
                    log(f"Deleting: {folder} ({months_old} months old)")
                    cmd = f"cd {log_path} && rm -rf '{folder}'"
                    ssh.exec_command(cmd)
                    log(f"  âœ“ Deleted")
                results["stats"]["folders_deleted"] += 1
            else:
                log(f"Keeping: {folder} ({months_old} months old)")
                if len(folder) == 6 and folder.isdigit():
                    kept_folders.append(folder)
        
        # Process broken logs
        log(f"\n{'='*50}")
        log(f"0-BYTE FILE CLEANUP (Retention: {file_retention} days)")
        log(f"{'='*50}")
        
        for filepath, days_old in sorted(broken_files, key=lambda x: x[1], reverse=True):
            if days_old > file_retention:
                if dry_run:
                    log(f"WOULD DELETE: {filepath} ({days_old} days old)")
                else:
                    log(f"Deleting: {filepath} ({days_old} days old)")
                    cmd = f"cd {log_path} && rm -f '{filepath}'"
                    ssh.exec_command(cmd)
                    log(f"  âœ“ Deleted")
                results["stats"]["broken_deleted"] += 1
        
        # Process loose files
        log(f"\n{'='*50}")
        log(f"LOOSE FILE CLEANUP (Retention: {file_retention} days)")
        log(f"{'='*50}")
        
        for filepath, days_old in sorted(loose_files, key=lambda x: x[1], reverse=True):
            if days_old > file_retention:
                if dry_run:
                    log(f"WOULD DELETE: {filepath} ({days_old} days old)")
                else:
                    log(f"Deleting: {filepath} ({days_old} days old)")
                    cmd = f"cd {log_path} && rm -f '{filepath}'"
                    ssh.exec_command(cmd)
                    log(f"  âœ“ Deleted")
                results["stats"]["loose_deleted"] += 1
        
        # Summary
        results["stats"]["total_deleted"] = (
            results["stats"]["folders_deleted"] + 
            results["stats"]["broken_deleted"] + 
            results["stats"]["loose_deleted"]
        )
        
        log(f"\n{'='*50}")
        log(f"{'DRY RUN ' if dry_run else ''}COMPLETE")
        log(f"{'='*50}")
        log(f"Folders: {results['stats']['folders_deleted']}")
        log(f"Broken files: {results['stats']['broken_deleted']}")
        log(f"Loose files: {results['stats']['loose_deleted']}")
        log(f"Total: {results['stats']['total_deleted']}")
        
        if kept_folders:
            log(f"\nâœ“ Files in kept folders ({', '.join(kept_folders)}) were preserved")
        
        ssh.close()
        results["success"] = True
        
    except Exception as e:
        log(f"\nâœ— ERROR: {str(e)}")
        log_tool('error', 'log_cleanup', f"Log cleanup error for {ip_address}: {e}")
        results["error"] = str(e)
    
    return results
