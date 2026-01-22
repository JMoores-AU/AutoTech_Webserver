@echo off
title MMS Scripts - KOA Data Check
mode con: cols=140
echo:
REM Check if password is already set (from launcher)
if not defined password (
    title MMS Scripts - KOA Data Check - Enter Password
    set /p password="Enter Password: "
) else (
    echo Password auto-filled from AutoTech launcher
)
cls
title MMS Scripts - KOA Data Check - Loading...
echo:
echo KOA Data at %date% %time%
echo:
echo:
C:\AutoTech_Client\plink.exe -t -noagent mms@10.110.19.107  -pw %password% "/home/mms/bin/remote_check/Random/MySQL/table_export.sh"
title MMS Scripts - KOA Data Check - Complete
echo:
REM pscp mms@10.110.19.107:/home/mms/bin/remote_check/Random/MySQL/detour* .
pause