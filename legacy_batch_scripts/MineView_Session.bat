@echo off

echo Live MineView Sessions
echo:
echo:
set /p password="Enter Password: " 
cls
echo Live MineView Sessions
echo:
echo:
plink.exe mms@10.110.19.107 -pw %password% "/home/mms/bin/MineView-Session.sh"
echo:
echo:
REM echo Downloading Latest Log File
REM echo:
REM pscp mms@10.110.19.107:/home/mms/Desktop/MineView-Session/MineView-%date:~10,4%-%date:~7,2%-%date:~4,2%* .
pause