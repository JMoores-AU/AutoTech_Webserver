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
echo   - Portable tools (PuTTY, WinSCP, VNC)
echo   - T1 Legacy MMS Scripts
echo   - Custom URI handlers
echo.
set /p confirm="Continue with installation? (Y/N): "
if /i not "%confirm%"=="Y" (
    echo.
    echo Installation cancelled.
    pause
    exit /b 0
)

:: Get the directory where this installer is located
set "INSTALLER_DIR=%~dp0"
set "INSTALL_PATH=C:\AutoTech_Client"

echo.
echo ============================================
echo  INSTALLING...
echo ============================================
echo.

:: Step 1: Create installation directory
echo [1/5] Creating installation directory...
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
echo.

:: Step 2: Copy portable tools and version file
echo [2/5] Copying portable tools...
if not exist "%INSTALLER_DIR%tools" (
    echo   [ERROR] tools folder not found!
    echo   Make sure tools folder is next to this installer.
    pause
    exit /b 1
)
copy /Y "%INSTALLER_DIR%tools\*.exe" "%INSTALL_PATH%\" >nul 2>&1

:: Copy VERSION file for update tracking
if exist "%INSTALLER_DIR%VERSION" (
    copy /Y "%INSTALLER_DIR%VERSION" "%INSTALL_PATH%\" >nul 2>&1
    echo   [OK] Copied portable tools + VERSION
) else (
    echo   [OK] Copied portable tools
)
echo.

:: Step 3: Copy scripts
echo [3/5] Copying scripts...
mkdir "%INSTALL_PATH%\scripts" 2>nul
mkdir "%INSTALL_PATH%\mms_scripts" 2>nul

if exist "%INSTALLER_DIR%scripts\*.bat" (
    copy /Y "%INSTALLER_DIR%scripts\*.bat" "%INSTALL_PATH%\scripts\" >nul 2>&1
)
if exist "%INSTALLER_DIR%scripts\mms_scripts\*.bat" (
    copy /Y "%INSTALLER_DIR%scripts\mms_scripts\*.bat" "%INSTALL_PATH%\mms_scripts\" >nul 2>&1
)
echo   [OK] Copied scripts
echo.

:: Step 4: Register URI handlers
echo [4/5] Registering custom URI handlers...

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

:: Step 5: Create Start Menu shortcuts (optional)
echo [5/5] Creating Start Menu shortcuts...
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
echo You can now use the AutoTech web interface!
echo.
pause
exit /b 0
