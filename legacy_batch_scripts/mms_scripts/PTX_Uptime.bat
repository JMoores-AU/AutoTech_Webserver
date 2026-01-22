@echo off
MODE CON: COLS=40 LINES=10
TITLE PTX Uptime Report

for /f "tokens=2-4 delims=/ " %%a in ('date /t') do set currentDate=%%c-%%a-%%b
for /f "tokens=1-5 delims=:. " %%a in ('echo %time%') do set currentTime=%%a:%%b
echo Date: %currentDate% %currentTime%, Computer Name: %COMPUTERNAME%, Username: %USERNAME% - Ran PTX Uptime script. >> C:\Komatsu_Tier1\T1_Tools\logs\scripts_logfile.txt
set logFile=C:\Komatsu_Tier1\T1_Tools\logs\scripts_logfile.txt
set networkPath=\\10.110.19.105\c$\Master_T1_Tools\logs
copy "%logFile%" "%networkPath%" /Y > NUL 2>&1

echo PTXC Uptime Report Download
echo:
echo:
set /p password="Enter Password: " 
cls
echo PTXC Uptime Report Download
echo:
echo:
C:\Komatsu_Tier1\T1_Tools\mms_scripts\plink.exe -batch mms@10.110.19.107 -pw %password% "echo $(date): PTX_Uptime_Report Download Initiated from  %COMPUTERNAME% by %USERNAME%. >> /home/mms/Logs/Report_Download.txt"
C:\Komatsu_Tier1\T1_Tools\mms_scripts\pscp.exe -pw %password% mms@10.110.19.107:/home/mms/Logs/PTX_Uptime_Report.html C:\Komatsu_Tier1\T1_Tools\temp
start "" "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" "C:\Komatsu_Tier1\T1_Tools\temp\PTX_Uptime_Report.html"
timeout /t 5 /nobreak > NUL 
REM del "PTXC_Uptime_Report.html"