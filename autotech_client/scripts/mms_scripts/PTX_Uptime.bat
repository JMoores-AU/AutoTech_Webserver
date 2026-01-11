@echo off

echo PTXC Uptime Report Download
echo:
echo:
set /p password="Enter Password: " 
cls
echo PTXC Uptime Report Download
echo:
echo:
C:AutoTech_Clientplink.exe mms@10.110.19.107 -pw %password% "echo $(date): PTX_Uptime_Report Download Initiated from  %COMPUTERNAME% by %USERNAME%. >> /home/mms/Logs/Report_Download.txt"
pscp -pw %password% mms@10.110.19.107:/home/mms/Logs/PTX_Uptime_Report.html C:\Komatsu_Tier1\Boxy_Adam
start "" "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" "C:\Komatsu_Tier1\Boxy_Adam\PTX_Uptime_Report.html"
timeout /t 5
REM del "PTXC_Uptime_Report.html"