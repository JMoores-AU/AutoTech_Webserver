@echo off
REM T1 Tools Client Setup Installer
REM Installs portable tools and registers custom URI handlers

echo ========================================
echo T1 Tools Client Setup
echo ========================================
echo.
echo This will install:
echo - PuTTY (SSH client)
echo - WinSCP (SFTP/SCP client)
echo - VNC Viewer (Remote desktop)
echo - Custom URI handlers
echo.
echo Installation folder: C:\T1_Tools_Client\
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
echo [1/4] Creating installation folder...
if not exist "C:\T1_Tools_Client" mkdir "C:\T1_Tools_Client"
if not exist "C:\T1_Tools_Client\scripts" mkdir "C:\T1_Tools_Client\scripts"

echo [2/4] Copying tools and scripts...
xcopy /Y /Q "%~dp0..\tools\*.*" "C:\T1_Tools_Client\"
xcopy /Y /Q "%~dp0*.bat" "C:\T1_Tools_Client\scripts\"

echo [3/4] Registering custom URI handlers...
regedit /s "%~dp0register_uri_handlers.reg"

echo [4/4] Creating uninstaller...
(
echo @echo off
echo echo Uninstalling T1 Tools Client...
echo reg delete "HKEY_CLASSES_ROOT\t1putty" /f
echo reg delete "HKEY_CLASSES_ROOT\t1winscp" /f
echo reg delete "HKEY_CLASSES_ROOT\t1vnc" /f
echo rmdir /s /q "C:\T1_Tools_Client"
echo echo Uninstall complete.
echo pause
) > "C:\T1_Tools_Client\Uninstall.bat"

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo You can now use the T1 Tools web interface to launch:
echo - PuTTY connections (t1putty://)
echo - WinSCP connections (t1winscp://)
echo - VNC connections (t1vnc://)
echo.
echo To uninstall, run: C:\T1_Tools_Client\Uninstall.bat
echo.
pause
