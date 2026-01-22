@echo off
title MMS Scripts - AVI MM2 Reboot
echo You are about to Reboot AVI Radio and MM2!!!
echo:
echo:
REM Check if password is already set (from launcher)
if not defined password (
    title MMS Scripts - AVI MM2 Reboot - Enter Password
    set /p password="Enter Password: "
) else (
    echo Password auto-filled from AutoTech launcher
)
cls
:loop
title MMS Scripts - AVI MM2 Reboot - Enter IP
echo:
echo You are about to Reboot AVI Radio and MM2!!!
echo:
echo:
set /p ip_address=Enter PTXC IP Address:
title MMS Scripts - AVI MM2 Reboot - Rebooting...
C:\AutoTech_Client\plink.exe -batch -t mms@10.110.19.107 -pw %password%  "echo $(date): Initiated from  %COMPUTERNAME% by %USERNAME% for %ip_address%. >> /home/mms/bin/remote_check/TempTool/MM2/Report.txt;/home/mms/bin/remote_check/TempTool/MM2/Check_Exe.sh %ip_address%"
title MMS Scripts - AVI MM2 Reboot - Complete
echo:
echo:
echo:
goto loop
pause
