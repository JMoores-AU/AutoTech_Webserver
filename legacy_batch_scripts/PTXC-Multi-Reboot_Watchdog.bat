@echo off

echo PTX Multi-Reboot Watchdog Deployment Process
echo:
echo:
set /p password="Enter Password: " 
cls
echo PTX Multi-Reboot Watchdog Deployment Process
:loop
echo:
echo:
set /p ip_address="Enter Equipment Name (CAPS) or PTXC IP Address to Confirm: "
::plink.exe -t mms@10.110.19.107 -pw %password% "/home/mms/bin/remote_check/Random/MySQL/ip_export_only.sh %ip_address%"
::set /p ip_address=Enter PTXC IP Address: 
plink.exe -t mms@10.110.19.107 -pw %password%  "echo $(date): Initiated from  %COMPUTERNAME% by %USERNAME% for %ip_address%. >> /home/mms/bin/remote_check/AVI_Watchdog/cacheWatchdog/Report.txt; /home/mms/bin/remote_check/Random/MySQL/ip_export_only.sh %ip_address%"
echo:
echo:
goto loop

