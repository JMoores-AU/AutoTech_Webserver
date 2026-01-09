@echo off
setlocal ENABLEDELAYEDEXPANSION

REM Handle internal function calls
if "%1"=="run_server_internal" goto run_server_internal
if "%1"=="build_exe_internal" goto build_exe_internal

:main_menu
cls
echo ================================================================
echo                    T1 TOOLS - MANAGER
echo ================================================================
echo.
echo [1] RUN WEB SERVER (Start T1 Tools on http://localhost:8888)
echo [2] BUILD EXECUTABLE (Create standalone .exe file)
echo [3] STOP SERVER (Stop any running T1 Tools server)
echo [4] RESTART SERVER (Stop and start server in new window)
echo [0] EXIT
echo.

choice /C 12340 /N /M "Select option (0-4): "
set "CHOICE=%ERRORLEVEL%"

if "%CHOICE%"=="1" goto launch_server
if "%CHOICE%"=="2" goto launch_build
if "%CHOICE%"=="3" goto stop_server
if "%CHOICE%"=="4" goto restart_server
if "%CHOICE%"=="5" goto exit_script

goto main_menu

:launch_server
echo.
echo Opening T1 Tools Server in new window...
start "T1 Tools Server" cmd /c call "%~dp0%~nx0" run_server_internal
goto main_menu

:launch_build
echo.
echo Opening Build Executable in new window...
start "T1 Tools Build" cmd /c call "%~dp0%~nx0" build_exe_internal
echo Build started in separate window...
echo.
goto main_menu

:stop_server
echo.
echo ================================================================
echo                    STOPPING T1 TOOLS SERVER
echo ================================================================
echo.
echo Stopping any running T1 Tools servers...
taskkill /F /IM python.exe /T >nul 2>&1
taskkill /F /IM pythonw.exe /T >nul 2>&1
echo.
echo Server processes terminated.
echo Any running T1 Tools servers have been stopped.
echo.
pause
goto main_menu

:restart_server
echo.
echo ================================================================
echo                    RESTARTING T1 TOOLS SERVER
echo ================================================================
echo.
echo Stopping any existing servers...
taskkill /F /IM python.exe /T >nul 2>&1
taskkill /F /IM pythonw.exe /T >nul 2>&1
timeout /t 2 /nobreak >nul
echo.
echo Starting server in new window...
start "T1 Tools Server" cmd /c call "%~dp0%~nx0" run_server_internal
echo Server started in separate window.
echo.
pause
goto main_menu

REM ================================================================
REM                    INTERNAL FUNCTIONS
REM ================================================================

:run_server_internal
cls
echo ================================================================
echo                    STARTING T1 TOOLS SERVER
echo ================================================================
echo.

REM Find Python
set "PYTHON_CMD="
for %%p in (py python python3) do (
    if "!PYTHON_CMD!"=="" (
        %%p --version >nul 2>&1
        if not errorlevel 1 (
            set "PYTHON_CMD=%%p"
            echo Found Python: %%p
            %%p --version
        )
    )
)

if "!PYTHON_CMD!"=="" (
    echo ERROR: No Python found! Install Python and try again.
    pause
    goto main_menu
)

REM Check main.py exists
if not exist "main.py" (
    echo ERROR: main.py not found! Run this from your T1_Tools_Web directory.
    pause
    goto main_menu
)

REM Kill any existing servers
echo.
echo Stopping any existing servers...
taskkill /F /IM python.exe /T >nul 2>&1
taskkill /F /IM pythonw.exe /T >nul 2>&1

REM Install core packages directly
echo.
echo Installing/updating required packages...
!PYTHON_CMD! -m pip install --user Flask paramiko requests ping3 psutil flask-cors beautifulsoup4 --upgrade --quiet

REM Test if packages work
echo.
echo Testing packages...
!PYTHON_CMD! -c "import flask, paramiko, requests, ping3, psutil; from bs4 import BeautifulSoup; print('All packages working!')" 2>nul
if errorlevel 1 (
    echo WARNING: Some packages may not be installed correctly.
    echo Continuing anyway - Flask might still work.
)

REM Create missing templates if they don't exist
if not exist "templates" mkdir "templates"
if not exist "static" mkdir "static"

if not exist "templates\login.html" (
    echo Creating basic login template...
    (
    echo ^<!DOCTYPE html^>
    echo ^<html^>^<head^>^<title^>T1 Tools Login^</title^>^</head^>
    echo ^<body^>^<h1^>T1 Tools Login^</h1^>
    echo ^<form method="POST"^>
    echo Password: ^<input type="password" name="password"^>
    echo ^<button type="submit"^>Login^</button^>
    echo ^</form^>^</body^>^</html^>
    ) > "templates\login.html"
)

if not exist "templates\enhanced_index.html" (
    echo Creating basic dashboard template...
    (
    echo ^<!DOCTYPE html^>
    echo ^<html^>^<head^>^<title^>T1 Tools Dashboard^</title^>^</head^>
    echo ^<body^>^<h1^>T1 Tools Web Dashboard^</h1^>
    echo ^<p^>Network Status: {{ network_status }}^</p^>
    echo ^<p^>Gateway IP: {{ gateway_ip }}^</p^>
    echo ^<p^>Timestamp: {{ timestamp }}^</p^>
    echo ^<a href="/run/IP Finder"^>IP Finder^</a^>
    echo ^<a href="/logout"^>Logout^</a^>
    echo ^</body^>^</html^>
    ) > "templates\enhanced_index.html"
)

if not exist "templates\ip_finder.html" (
    echo Creating basic IP Finder template...
    (
    echo ^<!DOCTYPE html^>
    echo ^<html^>^<head^>^<title^>IP Finder^</title^>^</head^>
    echo ^<body^>^<h1^>IP Finder^</h1^>
    echo ^<p^>Gateway IP: {{ gateway_ip }}^</p^>
    echo ^<p^>Timestamp: {{ timestamp }}^</p^>
    echo ^<a href="/"^>Back to Dashboard^</a^>
    echo ^</body^>^</html^>
    ) > "templates\ip_finder.html"
)

REM Start the server
echo.
echo ================================================================
echo  T1 TOOLS WEB SERVER STARTING
echo ================================================================
echo  URL: http://localhost:8888
echo  Password: komatsu
echo  Press Ctrl+C to stop and return to menu
echo ================================================================
echo.

!PYTHON_CMD! main.py

echo.
echo Server stopped.
echo Press any key to close this window...
pause
exit

:build_exe_internal
cls
echo ================================================================
echo                    BUILDING EXECUTABLE
echo ================================================================
echo.

REM Find Python
set "PYTHON_CMD="
for %%p in (py python python3) do (
    if "!PYTHON_CMD!"=="" (
        %%p --version >nul 2>&1
        if not errorlevel 1 (
            set "PYTHON_CMD=%%p"
            echo Found Python: %%p
            %%p --version
        )
    )
)

if "!PYTHON_CMD!"=="" (
    echo ERROR: No Python found!
    pause
    goto main_menu
)

REM Check files exist
if not exist "main.py" (
    echo ERROR: main.py not found!
    pause
    goto main_menu
)

if not exist "templates" (
    echo ERROR: templates folder not found! Run option 1 first to create templates.
    pause
    goto main_menu
)

REM Install PyInstaller if needed
echo.
echo Checking PyInstaller...
!PYTHON_CMD! -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo Installing PyInstaller...
    !PYTHON_CMD! -m pip install --user pyinstaller
    if errorlevel 1 (
        echo ERROR: Failed to install PyInstaller!
        pause
        goto main_menu
    )
)

