@echo off
echo:
set /p password="Enter Password: " 
cls
echo:
echo Live Equipment Info at %date% %time%
echo:
echo:
%PLINK_PATH% -t -noagent mms@10.110.19.107  -pw %password% "/home/mms/bin/remote_check/for_equipment/OnlineCount/OnlineCount.sh"
echo:
pscp -pw %password% mms@10.110.19.107:/home/mms/bin/remote_check/for_equipment/OnlineCount/equip_list* .
pause