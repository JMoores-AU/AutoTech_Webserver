@echo off
title MMS Scripts - Component Tracking
echo Welcome Field Component Info Utility
echo:
REM Check if password is already set (from launcher)
if not defined password (
    title MMS Scripts - Component Tracking - Enter Password
    set /p password="Enter Password: "
) else (
    echo Password auto-filled from AutoTech launcher
)
cls
echo:
echo Welcome Field Component Info Utility
:loop
title MMS Scripts - Component Tracking - Enter Equipment
echo:
echo:
set /p ip_address=Enter Equipment Name (CAPS):
title MMS Scripts - Component Tracking - Searching...
C:\AutoTech_Client\plink.exe -t mms@10.110.19.107 -pw %password% "/home/mms/bin/remote_check/Random/MySQL/Component/site_export.sh %ip_address%"
title MMS Scripts - Component Tracking - Complete
echo:
goto loop
