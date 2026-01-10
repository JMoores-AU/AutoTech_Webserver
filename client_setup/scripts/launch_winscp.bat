@echo off
REM T1 Tools - WinSCP Launcher
REM Parses t1winscp:// URI and launches WinSCP

setlocal enabledelayedexpansion

REM Get the URI from command line argument
set "URI=%~1"

REM Remove t1winscp:// prefix
set "URI=!URI:t1winscp://=!"

REM Parse format: user:password@host:port or user@host or host
REM Example: mms:password@10.110.19.107:22

REM Extract credentials and host
for /f "tokens=1,2 delims=@" %%a in ("!URI!") do (
    set "CREDS=%%a"
    set "HOSTPORT=%%b"
)

REM If no @ found, whole thing is host
if "!HOSTPORT!"=="" (
    set "HOSTPORT=!URI!"
    set "CREDS="
)

REM Extract username and password from credentials
for /f "tokens=1,2 delims=:" %%a in ("!CREDS!") do (
    set "USER=%%a"
    set "PASS=%%b"
)

REM Extract port from hostport
for /f "tokens=1,2 delims=:" %%a in ("!HOSTPORT!") do (
    set "HOST=%%a"
    set "PORT=%%b"
)

REM Default port if not specified
if "!PORT!"=="" set "PORT=22"

REM Build WinSCP connection string
set "WINSCP_CMD=C:\T1_Tools_Client\WinSCP.exe"

if "!USER!"=="" (
    start "" "!WINSCP_CMD!" "scp://!HOST!:!PORT!"
) else if "!PASS!"=="" (
    start "" "!WINSCP_CMD!" "scp://!USER!@!HOST!:!PORT!"
) else (
    start "" "!WINSCP_CMD!" "scp://!USER!:!PASS!@!HOST!:!PORT!"
)

endlocal
