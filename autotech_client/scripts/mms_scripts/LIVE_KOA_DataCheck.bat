@echo off
mode con: cols=140 
echo:
set /p password="Enter Password: " 
cls
echo:
echo KOA Data at %date% %time%
echo:
echo:
C:AutoTech_Clientplink.exe -t -noagent mms@10.110.19.107  -pw %password% "/home/mms/bin/remote_check/Random/MySQL/table_export.sh"
echo:
REM pscp mms@10.110.19.107:/home/mms/bin/remote_check/Random/MySQL/detour* .
pause