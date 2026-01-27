# AT_Client USB Drive Setup

## Overview
The AT_Client USB drive is a portable AutoTech client that runs all tools and scripts directly from the USB drive. Only the URI handlers and minimal launcher scripts are installed locally on each PC.

## USB Structure
```
AT_Client USB (E:\ or F:\)
├── Install_AutoTech_Client.bat       ← Run this as Administrator
├── AutoTech\
│   └── autotech_client\
│       ├── tools\                    ← PuTTY, WinSCP, VNC Viewer
│       ├── scripts\
│       │   ├── launch_*.bat          ← URI handler launchers
│       │   └── mms_scripts\          ← MMS batch scripts
│       └── VERSION
├── T1_Tools_Legacy\                  ← Legacy T1 Tools
├── frontrunnerV3-3.7.0-076-full\     ← Playback tools
├── CamStudio_USB\                    ← CamStudio portable
└── AT Monitor V3.7.0\                ← AT Monitor

```

## Installation Steps

### 1. Prepare the USB Drive
The build script automatically deploys the `autotech_client` folder to your USB drive at `X:\AutoTech\autotech_client\` when you run BUILD_WEBSERVER.bat (option 11 or 13).

**Manual deployment (if needed):**
- Copy the `autotech_client` folder to `X:\AutoTech\autotech_client\` on your USB drive
- Do NOT rename folders - scripts expect exact names

### 2. Install on Each PC
1. Plug in AT_Client USB drive
2. Navigate to `X:\AutoTech\autotech_client\` on the USB
3. Right-click `Install_AutoTech_Client.bat`
4. Select **"Run as administrator"**
5. Confirm installation when prompted

### 3. What Gets Installed Locally
The installer creates `C:\AutoTech_Client\` with:
- `scripts\launch_*.bat` - URI handler launchers (200KB total)
- `temp\` - Temporary files folder
- Registry entries for `autotech-ssh://`, `autotech-sftp://`, `autotech-vnc://`, `autotech-script://`

**All tools, executables, and MMS scripts stay on the USB drive.**

## How It Works

### URI Handlers
When the web interface calls a URI like `autotech-vnc://10.110.20.162:0`:

1. Windows registry redirects to `C:\AutoTech_Client\scripts\launch_vnc.bat`
2. Launcher script scans drives E-Z for `AutoTech\autotech_client\tools\vncviewer_5.3.2.exe`
3. Launches tool from USB with parsed parameters

### MMS Scripts
When calling `autotech-script://PTX_Uptime.bat`:

1. `C:\AutoTech_Client\scripts\launch_script.bat` receives the call
2. Scans drives for `X:\AutoTech\autotech_client\scripts\mms_scripts\PTX_Uptime.bat`
3. Opens CMD window and runs script from USB

## Troubleshooting

### "Tools not found" Error
- **Cause**: USB drive not plugged in or wrong drive letter
- **Fix**: Plug in USB and retry. Launcher scripts auto-detect E-Z drives.

### URI Handlers Not Working
- **Cause**: Installation not run as Administrator
- **Fix**: Re-run `Install_AutoTech_Client.bat` as Administrator

### Scripts Can't Find Tools
- **Cause**: USB folder structure doesn't match expected paths
- **Fix**: Verify `X:\AutoTech\autotech_client\tools\` contains:
  - `putty.exe`
  - `WinSCP.exe`
  - `vncviewer_5.3.2.exe`
  - `plink.exe`
  - `pscp.exe`

### Web Interface Shows "Client Not Installed"
- **Cause**: Browser hasn't detected URI handlers yet
- **Fix**:
  1. Close and reopen browser
  2. Click "Test Installation" on web dashboard
  3. Confirm when PuTTY window appears

## USB Drive Requirements
- **Size**: 2GB minimum (4GB recommended)
- **Format**: NTFS or FAT32
- **Drive Letter**: Any (E-Z auto-detected)
- **Speed**: USB 2.0 minimum (USB 3.0 recommended for faster tool launches)

## Updating the USB
To update tools/scripts on the USB:

1. Unplug from client PCs
2. Plug into admin/dev PC
3. Replace files in `AutoTech\autotech_client\tools\` or `scripts\mms_scripts\`
4. Update `VERSION` file if needed
5. Clients automatically use updated files on next launch (no reinstall needed)

## Security Notes
- URI handlers only launch tools from known paths
- Scripts validate file existence before execution
- No elevated privileges required for tool launches
- Registry entries point to local launchers only

## Maintenance

### Check USB Health
Run from USB root:
```batch
dir AutoTech\autotech_client\tools\*.exe
dir AutoTech\autotech_client\scripts\mms_scripts\*.bat
```

### Reinstall Client (if needed)
1. Uninstall: Delete `C:\AutoTech_Client\` folder
2. Remove registry: `reg delete HKCR\autotech-ssh /f` (repeat for -sftp, -vnc, -script)
3. Reinstall: Run `Install_AutoTech_Client.bat` as Administrator

## Version
Current Version: 1.1.1 (USB Portable Edition)
Last Updated: 2026-01-26
