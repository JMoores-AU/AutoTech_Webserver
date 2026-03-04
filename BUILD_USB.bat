@echo off
:: ============================================
:: AutoTech - Build Client USB Package
:: Option 18: Build USB (server + client tools, version-matched)
:: Called from BUILD_WEBSERVER.bat
:: ============================================
setlocal enabledelayedexpansion

cd /d "%~dp0"

cls
echo ============================================
echo  Build Client USB (autotech_client -^> USB root)
echo ============================================
echo.
echo This option creates a complete USB package with:
echo   - AutoTech.exe (server executable - run from USB)
echo   - Start_AutoTech_Server.bat (server launcher)
echo   - Install_AutoTech_Client.bat (client installer)
echo   - AutoTech\tools\ (putty, WinSCP, VNC, plink, pscp)
echo   - AutoTech\scripts\ (launch_*.bat scripts)
echo   - AutoTech\scripts\mms_scripts\ (MMS batch scripts)
echo   - VERSION file (server + client versions matched)
echo   - database\ (pre-populated databases)
echo   - Frontrunner playback tools
echo   - T1 Tools Legacy
echo   - CamStudio USB
echo.

:: Enumerate removable/fixed/remote (non-system) drives using PowerShell
:: DriveType 2=Removable, 3=Fixed, 4=Remote (includes RDP-redirected USB drives)
echo Scanning for USB drives (please wait)...
set "USB_DRIVE="
set "DRIVE_LIST="
for /f "usebackq delims=" %%D in (`powershell -NoLogo -NoProfile -Command "$sys=$env:SystemDrive; Get-CimInstance Win32_LogicalDisk | Where-Object { $_.DriveType -in 2,3,4 -and $_.DeviceID -ne $sys } | Select-Object -ExpandProperty DeviceID"`) do (
    set "DRIVE_LIST=!DRIVE_LIST! %%D"
    if not defined USB_DRIVE set "USB_DRIVE=%%D"
)

echo Available removable/fixed drives: %DRIVE_LIST%
if not defined USB_DRIVE (
    echo [ERROR] No removable/fixed drives detected. Plug in USB and retry.
    echo.
    pause
    exit /b 0
)

echo Detected default: %USB_DRIVE%
set /p USB_DRIVE_IN="Enter target drive letter (e.g. I) or press Enter to use %USB_DRIVE%: "
if not "%USB_DRIVE_IN%"=="" set "USB_DRIVE=%USB_DRIVE_IN%:"
if not "%USB_DRIVE:~-1%"==":" set "USB_DRIVE=%USB_DRIVE%:"

if not exist "%USB_DRIVE%\\" (
    echo [ERROR] Drive %USB_DRIVE% not found.
    pause
    exit /b 0
)

echo.
echo This will copy contents of autotech_client\ to %USB_DRIVE%\
echo (existing files will be updated; unique files on USB are kept).
set /p CONFIRM="Proceed? (Y/N): "
if /i not "%CONFIRM%"=="Y" (
    echo Cancelled.
    pause
    exit /b 0
)

:: Verify drive is still accessible
if not exist "%USB_DRIVE%\\" (
    echo [ERROR] Cannot access %USB_DRIVE%\
    pause
    exit /b 0
)

echo.
echo ============================================
echo  SYNCING CLIENT USB PACKAGE
echo ============================================
echo.
set "USB_OK=1"

:: [1/9] Copy VERSION from repo root to USB root (canonical version)
echo [1/9] Copying VERSION file...
if exist "VERSION" (
    copy /Y "VERSION" "%USB_DRIVE%\" >nul
    for /f %%v in ('type "VERSION"') do echo   [OK] VERSION %%v copied to USB root
) else (
    echo   [WARN] VERSION file not found at repo root
)
echo.

