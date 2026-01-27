# AutoTech Client Registration System

## Overview
Server now tracks which remote PCs have AutoTech Client installed and verified.

## How It Works

### 1. User Tests Client (Dashboard Only)
- User navigates to http://10.110.19.X:8888 (Dashboard)
- Sees installation banner if not yet verified
- Clicks "🧪 Test Installation" button
- Multi-step verification:
  1. **Step 1**: Confirms `C:\AutoTech_Client` folder exists
  2. **Step 2**: Confirms files exist (putty.exe, scripts/, etc.)
  3. **Step 3**: Tests URI handler by opening PuTTY
- User confirms PuTTY opened successfully

### 2. Server Registration
When test succeeds, client calls `/api/register-client`:

```javascript
POST /api/register-client
{
  "client_version": "1.1.1",
  "test_success": true
}
```

Server logs to console:
```
============================================================
[CLIENT REGISTERED]
  IP Address: 10.110.19.100
  Version: v1.1.1
  Timestamp: 2026-01-23 15:30:45
  User Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)...
  Test Success: true
============================================================
```

### 3. Result Caching
- **localStorage** (browser): Cached for 5 minutes
  - `autotech_client_check`: "true"
  - `autotech_client_version`: "1.1.1"
  - `autotech_client_check_time`: timestamp
- **Server console**: Permanent log entry

### 4. Other Pages (T1 Legacy, etc.)
- Read from localStorage cache only
- No testing functionality on these pages
- Show "Setup Required" if cache missing → directs to Dashboard

## API Endpoints

### `/api/check-client-installed` (GET)
Returns server version and client IP:
```json
{
  "server_version": "1.1.1",
  "client_ip": "10.110.19.100",
  "user_agent": "Mozilla/5.0..."
}
```

### `/api/register-client` (POST)
Registers verified client with server:
```json
Request:
{
  "client_version": "1.1.1",
  "test_success": true
}

Response:
{
  "success": true,
  "message": "Client registered: 10.110.19.100",
  "client_ip": "10.110.19.100",
  "timestamp": "2026-01-23 15:30:45"
}
```

## Server Logging

Server console shows every client registration:
- **IP Address**: Which remote PC
- **Version**: Client version installed
- **Timestamp**: When verified
- **User Agent**: Browser/OS info
- **Test Success**: Confirmation

## Dashboard Display

**Sidebar Footer** shows:
```
Network Online
────────────────
✅ Client: v1.1.1
```

**Status Colors**:
- 🟢 Green: Client verified and working
- 🟡 Yellow: Unknown (test required)
- 🔴 Red: Not installed

## Installation Instructions (For Remote PCs)

1. **Run Installer**:
   ```
   E:\AutoTech\autotech_client\Install_AutoTech_Client.bat
   (RIGHT-CLICK → Run as administrator)
   ```

2. **Test on Dashboard**:
   - Open http://10.110.19.X:8888
   - Click "🧪 Test Installation"
   - Follow 3-step verification
   - Confirm PuTTY opens

3. **Server Confirms**:
   - Server logs your IP and version
   - Dashboard shows "✅ Client: v1.1.1"
   - You're done!

4. **Use Tools**:
   - All pages now work (T1 Legacy, IP Finder, etc.)
   - Tools open locally on your PC via URI handlers

## Benefits

✅ **Server Tracking**: Know which IPs have client installed
✅ **One-Time Setup**: Test once per PC on Dashboard
✅ **No Duplicate Tests**: Other pages just read cache
✅ **Clear Feedback**: Server logs every registration
✅ **User-Friendly**: Multi-step verification catches issues

## Future Enhancements

Possible additions:
- [ ] Database storage (instead of console logs)
- [ ] Admin panel showing all registered clients
- [ ] Auto-detect outdated clients
- [ ] Push notifications when updates available
- [ ] Periodic heartbeat from active clients
