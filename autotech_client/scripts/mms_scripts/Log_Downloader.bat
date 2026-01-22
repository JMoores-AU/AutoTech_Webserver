@echo off
title MMS Scripts - Log Downloader
echo FrontRunner Logs Downloader (Including Broken Logs) - FRMASTER/ESTOPs/PTX (Max 6 Hours Allowed)
echo:
echo:
REM Check if password is already set (from launcher)
if not defined password (
    title MMS Scripts - Log Downloader - Enter Password
    set /p password="Enter Password: "
) else (
    echo Password auto-filled from AutoTech launcher
)
cls
:menu
title MMS Scripts - Log Downloader - Enter Details
echo FrontRunner Logs Downloader (Including Broken Logs) - FRMASTER/ESTOPs/PTX (Max 6 Hours Allowed)
echo:
echo:
set /p ip="Enter the IP address of the Remote Host: "
set /p user="Enter the Username of the Remote Host: "
REM set /p "pass=Enter the Password of the Remote Host: "
title MMS Scripts - Log Downloader - Running...
C:\AutoTech_Client\plink.exe -t mms@10.110.19.107 -pw %password% "echo $(date): Initiated from %COMPUTERNAME% by %USERNAME%. >> /home/mms/bin/remote_check/TempTool/DOWNLOAD/Report.txt; /home/mms/bin/remote_check/TempTool/DOWNLOAD/Log_Get.sh %ip% %user%"
echo:
echo:
echo Downloading Latest Log File Found. Press Enter...
title MMS Scripts - Log Downloader - Downloading...
for /f "tokens=* delims=" %%a in ('C:\AutoTech_Client\plink.exe mms@10.110.19.107 -pw %password% "ls -t /home/mms/bin/remote_check/TempTool/DOWNLOAD/%ip%*.zip 2> error.log | head -1"') do set OUTPUT=%%a
if "%OUTPUT:~-4%"==".zip" (
echo %OUTPUT%
C:\AutoTech_Client\pscp.exe -pw %password% mms@10.110.19.107:"%OUTPUT%" %USERPROFILE%\Downloads\
title MMS Scripts - Log Downloader - Complete
start ""  "%USERPROFILE%\Downloads\"
echo:
echo:
goto menu
) else (
echo:
echo:
cls
goto menu
)