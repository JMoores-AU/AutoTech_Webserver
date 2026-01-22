@echo off
title MMS Scripts - MineView Sessions
echo Live MineView Sessions
echo:
echo:
REM Check if password is already set (from launcher)
if not defined password (
    title MMS Scripts - MineView Sessions - Enter Password
    set /p password="Enter Password: "
) else (
    echo Password auto-filled from AutoTech launcher
)
cls
title MMS Scripts - MineView Sessions - Loading...
echo Live MineView Sessions
echo:
echo:
C:\AutoTech_Client\plink.exe mms@10.110.19.107 -pw %password% "/home/mms/bin/MineView-Session.sh"
title MMS Scripts - MineView Sessions - Complete
echo:
echo:
REM echo Downloading Latest Log File
REM echo:
REM pscp mms@10.110.19.107:/home/mms/Desktop/MineView-Session/MineView-%date:~10,4%-%date:~7,2%-%date:~4,2%* .
pause