@echo off
echo AVI-PTX Watchdog Deployment Process
echo:
echo:
set /p password="Enter Password: "
cls
echo AVI-PTX Watchdog Deployment Process...

:menu
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
set /p ip_address=Enter PTXC IP Address: 
%PLINK_PATH% -t mms@10.110.19.107 -pw %password% "echo $(date): Initiated from %COMPUTERNAME% by %USERNAME% for %ip_address%. >> /home/mms/bin/remote_check/AVI_Watchdog/Report.txt; /home/mms/bin/remote_check/AVI_Watchdog/watchdog_setup_single.sh %ip_address%"
echo:
echo:
goto menu

:callDifferentScript
set /p ip_address=Enter PTX10 IP Address: 
%PLINK_PATH% -t mms@10.110.19.107 -pw %password% "echo $(date): Initiated from %COMPUTERNAME% by %USERNAME% for %ip_address%. >> /home/mms/bin/remote_check/AVI_Watchdog/Report.txt; /home/mms/bin/remote_check/AVI_Watchdog/watchdog_setup_single_PTX10.sh %ip_address%"
echo:
echo:
goto menu