:: [2/9] Copy Install_AutoTech_Client.bat to USB root
echo [2/9] Copying installer...
if exist "autotech_client\Install_AutoTech_Client.bat" (
    copy /Y "autotech_client\Install_AutoTech_Client.bat" "%USB_DRIVE%\" >nul
    echo   [OK] Install_AutoTech_Client.bat
) else (
    echo   [ERROR] Install_AutoTech_Client.bat not found in autotech_client!
)
echo.

:: [3/9] Sync AutoTech folder (tools, scripts, mms_scripts, database)
echo [3/9] Syncing AutoTech folder (tools, scripts, database)...
if exist "autotech_client\AutoTech\" (
    where robocopy >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        robocopy "autotech_client\AutoTech" "%USB_DRIVE%\AutoTech" /E /COPY:DAT /R:2 /W:1 /NDL
    ) else (
        xcopy "autotech_client\AutoTech\*.*" "%USB_DRIVE%\AutoTech\" /E /I /Q /Y /D >nul
    )
    echo   [OK] AutoTech\ folder synced
    :: Verify key tools
    if exist "%USB_DRIVE%\AutoTech\tools\putty.exe" (
        echo        - tools\putty.exe
    ) else (
        echo        - [WARN] tools\putty.exe missing!
    )
    if exist "%USB_DRIVE%\AutoTech\tools\WinSCP.exe" (
        echo        - tools\WinSCP.exe
    ) else (
        echo        - [WARN] tools\WinSCP.exe missing!
    )
    if exist "%USB_DRIVE%\AutoTech\tools\vncviewer.exe" (
        echo        - tools\vncviewer.exe
    ) else (
        echo        - [WARN] tools\vncviewer.exe missing!
    )
    if exist "%USB_DRIVE%\AutoTech\scripts\launch_putty.bat" (
        echo        - scripts\launch_*.bat present
    ) else (
        echo        - [WARN] scripts\launch_*.bat missing!
    )
    if exist "%USB_DRIVE%\AutoTech\scripts\mms_scripts\T1_Tools.bat" (
        echo        - scripts\mms_scripts\ present
    ) else (
        echo        - [WARN] scripts\mms_scripts\ missing!
    )
) else (
    echo   [ERROR] autotech_client\AutoTech\ folder not found!
)
echo.

:: [4/9] Stamp server VERSION into AutoTech\scripts\VERSION so client+server versions always match
echo [4/9] Stamping server version into AutoTech\scripts\VERSION...
if exist "VERSION" (
    if exist "%USB_DRIVE%\AutoTech\scripts\" (
        copy /Y "VERSION" "%USB_DRIVE%\AutoTech\scripts\VERSION" >nul 2>&1
        echo   [OK] AutoTech\scripts\VERSION stamped
    ) else (
        echo   [WARN] USB\AutoTech\scripts\ not found - version stamp skipped
    )
) else (
    echo   [WARN] No VERSION file at repo root - version stamp skipped
)
echo.

:: [5/9] Sync Frontrunner playback folder
echo [5/9] Syncing Frontrunner playback tools...
if exist "autotech_client\frontrunnerV3-3.7.0-076-full\" (
    where robocopy >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        robocopy "autotech_client\frontrunnerV3-3.7.0-076-full" "%USB_DRIVE%\frontrunnerV3-3.7.0-076-full" /E /COPY:DAT /R:2 /W:1 /NDL
    ) else (
        xcopy "autotech_client\frontrunnerV3-3.7.0-076-full\*.*" "%USB_DRIVE%\frontrunnerV3-3.7.0-076-full\" /E /I /Q /Y /D >nul
    )
    echo   [OK] frontrunnerV3-3.7.0-076-full\ synced
) else (
    echo   [SKIP] frontrunnerV3-3.7.0-076-full\ not found (optional)
)
echo.

