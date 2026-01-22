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
└── AutoTech\                     <- Tools and client folder
    ├── tools\                    <- Server-side tools (plink, vnc, etc.)
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

## AutoTech Client Installation

Users on remote PCs can install the client tools via:

1. **Web Download:** Go to T1 Legacy Tools page, click "Download Full Package (ZIP)"
2. **Extract ZIP** to any folder
3. **Right-click `Install_AutoTech_Client.bat`** and select "Run as administrator"

The installer:
- Copies tools to `C:\AutoTech_Client\`
- Registers custom URI handlers (autotech-ssh://, autotech-sftp://, autotech-vnc://, autotech-script://)
- Creates Start Menu shortcuts

**No Python or dependencies required** - pure batch file installer works on any Windows PC.

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

## Version

Built with PyInstaller as a standalone Windows executable.
No installation required - run directly from USB drive.
