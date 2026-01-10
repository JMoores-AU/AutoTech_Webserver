@echo off
REM T1 Tools - PuTTY Launcher
REM Parses t1putty:// URI and launches PuTTY

setlocal enabledelayedexpansion

REM Get the URI from command line argument
set "URI=%~1"

REM Remove t1putty:// prefix
set "URI=!URI:t1putty://=!"

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

REM Build PuTTY command
set "PUTTY_CMD=C:\T1_Tools_Client\putty.exe"

if "!USER!"=="" (
    start "" "!PUTTY_CMD!" -ssh "!HOST!" -P "!PORT!"
) else (
    start "" "!PUTTY_CMD!" -ssh "!USER!@!HOST!" -P "!PORT!"
)

endlocal
