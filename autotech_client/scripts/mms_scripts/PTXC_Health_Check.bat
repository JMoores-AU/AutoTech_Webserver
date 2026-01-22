@echo off
title MMS Scripts - PTXC Health Check
echo Welcome Embedded Health Check
echo:
echo:
REM Check if password is already set (from launcher)
if not defined password (
    title MMS Scripts - PTXC Health Check - Enter Password
    set /p password="Enter Password: "
) else (
    echo Password auto-filled from AutoTech launcher
)
cls
echo Welcome Embedded Health Check
:loop
title MMS Scripts - PTXC Health Check - Enter Equipment
echo:
echo:
set /p ip_address="Enter Equipment Name (CAPS) or PTXC IP Address to Confirm: "
title MMS Scripts - PTXC Health Check - Checking...
C:\AutoTech_Client\plink.exe -t mms@10.110.19.107  -pw %password% "/home/mms/bin/remote_check/ping_check/HealthCheck/ip_export_only.sh %ip_address%"
title MMS Scripts - PTXC Health Check - Complete
echo:
REM pscp mms@10.110.19.107:/home/mms/bin/remote_check/ping_check/HealthCheck/output_%date:~10,4%-%date:~7,2%-%date:~4,2%* .
echo:
goto loop