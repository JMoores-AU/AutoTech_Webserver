# AutoTech USB Deployment Guide

## Overview
The AutoTech system uses a USB drive for portable tools and scripts. The USB structure matches the `autotech_client/` folder in this repository.

## USB Structure

```
USB Drive (E:\, F:\, etc.)
├── AutoTech.exe                          ← Server executable
├── Install_AutoTech_Client.bat           ← Client installer (run as admin)
├── VERSION                               ← Client version (1.2.0)
├── AutoTech\
│   ├── tools\
│   │   ├── putty.exe                     ← SSH client
│   │   ├── WinSCP.exe                    ← SFTP client
│   │   ├── vncviewer_5.3.2.exe          ← VNC client
│   │   ├── plink.exe, pscp.exe          ← PuTTY command-line tools
│   │   ├── equipment_db.py              ← Equipment database module
│   │   └── ptx_uptime_db.py             ← PTX uptime database module
│   ├── scripts\
│   │   ├── launch_putty.bat             ← URI handler for autotech-ssh://
│   │   ├── launch_winscp.bat            ← URI handler for autotech-sftp://
│   │   ├── launch_vnc.bat               ← URI handler for autotech-vnc://
│   │   ├── launch_script.bat            ← URI handler for autotech-script://
│   │   └── mms_scripts\
│   │       ├── PTX_Uptime.bat
│   │       ├── Playback_Tool.bat
│   │       ├── CamStudio.bat
│   │       ├── Linux_Health_Check.bat
│   │       └── ... (20+ MMS scripts)
│   ├── database\
│   │   └── equipment_cache.db           ← Cached equipment data
│   ├── Install_AutoTech_Service.bat     ← Server Windows service installer
│   └── Uninstall_AutoTech_Service.bat   ← Server service uninstaller
├── T1_Tools_Legacy\
│   └── bin\
│       ├── T1_Tools.bat
│       └── IP_list.dat
├── frontrunnerV3-3.7.0-076-full\
│   └── ... (Playback tools)
├── CamStudio_USB\
│   └── ... (CamStudio portable)
└── AT Monitor V3.7.0\
    └── ... (AT Monitor)
```

## Deployment Process

### 1. Build and Deploy to USB

Run BUILD_WEBSERVER.bat:
- **Option 11**: Build Executable (deploys to USB if detected)
- **Option 13**: Full Build Pipeline (recommended)

The build script automatically:
1. Detects USB drive with `\AutoTech` folder (drives D-L)
2. Copies `Install_AutoTech_Client.bat` → USB root
3. Copies `VERSION` → USB root
4. Syncs `autotech_client\AutoTech\*` → `USB:\AutoTech\`
5. Updates Python tools (equipment_db.py, ptx_uptime_db.py)
6. Copies server service installers

### 2. Install on Client PCs

On each client PC:
1. Plug in USB drive
2. Navigate to USB root (E:\, F:\, etc.)
3. Right-click `Install_AutoTech_Client.bat`
4. Select **"Run as administrator"**
5. Confirm installation

### 3. What Gets Installed Locally

The installer creates `C:\AutoTech_Client\` with:
- `scripts\launch_*.bat` - URI handler launchers (~10KB)
- `temp\` - Temporary files folder
- Registry entries for custom URI protocols

**All tools and scripts stay on the USB drive.**

## How It Works

### URI Protocol Flow

Example: User clicks "Connect via SSH" on web interface

1. Web page calls: `autotech-ssh://mms@10.110.19.107:22`
2. Windows registry redirects to: `C:\AutoTech_Client\scripts\launch_putty.bat`
3. Launcher scans drives E-Z for: `X:\AutoTech\tools\putty.exe`
4. Launches PuTTY from USB with parsed parameters

### MMS Script Flow

Example: User clicks "PTX Uptime" tool

1. Web page calls: `autotech-script://PTX_Uptime.bat`
2. Registry redirects to: `C:\AutoTech_Client\scripts\launch_script.bat`
3. Launcher finds: `X:\AutoTech\scripts\mms_scripts\PTX_Uptime.bat`
4. Opens CMD window and executes script from USB

### T1 Tools Flow

Example: User clicks "Launch T1 Tools"

1. Web page calls: `autotech-script://t1-tools`
2. Launcher finds: `X:\T1_Tools_Legacy\bin\T1_Tools.bat`
3. Opens CMD window in that directory

## Troubleshooting

### "Tools not found" Error
- **Cause**: USB drive not plugged in
- **Fix**: Plug in USB and retry. Launchers auto-detect drives E-Z.

### URI Handlers Not Working
- **Cause**: Installer not run as Administrator
- **Fix**: Re-run `Install_AutoTech_Client.bat` as Administrator

### Scripts Can't Find Tools
- **Cause**: USB folder structure doesn't match expected paths
- **Fix**: Verify USB has:
  - `X:\AutoTech\tools\putty.exe`
  - `X:\AutoTech\tools\WinSCP.exe`
  - `X:\AutoTech\tools\vncviewer_5.3.2.exe`
  - `X:\AutoTech\scripts\mms_scripts\*.bat`

### Playback Tools Not Working
- **Cause**: frontrunnerV3-3.7.0-076-full folder missing from USB root
- **Fix**: Copy playback tools folder to USB root

## Version History

- **1.2.0** (2026-01-26): Flat AutoTech\ structure, removed autotech_client subfolder
- **1.1.2**: USB-aware launchers with autotech_client\ subfolder
- **1.0.0**: Initial release

## Development Notes

### Local Folder Structure

The `autotech_client/` folder in this repository represents the USB root:
- `autotech_client/AutoTech/` → `USB:\AutoTech\`
- `Install_AutoTech_Client.bat` → `USB:\Install_AutoTech_Client.bat`
- `VERSION` → `USB:\VERSION`

### Updating Launch Scripts

Launch scripts are in: `autotech_client/AutoTech/scripts/launch_*.bat`

They scan drives E-Z looking for:
- `X:\AutoTech\tools\*.exe`
- `X:\AutoTech\scripts\mms_scripts\*.bat`
- `X:\T1_Tools_Legacy\bin\T1_Tools.bat`

### Updating MMS Scripts

Add/edit scripts in: `autotech_client/AutoTech/scripts/mms_scripts/`

Then rebuild and deploy to USB using BUILD_WEBSERVER.bat.

Clients don't need to reinstall - scripts run directly from USB.

### Updating Tools

Update executables in: `autotech_client/AutoTech/tools/`

Then rebuild and deploy. Clients don't need to reinstall.

## Security Notes

- URI handlers only launch tools from verified paths
- Scripts validate file existence before execution
- No elevated privileges required for tool launches
- Registry entries point to local launchers only (not external executables)
