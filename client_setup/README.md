# T1 Tools Client Setup

This package installs the necessary tools on remote PCs to enable seamless launching of PuTTY, WinSCP, and VNC Viewer from the web interface.

## What Gets Installed

1. **Portable Applications** (to C:\T1_Tools_Client\)
   - PuTTY (SSH client)
   - WinSCP (SFTP/SCP client)
   - VNC Viewer (Remote desktop)
   - plink.exe (Command-line SSH)
   - pscp.exe (Command-line SCP)

2. **Custom URI Handlers** (Windows Registry)
   - `t1putty://` - Launches PuTTY with connection details
   - `t1winscp://` - Launches WinSCP with connection details
   - `t1vnc://` - Launches VNC Viewer with connection details

## Installation

1. Download `T1_Tools_Client_Setup.exe` from the web server
2. Run as Administrator
3. Click through the installer
4. Done! Applications will now launch from the web interface

## How It Works

When you click a button in the web interface:
1. Server looks up equipment IP address
2. Server returns connection details (IP, port, credentials)
3. Browser triggers custom URI (e.g., `t1putty://mms@10.110.19.107:22`)
4. Windows launches installed PuTTY with those details
5. PuTTY connects automatically

## Uninstallation

Run `C:\T1_Tools_Client\Uninstall.bat` to:
- Remove installed tools
- Remove registry entries
- Delete installation folder
