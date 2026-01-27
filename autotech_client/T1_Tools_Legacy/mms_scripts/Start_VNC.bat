@echo off
MODE CON: COLS=55 LINES=15
TITLE PTX VNC Session

echo Welcome Embedded VNC Utility
echo:
echo:
set /p password="Enter Password: " 
cls
echo Welcome Embedded VNC Utility
echo:
echo:
set /p ip_address=Enter PTXC IP Address: 
C:\Komatsu_Tier1\T1_Tools\mms_scripts\plink.exe -batch -t mms@10.110.19.107 -pw %password%  "/home/mms/bin/remote_check/TempTool/VNC/Check_Exe.sh %ip_address%"
echo:
start "" "C:\Komatsu_Tier1\T1_Tools\tools\VNC\vncviewer.exe" %ip_address%:0

