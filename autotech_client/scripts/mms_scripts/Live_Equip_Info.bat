@echo off
title MMS Scripts - Live Equipment Info
echo:
REM Check if password is already set (from launcher)
if not defined password (
    title MMS Scripts - Live Equipment Info - Enter Password
    set /p password="Enter Password: "
) else (
    echo Password auto-filled from AutoTech launcher
)
cls
title MMS Scripts - Live Equipment Info - Loading...
echo:
echo Live Equipment Info at %date% %time%
echo:
echo:
C:\AutoTech_Client\plink.exe -t -noagent mms@10.110.19.107  -pw %password% "/home/mms/bin/remote_check/for_equipment/OnlineCount/OnlineCount.sh"
title MMS Scripts - Live Equipment Info - Downloading...
echo:
pscp -pw %password% mms@10.110.19.107:/home/mms/bin/remote_check/for_equipment/OnlineCount/equip_list* .
title MMS Scripts - Live Equipment Info - Complete
pause