:: [6/9] Sync T1 Tools Legacy
echo [6/9] Syncing T1 Tools Legacy...
if exist "autotech_client\T1_Tools_Legacy\" (
    where robocopy >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        robocopy "autotech_client\T1_Tools_Legacy" "%USB_DRIVE%\T1_Tools_Legacy" /E /COPY:DAT /R:2 /W:1 /NDL
    ) else (
        xcopy "autotech_client\T1_Tools_Legacy\*.*" "%USB_DRIVE%\T1_Tools_Legacy\" /E /I /Q /Y /D >nul
    )
    echo   [OK] T1_Tools_Legacy\ synced
) else (
    echo   [SKIP] T1_Tools_Legacy\ not found (optional)
)
echo.

:: [7/9] Sync CamStudio USB
echo [7/9] Syncing CamStudio USB tools...
if exist "autotech_client\CamStudio_USB\" (
    where robocopy >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        robocopy "autotech_client\CamStudio_USB" "%USB_DRIVE%\CamStudio_USB" /E /COPY:DAT /R:2 /W:1 /NDL
    ) else (
        xcopy "autotech_client\CamStudio_USB\*.*" "%USB_DRIVE%\CamStudio_USB\" /E /I /Q /Y /D >nul
    )
    echo   [OK] CamStudio_USB\ synced
) else (
    echo   [SKIP] CamStudio_USB\ not found (optional)
)
echo.

:: [8/9] Sync AT Monitor
echo [8/9] Syncing AT Monitor...
if exist "autotech_client\AT Monitor V3.7.0\" (
    where robocopy >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        robocopy "autotech_client\AT Monitor V3.7.0" "%USB_DRIVE%\AT Monitor V3.7.0" /E /COPY:DAT /R:2 /W:1 /NDL
    ) else (
        xcopy "autotech_client\AT Monitor V3.7.0\*.*" "%USB_DRIVE%\AT Monitor V3.7.0\" /E /I /Q /Y /D >nul
    )
    echo   [OK] AT Monitor V3.7.0\ synced
) else (
    echo   [SKIP] AT Monitor V3.7.0\ not found (optional)
)
echo.

:: [9/9] Copy AutoTech.exe server executable and launcher to USB root
echo [9/9] Copying server executable and database...
if exist "dist\AutoTech.exe" (
    copy /Y "dist\AutoTech.exe" "%USB_DRIVE%\AutoTech.exe" >nul 2>&1
    if exist "%USB_DRIVE%\AutoTech.exe" (
        echo   [OK] AutoTech.exe copied
    ) else (
        echo   [ERROR] Failed to copy AutoTech.exe to USB
        set "USB_OK=0"
    )
) else (
    echo   [WARN] dist\AutoTech.exe not found - run option 11 ^(Build^) first
    echo   [WARN] USB will have client tools only, no server executable
)
if exist "autotech_client\Start_AutoTech_Server.bat" (
    copy /Y "autotech_client\Start_AutoTech_Server.bat" "%USB_DRIVE%\Start_AutoTech_Server.bat" >nul 2>&1
    echo   [OK] Start_AutoTech_Server.bat copied
)
:: Copy database folder to AutoTech\database\ (server resolves BASE_DIR\AutoTech\database\ on USB)
if exist "database\" (
    where robocopy >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        robocopy "database" "%USB_DRIVE%\AutoTech\database" /E /COPY:DAT /R:2 /W:1 /NDL /XF "*.pyc"
    ) else (
        if not exist "%USB_DRIVE%\AutoTech\database" mkdir "%USB_DRIVE%\AutoTech\database" 2>nul
        xcopy "database\*.*" "%USB_DRIVE%\AutoTech\database\" /E /I /Q /Y /D >nul
    )
    echo   [OK] database\ folder synced to AutoTech\database\
)
echo.

:: Final verification
echo ============================================
echo  VERIFYING USB PACKAGE
echo ============================================
echo.

if not exist "%USB_DRIVE%\Install_AutoTech_Client.bat" (
    echo [ERROR] Missing: Install_AutoTech_Client.bat
    set "USB_OK=0"
) else (
    echo [OK] Install_AutoTech_Client.bat
)

