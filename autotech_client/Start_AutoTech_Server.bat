@echo off
:: ============================================
:: AutoTech Server Launcher (USB)
:: ============================================
:: Launches AutoTech.exe from this USB drive.
:: The server uses the USB root as BASE_DIR so
:: all databases are stored on the USB drive.
:: Keep USB plugged in while server is running.
:: ============================================

setlocal enabledelayedexpansion
title AutoTech Server (USB)

set "USB_DIR=%~dp0"
set "SERVER_EXE=%USB_DIR%AutoTech.exe"

if not exist "%SERVER_EXE%" (
    echo ============================================
    echo   AutoTech.exe NOT FOUND
    echo ============================================
    echo.
    echo Expected: %SERVER_EXE%
    echo.
    echo Rebuild the USB using BUILD_WEBSERVER.bat:
    echo   Option 11 - Build Executable
    echo   Option 18 - Build Client USB
    echo.
    pause
    exit /b 1
)

echo ============================================
echo   AUTOTECH SERVER - USB MODE
echo ============================================
echo.
echo Executable: %SERVER_EXE%
echo Web interface: http://localhost:8888
echo.
echo Starting server...
echo ============================================
echo.

:: Launch server — BASE_DIR will be the USB root
start "" "%SERVER_EXE%"

:: Give the server a moment to start, then open browser
timeout /t 3 /nobreak >nul
start "" "http://localhost:8888"

echo Server launched. Dashboard opening in browser.
echo.
echo NOTE: Keep USB plugged in while server is running.
echo       All databases are stored on this USB drive.
echo.
pause
endlocal
