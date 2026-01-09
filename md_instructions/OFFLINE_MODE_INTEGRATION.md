# INTEGRATED OFFLINE MODE - Log Cleanup

## Overview
The log cleanup automatically detects network mode and uses:
- **ONLINE** → Real SSH to equipment
- **OFFLINE** → Local test data

No checkbox needed - it just works!

---

## Step 1: Generate Test Data (One Time)

```cmd
cd C:\T1_Tools_Web
python test_log_generator.py
```

Creates: `C:\T1_Tools_Web\test_logs\`

---

## Step 2: Add Test Mode Function to main.py

**Add this function after your existing `cleanup_logs()` function (around line 730):**

```python
def cleanup_logs_test_mode(folder_retention=2, file_retention=7, dry_run=True):
    """
    Test/Offline mode cleanup - uses local test data.
    Automatically used when is_online_network() returns False.
    """
    import os
    import shutil
    
    TEST_PATH = "C:/T1_Tools_Web/test_logs"
    
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
        # Check test data exists
        if not os.path.exists(TEST_PATH):
            results["error"] = "Offline mode: Test data not found. Run: python test_log_generator.py"
            return results
        
        log("🔌 OFFLINE MODE - Using local test data")
        log(f"Path: {TEST_PATH}")
        
        current_date = datetime.now()
        current_time = current_date.timestamp()
        
        # Scan folders
        folders = []
        for item in os.listdir(TEST_PATH):
            path = os.path.join(TEST_PATH, item)
            if os.path.isdir(path) and len(item) == 6 and item.isdigit():
                year = int(item) // 100
                month = int(item) % 100
                if 1 <= month <= 12:
                    months_diff = (current_date.year - year) * 12 + (current_date.month - month)
                    folders.append((item, months_diff))
        
        # Scan 0-byte files in root
        broken = []
        for item in os.listdir(TEST_PATH):
            path = os.path.join(TEST_PATH, item)
            if os.path.isfile(path) and os.path.getsize(path) == 0:
                days_old = int((current_time - os.path.getmtime(path)) / 86400)
                broken.append((item, days_old))
        
        # Scan loose files in root
        loose = []
        for item in os.listdir(TEST_PATH):
            path = os.path.join(TEST_PATH, item)
            if os.path.isfile(path) and os.path.getsize(path) > 0:
                days_old = int((current_time - os.path.getmtime(path)) / 86400)
                loose.append((item, days_old))
        
        log(f"\nFound {len(folders)} folders, {len(broken)} 0-byte files, {len(loose)} loose files")
        
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
                    shutil.rmtree(os.path.join(TEST_PATH, folder))
                    log(f"  ✓ Deleted")
                results["stats"]["folders_deleted"] += 1
            else:
                log(f"Keeping: {folder} ({months_old} months old)")
                kept_folders.append(folder)
        
        # Process 0-byte files
        log(f"\n{'='*50}")
        log(f"0-BYTE FILE CLEANUP (Retention: {file_retention} days)")
        log(f"{'='*50}")
        
        for filepath, days_old in sorted(broken, key=lambda x: x[1], reverse=True):
            if days_old > file_retention:
                if dry_run:
                    log(f"WOULD DELETE: {filepath} ({days_old} days old)")
                else:
                    log(f"Deleting: {filepath} ({days_old} days old)")
                    os.remove(os.path.join(TEST_PATH, filepath))
                    log(f"  ✓ Deleted")
                results["stats"]["broken_deleted"] += 1
        
        # Process loose files
        log(f"\n{'='*50}")
        log(f"LOOSE FILE CLEANUP (Retention: {file_retention} days)")
        log(f"{'='*50}")
        
        for filepath, days_old in sorted(loose, key=lambda x: x[1], reverse=True):
            if days_old > file_retention:
                if dry_run:
                    log(f"WOULD DELETE: {filepath} ({days_old} days old)")
                else:
                    log(f"Deleting: {filepath} ({days_old} days old)")
                    os.remove(os.path.join(TEST_PATH, filepath))
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
        
        results["success"] = True
        
    except Exception as e:
        log(f"\n✗ ERROR: {str(e)}")
        results["error"] = str(e)
    
    return results
