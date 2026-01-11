@echo off
echo Welcome Embedded VNC Utility
echo:
echo:
set /p password="Enter Password: " 
cls
echo Welcome Embedded VNC Utility
echo:
echo:
set /p ip_address=Enter PTXC IP Address: 
C:\Komatsu_Tier1\Boxy_Adam\Adam_PTXC_VNC\C:AutoTech_Clientplink.exe -batch -t mms@10.110.19.107 -pw %password%  "/home/mms/bin/remote_check/TempTool/VNC/Check_Exe.sh %ip_address%"
echo:
start "" "C:\Komatsu_Tier1\Boxy_Adam\Adam_PTXC_VNC\vncviewer_5.3.2.exe" %ip_address%:0

