@echo off
MODE CON: COLS=85 LINES=30
TITLE MineView Sessions

for /f "tokens=2-4 delims=/ " %%a in ('date /t') do set currentDate=%%c-%%a-%%b
for /f "tokens=1-5 delims=:. " %%a in ('echo %time%') do set currentTime=%%a:%%b
echo Date: %currentDate% %currentTime%, Computer Name: %COMPUTERNAME%, Username: %USERNAME% - Ran MineView Session script. >> C:\Komatsu_Tier1\T1_Tools\logs\scripts_logfile.txt
set logFile=C:\Komatsu_Tier1\T1_Tools\logs\scripts_logfile.txt
set networkPath=\\10.110.19.105\c$\Master_T1_Tools\logs
copy "%logFile%" "%networkPath%" /Y > NUL 2>&1

echo Live MineView Sessions
echo:
echo:
set /p password="Enter Password: " 
cls
echo Live MineView Sessions
echo:
echo:
C:\Komatsu_Tier1\T1_Tools\mms_scripts\plink.exe -batch mms@10.110.19.107 -pw %password% "/home/mms/bin/MineView-Session.sh"
echo:
echo:
REM echo Downloading Latest Log File
REM echo:
REM pscp mms@10.110.19.107:/home/mms/Desktop/MineView-Session/MineView-%date:~10,4%-%date:~7,2%-%date:~4,2%* .
pause