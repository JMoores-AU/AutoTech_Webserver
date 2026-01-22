# AutoTech Web Dashboard

Mining equipment remote access system for Komatsu equipment. Provides web-based tools for T1 Legacy scripts and GRM equipment management.

## Quick Start

### Running the Server

**Development (from source):**
```batch
python main.py
```

**Production (from USB):**
```batch
E:\AutoTech.exe
```

**As Windows Service (runs 24/7, no user login needed):**
```batch
Install_AutoTech_Service.bat   # Run as admin
```

Access at: `http://localhost:8888`
Password: `komatsu`

---

## Building & Deployment

Use `BUILD_WEBSERVER.bat` for all build tasks:

| Option | Description |
|--------|-------------|
| 1 | Run development server |
| 9 | Build executable |
| 11 | Full build pipeline (recommended) |

When USB drive is connected, option 9 and 11 will automatically:
- Copy `AutoTech.exe` to USB root
- Deploy `autotech_client/` folder with installer package

---

## USB Drive Structure

After building with USB connected:

```
E:\ (AUTOTECH USB)
├── AutoTech.exe                  <- Web server executable
└── AutoTech\                     <- Tools and installers
    ├── Install_AutoTech_Service.bat      <- Windows service installer
    ├── Uninstall_AutoTech_Service.bat    <- Windows service uninstaller
    ├── tools\                    <- Server-side Python modules
    ├── database\                 <- SQLite databases
    └── autotech_client\          <- Client installer package
        ├── Install_AutoTech_Client.bat
        ├── tools\
        │   ├── putty.exe
        │   ├── plink.exe
        │   ├── WinSCP.exe
        │   └── vncviewer_5.3.2.exe
        └── scripts\
            ├── launch_putty.bat
            ├── launch_winscp.bat
            ├── launch_vnc.bat
            ├── launch_script.bat
            └── mms_scripts\
                └── (all MMS batch scripts)
```

---

## AutoTech Client Installation (REQUIRED FOR REMOTE PCs)

**IMPORTANT:** Without the client installed, VNC/SSH/SFTP tools will open **on the server** instead of your local PC!

### Remote PC Setup

Users on remote PCs **MUST** install the client tools:

1. Copy `E:\AutoTech\autotech_client` folder from USB to remote PC
2. Right-click `Install_AutoTech_Client.bat` and select "Run as administrator"
3. Installer copies tools to `C:\AutoTech_Client\`
4. Registers custom URI handlers (autotech-ssh://, autotech-sftp://, autotech-vnc://, autotech-script://)

**No Python or dependencies required** - pure batch file installer works on any Windows PC.

### How It Works

**Without client:**
- Server at 10.110.19.105:8888
- Remote PC at 10.110.19.100 opens browser
- Click VNC → Opens on **SERVER** (10.110.19.105) ❌

**With client installed:**
- Server at 10.110.19.105:8888
- Remote PC at 10.110.19.100 opens browser + has client installed
- Click VNC → Opens on **REMOTE PC** (10.110.19.100) ✅

The client installer registers Windows URI handlers that intercept `autotech-vnc://`, `autotech-ssh://`, etc. links and launch tools locally.

---

## Project Structure

```
T1_Tools_Web-1/
├── main.py                    <- Flask application
├── AutoTech.spec              <- PyInstaller spec file
├── BUILD_WEBSERVER.bat        <- Build & deployment script
├── requirements.txt           <- Python dependencies
├── autotech_client/           <- Client installer source
├── templates/                 <- HTML templates
├── static/                    <- CSS, images
├── tools/                     <- Python utility modules
└── legacy_batch_scripts/      <- MMS batch scripts (server-side)
```

---

## Features

### T1 Legacy Tools Page
- **MMS Batch Scripts:** Launch scripts in local CMD windows via custom URI handlers
- **GRM Scripts:** Web-based terminal for equipment queries
- **Auto-fill password:** MMS scripts auto-fill the "komatsu" password

### Custom URI Handlers
- `autotech-ssh://user@host` - Opens PuTTY SSH session
- `autotech-sftp://user@host` - Opens WinSCP SFTP session
- `autotech-vnc://host` - Opens VNC viewer
- `autotech-script://ScriptName.bat` - Launches MMS batch script

---

## Requirements

**Development:**
- Python 3.8+
- Flask, paramiko, ping3, requests
- PyInstaller (for building)

**Production:**
- Windows PC with AutoTech Client installed
- Network access to mining equipment

---

## Windows Service Installation

To run AutoTech 24/7 as a Windows service (survives reboots, no user login required):

1. Build and deploy to USB via `BUILD_WEBSERVER.bat`
2. On server PC, right-click `Install_AutoTech_Service.bat` → Run as administrator
3. Installer will:
   - Find `AutoTech.exe` (searches E:\, C:\AutoTech\, or asks for path)
   - Create Windows service named "AutoTech"
   - Set to auto-start on boot
   - Configure auto-restart on failure

**Management:**
```batch
sc start AutoTech    # Start service
sc stop AutoTech     # Stop service
sc query AutoTech    # Check status
Uninstall_AutoTech_Service.bat  # Remove service
```

**Security:** Uses built-in Windows `sc.exe` command (no external tools, no security warnings).

---

## Version

Built with PyInstaller as a standalone Windows executable.
No installation required - run directly from USB drive.
