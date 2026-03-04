@echo off
title MMS Scripts - Start VNC
setlocal enabledelayedexpansion

echo Welcome Embedded VNC Utility
echo.
echo.

:: Check if password is already set (from launcher)
if not defined password (
    title MMS Scripts - Start VNC - Enter Password
    set /p password="Enter Password: "
) else (
    echo Password auto-filled from AutoTech launcher
)

cls
echo Welcome Embedded VNC Utility
echo.
echo.

:: Get IP
title MMS Scripts - Start VNC - Enter IP
set /p ip_address=Enter PTXC IP Address:
title MMS Scripts - Start VNC - Connecting...

:: ============================================================
:: Locate plink.exe
:: Priority: 1) local C:\AutoTech_Client\  2) USB X:\AutoTech\tools\  3) USB X:\T1_Tools_Legacy\mms_scripts\
:: ============================================================
set "PLINK_CMD="
if exist "C:\AutoTech_Client\plink.exe" set "PLINK_CMD=C:\AutoTech_Client\plink.exe"
if "!PLINK_CMD!"=="" (
    for %%D in (E D F G H I J K L M N O P Q R S T U V W X Y Z) do (
        if "!PLINK_CMD!"=="" if exist "%%D:\AutoTech\tools\plink.exe" set "PLINK_CMD=%%D:\AutoTech\tools\plink.exe"
    )
)
if "!PLINK_CMD!"=="" (
    for %%D in (E D F G H I J K L M N O P Q R S T U V W X Y Z) do (
        if "!PLINK_CMD!"=="" if exist "%%D:\T1_Tools_Legacy\mms_scripts\plink.exe" set "PLINK_CMD=%%D:\T1_Tools_Legacy\mms_scripts\plink.exe"
    )
)
if "!PLINK_CMD!"=="" (
    echo [ERROR] plink.exe not found.
    echo   Checked: C:\AutoTech_Client\plink.exe
    echo   Scanned USB drives for X:\AutoTech\tools\plink.exe
    echo   Scanned USB drives for X:\T1_Tools_Legacy\mms_scripts\plink.exe
    echo.
    echo   Please plug in the AutoTech USB drive and try again.
    pause
    exit /b 1
)

:: Run VNC setup script on MMS server
"!PLINK_CMD!" -batch -t mms@10.110.19.107 -pw !password! "/home/mms/bin/remote_check/TempTool/VNC/Check_Exe.sh !ip_address!"
echo.
title MMS Scripts - Start VNC - Complete

:: ============================================================
:: Locate vncviewer.exe
:: Priority: 1) local C:\AutoTech_Client\  2) USB X:\AutoTech\tools\
:: ============================================================
set "VNC_CMD="
if exist "C:\AutoTech_Client\vncviewer.exe" set "VNC_CMD=C:\AutoTech_Client\vncviewer.exe"
if "!VNC_CMD!"=="" (
    for %%D in (E D F G H I J K L M N O P Q R S T U V W X Y Z) do (
        if "!VNC_CMD!"=="" if exist "%%D:\AutoTech\tools\vncviewer.exe" set "VNC_CMD=%%D:\AutoTech\tools\vncviewer.exe"
    )
)
if "!VNC_CMD!"=="" (
    echo [ERROR] vncviewer.exe not found.
    echo   Checked: C:\AutoTech_Client\vncviewer.exe
    echo   Scanned USB drives for X:\AutoTech\tools\vncviewer.exe
    echo.
    echo   Please plug in the AutoTech USB drive and try again.
    pause
    exit /b 1
)

start "" "!VNC_CMD!" !ip_address!:0

endlocal
