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

REM If no : found, whole thing is host
if "!PORTDISP!"=="" (
    set "HOST=!URI!"
    set "PORTDISP=0"
)

REM Build VNC Viewer command
set "VNC_CMD=C:\AutoTech_Client\vncviewer_5.3.2.exe"

REM VNC Viewer format: host::port or host:display
REM If port > 100, use ::port format, otherwise use :display
if !PORTDISP! GTR 100 (
    start "" "!VNC_CMD!" "!HOST!::!PORTDISP!"
) else (
    start "" "!VNC_CMD!" "!HOST!:!PORTDISP!"
)

endlocal
