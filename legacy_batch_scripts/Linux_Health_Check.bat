@echo off

echo Linux Performance and Usage Check (PTX/Servers/ESTOP_Machines)
echo:
echo:
set /p password="Enter Password: " 
cls
echo Linux Performance and Usage Check (PTX/Servers/ESTOP_Machines)
:loop
echo:
echo:
%PLINK_PATH% -t mms@10.110.19.107  -pw %password% "/home/mms/bin/remote_check/Random/LinuxCheck/For_Support/Check_Exe.sh"
echo:
REM pscp mms@10.110.19.107:/home/mms/bin/remote_check/ping_check/HealthCheck/output_%date:~10,4%-%date:~7,2%-%date:~4,2%* .
goto loop