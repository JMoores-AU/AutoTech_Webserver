# AutoTech Client Installation Fix - Critical Architecture Change

## Problem Identified
The AutoTech web server was incorrectly checking its **own** filesystem (server-side) to detect if the client was installed, instead of checking the **remote user's PC** (client-side). This caused:

1. ✗ Remote users saw "Client v1.1.1" even when NOT installed locally
2. ✗ Tools opened on the SERVER instead of the remote PC
3. ✗ No verification that files/folders were actually installed on client machines

## Root Cause
**Server-side detection cannot access remote client filesystems.** The `/api/check-client-installed` endpoint was checking `C:\AutoTech_Client` on the web server, not on the user's remote machine at 10.110.19.100.

## Solution Implemented

### 1. Backend Changes (main.py)
**File**: `main.py`

**Changed**: `/api/check-client-installed` endpoint
- **Before**: Checked server's `C:\AutoTech_Client` folder
- **After**: Returns only the available server version for comparison
- **Why**: Servers cannot detect what's installed on remote clients

```python
# OLD (WRONG)
is_installed = os.path.exists("C:\\AutoTech_Client")  # Checks SERVER filesystem

# NEW (CORRECT)
return jsonify({
    'server_version': server_version,
    'note': 'Client installation must be checked client-side'
})
```

### 2. Frontend Changes (t1_legacy.html)
**File**: `templates/t1_legacy.html`

**Added**: Client-side detection with manual verification
- `testClientURIHandler()` - Tests if URI handlers work locally
- `testClientInstallation()` - Manual test button users can click
- LocalStorage caching to remember test results (5-minute cache)

**Flow**:
1. User clicks "Test Installation" button
2. Opens `autotech-ssh://test@127.0.0.1` to test if PuTTY launches
3. User confirms if PuTTY opened successfully
4. Result cached in browser localStorage
5. Page shows correct status based on ACTUAL client installation

### 3. Updated Install Instructions
**File**: `templates/t1_legacy.html` (install-info-box)

**Added**:
- ⚠️ Clear warning: "Installer must be run on EACH remote PC"
- 🧪 "Test Installation" button for manual verification
- Explanation: Web server runs centrally, tools open locally

## How It Works Now

### Client Installation Process
```
┌─────────────────────────────────────────────────────────────┐
│                     SERVER PC (10.110.19.X)                 │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  AutoTech Web Server (Flask)                        │  │
│  │  - Serves web dashboard                            │  │
│  │  - Returns server version for comparison           │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  E:\AutoTech\autotech_client\                       │  │
│  │  - Install_AutoTech_Client.bat                      │  │
│  │  - tools\ (putty.exe, winscp.exe, etc.)           │  │
│  │  - scripts\ (URI handler launchers)                │  │
│  │  - VERSION (1.1.1)                                  │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP: User browses to
                              │ http://10.110.19.X:8888
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    REMOTE PC (10.110.19.100)                │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  Web Browser                                         │  │
│  │  - Displays AutoTech dashboard                       │  │
│  │  - Runs JavaScript client-side checks               │  │
│  │  - Handles autotech:// URI protocol clicks          │  │
│  └─────────────────────────────────────────────────────┘  │
│                       │                                     │
│                       │ Launches via URI handler           │
│                       ▼                                     │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  C:\AutoTech_Client\                                │  │
│  │  ✓ putty.exe, winscp.exe, vncviewer.exe            │  │
│  │  ✓ scripts\launch_putty.bat                         │  │
│  │  ✓ mms_scripts\*.bat                                │  │
│  │  ✓ Registry: autotech-ssh:// handlers               │  │
│  │  ✓ VERSION (1.1.1)                                   │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Installation Steps (MUST be done on EACH remote PC)
1. **On Remote PC**: Map USB drive or network path to server
2. **On Remote PC**: Navigate to `E:\AutoTech\autotech_client\`
3. **On Remote PC**: Right-click `Install_AutoTech_Client.bat` → "Run as administrator"
4. **On Remote PC**: Open AutoTech dashboard in browser (http://10.110.19.X:8888)
5. **On Remote PC**: Click "🧪 Test Installation" button
6. **Verify**: PuTTY should open automatically
7. **Confirm**: Click OK in the confirmation dialog

## Files Changed

| File | Change | Why |
|------|--------|-----|
| `main.py` | Modified `/api/check-client-installed` | Remove server-side filesystem check |
| `templates/t1_legacy.html` | Added `testClientInstallation()` | Manual client verification |
| `templates/t1_legacy.html` | Updated install info box | Clearer instructions |
| `templates/t1_legacy.html` | Added localStorage caching | Remember test results |

## Testing the Fix

### Server (10.110.19.X)
```bash
# Rebuild exe with fixes
python -m PyInstaller AutoTech.spec --noconfirm

# Copy to USB
copy dist\AutoTech.exe E:\AutoTech.exe
```

### Remote PC (10.110.19.100)
```
1. Open browser → http://10.110.19.X:8888
2. Login with password
3. Go to T1 Legacy Tools page
4. See "⚠️ Installation Required" message
5. Run E:\AutoTech\autotech_client\Install_AutoTech_Client.bat as admin
6. Click "🧪 Test Installation" button
7. Confirm PuTTY opens
8. Status should change to "✅ Client v1.1.1"
```

## Future Improvements Needed
- [ ] Add test page accessible from all tool pages (not just T1 Legacy)
- [ ] Add version check to other template pages
- [ ] Create automated installer updater
- [ ] Add client health check API endpoint (test URI handlers automatically)

## Summary
**Before**: Server checked its own filesystem → Wrong results
**After**: Client tests its own URI handlers → Correct results

**Critical**: Installer MUST run on every remote PC individually!
