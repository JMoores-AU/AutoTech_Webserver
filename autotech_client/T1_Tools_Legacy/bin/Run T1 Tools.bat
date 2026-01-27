@echo off
REM ========================================
REM T1 TOOLS - USB PORTABLE LAUNCHER
REM ========================================
REM This script runs from USB and doesn't require network sync

REM Get the USB drive letter where this script is located
set "SCRIPTDIR=%~dp0"
set "USBFOLDER=%SCRIPTDIR%T1_Tools_Legacy\bin"

REM Check if T1_Tools_Legacy exists on USB
if not exist "%USBFOLDER%\T1_Tools.bat" (
    echo ERROR: T1_Tools.bat not found!
    echo Expected location: %USBFOLDER%\T1_Tools.bat
    echo.
    echo Please ensure the USB structure is:
    echo USB:\T1_Tools_Legacy\bin\T1_Tools.bat
    pause
    exit /b 1
)

REM Log the launch (optional)
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do set currentDate=%%c-%%a-%%b
for /f "tokens=1-5 delims=:. " %%a in ('echo %time%') do set currentTime=%%a:%%b

REM Create logs directory if it doesn't exist
if not exist "%USBFOLDER%\logs" mkdir "%USBFOLDER%\logs"

echo Date: %currentDate% %currentTime%, Computer: %COMPUTERNAME%, User: %USERNAME% - Opened T1 Tools >> "%USBFOLDER%\logs\access.log"

REM Launch T1_Scripts.ps1 (PowerShell GUI)
echo Launching T1 Tools GUI...
start powershell -WindowStyle Normal -ExecutionPolicy Bypass -File "%USBFOLDER%\T1_Scripts.ps1"

exit /b 0