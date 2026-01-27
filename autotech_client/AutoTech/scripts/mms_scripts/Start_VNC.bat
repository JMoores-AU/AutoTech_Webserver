@echo off
title MMS Scripts - Start VNC
echo Welcome Embedded VNC Utility
echo:
echo:
REM Check if password is already set (from launcher)
if not defined password (
    title MMS Scripts - Start VNC - Enter Password
    set /p password="Enter Password: "
) else (
    echo Password auto-filled from AutoTech launcher
)
cls
echo:
echo Welcome Embedded VNC Utility
echo:
echo:
title MMS Scripts - Start VNC - Enter IP
set /p ip_address=Enter PTXC IP Address:
title MMS Scripts - Start VNC - Connecting...
C:\AutoTech_Client\plink.exe -batch -t mms@10.110.19.107 -pw %password%  "/home/mms/bin/remote_check/TempTool/VNC/Check_Exe.sh %ip_address%"
title MMS Scripts - Start VNC - Complete
echo:
start "" "AutoTech_Client\tools\vncviewer_5.3.2.exe" %ip_address%:0

