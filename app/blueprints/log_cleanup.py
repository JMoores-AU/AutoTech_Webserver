"""
app/blueprints/log_cleanup.py
==============================
Log cleanup API routes:
  /api/cleanup-logs, /api/cleanup-logs/preview, /api/cleanup-logs/generate-test-data

Includes SSH helper functions for scanning and cleaning remote log directories.
"""

import logging
import os
import shutil
import subprocess
import sys
from datetime import datetime

from flask import Blueprint, jsonify, request

from app.config import BASE_DIR
from app.utils import connect_to_equipment, is_online_network

logger = logging.getLogger(__name__)

bp = Blueprint('log_cleanup', __name__, url_prefix='')


# ==============================================================================
# SSH HELPER FUNCTIONS
# ==============================================================================

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

        log(f"✓ Connected as {cred_type}")

        # Find log directory
        log("Searching for log directory...")
        log_path, error = find_log_directory(ssh)
        if not log_path:
            results["error"] = error
            ssh.close()
            return results

        log(f"✓ Found logs: {log_path}")

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
                    log(f"  ✓ Deleted")
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
                    log(f"  ✓ Deleted")
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
                    log(f"  ✓ Deleted")
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
            log(f"\n✓ Files in kept folders ({', '.join(kept_folders)}) were preserved")

        ssh.close()
        results["success"] = True

    except Exception as e:
        log(f"\n✗ ERROR: {str(e)}")
        results["error"] = str(e)

    return results


def cleanup_logs_test_mode(folder_retention=2, file_retention=7, dry_run=True):
    """
    Offline mode cleanup - uses local test data.
    Auto-called when is_online_network() returns False.
    """
    # Use test_logs directory in project root
    TEST_PATH = os.path.join(BASE_DIR, "test_logs")

    results = {
        "success": False,
        "log": [],
        "stats": {"folders_deleted": 0, "broken_deleted": 0, "loose_deleted": 0, "total_deleted": 0}
    }

    def log(msg):
        results["log"].append(msg)

    try:
        print(f"[DEBUG] Looking for test data at: {TEST_PATH}")
        print(f"[DEBUG] BASE_DIR = {BASE_DIR}")
        print(f"[DEBUG] Path exists: {os.path.exists(TEST_PATH)}")

        # Auto-generate test data if it doesn't exist
        if not os.path.exists(TEST_PATH):
            log("[OFFLINE MODE] Test data not found - generating now...")
            print("[CLEANUP] Auto-generating test data...")

            generator_path = os.path.join(BASE_DIR, 'tools', 'test_log_generator.py')

            try:
                result = subprocess.run([sys.executable, generator_path],
                                        capture_output=True, text=True, timeout=60)
                if result.returncode != 0:
                    results["error"] = f"Failed to generate test data: {result.stderr}"
                    return results
                log("[SUCCESS] Test data generated successfully")
                print("[CLEANUP] Test data generation complete")
            except Exception as gen_error:
                results["error"] = f"Failed to generate test data: {str(gen_error)}"
                return results

        log("[OFFLINE MODE] Using local test data")
        log(f"Path: {TEST_PATH}")

        current_date = datetime.now()
        current_time = current_date.timestamp()

        # Scan folders
        folders = []
        for item in os.listdir(TEST_PATH):
            path = os.path.join(TEST_PATH, item)
            if os.path.isdir(path) and len(item) == 6 and item.isdigit():
                year, month = int(item) // 100, int(item) % 100
                if 1 <= month <= 12:
                    months_diff = (current_date.year - year) * 12 + (current_date.month - month)
                    folders.append((item, months_diff))

        # Scan 0-byte files
        broken = [(f, int((current_time - os.path.getmtime(os.path.join(TEST_PATH, f))) / 86400))
                  for f in os.listdir(TEST_PATH)
                  if os.path.isfile(os.path.join(TEST_PATH, f)) and os.path.getsize(os.path.join(TEST_PATH, f)) == 0]

        # Scan loose files
        loose = [(f, int((current_time - os.path.getmtime(os.path.join(TEST_PATH, f))) / 86400))
                 for f in os.listdir(TEST_PATH)
                 if os.path.isfile(os.path.join(TEST_PATH, f)) and os.path.getsize(os.path.join(TEST_PATH, f)) > 0]

        log(f"\nFound {len(folders)} folders, {len(broken)} 0-byte files, {len(loose)} loose files")

        # Process folders
        log(f"\n{'='*50}\nFOLDER CLEANUP (Keep: current + last {folder_retention} months)\n{'='*50}")
        kept = []
        for folder, age in sorted(folders, key=lambda x: x[1], reverse=True):
            if age > folder_retention:
                log(f"{'WOULD DELETE' if dry_run else 'Deleting'}: {folder} ({age} months old)")
                if not dry_run:
                    shutil.rmtree(os.path.join(TEST_PATH, folder))
                results["stats"]["folders_deleted"] += 1
            else:
                log(f"Keeping: {folder} ({age} months old)")
                kept.append(folder)

        # Process 0-byte
        log(f"\n{'='*50}\n0-BYTE FILE CLEANUP (Retention: {file_retention} days)\n{'='*50}")
        for file, age in broken:
            if age > file_retention:
                log(f"{'WOULD DELETE' if dry_run else 'Deleting'}: {file} ({age} days old)")
                if not dry_run:
                    os.remove(os.path.join(TEST_PATH, file))
                results["stats"]["broken_deleted"] += 1

        # Process loose
        log(f"\n{'='*50}\nLOOSE FILE CLEANUP (Retention: {file_retention} days)\n{'='*50}")
        for file, age in loose:
            if age > file_retention:
                log(f"{'WOULD DELETE' if dry_run else 'Deleting'}: {file} ({age} days old)")
                if not dry_run:
                    os.remove(os.path.join(TEST_PATH, file))
                results["stats"]["loose_deleted"] += 1

        results["stats"]["total_deleted"] = sum(results["stats"].values())

        log(f"\n{'='*50}\n{'DRY RUN ' if dry_run else ''}COMPLETE\n{'='*50}")
        log(f"Folders: {results['stats']['folders_deleted']}")
        log(f"Broken: {results['stats']['broken_deleted']}")
        log(f"Loose: {results['stats']['loose_deleted']}")
        log(f"Total: {results['stats']['total_deleted']}")

        if kept:
            log(f"\n[KEPT] Folders: {', '.join(kept)}")

        results["success"] = True

        # Delete test_logs folder after successful execution (not dry run)
        if not dry_run:
            log(f"\n{'='*50}")
            log("CLEANUP COMPLETE - RESETTING TEST DATA")
            log(f"{'='*50}")

            try:
                shutil.rmtree(TEST_PATH)
                log(f"[RESET] Test data folder deleted: {TEST_PATH}")
                log(f"[NOTE] Fresh test data will be auto-generated on next cleanup")
                print(f"[CLEANUP] Test data folder deleted and reset")
            except Exception as del_error:
                log(f"[WARNING] Could not delete test folder: {str(del_error)}")

    except Exception as e:
        log(f"\n[ERROR] {str(e)}")
        results["error"] = str(e)

    return results


