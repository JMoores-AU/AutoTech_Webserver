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

REM ========================================
REM Standard MMS Script Handler
REM ========================================

REM Create display name: remove .bat and replace underscores with spaces
set "DISPLAY_NAME=!SCRIPT_NAME:.bat=!"
set "DISPLAY_NAME=!DISPLAY_NAME:_= !"

REM Full path to script
set "SCRIPT_PATH=C:\AutoTech_Client\mms_scripts\!SCRIPT_NAME!"

REM Check if script exists
if not exist "!SCRIPT_PATH!" (
    title MMS Scripts - Error
    echo ERROR: Script not found: !SCRIPT_PATH!
    echo.
    echo Listing files in mms_scripts:
    dir "C:\AutoTech_Client\mms_scripts\*.bat" /b
    echo.
    pause
    exit /b 1
)

REM Launch in new window with password environment variable
REM Title format: "MMS Scripts - Script Name"
start "MMS Scripts - !DISPLAY_NAME!" cmd /k "set password=komatsu && cd /d C:\AutoTech_Client\mms_scripts && !SCRIPT_NAME!"
goto :END

REM ========================================
REM T1 Tools Launch Handler
REM ========================================
:LAUNCH_T1_TOOLS
REM Try USB drive first (E:\T1_Tools_Legacy\bin\T1_Tools.bat)
if exist "E:\T1_Tools_Legacy\bin\T1_Tools.bat" (
    start "T1 Tools" cmd /k "cd /d E:\T1_Tools_Legacy\bin && T1_Tools.bat"
    goto :END
)

REM Try dev environment
if exist "C:\AutoTech_WebApps\T1_Tools_Web-1\legacy_batch_scripts\bin\T1_Tools.bat" (
    start "T1 Tools" cmd /k "cd /d C:\AutoTech_WebApps\T1_Tools_Web-1\legacy_batch_scripts\bin && T1_Tools.bat"
    goto :END
)

REM Not found - show error
title T1 Tools - Error
echo ERROR: T1_Tools.bat not found!
echo.
echo Searched locations:
echo   E:\T1_Tools_Legacy\bin\T1_Tools.bat
echo   C:\AutoTech_WebApps\T1_Tools_Web-1\legacy_batch_scripts\bin\T1_Tools.bat
echo.
pause
goto :END

:END
endlocal
