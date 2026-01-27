@echo off
:: ============================================
:: AutoTech Service Uninstaller
:: ============================================

setlocal
title AutoTech Service Uninstaller

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
echo   AUTOTECH SERVICE UNINSTALLER
echo ============================================
echo.

:: Check if service exists
sc query AutoTech >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [INFO] AutoTech service is not installed.
    echo.
    pause
    exit /b 0
)

:: Show current status
echo Current service status:
sc query AutoTech | findstr "STATE"
echo.

set /p confirm="Remove AutoTech service? (Y/N): "
if /i not "%confirm%"=="Y" (
    echo.
    echo Uninstall cancelled.
    pause
    exit /b 0
)

echo.
echo [1/2] Stopping service...
sc stop AutoTech >nul 2>&1
timeout /t 3 /nobreak >nul

sc query AutoTech | findstr "STOPPED" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] Service stopped
) else (
    echo [WARNING] Service may still be running
)
echo.

echo [2/2] Removing service...
sc delete AutoTech
if %ERRORLEVEL% EQU 0 (
    echo [OK] Service removed successfully!
    echo.
    echo AutoTech service has been uninstalled.
    echo The executable file was not deleted.
) else (
    echo [ERROR] Failed to remove service!
    echo.
    echo Try:
    echo   1. Close any AutoTech windows
    echo   2. Run this script again
    echo   3. Restart Windows if needed
)

echo.
pause
exit /b 0
