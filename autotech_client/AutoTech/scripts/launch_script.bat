@echo off
REM AutoTech - Batch Script Launcher
REM Parses autotech-script:// URI and launches batch file

setlocal enabledelayedexpansion

REM Get the URI from command line argument
set "URI=%~1"

REM Remove autotech-script:// prefix
set "URI=!URI:autotech-script://=!"

REM Remove any trailing slashes or extra characters
set "URI=!URI:/=!"

REM Extract script name from URI
set "SCRIPT_NAME=!URI!"

REM ========================================
REM Special handler for T1 Tools
REM ========================================
if /i "!SCRIPT_NAME!"=="t1-tools" goto :LAUNCH_T1_TOOLS

REM Locate AutoTech client on USB (tools and scripts stay on USB) - first match wins
set "USB_BASE="
for %%D in (D E F G H I J K L M N O P Q R S T U V W X Y Z) do (
    if not defined USB_BASE if exist "%%D:\AutoTech\scripts\mms_scripts\!SCRIPT_NAME!" set "USB_BASE=%%D:\AutoTech"
)

if "%USB_BASE%"=="" (
    echo [ERROR] AutoTech USB not found. Please plug in the AT_Client USB drive.
    echo Looking for: X:\AutoTech\scripts\mms_scripts\!SCRIPT_NAME!
    pause
    exit /b 1
)

set "MMS_SCRIPTS=%USB_BASE%\scripts\mms_scripts"

REM ========================================
REM Standard MMS Script Handler
REM ========================================

REM Create display name: remove .bat and replace underscores with spaces
set "DISPLAY_NAME=!SCRIPT_NAME:.bat=!"
set "DISPLAY_NAME=!DISPLAY_NAME:_= !"

REM Full path to script
set "SCRIPT_PATH=%MMS_SCRIPTS%\!SCRIPT_NAME!"

REM Check if script exists
if not exist "!SCRIPT_PATH!" (
    title MMS Scripts - Error
    echo ERROR: Script not found: !SCRIPT_PATH!
    echo.
    echo Listing files in mms_scripts:
    dir "!MMS_SCRIPTS!\*.bat" /b 2>nul
    echo.
    pause
    exit /b 1
)

REM Launch in new window with password environment variable
REM Title format: "MMS Scripts - Script Name"
start "MMS Scripts - !DISPLAY_NAME!" cmd /k "set password=komatsu && cd /d %MMS_SCRIPTS% && !SCRIPT_NAME!"
goto :END

REM ========================================
REM T1 Tools Launch Handler
REM ========================================
:LAUNCH_T1_TOOLS
REM Scan USB drives D-Z for T1_Tools_Legacy (first match wins, no C: drive)
for %%D in (D E F G H I J K L M N O P Q R S T U V W X Y Z) do (
    if exist "%%D:\T1_Tools_Legacy\bin\T1_Tools.bat" (
        start "T1 Tools" cmd /k "cd /d %%D:\T1_Tools_Legacy\bin && T1_Tools.bat"
        goto :END
    )
)

title T1 Tools - Error
echo ERROR: T1_Tools.bat not found!
echo.
echo Plug in USB containing T1_Tools_Legacy\bin\T1_Tools.bat
echo.
pause
goto :END

:END
endlocal
