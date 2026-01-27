@echo off
MODE CON: COLS=60
TITLE IP Finder

for /f "tokens=2-4 delims=/ " %%a in ('date /t') do set currentDate=%%c-%%a-%%b
for /f "tokens=1-5 delims=:. " %%a in ('echo %time%') do set currentTime=%%a:%%b
echo Date: %currentDate% %currentTime%, Computer Name: %COMPUTERNAME%, Username: %USERNAME% - Ran IP Finder script. >> C:\Komatsu_Tier1\T1_Tools\logs\scripts_logfile.txt
set logFile=C:\Komatsu_Tier1\T1_Tools\logs\scripts_logfile.txt
set networkPath=\\10.110.19.105\c$\Master_T1_Tools\logs
copy "%logFile%" "%networkPath%" /Y > NUL 2>&1

echo Welcome Embedded Info Utility
echo:
set /p password="Enter Password: "
cls
:loop
echo:
echo:
set /p ip_address=Enter Equipment Name (CAPS) or PTXC IP Address: 
C:\Komatsu_Tier1\T1_Tools\mms_scripts\plink.exe -batch -t mms@10.110.19.107 -pw %password% "/home/mms/bin/remote_check/Random/MySQL/ip_export.sh %ip_address%"
echo:
goto loop

