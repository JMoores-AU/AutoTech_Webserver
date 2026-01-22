@echo off
mode con: cols=100
title Perf/Usage Check

for /f "tokens=2-4 delims=/ " %%a in ('date /t') do set currentDate=%%c-%%a-%%b
for /f "tokens=1-5 delims=:. " %%a in ('echo %time%') do set currentTime=%%a:%%b
echo Date: %currentDate% %currentTime%, Computer Name: %COMPUTERNAME%, Username: %USERNAME% - Ran Linux Health Check script. >> C:\Komatsu_Tier1\T1_Tools\logs\scripts_logfile.txt
set logFile=C:\Komatsu_Tier1\T1_Tools\logs\scripts_logfile.txt
set networkPath=\\10.110.19.105\c$\Master_T1_Tools\logs
copy "%logFile%" "%networkPath%" /Y > NUL 2>&1

echo Linux Performance and Usage Check (PTX/Servers/ESTOP_Machines)
echo:
echo:
set /p password="Enter Password: " 
cls
echo Linux Performance and Usage Check (PTX/Servers/ESTOP_Machines)
:loop
echo:
echo:
C:\Komatsu_Tier1\T1_Tools\mms_scripts\plink.exe -batch -t mms@10.110.19.107  -pw %password% "/home/mms/bin/remote_check/Random/LinuxCheck/For_Support/Check_Exe.sh"
echo:
REM pscp mms@10.110.19.107:/home/mms/bin/remote_check/ping_check/HealthCheck/output_%date:~10,4%-%date:~7,2%-%date:~4,2%* .
goto loop