if not exist "%USB_DRIVE%\VERSION" (
    echo [WARN] Missing: VERSION
) else (
    for /f %%v in ('type "%USB_DRIVE%\VERSION"') do echo [OK] VERSION (%%v)
)

if not exist "%USB_DRIVE%\AutoTech\tools\putty.exe" (
    echo [ERROR] Missing: AutoTech\tools\putty.exe
    set "USB_OK=0"
) else (
    echo [OK] AutoTech\tools\ (putty, WinSCP, VNC, plink, pscp)
)

if not exist "%USB_DRIVE%\AutoTech\scripts\launch_putty.bat" (
    echo [ERROR] Missing: AutoTech\scripts\launch_*.bat
    set "USB_OK=0"
) else (
    echo [OK] AutoTech\scripts\ (launch scripts)
)

if not exist "%USB_DRIVE%\AutoTech\scripts\mms_scripts\T1_Tools.bat" (
    echo [WARN] Missing: AutoTech\scripts\mms_scripts\
) else (
    echo [OK] AutoTech\scripts\mms_scripts\ (MMS scripts)
)

if not exist "%USB_DRIVE%\AutoTech.exe" (
    echo [WARN] Missing: AutoTech.exe (server - run option 11 first, then rerun option 18)
) else (
    echo [OK] AutoTech.exe (server executable)
)

:: Verify version consistency
set "VER_ROOT="
set "VER_CLIENT="
if exist "%USB_DRIVE%\VERSION" for /f "usebackq" %%a in ("%USB_DRIVE%\VERSION") do set "VER_ROOT=%%a"
if exist "%USB_DRIVE%\AutoTech\scripts\VERSION" for /f "usebackq" %%b in ("%USB_DRIVE%\AutoTech\scripts\VERSION") do set "VER_CLIENT=%%b"
if defined VER_ROOT if defined VER_CLIENT (
    if "!VER_ROOT!"=="!VER_CLIENT!" (
        echo [OK] Version match: !VER_ROOT!
    ) else (
        echo [WARN] Version mismatch: root=!VER_ROOT! client=!VER_CLIENT!
    )
)

echo.
echo ============================================
if "!USB_OK!"=="1" (
    echo  USB BUILD COMPLETE!
) else (
    echo  USB BUILD INCOMPLETE - CHECK ERRORS ABOVE
)
echo ============================================
echo.
echo Target: %USB_DRIVE%\
echo.
echo USB Structure:
echo   %USB_DRIVE%\AutoTech.exe                 (server - double-click to run)
echo   %USB_DRIVE%\Start_AutoTech_Server.bat    (server launcher with browser open)
echo   %USB_DRIVE%\Install_AutoTech_Client.bat  (client installer - run as admin)
echo   %USB_DRIVE%\VERSION
echo   %USB_DRIVE%\AutoTech\database\            (server databases)
echo   %USB_DRIVE%\AutoTech\tools\              (putty, WinSCP, VNC)
echo   %USB_DRIVE%\AutoTech\scripts\            (launch_*.bat)
echo   %USB_DRIVE%\AutoTech\scripts\mms_scripts\   (MMS batch scripts)
echo   %USB_DRIVE%\frontrunnerV3-3.7.0-076-full\   (playback tools)
echo   %USB_DRIVE%\T1_Tools_Legacy\             (legacy T1 tools)
echo   %USB_DRIVE%\CamStudio_USB\               (screen recording)
echo   %USB_DRIVE%\AT Monitor V3.7.0\           (AT Monitor)
echo.
echo SERVER USAGE:
echo   Double-click: %USB_DRIVE%\AutoTech.exe
echo   Or run:       %USB_DRIVE%\Start_AutoTech_Server.bat
echo   Dashboard:    http://localhost:8888
echo.
echo CLIENT INSTALL:
echo   Right-click Install_AutoTech_Client.bat and select Run as administrator
echo.
echo Rerun this option anytime to refresh the USB.
echo.
pause
exit /b 0
