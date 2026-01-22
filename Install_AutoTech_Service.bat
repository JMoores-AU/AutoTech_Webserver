@echo off
:: ============================================
:: AutoTech Service Installer
:: ============================================
:: Uses built-in Windows sc.exe (no external tools)
:: Installs AutoTech.exe as a Windows service
:: ============================================

setlocal enabledelayedexpansion
title AutoTech Service Installer

:: Check for admin rights
net session >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ============================================
    echo   ADMINISTRATOR PRIVILEGES REQUIRED
    echo ============================================
    echo.
    echo Please right-click this file and select:
    echo   "Run as administrator"
    echo.
    pause
    exit /b 1
)

cls
echo ============================================
echo   AUTOTECH SERVICE INSTALLER
echo ============================================
echo.

:: Check if service already exists
sc query AutoTech >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo Service "AutoTech" already exists.
    echo.
    set /p remove="Remove existing service first? (Y/N): "
    if /i "!remove!"=="Y" (
        echo.
        echo Stopping service...
        sc stop AutoTech >nul 2>&1
        timeout /t 2 /nobreak >nul
        echo Removing service...
        sc delete AutoTech
        if !ERRORLEVEL! EQU 0 (
            echo [OK] Old service removed
        ) else (
            echo [ERROR] Failed to remove service
            pause
            exit /b 1
        )
        echo.
        timeout /t 2 /nobreak >nul
    ) else (
        echo Installation cancelled.
        pause
        exit /b 0
    )
)

:: Find AutoTech.exe
set "EXE_PATH="

:: Check common locations
if exist "E:\AutoTech.exe" set "EXE_PATH=E:\AutoTech.exe"
if exist "C:\AutoTech\AutoTech.exe" set "EXE_PATH=C:\AutoTech\AutoTech.exe"
if exist "%~dp0AutoTech.exe" set "EXE_PATH=%~dp0AutoTech.exe"
if exist "%~dp0dist\AutoTech.exe" set "EXE_PATH=%~dp0dist\AutoTech.exe"

if "%EXE_PATH%"=="" (
    echo [ERROR] AutoTech.exe not found!
    echo.
    echo Searched locations:
    echo   E:\AutoTech.exe
    echo   C:\AutoTech\AutoTech.exe
    echo   %~dp0AutoTech.exe
    echo   %~dp0dist\AutoTech.exe
    echo.
    set /p EXE_PATH="Enter full path to AutoTech.exe: "
    if not exist "!EXE_PATH!" (
        echo [ERROR] File not found: !EXE_PATH!
        pause
        exit /b 1
    )
)

echo.
echo ============================================
echo  INSTALLING SERVICE
echo ============================================
echo.
echo Executable: %EXE_PATH%
echo Service Name: AutoTech
echo Display Name: AutoTech Dashboard
echo Start Type: Automatic
echo.

:: Create the service
echo [1/3] Creating service...
sc create AutoTech binPath= "%EXE_PATH%" start= auto DisplayName= "AutoTech Dashboard"
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to create service!
    echo.
    echo This may be because:
    echo   - Service already exists (use sc delete AutoTech first)
    echo   - Path contains invalid characters
    echo   - Insufficient permissions
    echo.
    pause
    exit /b 1
)
echo [OK] Service created
echo.

:: Set description
echo [2/3] Setting description...
sc description AutoTech "AutoTech Mining Equipment Dashboard - Web interface for PTX uptime, IP finder, and legacy tools"
if %ERRORLEVEL% EQU 0 (
    echo [OK] Description set
) else (
    echo [WARNING] Could not set description
)
echo.

:: Configure failure actions (restart on failure)
echo [3/3] Configuring failure recovery...
sc failure AutoTech reset= 86400 actions= restart/60000/restart/60000/restart/60000
if %ERRORLEVEL% EQU 0 (
    echo [OK] Auto-restart configured
) else (
    echo [WARNING] Could not set failure recovery
)
echo.

:: Ask to start service now
echo ============================================
echo  INSTALLATION COMPLETE!
echo ============================================
echo.
set /p start="Start the AutoTech service now? (Y/N): "
if /i "%start%"=="Y" (
    echo.
    echo Starting service...
    sc start AutoTech
    if !ERRORLEVEL! EQU 0 (
        echo [OK] Service started successfully!
        echo.
        echo AutoTech is now running at: http://localhost:8888
    ) else (
        echo [ERROR] Failed to start service!
        echo.
        echo Check Event Viewer for details:
        echo   Windows Logs ^> Application
        echo.
        echo Common issues:
        echo   - Port 8888 already in use
        echo   - Missing dependencies
        echo   - Database file locked
    )
) else (
    echo.
    echo Service installed but not started.
    echo To start manually: sc start AutoTech
)

echo.
echo ============================================
echo  MANAGEMENT COMMANDS
echo ============================================
echo.
echo Start:   sc start AutoTech
echo Stop:    sc stop AutoTech
echo Status:  sc query AutoTech
echo Remove:  sc delete AutoTech
echo.
echo Service runs even when no user is logged in.
echo Access dashboard at: http://localhost:8888
echo.
pause
exit /b 0
