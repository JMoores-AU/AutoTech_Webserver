@echo off

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