@echo off
mode con: cols=130 
echo:
set /p password="Enter Password: " 
cls
echo:
echo SpeedLimit Data at %date% %time%
echo:
echo:
%PLINK_PATH% -t -noagent mms@10.110.19.107  -pw %password% "/home/mms/bin/remote_check/Random/MySQL/LASL_export.sh"
echo:
pause