@echo off
REM AutoTech - VNC Viewer Launcher
REM Parses autotech-vnc:// URI and launches VNC Viewer

setlocal enabledelayedexpansion

REM Get the URI from command line argument
set "URI=%~1"

REM Remove autotech-vnc:// prefix
set "URI=!URI:autotech-vnc://=!"

REM Parse format: host:port or host:display or host
REM Example: 10.110.21.87:5900 or 10.110.21.87:0 or 10.110.21.87

REM Extract host and port/display
for /f "tokens=1,2 delims=:" %%a in ("!URI!") do (
    set "HOST=%%a"
    set "PORTDISP=%%b"
)

REM Trim trailing path/slash from host and port
for /f "tokens=1 delims=/" %%x in ("!HOST!") do set "HOST=%%x"
for /f "tokens=1 delims=/" %%x in ("!PORTDISP!") do set "PORTDISP=%%x"
for /f "tokens=1 delims=\ " %%x in ("!PORTDISP!") do set "PORTDISP=%%x"

REM If no : found, whole thing is host
if "!PORTDISP!"=="" (
    set "HOST=!URI!"
    set "PORTDISP=0"
)

REM Validate numeric port/display
echo "!PORTDISP!" | findstr /R "^[0-9][0-9]*$" >nul
if errorlevel 1 set "PORTDISP=0"

REM Locate AutoTech client on USB (preferred) or local
set "VNC_CMD="
for %%D in (E D F G H I J K L M N O P Q R S T U V W X Y Z C) do (
    if exist "%%D:\AutoTech\tools\vncviewer_5.3.2.exe" set "VNC_CMD=%%D:\AutoTech\tools\vncviewer_5.3.2.exe"
)
if "%VNC_CMD%"=="" if exist "C:\AutoTech\tools\vncviewer_5.3.2.exe" set "VNC_CMD=C:\AutoTech\tools\vncviewer_5.3.2.exe"

if "%VNC_CMD%"=="" (
    echo [ERROR] vncviewer_5.3.2.exe not found. Plug in the AutoTech USB and reinstall client.
    pause
    exit /b 1
)

REM Always use display syntax host:display (default display 0)
start "" "!VNC_CMD!" "!HOST!:!PORTDISP!"

endlocal
