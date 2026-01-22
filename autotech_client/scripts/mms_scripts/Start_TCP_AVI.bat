@echo off
title MMS Scripts - TCP AVI
echo Start TCPDump on AVI
echo:
echo:
REM Check if password is already set (from launcher)
if not defined password (
    title MMS Scripts - TCP AVI - Enter Password
    set /p password="Enter Password: "
) else (
    echo Password auto-filled from AutoTech launcher
)
cls
title MMS Scripts - TCP AVI - Running...
echo Start TCPDump on AVI
echo:
echo:
C:\AutoTech_Client\plink.exe -t mms@10.110.19.107 -pw %password%  "/home/mms/bin/remote_check/for_equipment/SCP/AVI_TCP.sh"
title MMS Scripts - TCP AVI - Complete
echo:
TIMEOUT 10