```

---

## Step 3: Update Cleanup Routes (Auto-Detect Offline)

**REPLACE your existing cleanup routes (lines ~2683 & ~2710) with these:**

```python
@app.route('/api/cleanup-logs', methods=['POST'])
def api_cleanup_logs():
    """Execute log cleanup - auto-detects online/offline mode."""
    try:
        data = request.json
        folder_retention = int(data.get('folder_retention', 2))
        file_retention = int(data.get('file_retention', 7))
        dry_run = data.get('dry_run', True)
        
        # AUTO-DETECT: Use test mode when offline
        if not is_online_network():
            print("[CLEANUP] OFFLINE MODE - Using test data")
            results = cleanup_logs_test_mode(
                folder_retention=folder_retention,
                file_retention=file_retention,
                dry_run=dry_run
            )
            return jsonify(results)
        
        # ONLINE MODE: Use real SSH
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


@app.route('/api/cleanup-logs/preview', methods=['POST'])
def api_cleanup_logs_preview():
    """Preview cleanup - auto-detects online/offline mode."""
    try:
        data = request.json
        folder_retention = int(data.get('folder_retention', 2))
        file_retention = int(data.get('file_retention', 7))
        
        # AUTO-DETECT: Use test mode when offline
        if not is_online_network():
            print("[CLEANUP] OFFLINE MODE - Preview with test data")
            results = cleanup_logs_test_mode(
                folder_retention=folder_retention,
                file_retention=file_retention,
                dry_run=True
            )
            return jsonify(results)
        
        # ONLINE MODE: Use real SSH
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
```

---

## Step 4: Add Network Mode Indicator to Modal (Optional)

**In `ip_finder.html`, update the modal to show network status:**

```html
<div class="cleanup-config">
    <p><strong>Equipment:</strong> <span id="cleanup-equipment"></span></p>
    <p><strong>IP Address:</strong> <span id="cleanup-ip"></span></p>
    
    <!-- NEW: Network Status Indicator -->
    <p>
        <strong>Mode:</strong> 
        <span id="cleanup-mode" style="padding: 2px 8px; border-radius: 4px; font-size: 0.85rem;">
            {{ '🔌 OFFLINE (Test Data)' if not online else '🌐 ONLINE (Real Equipment)' }}
        </span>
    </p>
    
    <!-- Rest of modal... -->
</div>
```

---

## ✅ That's It! How It Works:

### When OFFLINE (Laptop/Dev):
```
1. Click "Clean Logs"
2. Shows: "🔌 OFFLINE (Test Data)"
3. Uses local test data automatically
4. No real SSH connections
```

### When ONLINE (Production):
```
1. Click "Clean Logs"  
2. Shows: "🌐 ONLINE (Real Equipment)"
3. Connects via SSH to real equipment
4. Performs actual cleanup
```

---

## 🔄 Testing Both Modes:

### Test Offline Mode:
```cmd
# Force offline
set T1_OFFLINE=1
python main.py
```

### Test Online Mode:
```cmd
# On production network (or force online)
set T1_FORCE_ONLINE=1
python main.py
```

---

## 🎯 Advantages of This Approach:

✅ **Automatic** - No checkbox needed, detects network mode  
✅ **Consistent** - Same pattern as other tools in your system  
✅ **Safe** - Can't accidentally run test mode in production  
✅ **Universal** - All tools can follow this pattern  
✅ **Clean** - Uses existing infrastructure  

---

## 📊 Console Output Examples:

**Offline:**
```
Network Mode: OFFLINE
[CLEANUP] OFFLINE MODE - Using test data
```

**Online:**
```
Network Mode: ONLINE
[CLEANUP] ONLINE MODE - Connecting to equipment
```

---

## 🔧 Bonus: Force Offline for Testing

```cmd
# In your environment or batch file
set T1_OFFLINE=1
python main.py
```

Now even on the production network, it will use test data!

---

**Files Needed:**
1. `test_log_generator.py` - Generate test data
2. Updated routes in `main.py` - Auto-detect mode
3. `cleanup_logs_test_mode()` function - Offline handler

**No UI changes needed!** It just works based on network detection.