# ==============================================================================
# ROUTES
# ==============================================================================

@bp.route('/api/cleanup-logs', methods=['POST'])
def api_cleanup_logs():
    """Execute log cleanup - auto-detects online/offline mode."""
    print("[CLEANUP ROUTE] /api/cleanup-logs called")
    try:
        data = request.json
        if data is None:
            return jsonify({"success": False, "error": "No JSON data provided"}), 400
        folder_retention = int(data.get('folder_retention', 2))
        file_retention = int(data.get('file_retention', 7))
        dry_run = data.get('dry_run', True)

        print(f"[CLEANUP] Received: dry_run={dry_run}, folder_retention={folder_retention}, file_retention={file_retention}")

        # AUTO-DETECT OFFLINE MODE
        if not is_online_network():
            print(f"[CLEANUP] OFFLINE MODE - Using test data (dry_run={dry_run})")
            results = cleanup_logs_test_mode(
                folder_retention=folder_retention,
                file_retention=file_retention,
                dry_run=dry_run
            )
            return jsonify(results)

        # ONLINE MODE
        print("[CLEANUP] ONLINE MODE - Connecting to equipment")
        ip_address = data.get('ip')

        if not ip_address:
            return jsonify({"success": False, "error": "No IP address provided"}), 400

        results = cleanup_logs(
            ip_address=ip_address,
            folder_retention=folder_retention,
            file_retention=file_retention,
            dry_run=dry_run
        )

        return jsonify(results)

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route('/api/cleanup-logs/preview', methods=['POST'])
def api_cleanup_logs_preview():
    """Preview cleanup - auto-detects online/offline mode."""
    print("[CLEANUP ROUTE] /api/cleanup-logs/preview called")
    try:
        data = request.json
        if data is None:
            return jsonify({"success": False, "error": "No JSON data provided"}), 400
        folder_retention = int(data.get('folder_retention', 2))
        file_retention = int(data.get('file_retention', 7))

        # AUTO-DETECT OFFLINE MODE
        if not is_online_network():
            print("[CLEANUP] OFFLINE MODE - Preview with test data")
            results = cleanup_logs_test_mode(
                folder_retention=folder_retention,
                file_retention=file_retention,
                dry_run=True
            )
            return jsonify(results)

        # ONLINE MODE
        print("[CLEANUP] ONLINE MODE - Preview real equipment")
        ip_address = data.get('ip')

        if not ip_address:
            return jsonify({"success": False, "error": "No IP address provided"}), 400

        results = cleanup_logs(
            ip_address=ip_address,
            folder_retention=folder_retention,
            file_retention=file_retention,
            dry_run=True
        )

        return jsonify(results)

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route('/api/cleanup-logs/generate-test-data', methods=['POST'])
def api_generate_test_data():
    """Generate test data for offline mode testing."""
    try:
        # Only works in offline mode
        if is_online_network():
            return jsonify({"success": False, "error": "Test data generation only available in offline mode"}), 400

        print("[TEST DATA] Generating test log files...")

        generator_path = os.path.join(BASE_DIR, 'tools', 'test_log_generator.py')

        if not os.path.exists(generator_path):
            return jsonify({"success": False, "error": f"Generator not found at {generator_path}"}), 500

        # Run the generator
        result = subprocess.run([sys.executable, generator_path],
                                capture_output=True, text=True, timeout=60)

        if result.returncode == 0:
            print("[TEST DATA] Generation complete")
            return jsonify({
                "success": True,
                "message": "Test data generated successfully"
            })
        else:
            error_msg = result.stderr[:500] if result.stderr else "Unknown error"
            print(f"[TEST DATA] Generation failed: {error_msg}")
            return jsonify({
                "success": False,
                "error": f"Generation failed: {error_msg}"
            }), 500

    except subprocess.TimeoutExpired:
        return jsonify({"success": False, "error": "Test data generation timed out"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
