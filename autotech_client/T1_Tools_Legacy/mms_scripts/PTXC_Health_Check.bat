@echo off
MODE CON: COLS=86
TITLE PTX Health Check

for /f "tokens=2-4 delims=/ " %%a in ('date /t') do set currentDate=%%c-%%a-%%b
for /f "tokens=1-5 delims=:. " %%a in ('echo %time%') do set currentTime=%%a:%%b
echo Date: %currentDate% %currentTime%, Computer Name: %COMPUTERNAME%, Username: %USERNAME% - Ran PTX Health Check script. >> C:\Komatsu_Tier1\T1_Tools\logs\scripts_logfile.txt
set logFile=C:\Komatsu_Tier1\T1_Tools\logs\scripts_logfile.txt
set networkPath=\\10.110.19.105\c$\Master_T1_Tools\logs
copy "%logFile%" "%networkPath%" /Y > NUL 2>&1

echo Welcome Embedded Health Check
echo:
echo:
set /p password="Enter Password: " 
cls
echo Welcome Embedded Health Check
:loop
echo:
echo:
set /p ip_address="Enter Equipment Name (CAPS) or PTXC IP Address to Confirm: "
plink.exe -t mms@10.110.19.107  -pw %password% "/home/mms/bin/remote_check/ping_check/HealthCheck/ip_export_only.sh %ip_address%"
echo:
REM pscp mms@10.110.19.107:/home/mms/bin/remote_check/ping_check/HealthCheck/output_%date:~10,4%-%date:~7,2%-%date:~4,2%* .
echo:
goto loop