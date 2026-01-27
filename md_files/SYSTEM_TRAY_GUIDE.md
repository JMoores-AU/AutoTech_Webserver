# AutoTech System Tray Application

Run AutoTech in the background with a system tray icon (no command window).

## What It Does

- **No command window** - Runs silently in background
- **System tray icon** - Shows in taskbar (next to clock)
- **Right-click menu** - Start/Stop/Restart/Open Dashboard
- **Auto-start** - Automatically starts AutoTech on launch
- **Easy access** - Click icon to open dashboard

## How to Use

### Option 1: Quick Start (Recommended)
```
Double-click: AutoTech_Tray.exe
```
- AutoTech starts automatically in background
- Tray icon appears (🔧 wrench icon)
- Green = Running, Red = Stopped

### Option 2: Windows Service (Advanced)
For 24/7 server operation (survives reboots, no user login):
```
Run: Install_AutoTech_Service.bat (as admin)
```

## Tray Icon Menu

**Right-click the tray icon:**

| Menu Item | Action |
|-----------|--------|
| **Open Dashboard** | Opens browser to http://localhost:8888 |
| Start Server | Starts AutoTech.exe in background |
| Stop Server | Stops AutoTech.exe |
| Restart Server | Stops and starts AutoTech.exe |
| Exit | Closes tray app and stops AutoTech |

**Left-click (or double-click):**
- Opens dashboard in browser

## Building

To build the tray application:

```batch
BUILD_WEBSERVER.bat → Option 11 (Build Executable)
```

This builds both:
- `dist/AutoTech.exe` (web server)
- `dist/AutoTech_Tray.exe` (tray launcher)

Or full pipeline with USB deployment:
```batch
BUILD_WEBSERVER.bat → Option 13 (Full Build Pipeline)
```

## Installation

### USB Structure
```
E:\
├── AutoTech.exe              (Web server)
├── AutoTech_Tray.exe         (System tray launcher - USE THIS)
└── AutoTech\
    ├── Install_AutoTech_Service.bat
    └── ...
```

### For Server PC
1. Copy `AutoTech_Tray.exe` to desktop or startup folder
2. Double-click to run
3. Icon appears in system tray

### Auto-Start on Windows Boot
**Option A: Startup Folder**
1. Press `Win+R`, type `shell:startup`, press Enter
2. Create shortcut to `AutoTech_Tray.exe` in startup folder
3. AutoTech will start automatically when Windows boots

**Option B: Task Scheduler**
1. Open Task Scheduler
2. Create Basic Task: "AutoTech Tray"
3. Trigger: At startup
4. Action: Start program → `AutoTech_Tray.exe`
5. Finish

## Troubleshooting

### Tray icon not appearing
- Check Windows Settings → Personalization → Taskbar → System Tray Icons
- Enable "AutoTech" icon visibility

### "AutoTech.exe not found" error
- Ensure both `AutoTech.exe` and `AutoTech_Tray.exe` are in same folder
- Or place them in: `E:\` (USB root) or `C:\AutoTech\`

### Port 8888 already in use
- Another AutoTech instance is running
- Right-click tray → Stop Server
- Or: `taskkill /f /im AutoTech.exe`

### Can't stop AutoTech
- Right-click tray → Exit
- Or: Open Task Manager → End "AutoTech.exe"

## Technical Details

**What gets started:**
- `AutoTech_Tray.exe` (tray application)
- `AutoTech.exe` (web server, hidden)

**Process check:**
```batch
tasklist | findstr AutoTech
```

**Port check:**
```batch
netstat -an | findstr :8888
```

## Comparison: Tray vs Service

| Feature | System Tray | Windows Service |
|---------|-------------|-----------------|
| Command window | ❌ None | ❌ None |
| User login required | ✅ Yes | ❌ No |
| Taskbar icon | ✅ Yes | ❌ No |
| Easy start/stop | ✅ Right-click menu | ❌ Command line |
| Auto-restart on crash | ❌ No | ✅ Yes |
| Runs on boot | ⚠️ Needs setup | ✅ Yes |
| Best for | **Desktop/workstation** | **24/7 server** |

## Recommended Usage

**Field Laptop (moves between sites):**
```
Use: AutoTech_Tray.exe
- Easy to start/stop
- Visible tray icon
- No admin rights needed
```

**Permanent Server (site office):**
```
Use: Install_AutoTech_Service.bat
- Runs 24/7
- Survives reboots
- No user login needed
```

---

## Version
System tray support added in v1.2.0
