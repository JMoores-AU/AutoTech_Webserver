@echo off
:: ============================================================
:: AutoTech Client Setup (legacy installer — runs from USB X:\AutoTech\scripts\)
:: This installer copies tools locally so they work WITHOUT USB plugged in.
::
:: For the recommended USB-portable installer, run:
::   X:\Install_AutoTech_Client.bat  (at USB root)
:: ============================================================

setlocal enabledelayedexpansion
title AutoTech Client Setup (Local Install)

echo ========================================
echo AutoTech Client Setup
echo ========================================
echo.
echo This will install tools locally to C:\AutoTech_Client\
echo so they work without the USB plugged in.
echo.
echo Installed:
echo   - PuTTY (SSH client)
echo   - WinSCP (SFTP/SCP client)
echo   - VNC Viewer (Remote desktop)
echo   - plink.exe (for SSH scripting)
echo   - MMS launch scripts
echo   - Custom URI handlers
echo.
pause

:: Check for admin rights
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: This installer must be run as Administrator!
    echo Right-click and select "Run as administrator"
    pause
    exit /b 1
)

echo.
echo [1/5] Creating installation folder...
if not exist "C:\AutoTech_Client"          mkdir "C:\AutoTech_Client"
if not exist "C:\AutoTech_Client\scripts"  mkdir "C:\AutoTech_Client\scripts"
if not exist "C:\AutoTech_Client\temp"     mkdir "C:\AutoTech_Client\temp"

echo [2/5] Copying tools...
:: Copy tools from USB X:\AutoTech\tools\ (one level up from this scripts folder)
xcopy /Y /Q "%~dp0..\tools\*.*" "C:\AutoTech_Client\" 2>nul
if exist "C:\AutoTech_Client\plink.exe"     echo   [OK] plink.exe
if exist "C:\AutoTech_Client\putty.exe"     echo   [OK] putty.exe
if exist "C:\AutoTech_Client\WinSCP.exe"    echo   [OK] WinSCP.exe
if exist "C:\AutoTech_Client\vncviewer.exe" echo   [OK] vncviewer.exe

echo [3/5] Copying launcher scripts...
xcopy /Y /Q "%~dp0launch_*.bat" "C:\AutoTech_Client\scripts\" 2>nul
echo   [OK] Launch scripts copied

echo [4/5] Copying MMS legacy scripts...
if not exist "C:\AutoTech_Client\mms_scripts" mkdir "C:\AutoTech_Client\mms_scripts"
xcopy /Y /Q "%~dp0mms_scripts\*.bat" "C:\AutoTech_Client\mms_scripts\" 2>nul
echo   [OK] MMS scripts copied

echo [5/5] Registering custom URI handlers...
regedit /s "%~dp0register_uri_handlers.reg"
echo   [OK] URI handlers registered

echo.
echo Creating uninstaller...
(
echo @echo off
echo echo Uninstalling AutoTech Client...
echo reg delete "HKEY_CLASSES_ROOT\autotech-ssh" /f ^>nul 2^>^&1
echo reg delete "HKEY_CLASSES_ROOT\autotech-sftp" /f ^>nul 2^>^&1
echo reg delete "HKEY_CLASSES_ROOT\autotech-vnc" /f ^>nul 2^>^&1
echo reg delete "HKEY_CLASSES_ROOT\autotech-script" /f ^>nul 2^>^&1
echo rmdir /s /q "C:\AutoTech_Client"
echo echo Uninstall complete.
echo pause
) > "C:\AutoTech_Client\Uninstall.bat"

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo Tools installed locally to: C:\AutoTech_Client\
echo URI handlers registered:
echo   - autotech-ssh://
echo   - autotech-sftp://
echo   - autotech-vnc://
echo   - autotech-script://
echo.
echo To uninstall, run: C:\AutoTech_Client\Uninstall.bat
echo.
pause
endlocal
