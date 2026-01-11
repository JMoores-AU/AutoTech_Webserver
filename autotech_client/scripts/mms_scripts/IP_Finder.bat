@echo off
echo Welcome Embedded Info Utility
echo:
set /p password="Enter Password: "
cls
:loop
echo:
echo:
set /p ip_address=Enter Equipment Name (CAPS) or PTXC IP Address: 
C:AutoTech_Clientplink.exe -t mms@10.110.19.107 -pw %password% "/home/mms/bin/remote_check/Random/MySQL/ip_export.sh %ip_address%"
echo:
goto loop

