@echo off
title MMS Scripts - PTX Uptime
echo PTXC Uptime Report Download
echo:
echo:
REM Check if password is already set (from launcher)
if not defined password (
    title MMS Scripts - PTX Uptime - Enter Password
    set /p password="Enter Password: "
) else (
    echo Password auto-filled from AutoTech launcher
)
cls
title MMS Scripts - PTX Uptime - Loading...
echo PTXC Uptime Report Download
echo:
echo:
C:\AutoTech_Client\plink.exe mms@10.110.19.107 -pw %password% "echo $(date): PTX_Uptime_Report Download Initiated from  %COMPUTERNAME% by %USERNAME%. >> /home/mms/Logs/Report_Download.txt"
title MMS Scripts - PTX Uptime - Downloading...
pscp -pw %password% mms@10.110.19.107:/home/mms/Logs/PTX_Uptime_Report.html C:\Komatsu_Tier1\Boxy_Adam
title MMS Scripts - PTX Uptime - Complete
start "" "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" "C:\Komatsu_Tier1\Boxy_Adam\PTX_Uptime_Report.html"
timeout /t 5
REM del "PTXC_Uptime_Report.html"