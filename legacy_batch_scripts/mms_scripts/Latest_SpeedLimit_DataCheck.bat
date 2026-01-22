@echo off
title Live LASL Report

for /f "tokens=2-4 delims=/ " %%a in ('date /t') do set currentDate=%%c-%%a-%%b
for /f "tokens=1-5 delims=:. " %%a in ('echo %time%') do set currentTime=%%a:%%b
echo Date: %currentDate% %currentTime%, Computer Name: %COMPUTERNAME%, Username: %USERNAME% - Ran Speed Limit data check script. >> C:\Komatsu_Tier1\T1_Tools\logs\scripts_logfile.txt
set logFile=C:\Komatsu_Tier1\T1_Tools\logs\scripts_logfile.txt
set networkPath=\\10.110.19.105\c$\Master_T1_Tools\logs
copy "%logFile%" "%networkPath%" /Y > NUL 2>&1

mode con: cols=130 
echo:
set /p password="Enter Password: " 
cls
echo:
echo SpeedLimit Data at %date% %time%
echo:
echo:
C:\Komatsu_Tier1\T1_Tools\mms_scripts\plink.exe -batch -t -noagent mms@10.110.19.107  -pw %password% "/home/mms/bin/remote_check/Random/MySQL/LASL_export.sh"
echo:
pause