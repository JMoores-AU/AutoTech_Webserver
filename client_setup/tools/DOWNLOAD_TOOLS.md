# Download Required Portable Tools

Before building the client setup, download the following portable versions:

## 1. PuTTY (SSH Client)
- **Download:** https://the.earth.li/~sgtatham/putty/latest/w64/putty.exe
- **Save as:** `putty.exe`
- **Place in:** `client_setup/tools/`

## 2. plink (Command-line SSH)
- **Download:** https://the.earth.li/~sgtatham/putty/latest/w64/plink.exe
- **Save as:** `plink.exe`
- **Place in:** `client_setup/tools/`

## 3. pscp (Command-line SCP)
- **Download:** https://the.earth.li/~sgtatham/putty/latest/w64/pscp.exe
- **Save as:** `pscp.exe`
- **Place in:** `client_setup/tools/`

## 4. WinSCP (SFTP/SCP Client)
- **Download:** https://winscp.net/download/WinSCP-5.21.7-Portable.zip
- **Extract:** WinSCP.exe
- **Save as:** `WinSCP.exe`
- **Place in:** `client_setup/tools/`

## 5. VNC Viewer (Remote Desktop)
- **Download:** https://www.realvnc.com/en/connect/download/viewer/windows/
- **Get:** VNC Viewer standalone executable (version 5.3.2)
- **Save as:** `vncviewer_5.3.2.exe`
- **Place in:** `client_setup/tools/`

## Alternative: Use Existing Tools from T1_Tools_Legacy

If you already have these tools in your USB T1_Tools installation:
```
E:\T1_Tools_Legacy\bin\putty.exe
E:\T1_Tools_Legacy\bin\plink.exe
E:\T1_Tools_Legacy\bin\pscp.exe
E:\T1_Tools_Legacy\bin\WinSCP.exe
```

Copy them to `client_setup/tools/`

## After Downloading

1. Verify all files are in `client_setup/tools/`:
   - putty.exe
   - plink.exe
   - pscp.exe
   - WinSCP.exe
   - vncviewer_5.3.2.exe

2. You can then package the installer or serve it from the web server