REM ================== VERSION MANAGEMENT =================
echo.
echo ================================================================
echo                    VERSION MANAGEMENT
echo ================================================================

REM Get current version
set "VERSION=1.0.0"
if exist "VERSION.txt" (
    for /f %%v in (VERSION.txt) do set "VERSION=%%v"
)

echo Current version: !VERSION!
echo.
echo [0] Keep current version (!VERSION!)
echo [1] Bump PATCH  (x.y.Z)
echo [2] Bump MINOR  (x.Y.0)
echo [3] Bump MAJOR  (X.0.0)
echo [4] Enter custom version (x.y.z)
echo.

choice /C 01234 /N /M "Select version option (0-4): "
set "VER_CHOICE=%ERRORLEVEL%"

if "%VER_CHOICE%"=="1" goto ver_keep
if "%VER_CHOICE%"=="2" goto ver_patch
if "%VER_CHOICE%"=="3" goto ver_minor
if "%VER_CHOICE%"=="4" goto ver_major
if "%VER_CHOICE%"=="5" goto ver_custom

:ver_keep
set "NEW_VERSION=!VERSION!"
goto ver_done

:ver_patch
for /f "tokens=1-3 delims=." %%A in ("!VERSION!") do (
    set "MAJ=%%A"
    set "MIN=%%B"
    set "PAT=%%C"
)
if not defined MAJ set "MAJ=1"
if not defined MIN set "MIN=0"
if not defined PAT set "PAT=0"
set /a PAT=PAT+1
set "NEW_VERSION=!MAJ!.!MIN!.!PAT!"
goto ver_done

