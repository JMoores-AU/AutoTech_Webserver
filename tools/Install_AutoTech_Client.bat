@echo off
:: ============================================
:: AutoTech Client Installer (Batch)
:: ============================================
:: No Python or dependencies required
:: Works on any Windows PC
:: ============================================

setlocal enabledelayedexpansion
title AutoTech Client Installer

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
echo   AUTOTECH CLIENT INSTALLER
echo ============================================
echo.
echo This will install AutoTech Client to:
echo   C:\AutoTech_Client
echo.
echo Components:
echo   - Custom URI handlers (installed locally)
echo   - Lightweight launch scripts
echo   - NOTE: Tools/scripts stay on USB (AutoTech\autotech_client, frontrunner folder)
echo.
set /p confirm="Continue with installation? (Y/N): "
if /i not "%confirm%"=="Y" (
    echo.
    echo Installation cancelled.
    pause
    exit /b 0
)

:: Get the directory where this installer is located (USB root X:\)
set "INSTALLER_DIR=%~dp0"
set "INSTALL_PATH=C:\AutoTech_Client"

echo.
echo ============================================
echo  INSTALLING...
echo ============================================
echo.

:: Step 1: Create installation directory
echo [1/4] Creating installation directory...
if exist "%INSTALL_PATH%" (
    echo   Removing old installation...
    rmdir /s /q "%INSTALL_PATH%" 2>nul
)
mkdir "%INSTALL_PATH%"
if not exist "%INSTALL_PATH%" (
    echo   [ERROR] Failed to create directory!
    pause
    exit /b 1
)
echo   [OK] Created %INSTALL_PATH%

:: Create temp subfolder
mkdir "%INSTALL_PATH%\temp" 2>nul
echo   [OK] Created temp folder
echo.

:: Step 2: Copy launch scripts only (portable tools stay on USB)
echo [2/4] Installing minimal launchers...
if exist "%INSTALL_PATH%\scripts" rmdir /s /q "%INSTALL_PATH%\scripts" 2>nul
mkdir "%INSTALL_PATH%\scripts"
if exist "%INSTALLER_DIR%AutoTech\scripts\launch_*.bat" (
    copy /Y "%INSTALLER_DIR%AutoTech\scripts\launch_*.bat" "%INSTALL_PATH%\scripts\" >nul 2>&1
    echo   [OK] Copied launch scripts from USB
) else (
    echo   [WARNING] Launch scripts not found at %INSTALLER_DIR%AutoTech\scripts\
)

if exist "%INSTALLER_DIR%AutoTech\scripts\VERSION" (
    copy /Y "%INSTALLER_DIR%AutoTech\scripts\VERSION" "%INSTALL_PATH%\" >nul 2>&1
)
echo   [OK] Launchers installed; all tools/scripts run from X:\AutoTech\
echo.

:: Step 3: Register URI handlers
echo [3/4] Registering custom URI handlers...

:: autotech-ssh://
reg add "HKCR\autotech-ssh" /ve /d "URL:AutoTech SSH Protocol" /f >nul 2>&1
reg add "HKCR\autotech-ssh" /v "URL Protocol" /d "" /f >nul 2>&1
reg add "HKCR\autotech-ssh\shell\open\command" /ve /d "\"%INSTALL_PATH%\scripts\launch_putty.bat\" \"%%1\"" /f >nul 2>&1
echo   [OK] autotech-ssh://

:: autotech-sftp://
reg add "HKCR\autotech-sftp" /ve /d "URL:AutoTech SFTP Protocol" /f >nul 2>&1
reg add "HKCR\autotech-sftp" /v "URL Protocol" /d "" /f >nul 2>&1
reg add "HKCR\autotech-sftp\shell\open\command" /ve /d "\"%INSTALL_PATH%\scripts\launch_winscp.bat\" \"%%1\"" /f >nul 2>&1
echo   [OK] autotech-sftp://

:: autotech-vnc://
reg add "HKCR\autotech-vnc" /ve /d "URL:AutoTech VNC Protocol" /f >nul 2>&1
reg add "HKCR\autotech-vnc" /v "URL Protocol" /d "" /f >nul 2>&1
reg add "HKCR\autotech-vnc\shell\open\command" /ve /d "\"%INSTALL_PATH%\scripts\launch_vnc.bat\" \"%%1\"" /f >nul 2>&1
echo   [OK] autotech-vnc://

:: autotech-script://
reg add "HKCR\autotech-script" /ve /d "URL:AutoTech Script Protocol" /f >nul 2>&1
reg add "HKCR\autotech-script" /v "URL Protocol" /d "" /f >nul 2>&1
reg add "HKCR\autotech-script\shell\open\command" /ve /d "\"%INSTALL_PATH%\scripts\launch_script.bat\" \"%%1\"" /f >nul 2>&1
echo   [OK] autotech-script://
echo.

:: Step 4: Create Start Menu shortcuts (optional)
echo [4/4] Creating Start Menu shortcuts...
set "START_MENU=%ProgramData%\Microsoft\Windows\Start Menu\Programs\AutoTech Client"
mkdir "%START_MENU%" 2>nul

:: Create shortcuts using PowerShell (available on all modern Windows)
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%START_MENU%\T1 Legacy Tools.lnk'); $s.TargetPath = '%INSTALL_PATH%\mms_scripts\T1_Tools.bat'; $s.WorkingDirectory = '%INSTALL_PATH%\mms_scripts'; $s.Save()" 2>nul
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%START_MENU%\IP Finder.lnk'); $s.TargetPath = '%INSTALL_PATH%\mms_scripts\IP_Finder.bat'; $s.WorkingDirectory = '%INSTALL_PATH%\mms_scripts'; $s.Save()" 2>nul

if exist "%START_MENU%\T1 Legacy Tools.lnk" (
    echo   [OK] Start Menu shortcuts created
) else (
    echo   [INFO] Shortcuts skipped (PowerShell not available)
)
echo.

:: Success!
echo ============================================
echo   INSTALLATION COMPLETE!
echo ============================================
echo.
echo AutoTech Client installed to:
echo   %INSTALL_PATH%
echo.
echo Start Menu shortcuts:
echo   - T1 Legacy Tools
echo   - IP Finder
echo.
echo Custom URI handlers registered:
echo   - autotech-ssh://
echo   - autotech-sftp://
echo   - autotech-vnc://
echo   - autotech-script://
echo.
echo IMPORTANT: Keep USB plugged in!
echo All tools run from USB at:
echo   - X:\AutoTech\tools\ (PuTTY/WinSCP/VNC)
echo   - X:\AutoTech\scripts\mms_scripts\ (MMS scripts)
echo   - X:\T1_Tools_Legacy\ (T1 Tools)
echo   - X:\frontrunnerV3-3.7.0-076-full\ (playback)
echo.
echo You can now use the AutoTech web interface!
echo.
pause
exit /b 0
