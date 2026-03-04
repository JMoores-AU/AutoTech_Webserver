@echo off
REM AutoTech - WinSCP Launcher
REM Parses autotech-sftp:// URI and launches WinSCP

setlocal enabledelayedexpansion

REM Get the URI from command line argument
set "URI=%~1"

REM Remove autotech-sftp:// prefix
set "URI=!URI:autotech-sftp://=!"

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

REM Locate AutoTech client on USB (tools stay on USB) - first match wins
set "WINSCP_CMD="
for %%D in (D E F G H I J K L M N O P Q R S T U V W X Y Z) do (
    if not defined WINSCP_CMD if exist "%%D:\AutoTech\tools\WinSCP.exe" set "WINSCP_CMD=%%D:\AutoTech\tools\WinSCP.exe"
)

if "%WINSCP_CMD%"=="" (
    echo [ERROR] WinSCP.exe not found. Please plug in the AT_Client USB drive.
    echo Looking for: X:\AutoTech\tools\WinSCP.exe
    pause
    exit /b 1
)

if "!USER!"=="" (
    start "" "!WINSCP_CMD!" "scp://!HOST!:!PORT!"
) else if "!PASS!"=="" (
    start "" "!WINSCP_CMD!" "scp://!USER!@!HOST!:!PORT!"
) else (
    start "" "!WINSCP_CMD!" "scp://!USER!:!PASS!@!HOST!:!PORT!"
)

endlocal
