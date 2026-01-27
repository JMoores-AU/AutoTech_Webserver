@echo off

echo AVI-PTX Watchdog Deployment Process
echo:
echo:
set /p password="Enter Password: " 
cls
echo AVI-PTX Watchdog Deployment Process
:loop
echo:
echo:
set /p ip_address=Enter PTXC IP Address: 
plink.exe -t mms@10.110.19.107 -pw %password%  "echo $(date): Initiated from  %COMPUTERNAME% by %USERNAME% for %ip_address%. >> /home/mms/bin/remote_check/AVI_Watchdog/ActivityReport.txt; /home/mms/bin/remote_check/AVI_Watchdog/watchdog_setup_single.sh %ip_address%"
echo:
pscp -pw %password% mms@10.110.19.107:/home/mms/bin/remote_check/AVI_Watchdog/completed_ips_%date:~10,4%* C:\Komatsu_Tier1\Boxy_Adam\PTX-AVI_Watchdog_SingleDeploy
echo:
echo:
goto loop

