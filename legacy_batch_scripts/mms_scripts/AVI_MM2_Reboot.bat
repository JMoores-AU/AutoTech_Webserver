@echo off
MODE CON: COLS=85
TITLE AVI/MM2 Reboot

for /f "tokens=2-4 delims=/ " %%a in ('date /t') do set currentDate=%%c-%%a-%%b
for /f "tokens=1-5 delims=:. " %%a in ('echo %time%') do set currentTime=%%a:%%b
echo Date: %currentDate% %currentTime%, Computer Name: %COMPUTERNAME%, Username: %USERNAME% - Ran AVI/MM2 reboot script. >> C:\Komatsu_Tier1\T1_Tools\logs\scripts_logfile.txt
set logFile=C:\Komatsu_Tier1\T1_Tools\logs\scripts_logfile.txt
set networkPath=\\10.110.19.105\c$\Master_T1_Tools\logs
copy "%logFile%" "%networkPath%" /Y > NUL 2>&1

echo You are about to Reboot AVI Radio and MM2!!!
echo:
echo:
set /p password="Enter Password: " 
cls
:loop
echo You are about to Reboot AVI Radio and MM2!!!
echo:
echo:
set /p ip_address=Enter PTXC IP Address: 
C:\Komatsu_Tier1\T1_Tools\mms_scripts\plink.exe -batch -t mms@10.110.19.107 -pw %password%  "echo $(date): Initiated from  %COMPUTERNAME% by %USERNAME% for %ip_address%. >> /home/mms/bin/remote_check/TempTool/MM2/Report.txt;/home/mms/bin/remote_check/TempTool/MM2/Check_Exe.sh %ip_address%"
echo:
goto loop

