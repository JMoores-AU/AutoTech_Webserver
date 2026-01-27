@echo off
title MMS Scripts - Linux Health Check
echo:
echo Linux Performance and Usage Check (PTX/Servers/ESTOP_Machines)
echo:
REM Check if password is already set (from launcher)
if not defined password (
    title MMS Scripts - Linux Health Check - Enter Password
    set /p password="Enter Password: "
) else (
    echo Password auto-filled from AutoTech launcher
)
cls
echo:
:loop
title MMS Scripts - Linux Health Check - Enter IP
echo:
echo Linux Performance and Usage Check (PTX/Servers/ESTOP_Machines)
echo:
echo FrontRunner - 10.110.19.16
echo:
echo Estop-Coal - 10.110.19.33
echo:
echo Estop-North - 10.110.19.32
echo:
echo Estop-Central - 10.110.19.27
echo:
echo Estop-South - 10.110.19.30
echo:
echo Estop-B2 - 10.110.19.26 - (Support Desk)
echo:
echo Estop-B3 - 10.110.19.101 - (Failover Desk)
echo:
title MMS Scripts - Linux Health Check - Running...
C:\AutoTech_Client\plink.exe -t mms@10.110.19.107  -pw %password% "/home/mms/bin/remote_check/Random/LinuxCheck/For_Support/Check_Exe.sh"
title MMS Scripts - Linux Health Check - Complete
echo:
REM pscp mms@10.110.19.107:/home/mms/bin/remote_check/ping_check/HealthCheck/output_%date:~10,4%-%date:~7,2%-%date:~4,2%* .
goto loop