:ver_minor
for /f "tokens=1-3 delims=." %%A in ("!VERSION!") do (
    set "MAJ=%%A"
    set "MIN=%%B"
    set "PAT=%%C"
)
if not defined MAJ set "MAJ=1"
if not defined MIN set "MIN=0"
set /a MIN=MIN+1
set "PAT=0"
set "NEW_VERSION=!MAJ!.!MIN!.!PAT!"
goto ver_done

:ver_major
for /f "tokens=1-3 delims=." %%A in ("!VERSION!") do (
    set "MAJ=%%A"
    set "MIN=%%B"
    set "PAT=%%C"
)
if not defined MAJ set "MAJ=1"
set /a MAJ=MAJ+1
set "MIN=0"
set "PAT=0"
set "NEW_VERSION=!MAJ!.!MIN!.!PAT!"
goto ver_done

:ver_custom
echo.
set /p NEW_VERSION=Enter version (x.y.z): 
echo.!NEW_VERSION!| findstr /r "\." >nul || (echo Invalid format. Using current version.& set "NEW_VERSION=!VERSION!")
for /f "tokens=1-3 delims=." %%A in ("!NEW_VERSION!") do set "CHK3=%%C"
if not defined CHK3 (
    echo Invalid format. Using current version.
    set "NEW_VERSION=!VERSION!"
)
goto ver_done

:ver_done
echo !NEW_VERSION!>VERSION.txt
echo Using version: !NEW_VERSION!
set "VERSION=!NEW_VERSION!"
echo.

REM Clean old builds
echo.
echo Cleaning old builds...
if exist "build" rmdir /s /q "build" >nul 2>&1
if exist "dist" rmdir /s /q "dist" >nul 2>&1
if exist "*.spec" del "*.spec" >nul 2>&1

REM Build executable
echo.
echo Building T1_Tools_Web_v!VERSION!.exe...
echo This may take a few minutes...
echo.

!PYTHON_CMD! -m PyInstaller --name "T1_Tools_Web_v!VERSION!" --onefile --noconfirm --add-data "templates;templates" --add-data "static;static" --hidden-import flask_cors --hidden-import requests --hidden-import psutil --hidden-import ping3 --hidden-import paramiko main.py

echo.
if exist "dist\T1_Tools_Web_v!VERSION!.exe" (
    for %%A in ("dist\T1_Tools_Web_v!VERSION!.exe") do set "EXE_SIZE=%%~zA"
    echo ================================================================
    echo                    BUILD SUCCESS!
    echo ================================================================
    echo File: dist\T1_Tools_Web_v!VERSION!.exe
    echo Size: !EXE_SIZE! bytes
    echo.
    echo This executable can run on Windows machines without Python.
    echo Just copy the .exe file and run it - it will start the web server
    echo on http://localhost:8888 with password: komatsu
    echo ================================================================
) else (
    echo ================================================================
    echo                    BUILD FAILED!
    echo ================================================================
    echo Check the error messages above for details.
    echo Common issues:
    echo - Missing dependencies (run option 1 first)
    echo - Antivirus blocking PyInstaller
    echo - Insufficient disk space
    echo ================================================================
)

pause
echo.
echo Closing build window and returning to main menu...
timeout /t 2 /nobreak >nul
exit

REM ================================================================
REM                           EXIT
REM ================================================================

:exit_script
echo.
echo Thanks for using T1 Tools Manager!
pause
exit /b 0

endlocal
