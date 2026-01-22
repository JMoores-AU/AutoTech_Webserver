@echo off
title MMS Scripts - AVI Watchdog Deploy
echo AVI-PTX Watchdog Deployment Process
echo:
echo:
REM Check if password is already set (from launcher)
if not defined password (
    title MMS Scripts - AVI Watchdog Deploy - Enter Password
    set /p password="Enter Password: "
) else (
    echo Password auto-filled from AutoTech launcher
)
cls
echo AVI-PTX Watchdog Deployment Process...

:menu
title MMS Scripts - AVI Watchdog Deploy - Select Option
echo:
echo Please choose an option:
echo 1. PTXC
echo 2. PTX10
set /p choice="Enter your choice (1/2): "

if "%choice%"=="1" (
    echo:
    call :callCurrentScript
) else if "%choice%"=="2" (
    echo:
    call :callDifferentScript
) else (
    echo Invalid choice. Please try again.
    goto menu
)

exit /b

:callCurrentScript
title MMS Scripts - AVI Watchdog Deploy - Enter PTXC IP
set /p ip_address=Enter PTXC IP Address:
title MMS Scripts - AVI Watchdog Deploy - Deploying...
C:\AutoTech_Client\plink.exe -t mms@10.110.19.107 -pw %password% "echo $(date): Initiated from %COMPUTERNAME% by %USERNAME% for %ip_address%. >> /home/mms/bin/remote_check/AVI_Watchdog/Report.txt; /home/mms/bin/remote_check/AVI_Watchdog/watchdog_setup_single.sh %ip_address%"
title MMS Scripts - AVI Watchdog Deploy - Complete
echo:
echo:
goto menu

:callDifferentScript
title MMS Scripts - AVI Watchdog Deploy - Enter PTX10 IP
set /p ip_address=Enter PTX10 IP Address:
title MMS Scripts - AVI Watchdog Deploy - Deploying...
C:\AutoTech_Client\plink.exe -t mms@10.110.19.107 -pw %password% "echo $(date): Initiated from %COMPUTERNAME% by %USERNAME% for %ip_address%. >> /home/mms/bin/remote_check/AVI_Watchdog/Report.txt; /home/mms/bin/remote_check/AVI_Watchdog/watchdog_setup_single_PTX10.sh %ip_address%"
title MMS Scripts - AVI Watchdog Deploy - Complete
echo:
echo:
goto menu
