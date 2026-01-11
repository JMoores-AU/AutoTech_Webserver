@echo off
echo Welcome Field Component Info Utility
echo:
set /p password="Enter Password: "
cls
echo Welcome Field Component Info Utility
:loop
echo:
echo:
set /p ip_address=Enter Equipment Name (CAPS): 
C:AutoTech_Clientplink.exe -t mms@10.110.19.107 -pw %password% "/home/mms/bin/remote_check/Random/MySQL/Component/site_export.sh %ip_address%"
echo:
goto loop

