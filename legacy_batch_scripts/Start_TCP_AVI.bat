@echo off

echo Start TCPDump on AVI
echo:
echo:
set /p password="Enter Password: " 
cls
echo Start TCPDump on AVI
echo:
echo:
%PLINK_PATH% -t mms@10.110.19.107 -pw %password%  "/home/mms/bin/remote_check/for_equipment/SCP/AVI_TCP.sh"
echo:
TIMEOUT 10