@echo off
title MMS Scripts - Multi-Reboot Watchdog
echo PTX Multi-Reboot Watchdog Deployment Process
echo:
echo:
REM Check if password is already set (from launcher)
if not defined password (
    title MMS Scripts - Multi-Reboot Watchdog - Enter Password
    set /p password="Enter Password: "
) else (
    echo Password auto-filled from AutoTech launcher
)
cls
echo PTX Multi-Reboot Watchdog Deployment Process
:loop
title MMS Scripts - Multi-Reboot Watchdog - Enter Equipment
echo:
echo:
set /p ip_address="Enter Equipment Name (CAPS) or PTXC IP Address to Confirm: "
title MMS Scripts - Multi-Reboot Watchdog - Running...
::C:\AutoTech_Client\plink.exe -t mms@10.110.19.107 -pw %password% "/home/mms/bin/remote_check/Random/MySQL/ip_export_only.sh %ip_address%"
::set /p ip_address=Enter PTXC IP Address:
C:\AutoTech_Client\plink.exe -t mms@10.110.19.107 -pw %password%  "echo $(date): Initiated from  %COMPUTERNAME% by %USERNAME% for %ip_address%. >> /home/mms/bin/remote_check/AVI_Watchdog/cacheWatchdog/Report.txt; /home/mms/bin/remote_check/Random/MySQL/ip_export_only.sh %ip_address%"
title MMS Scripts - Multi-Reboot Watchdog - Complete
echo:
echo:
goto loop

