@echo off
title MMS Scripts - Speed Limit Data
mode con: cols=130
echo:
REM Check if password is already set (from launcher)
if not defined password (
    title MMS Scripts - Speed Limit Data - Enter Password
    set /p password="Enter Password: "
) else (
    echo Password auto-filled from AutoTech launcher
)
cls
title MMS Scripts - Speed Limit Data - Loading...
echo:
echo SpeedLimit Data at %date% %time%
echo:
echo:
C:\AutoTech_Client\plink.exe -t -noagent mms@10.110.19.107  -pw %password% "/home/mms/bin/remote_check/Random/MySQL/LASL_export.sh"
title MMS Scripts - Speed Limit Data - Complete
echo:
pause
