@echo off
REM AutoTech Client Setup Installer
REM Installs portable tools and registers custom URI handlers

echo ========================================
echo AutoTech Client Setup
echo ========================================
echo.
echo This will install:
echo - PuTTY (SSH client)
echo - WinSCP (SFTP/SCP client)
echo - VNC Viewer (Remote desktop)
echo - T1 Legacy MMS Scripts
echo - Custom URI handlers
echo.
echo Installation folder: C:\AutoTech_Client\
echo.
pause

REM Check for admin rights
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: This installer must be run as Administrator!
    echo Right-click and select "Run as administrator"
    pause
    exit /b 1
)

echo.
echo [1/5] Creating installation folder...
if not exist "C:\AutoTech_Client" mkdir "C:\AutoTech_Client"
if not exist "C:\AutoTech_Client\scripts" mkdir "C:\AutoTech_Client\scripts"
if not exist "C:\AutoTech_Client\mms_scripts" mkdir "C:\AutoTech_Client\mms_scripts"

echo [2/5] Copying tools...
xcopy /Y /Q "%~dp0..\tools\*.*" "C:\AutoTech_Client\"

echo [3/5] Copying launcher scripts...
xcopy /Y /Q "%~dp0*.bat" "C:\AutoTech_Client\scripts\"

echo [4/5] Copying MMS legacy scripts...
xcopy /Y /Q "%~dp0mms_scripts\*.bat" "C:\AutoTech_Client\mms_scripts\"

echo [5/5] Registering custom URI handlers...
regedit /s "%~dp0register_uri_handlers.reg"

echo.
echo Creating uninstaller...
(
echo @echo off
echo echo Uninstalling AutoTech Client...
echo reg delete "HKEY_CLASSES_ROOT\autotech-ssh" /f
echo reg delete "HKEY_CLASSES_ROOT\autotech-sftp" /f
echo reg delete "HKEY_CLASSES_ROOT\autotech-vnc" /f
echo rmdir /s /q "C:\AutoTech_Client"
echo echo Uninstall complete.
echo pause
) > "C:\AutoTech_Client\Uninstall.bat"

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo You can now use the AutoTech web interface to launch:
echo - PuTTY connections (autotech-ssh://)
echo - WinSCP connections (autotech-sftp://)
echo - VNC connections (autotech-vnc://)
echo.
echo To uninstall, run: C:\AutoTech_Client\Uninstall.bat
echo.
pause
