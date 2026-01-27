@echo off
MODE CON: COLS=140
TITLE KOA Data

for /f "tokens=2-4 delims=/ " %%a in ('date /t') do set currentDate=%%c-%%a-%%b
for /f "tokens=1-5 delims=:. " %%a in ('echo %time%') do set currentTime=%%a:%%b
echo Date: %currentDate% %currentTime%, Computer Name: %COMPUTERNAME%, Username: %USERNAME% - Ran Live KOA Data script. >> C:\Komatsu_Tier1\T1_Tools\logs\scripts_logfile.txt
set logFile=C:\Komatsu_Tier1\T1_Tools\logs\scripts_logfile.txt
set networkPath=\\10.110.105\c$\Master_T1_Tools\logs
copy "%logFile%" "%networkPath%" /Y > NUL 2>&1
echo:
set /p password="Enter Password: " 
cls
echo:
echo KOA Data at %date% %time%
echo:
echo:
C:\Komatsu_Tier1\T1_Tools\mms_scripts\plink.exe -batch -t -noagent mms@10.110.19.107  -pw %password% "/home/mms/bin/remote_check/Random/MySQL/table_export.sh"
echo:
REM pscp mms@10.110.19.107:/home/mms/bin/remote_check/Random/MySQL/detour* .
pause