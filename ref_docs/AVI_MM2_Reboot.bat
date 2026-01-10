@echo off
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
C:\Komatsu_Tier1\Boxy_Adam\plink.exe -batch -t mms@10.110.19.107 -pw %password%  "echo $(date): Initiated from  %COMPUTERNAME% by %USERNAME% for %ip_address%. >> /home/mms/bin/remote_check/TempTool/MM2/Report.txt;/home/mms/bin/remote_check/TempTool/MM2/Check_Exe.sh %ip_address%"
echo:
echo:
echo:
goto loop
pause
