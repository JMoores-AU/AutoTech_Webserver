@echo off
title MMS Scripts - IP Finder
echo:
echo Welcome Embedded Info Utility
echo:
REM Check if password is already set (from launcher)
if not defined password (
    title MMS Scripts - IP Finder - Enter Password
    set /p password="Enter Password: "
) else (
    echo Password auto-filled from AutoTech launcher
)
cls
:loop
title MMS Scripts - IP Finder - Enter Equipment
echo:
echo:
set /p ip_address=Enter Equipment Name (CAPS) or PTXC IP Address:
title MMS Scripts - IP Finder - Searching...
C:\AutoTech_Client\plink.exe -t mms@10.110.19.107 -pw %password% "/home/mms/bin/remote_check/Random/MySQL/ip_export.sh %ip_address%"
title MMS Scripts - IP Finder - Complete
echo:
goto loop

