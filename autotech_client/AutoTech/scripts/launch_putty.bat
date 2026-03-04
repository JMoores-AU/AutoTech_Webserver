@echo off
REM AutoTech - PuTTY Launcher
REM Parses autotech-ssh:// URI and launches PuTTY

setlocal enabledelayedexpansion

REM Get the URI from command line argument
set "URI=%~1"

REM Remove autotech-ssh:// prefix
set "URI=!URI:autotech-ssh://=!"

REM Parse format: user@host:port or user@host or host
REM Example: mms@10.110.19.107:22

REM Extract username if present
for /f "tokens=1,2 delims=@" %%a in ("!URI!") do (
    set "USER=%%a"
    set "HOSTPORT=%%b"
)

REM If no @ found, whole thing is host
if "!HOSTPORT!"=="" (
    set "HOSTPORT=!URI!"
    set "USER="
)

REM Extract port if present
for /f "tokens=1,2 delims=:" %%a in ("!HOSTPORT!") do (
    set "HOST=%%a"
    set "PORT=%%b"
)

REM Default port if not specified
if "!PORT!"=="" set "PORT=22"

REM Locate AutoTech client on USB (tools stay on USB) - first match wins
set "PUTTY_CMD="
for %%D in (D E F G H I J K L M N O P Q R S T U V W X Y Z) do (
    if not defined PUTTY_CMD if exist "%%D:\AutoTech\tools\putty.exe" set "PUTTY_CMD=%%D:\AutoTech\tools\putty.exe"
)

if "%PUTTY_CMD%"=="" (
    echo [ERROR] putty.exe not found. Please plug in the AT_Client USB drive.
    echo Looking for: X:\AutoTech\tools\putty.exe
    pause
    exit /b 1
)

if "!USER!"=="" (
    start "" "!PUTTY_CMD!" -ssh "!HOST!" -P "!PORT!"
) else (
    start "" "!PUTTY_CMD!" -ssh "!USER!@!HOST!" -P "!PORT!"
)

endlocal
