@echo off
setlocal enabledelayedexpansion
:: ============================================
:: AutoTech Web - Build & Test Script (FIXED)
:: ============================================
:: Fixes added:
::  - Always kills anything holding port 8888
::  - Also kills AutoTech.exe + AutoTech_Tray.exe (tray app) so stale HTML can’t persist
::  - Option 13 (FULLBUILD) preserved
:: ============================================

title AutoTech - Build Script

:: Check if Git is available
git --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    set GIT_AVAILABLE=0
    echo [WARNING] Git not found. Version control features disabled.
) else (
    set GIT_AVAILABLE=1
)

:MENU
cls
echo ============================================
echo    AUTOTECH WEBSERVER - BUILD ^& TEST
echo ============================================
echo.
echo  DEVELOPMENT ^& TESTING
echo    1. Start Server (opens browser)
echo    2. Restart Server (no browser)
echo    3. Stop Server
echo    4. Verify Code (check_main.py)
echo    5. Run Tests ^& Show Git Status
echo.
echo  VERSION CONTROL (Git)
if %GIT_AVAILABLE%==1 (
    echo    6. Save Changes (Git Commit)
    echo    7. View Changes (Git Diff)
    echo    8. Undo Changes (Git Checkout)
    echo    9. View History (Git Log)
) else (
    echo    6-9. [Git not installed]
)
echo.
echo  BUILD ^& DEPLOYMENT
echo    10. Pre-Build Checklist
echo    11. Build Executable
echo    12. Test Executable
echo    13. Full Build Pipeline (USB Deploy)
echo    18. Build Client USB (sync autotech_client)
echo.
echo  UTILITIES
echo    14. Create Backup
echo    15. Clean Build Folders
echo    16. Setup Git (first time)
echo    17. Exit
echo.
echo ============================================
echo.
set /p choice="Select option (1-17): "

if "%choice%"=="1" goto DEVSERVER
if "%choice%"=="2" goto RESTARTSERVER
if "%choice%"=="3" goto STOPSERVER
if "%choice%"=="4" goto VERIFY
if "%choice%"=="5" goto RUNTESTS
if "%choice%"=="6" goto GITCOMMIT
if "%choice%"=="7" goto GITDIFF
if "%choice%"=="8" goto GITCHECKOUT
if "%choice%"=="9" goto GITLOG
if "%choice%"=="10" goto PREBUILD
if "%choice%"=="11" goto BUILD
if "%choice%"=="12" goto TESTEXE
if "%choice%"=="13" goto FULLBUILD
if "%choice%"=="18" goto BUILDCLIENTUSB
if "%choice%"=="14" goto BACKUP
if "%choice%"=="15" goto CLEAN
if "%choice%"=="16" goto SETUPGIT
if "%choice%"=="17" goto END

echo Invalid option. Press any key to try again...
pause >nul
goto MENU


:: ============================================
:: ROUTINE: Kill anything that could be serving 8888
:: ============================================
:KILL_8888
echo  Stopping anything serving on port 8888...

:: Kill by port (LISTENING)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8888 ^| findstr LISTENING') do (
    echo    - Killing PID %%a (LISTENING :8888)
    taskkill /PID %%a /F >nul 2>&1
)

:: Kill known packaged binaries that may stay alive in tray
taskkill /IM AutoTech.exe /F >nul 2>&1
taskkill /IM AutoTech_Tray.exe /F >nul 2>&1

timeout /t 1 /nobreak >nul
exit /b 0


:: ============================================
:: DEVELOPMENT SERVER (with browser)
:: ============================================
:DEVSERVER
cls
echo ============================================
echo  Starting Development Server...
echo ============================================
echo.

echo  Stopping any existing server...
call :KILL_8888

echo  Clearing Python cache...
if exist __pycache__ rmdir /s /q __pycache__
if exist tools\__pycache__ rmdir /s /q tools\__pycache__
echo.
echo  Server will start in a new window.
echo  Access at: http://localhost:8888
echo  Password: komatsu
echo.
echo ============================================

:: Start server in new window
start "AutoTech Server" cmd /k "python main.py"

:: Wait a moment for server to start
timeout /t 2 /nobreak >nul

:: Open browser
start http://localhost:8888

goto MENU


:: ============================================
:: RESTART SERVER (no browser)
:: ============================================
:RESTARTSERVER
cls
echo ============================================
echo  Restarting Development Server...
echo ============================================
echo.

echo  Stopping existing server...
call :KILL_8888

echo  Clearing Python cache...
if exist __pycache__ rmdir /s /q __pycache__
if exist tools\__pycache__ rmdir /s /q tools\__pycache__
echo.
echo  Server restarting in new window...
echo  Access at: http://localhost:8888
echo.
echo ============================================

:: Start server in new window
start "AutoTech Server" cmd /k "python main.py"

goto MENU


:: ============================================
:: STOP SERVER
:: ============================================
:STOPSERVER
cls
echo ============================================
echo  Stopping Development Server...
echo ============================================
echo.

call :KILL_8888

echo.
echo  Server stopped.
echo.
pause
goto MENU


:: ============================================
:: VERIFY CODE
:: ============================================
:VERIFY
cls
echo ============================================
echo  Verifying Code with check_main.py
echo ============================================
echo.

if not exist "check_main.py" (
    echo [ERROR] check_main.py not found!
    echo Please copy check_main.py to this directory.
    echo.
    pause
    goto MENU
)

python check_main.py main.py
echo.
if %ERRORLEVEL% EQU 0 (
    echo [SUCCESS] All checks passed!
) else (
    echo [WARNING] Some checks failed. Review errors above.
)
echo.
pause
goto MENU


:: ============================================
:: RUN TESTS & GIT STATUS
:: ============================================
:RUNTESTS
cls
echo ============================================
echo  Running Tests ^& Git Status
echo ============================================
echo.

echo [1/3] Python Syntax Check...
python -m py_compile main.py 2>nul
if %ERRORLEVEL% EQU 0 (
    echo   [OK] Syntax valid
) else (
    echo   [ERROR] Syntax errors found!
)
echo.

echo [2/3] Code Verification...
if exist "check_main.py" (
    python check_main.py main.py >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo   [OK] All components present
    ) else (
        echo   [WARNING] Missing components - run option 4 for details
    )
) else (
    echo   [SKIP] check_main.py not found
)
echo.

echo [3/3] Git Status...
if %GIT_AVAILABLE%==1 (
    git status --short
    if %ERRORLEVEL% EQU 0 (
        echo.
        echo   [OK] Git status shown above
    )
) else (
    echo   [SKIP] Git not available
)
echo.
pause
goto MENU


:: ============================================
:: GIT COMMIT
:: ============================================
:GITCOMMIT
if %GIT_AVAILABLE%==0 (
    echo [ERROR] Git not installed!
    pause
    goto MENU
)

cls
echo ============================================
echo  Save Changes (Git Commit)
echo ============================================
echo.

echo Current changes:
git status --short
echo.

set /p commit_msg="Enter commit message (or CANCEL to abort): "
if /i "%commit_msg%"=="CANCEL" goto MENU
if "%commit_msg%"=="" (
    echo [ERROR] Commit message cannot be empty!
    pause
    goto MENU
)

echo.
echo Committing changes...
git add .
git commit -m "%commit_msg%"

if %ERRORLEVEL% EQU 0 (
    echo [SUCCESS] Changes committed!
) else (
    echo [ERROR] Commit failed!
)
echo.
pause
goto MENU


:: ============================================
:: GIT DIFF
:: ============================================
:GITDIFF
if %GIT_AVAILABLE%==0 (
    echo [ERROR] Git not installed!
    pause
    goto MENU
)

cls
echo ============================================
echo  View Changes (Git Diff)
echo ============================================
echo.

git diff main.py
if %ERRORLEVEL% NEQ 0 (
    echo No changes in main.py
)
echo.
pause
goto MENU


:: ============================================
:: GIT CHECKOUT (UNDO)
:: ============================================
:GITCHECKOUT
if %GIT_AVAILABLE%==0 (
    echo [ERROR] Git not installed!
    pause
    goto MENU
)

cls
echo ============================================
echo  Undo Changes (Git Checkout)
echo ============================================
echo.
echo [WARNING] This will DISCARD all uncommitted changes!
echo.
echo Current changes:
git status --short
echo.

set /p confirm="Are you sure? Type YES to confirm: "
if /i not "%confirm%"=="YES" (
    echo Cancelled.
    pause
    goto MENU
)

git checkout .
echo.
echo [DONE] Changes discarded. Reverted to last commit.
echo.
pause
goto MENU


:: ============================================
:: GIT LOG
:: ============================================
:GITLOG
if %GIT_AVAILABLE%==0 (
    echo [ERROR] Git not installed!
    pause
    goto MENU
)

cls
echo ============================================
echo  View History (Git Log)
echo ============================================
echo.

git log --oneline -20
echo.
echo (Showing last 20 commits)
echo.
pause
goto MENU


:: ============================================
:: PRE-BUILD CHECKLIST
:: ============================================
:PREBUILD
cls
echo ============================================
echo  Pre-Build Checklist
echo ============================================
echo.

set checklist_pass=1

echo [1/6] Checking if main.py exists...
if exist "main.py" (
    echo   [OK] main.py found
) else (
    echo   [ERROR] main.py not found!
    set checklist_pass=0
)

echo [2/6] Checking Python syntax...
python -m py_compile main.py 2>nul
if %ERRORLEVEL% EQU 0 (
    echo   [OK] Syntax valid
) else (
    echo   [ERROR] Syntax errors!
    set checklist_pass=0
)

echo [3/6] Verifying code components...
if exist "check_main.py" (
    python check_main.py main.py >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo   [OK] All components present
    ) else (
        echo   [ERROR] Missing components!
        set checklist_pass=0
    )
) else (
    echo   [SKIP] check_main.py not found
)

echo [4/6] Checking if templates exist...
if exist "templates\enhanced_index.html" (
    echo   [OK] enhanced_index.html found
) else (
    echo   [ERROR] enhanced_index.html missing!
    set checklist_pass=0
)

echo [5/6] Checking if static folder exists...
if exist "static\style.css" (
    echo   [OK] style.css found
) else (
    echo   [ERROR] style.css missing!
    set checklist_pass=0
)

echo [6/6] Checking Git status...
if %GIT_AVAILABLE%==1 (
    git diff-index --quiet HEAD --
    if %ERRORLEVEL% EQU 0 (
        echo   [OK] No uncommitted changes
    ) else (
        echo   [WARNING] You have uncommitted changes
        echo   [INFO] Consider committing before building
    )
) else (
    echo   [SKIP] Git not available
)

echo.
echo ============================================
if %checklist_pass%==1 (
    echo  [SUCCESS] All checks passed!
    echo  Ready to build.
) else (
    echo  [FAILED] Some checks failed!
    echo  Fix errors before building.
)
echo ============================================
echo.
pause
goto MENU


:: ============================================
:: BUILD EXECUTABLE
:: ============================================
:BUILD
cls
echo ============================================
echo  Building Executable...
echo ============================================
echo.

echo Running pre-build checks...
if exist "check_main.py" (
    python check_main.py main.py >nul 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Pre-build verification failed!
        echo Run option 4 for details.
        pause
        goto MENU
    )
    echo [OK] Pre-build checks passed
    echo.
)

echo Performing deep clean (removing ALL caches)...
echo   - Removing build/dist directories...
if exist "build" rmdir /s /q build 2>nul
if exist "dist" rmdir /s /q dist 2>nul
echo   - Cleaning Python cache files...
if exist "__pycache__" rmdir /s /q __pycache__ 2>nul
if exist "tools\__pycache__" rmdir /s /q tools\__pycache__ 2>nul
del /s /q *.pyc 2>nul >nul
echo   - Removing application cache files...
del /q *_cache.json 2>nul >nul
del /q *.log 2>nul >nul
del /q nul 2>nul >nul
echo   [OK] Deep clean complete - NO cached data will be bundled
echo.

echo Building with PyInstaller...
echo [1/2] Building AutoTech.exe (using --clean to prevent archive corruption)...
python -m PyInstaller AutoTech.spec --noconfirm --clean
echo.

echo [2/2] Building AutoTech_Tray.exe...
python -m PyInstaller AutoTech_Tray.spec --noconfirm --clean
echo.

if exist "dist\AutoTech.exe" (
    echo [SUCCESS] Build complete!
    echo Location: dist\AutoTech.exe
    if exist "dist\AutoTech_Tray.exe" (
        echo           dist\AutoTech_Tray.exe
    )
    echo.

    :: Copy to USB if detected
    set "USB_DRIVE="
    for %%D in (D E F G H I J K L) do (
        if exist "%%D:\AutoTech" set "USB_DRIVE=%%D:"
    )

    if defined USB_DRIVE (
        echo [USB] Detected AUTOTECH drive: !USB_DRIVE!
        echo.

        set "DEPLOY_SERVER_BIN=Y"
        set /p DEPLOY_SERVER_BIN="Deploy server binaries (AutoTech.exe, service installers) to this USB? (Y/N): "
        if /i "!DEPLOY_SERVER_BIN!"=="Y" (
            :: Check if AutoTech.exe needs updating (compare file sizes)
            set "NEED_EXE_UPDATE=0"
            if not exist "!USB_DRIVE!\AutoTech.exe" (
                set "NEED_EXE_UPDATE=1"
            ) else (
                for %%A in ("dist\AutoTech.exe") do set "SRC_SIZE=%%~zA"
                for %%A in ("!USB_DRIVE!\AutoTech.exe") do set "DST_SIZE=%%~zA"
                if not "!SRC_SIZE!"=="!DST_SIZE!" set "NEED_EXE_UPDATE=1"
            )

            if "!NEED_EXE_UPDATE!"=="1" (
                echo [USB] Copying AutoTech.exe...
                copy /Y "dist\AutoTech.exe" "!USB_DRIVE!\" >nul
                if exist "!USB_DRIVE!\AutoTech.exe" (
                    echo   [OK] Copied to !USB_DRIVE!\AutoTech.exe
                ) else (
                    echo   [ERROR] Failed to copy AutoTech.exe
                )
            ) else (
                echo [USB] AutoTech.exe is up-to-date, skipping
            )

            :: Copy AutoTech_Tray.exe if it exists
            if exist "dist\AutoTech_Tray.exe" (
                copy /Y "dist\AutoTech_Tray.exe" "!USB_DRIVE!\" >nul
                if exist "!USB_DRIVE!\AutoTech_Tray.exe" (
                    echo   [OK] Copied to !USB_DRIVE!\AutoTech_Tray.exe
                )
            )

            :: Deploy Windows Service installers to E:\AutoTech
            echo.
            echo [USB] Checking service installers...
            if exist "Install_AutoTech_Service.bat" (
                copy /Y "Install_AutoTech_Service.bat" "!USB_DRIVE!\AutoTech\" >nul
                echo   [OK] Install_AutoTech_Service.bat synced
            )
            if exist "Uninstall_AutoTech_Service.bat" (
                copy /Y "Uninstall_AutoTech_Service.bat" "!USB_DRIVE!\AutoTech\" >nul
                echo   [OK] Uninstall_AutoTech_Service.bat synced
            )
        ) else (
            echo [USB] Skipping server binaries for client-only USB.
        )
        echo.

        :: Deploy AutoTech Client structure to USB
        echo [USB] Deploying client structure from autotech_client/...

        :: Copy Install_AutoTech_Client.bat to USB root
        if exist "Install_AutoTech_Client.bat" (
            copy /Y "Install_AutoTech_Client.bat" "!USB_DRIVE!\" >nul
            echo   [OK] Install_AutoTech_Client.bat
        )

        :: Copy VERSION to USB root
        if exist "VERSION" (
            copy /Y "VERSION" "!USB_DRIVE!\" >nul
            for /f %%v in ('type "VERSION"') do echo   [OK] VERSION %%v
        )

        :: Sync AutoTech folder from autotech_client/AutoTech/ to USB
        if exist "autotech_client\AutoTech\" (
            if not exist "!USB_DRIVE!\AutoTech\" mkdir "!USB_DRIVE!\AutoTech\"
            xcopy "autotech_client\AutoTech\*.*" "!USB_DRIVE!\AutoTech\" /E /I /Q /Y /D >nul
            echo   [OK] AutoTech\ folder synced (tools, scripts, database)
        )

        :: Copy standalone playback launcher to AutoTech root
        if exist "V3.7.0 Playback Tool.bat" (
            copy /Y "V3.7.0 Playback Tool.bat" "!USB_DRIVE!\AutoTech\" >nul
            echo   [OK] V3.7.0 Playback Tool.bat copied
        )

        :: Update Python tools in AutoTech\tools
        echo.
        echo [USB] Updating Python tools...
        if exist "tools\equipment_db.py" (
            copy /Y "tools\equipment_db.py" "!USB_DRIVE!\AutoTech\tools\" >nul
            echo   [OK] equipment_db.py
        )
        if exist "tools\ptx_uptime_db.py" (
            copy /Y "tools\ptx_uptime_db.py" "!USB_DRIVE!\AutoTech\tools\" >nul
            echo   [OK] ptx_uptime_db.py
        )
        if exist "tools\__init__.py" (
            copy /Y "tools\__init__.py" "!USB_DRIVE!\AutoTech\tools\" >nul
        )

        :: Deploy Windows Service installers to E:\AutoTech (again - preserved from your original)
        echo.
        echo [USB] Checking service installers...
        if exist "Install_AutoTech_Service.bat" (
            copy /Y "Install_AutoTech_Service.bat" "!USB_DRIVE!\AutoTech\" >nul
            echo   [OK] Install_AutoTech_Service.bat synced
        )
        if exist "Uninstall_AutoTech_Service.bat" (
            copy /Y "Uninstall_AutoTech_Service.bat" "!USB_DRIVE!\AutoTech\" >nul
            echo   [OK] Uninstall_AutoTech_Service.bat synced
        )

        echo.
        echo [USB] Deployment complete!
        echo.
        echo ============================================
        echo  USB DEPLOYMENT COMPLETE!
        echo ============================================
        echo.
        echo  USB Structure:
        echo    !USB_DRIVE!\Install_AutoTech_Client.bat
        echo    !USB_DRIVE!\AutoTech\tools\ (PuTTY, WinSCP, VNC, Python tools)
        echo    !USB_DRIVE!\AutoTech\scripts\ (launchers + mms_scripts)
        echo    !USB_DRIVE!\AutoTech\database\
        echo.
        echo  REMINDER: Remote clients must run Install_AutoTech_Client.bat
        echo  from USB root to update their local launchers.
        echo ============================================
    ) else (
        echo [INFO] USB drive not detected - skipping USB deployment
        echo.
        echo ============================================
        echo  WARNING: Changes NOT deployed to live USB!
        echo  Connect USB and rebuild to deploy changes.
        echo ============================================
    )

    :: Tag this build in Git if available
    if %GIT_AVAILABLE%==1 (
        echo.
        set /p tag_build="Tag this build in Git? (Y/N): "
        if /i "!tag_build!"=="Y" (
            for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set build_date=%%c-%%a-%%b)
            for /f "tokens=1-2 delims=/:" %%a in ('time /t') do (set build_time=%%a%%b)
            git tag -a "build_!build_date!_!build_time!" -m "Build on !build_date! !build_time!"
            echo [OK] Tagged as build_!build_date!_!build_time!
        )
    )
) else (
    echo [ERROR] Build failed! Check errors above.
)
echo.
pause
goto MENU


:: ============================================
:: BUILD CLIENT USB (sync autotech_client)
:: ============================================
:BUILDCLIENTUSB
cls
echo ============================================
echo  Build Client USB (autotech_client -> USB root)
echo ============================================
echo.
echo This option creates a complete client USB package with:
echo   - Install_AutoTech_Client.bat (installer)
echo   - AutoTech\tools\ (putty, WinSCP, VNC, plink, pscp)
echo   - AutoTech\scripts\ (launch_*.bat scripts)
echo   - AutoTech\scripts\mms_scripts\ (MMS batch scripts)
echo   - VERSION file
echo   - Frontrunner playback tools
echo   - T1 Tools Legacy
echo   - CamStudio USB
echo.

:: Enumerate removable/fixed (non-system) drives using PowerShell to avoid network shares
set "USB_DRIVE="
set "DRIVE_LIST="
for /f "usebackq delims=" %%D in (`powershell -NoLogo -NoProfile -Command "Get-CimInstance Win32_LogicalDisk | Where-Object { $_.DriveType -in 2,3 } | Select-Object -ExpandProperty DeviceID"` ) do (
    set "DRIVE_LIST=!DRIVE_LIST! %%D"
    if not defined USB_DRIVE set "USB_DRIVE=%%D"
)

echo Available removable/fixed drives: %DRIVE_LIST%
if not defined USB_DRIVE (
    echo [ERROR] No removable/fixed drives detected. Plug in USB and retry.
    echo.
    pause
    goto MENU
)

echo Detected default: %USB_DRIVE%
set /p USB_DRIVE_IN="Enter target drive letter (e.g. I) or press Enter to use %USB_DRIVE%: "
if not "%USB_DRIVE_IN%"=="" set "USB_DRIVE=%USB_DRIVE_IN%:"
if not "%USB_DRIVE:~-1%"==":" set "USB_DRIVE=%USB_DRIVE%:"

if not exist "%USB_DRIVE%\\" (
    echo [ERROR] Drive %USB_DRIVE% not found.
    pause
    goto MENU
)

echo.
echo This will copy contents of autotech_client\\ to %USB_DRIVE%\\
echo (existing files will be updated; unique files on USB are kept).
set /p CONFIRM="Proceed? (Y/N): "
if /i not "%CONFIRM%"=="Y" (
    echo Cancelled.
    pause
    goto MENU
)

:: Create destination folders
if not exist "%USB_DRIVE%\\" (
    echo [ERROR] Cannot access %USB_DRIVE%\\
    pause
    goto MENU
)

echo.
echo ============================================
echo  SYNCING CLIENT USB PACKAGE
echo ============================================
echo.

:: Copy VERSION from repo root to USB root (canonical version)
echo [1/7] Copying VERSION file...
if exist "VERSION" (
    copy /Y "VERSION" "%USB_DRIVE%\\" >nul
    for /f %%v in ('type "VERSION"') do echo   [OK] VERSION %%v copied to USB root
) else (
    echo   [WARN] VERSION file not found at repo root
)
echo.

:: Copy Install_AutoTech_Client.bat to USB root
echo [2/7] Copying installer...
if exist "autotech_client\Install_AutoTech_Client.bat" (
    copy /Y "autotech_client\Install_AutoTech_Client.bat" "%USB_DRIVE%\\" >nul
    echo   [OK] Install_AutoTech_Client.bat
) else (
    echo   [ERROR] Install_AutoTech_Client.bat not found in autotech_client!
)
echo.

:: Sync AutoTech folder (tools, scripts, mms_scripts, database)
echo [3/7] Syncing AutoTech folder (tools, scripts, database)...
if exist "autotech_client\AutoTech\" (
    where robocopy >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        robocopy "autotech_client\AutoTech" "%USB_DRIVE%\AutoTech" /E /COPY:DAT /R:2 /W:1 /NFL /NDL /NP >nul
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
    if exist "%USB_DRIVE%\AutoTech\tools\vncviewer_5.3.2.exe" (
        echo        - tools\vncviewer_5.3.2.exe
    ) else (
        echo        - [WARN] tools\vncviewer missing!
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

:: Sync Frontrunner playback folder
echo [4/7] Syncing Frontrunner playback tools...
if exist "autotech_client\frontrunnerV3-3.7.0-076-full\" (
    where robocopy >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        robocopy "autotech_client\frontrunnerV3-3.7.0-076-full" "%USB_DRIVE%\frontrunnerV3-3.7.0-076-full" /E /COPY:DAT /R:2 /W:1 /NFL /NDL /NP >nul
    ) else (
        xcopy "autotech_client\frontrunnerV3-3.7.0-076-full\*.*" "%USB_DRIVE%\frontrunnerV3-3.7.0-076-full\" /E /I /Q /Y /D >nul
    )
    echo   [OK] frontrunnerV3-3.7.0-076-full\ synced
) else (
    echo   [SKIP] frontrunnerV3-3.7.0-076-full\ not found (optional)
)
echo.

:: Sync T1 Tools Legacy
echo [5/7] Syncing T1 Tools Legacy...
if exist "autotech_client\T1_Tools_Legacy\" (
    where robocopy >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        robocopy "autotech_client\T1_Tools_Legacy" "%USB_DRIVE%\T1_Tools_Legacy" /E /COPY:DAT /R:2 /W:1 /NFL /NDL /NP >nul
    ) else (
        xcopy "autotech_client\T1_Tools_Legacy\*.*" "%USB_DRIVE%\T1_Tools_Legacy\" /E /I /Q /Y /D >nul
    )
    echo   [OK] T1_Tools_Legacy\ synced
) else (
    echo   [SKIP] T1_Tools_Legacy\ not found (optional)
)
echo.

:: Sync CamStudio USB
echo [6/7] Syncing CamStudio USB tools...
if exist "autotech_client\CamStudio_USB\" (
    where robocopy >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        robocopy "autotech_client\CamStudio_USB" "%USB_DRIVE%\CamStudio_USB" /E /COPY:DAT /R:2 /W:1 /NFL /NDL /NP >nul
    ) else (
        xcopy "autotech_client\CamStudio_USB\*.*" "%USB_DRIVE%\CamStudio_USB\" /E /I /Q /Y /D >nul
    )
    echo   [OK] CamStudio_USB\ synced
) else (
    echo   [SKIP] CamStudio_USB\ not found (optional)
)
echo.

:: Sync AT Monitor
echo [7/7] Syncing AT Monitor...
if exist "autotech_client\AT Monitor V3.7.0\" (
    where robocopy >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        robocopy "autotech_client\AT Monitor V3.7.0" "%USB_DRIVE%\AT Monitor V3.7.0" /E /COPY:DAT /R:2 /W:1 /NFL /NDL /NP >nul
    ) else (
        xcopy "autotech_client\AT Monitor V3.7.0\*.*" "%USB_DRIVE%\AT Monitor V3.7.0\" /E /I /Q /Y /D >nul
    )
    echo   [OK] AT Monitor V3.7.0\ synced
) else (
    echo   [SKIP] AT Monitor V3.7.0\ not found (optional)
)
echo.

:: Final verification
echo ============================================
echo  VERIFYING USB PACKAGE
echo ============================================
echo.
set "USB_OK=1"

:: Check required files
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

echo.
echo ============================================
if "!USB_OK!"=="1" (
    echo  CLIENT USB BUILD COMPLETE!
) else (
    echo  CLIENT USB BUILD INCOMPLETE - CHECK ERRORS ABOVE
)
echo ============================================
echo.
echo Target: %USB_DRIVE%\
echo.
echo USB Structure:
echo   %USB_DRIVE%\Install_AutoTech_Client.bat  (run on client PC)
echo   %USB_DRIVE%\VERSION
echo   %USB_DRIVE%\AutoTech\tools\             (putty, WinSCP, VNC)
echo   %USB_DRIVE%\AutoTech\scripts\           (launch_*.bat)
echo   %USB_DRIVE%\AutoTech\scripts\mms_scripts\  (MMS batch scripts)
echo   %USB_DRIVE%\AutoTech\database\          (optional DBs)
echo   %USB_DRIVE%\frontrunnerV3-3.7.0-076-full\  (playback tools)
echo   %USB_DRIVE%\T1_Tools_Legacy\            (legacy T1 tools)
echo   %USB_DRIVE%\CamStudio_USB\              (screen recording)
echo   %USB_DRIVE%\AT Monitor V3.7.0\          (AT Monitor)
echo.
echo USAGE: On client PC, right-click Install_AutoTech_Client.bat
echo        and select "Run as administrator"
echo.
echo Rerun this option anytime to refresh the USB.
echo.
pause
goto MENU


:: ============================================
:: TEST EXECUTABLE
:: ============================================
:TESTEXE
cls
echo ============================================
echo  Testing Executable...
echo ============================================
echo.

if not exist "dist\AutoTech.exe" (
    echo [ERROR] Executable not found!
    echo Run option 11 to build first.
    pause
    goto MENU
)

echo [IMPORTANT]
echo This runs the PACKAGED AutoTech.exe.
echo It may stay running in the SYSTEM TRAY and keep serving port 8888.
echo Close it from the tray after testing, or run option 3 (Stop Server).
echo.
pause

echo Starting AutoTech.exe...
echo.
echo  Access at: http://localhost:8888
echo  Password: komatsu
echo.
echo  TESTING CHECKLIST:
echo  - Dashboard loads
echo  - Login works
echo  - IP Finder page loads
echo  - Legacy Tools page loads
echo  - Terminal starts
echo  - No console errors (F12)
echo.
echo  Close the application window (and tray icon if present) to return here.
echo ============================================
start /wait dist\AutoTech.exe

echo.
echo If anything stayed running, clearing port 8888 now...
call :KILL_8888

goto MENU


:: ============================================
:: CREATE BACKUP
:: ============================================
:BACKUP
cls
echo ============================================
echo  Create Backup
echo ============================================
echo.

if not exist "backups" mkdir backups

for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set backup_date=%%c-%%a-%%b)
for /f "tokens=1-2 delims=/:" %%a in ('time /t') do (set backup_time=%%a-%%b)
set backup_time=%backup_time: =0%

set backup_name=main_BACKUP_%backup_date%_%backup_time%.py

copy main.py "backups\%backup_name%"
if %ERRORLEVEL% EQU 0 (
    echo [SUCCESS] Backup created!
    echo Location: backups\%backup_name%
) else (
    echo [ERROR] Backup failed!
)
echo.
pause
goto MENU


:: ============================================
:: CLEAN BUILD FOLDERS
:: ============================================
:CLEAN
cls
echo ============================================
echo  Deep Clean (Remove ALL Caches)
echo ============================================
echo.
echo This will remove:
echo   - build\ and dist\ directories
echo   - Python cache files (__pycache__, *.pyc)
echo   - Application cache files (*_cache.json, *.log)
echo.

if exist "build" (
    rmdir /s /q build 2>nul
    echo Removed: build\
)
if exist "dist" (
    rmdir /s /q dist 2>nul
    echo Removed: dist\
)
if exist "__pycache__" (
    rmdir /s /q __pycache__ 2>nul
    echo Removed: __pycache__\
)
if exist "tools\__pycache__" (
    rmdir /s /q tools\__pycache__ 2>nul
    echo Removed: tools\__pycache__\
)

echo Removing .pyc files...
del /s /q *.pyc 2>nul >nul

echo Removing application cache files...
del /q *_cache.json 2>nul >nul
del /q *.log 2>nul >nul
del /q nul 2>nul >nul

echo.
echo [DONE] Deep clean complete - all caches removed!
echo.
pause
goto MENU


:: ============================================
:: FULL BUILD PIPELINE
:: ============================================
:FULLBUILD
cls
echo ============================================
echo  Full Build Pipeline
echo ============================================
echo.

echo [1/8] Creating backup...
if not exist "backups" mkdir backups
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set backup_date=%%c-%%a-%%b)
copy main.py "backups\main_PREBUILD_%backup_date%.py" >nul
echo   [OK] Backup created
echo.

echo [2/8] Verifying code...
if exist "check_main.py" (
    python check_main.py main.py >nul 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo   [ERROR] Verification failed! Aborting.
        pause
        goto MENU
    )
    echo   [OK] Code verified
) else (
    echo   [SKIP] check_main.py not found
)
echo.

echo [3/8] Committing to Git...
if %GIT_AVAILABLE%==1 (
    git diff-index --quiet HEAD --
    if %ERRORLEVEL% NEQ 0 (
        set /p auto_commit="Uncommitted changes found. Commit now? (Y/N): "
        if /i "!auto_commit!"=="Y" (
            git add .
            git commit -m "Pre-build commit %date% %time%"
            echo   [OK] Changes committed
        ) else (
            echo   [SKIP] User skipped commit
        )
    ) else (
        echo   [OK] No uncommitted changes
    )
) else (
    echo   [SKIP] Git not available
)
echo.

echo [4/8] Deep cleaning (removing ALL caches)...
echo   - Removing build/dist directories...
if exist "build" rmdir /s /q build 2>nul
if exist "dist" rmdir /s /q dist 2>nul
echo   - Cleaning Python cache files...
if exist "__pycache__" rmdir /s /q __pycache__ 2>nul
if exist "tools\__pycache__" rmdir /s /q tools\__pycache__ 2>nul
del /s /q *.pyc 2>nul >nul
echo   - Removing application cache files...
del /q *_cache.json 2>nul >nul
del /q *.log 2>nul >nul
del /q nul 2>nul >nul
echo   [OK] Deep clean complete - NO cached data will be bundled
echo.

echo [5/8] Building executable...
python -m PyInstaller AutoTech.spec --noconfirm --clean
echo.

if not exist "dist\AutoTech.exe" (
    echo   [ERROR] Build failed!
    pause
    goto MENU
)
echo   [OK] Build complete
echo.

echo [6/8] Deploying to USB...
set "USB_DRIVE="
for %%D in (D E F G H I J K L) do (
    if exist "%%D:\AutoTech" set "USB_DRIVE=%%D:"
)

if defined USB_DRIVE (
    echo   USB detected: !USB_DRIVE!

    set "DEPLOY_SERVER_BIN=Y"
    set /p DEPLOY_SERVER_BIN="Deploy server binaries (AutoTech.exe, service installers) to this USB? (Y/N): "
    if /i "!DEPLOY_SERVER_BIN!"=="Y" (
        :: Check if AutoTech.exe needs updating (compare file sizes)
        set "NEED_EXE_UPDATE=0"
        if not exist "!USB_DRIVE!\AutoTech.exe" (
            set "NEED_EXE_UPDATE=1"
        ) else (
            for %%A in ("dist\AutoTech.exe") do set "SRC_SIZE=%%~zA"
            for %%A in ("!USB_DRIVE!\AutoTech.exe") do set "DST_SIZE=%%~zA"
            if not "!SRC_SIZE!"=="!DST_SIZE!" set "NEED_EXE_UPDATE=1"
        )
        if "!NEED_EXE_UPDATE!"=="1" (
            copy /Y "dist\AutoTech.exe" "!USB_DRIVE!\" >nul
            echo   [OK] AutoTech.exe updated
        ) else (
            echo   [SKIP] AutoTech.exe up-to-date
        )
    ) else (
        echo   [SKIP] Server binaries skipped for client-only USB
    )

    :: Deploy client structure from autotech_client/ (represents USB root)
    if exist "Install_AutoTech_Client.bat" (
        copy /Y "Install_AutoTech_Client.bat" "!USB_DRIVE!\" >nul
        echo   [OK] Install_AutoTech_Client.bat
    )

    if exist "VERSION" (
        copy /Y "VERSION" "!USB_DRIVE!\" >nul
        for /f %%v in ('type "VERSION"') do echo   [OK] VERSION %%v
    )

    if exist "autotech_client\AutoTech\" (
        if not exist "!USB_DRIVE!\AutoTech\" mkdir "!USB_DRIVE!\AutoTech\"
        xcopy "autotech_client\AutoTech\*.*" "!USB_DRIVE!\AutoTech\" /E /I /Q /Y /D >nul
        echo   [OK] AutoTech\ synced
    )

    :: Update Python tools
    if exist "tools\equipment_db.py" (
        copy /Y "tools\equipment_db.py" "!USB_DRIVE!\AutoTech\tools\" >nul
        echo   [OK] equipment_db.py
    )
    if exist "tools\ptx_uptime_db.py" (
        copy /Y "tools\ptx_uptime_db.py" "!USB_DRIVE!\AutoTech\tools\" >nul
        echo   [OK] ptx_uptime_db.py
    )
    if exist "tools\__init__.py" (
        copy /Y "tools\__init__.py" "!USB_DRIVE!\AutoTech\tools\" >nul
    )
) else (
    echo   [SKIP] USB drive not detected
)
echo.

echo [7/8] Tagging build...
if %GIT_AVAILABLE%==1 (
    for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set build_date=%%c-%%a-%%b)
    for /f "tokens=1-2 delims=/:" %%a in ('time /t') do (set build_time=%%a%%b)
    git tag -a "build_%build_date%_%build_time%" -m "Auto-build %build_date% %build_time%" 2>nul
    echo   [OK] Tagged as build_%build_date%_%build_time%
) else (
    echo   [SKIP] Git not available
)
echo.

echo [8/8] Build summary...
echo.
echo ============================================
echo  BUILD SUCCESSFUL!
echo ============================================
echo.
echo  Executable: dist\AutoTech.exe
echo  Backup: backups\main_PREBUILD_%backup_date%.py
echo.
if defined USB_DRIVE (
    echo  USB DEPLOYMENT STATUS:
    echo    Drive: !USB_DRIVE!
    echo    - AutoTech.exe
    echo    - Install_AutoTech_Client.bat
    echo    - VERSION
    echo    - AutoTech\tools\ (PuTTY, WinSCP, VNC, Python tools)
    echo    - AutoTech\scripts\ (launchers + mms_scripts)
    echo    - AutoTech\database\
    echo    - AutoTech\service installers
    echo.
) else (
    echo  *** USB NOT CONNECTED ***
    echo  Changes have NOT been deployed to live environment!
    echo  Connect USB and run build again to deploy.
    echo.
)
echo  DEPLOYMENT CHECKLIST:
echo  --------------------------------------------
echo  [ ] USB connected and files synced
echo  [ ] Test executable locally (option 12)
echo  [ ] Test ALL pages visually
echo  [ ] Check browser console for errors (F12)
echo  [ ] Test with internet disabled (offline mode)
echo  [ ] Verify VERSION file updated if needed
echo  [ ] Remote clients need to re-run installer
echo      to receive client updates
echo.
echo  IMPORTANT: Changes in test environment are
echo  NOT automatically transferred to remote clients.
echo  Users must re-run Install_AutoTech_Client.bat
echo  from USB to get the latest client tools.
echo.
echo ============================================
pause
goto MENU


:: ============================================
:: SETUP GIT
:: ============================================
:SETUPGIT
cls
echo ============================================
echo  Git Setup
echo ============================================
echo.

git --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Git is not installed!
    echo.
    echo Download Git from: https://git-scm.com/download/win
    echo Then run this option again.
    pause
    goto MENU
)

if exist ".git" (
    echo [INFO] Git repository already initialized.
    echo.
    git status
    echo.
    pause
    goto MENU
)

echo Initializing Git repository...
git init
echo [OK] Git initialized
echo.

echo Creating .gitignore...
(
echo # Python
echo __pycache__/
echo *.py[cod]
echo *.so
echo.
echo # PyInstaller
echo build/
echo dist/
echo *.spec
echo.
echo # Backups
echo backups/
echo.
echo # IDE
echo .vscode/
echo.
echo # OS
echo Thumbs.db
) > .gitignore
echo [OK] .gitignore created
echo.

echo Adding files to Git...
git add .
echo [OK] Files added
echo.

echo Creating initial commit...
git commit -m "Initial commit - AutoTech Web Dashboard"
echo [OK] Initial commit created
echo.

echo Creating backups directory...
if not exist "backups" mkdir backups
echo [OK] Backups directory created
echo.

echo ============================================
echo  [SUCCESS] Git setup complete!
echo ============================================
echo.
echo You can now use Git options 6-9 in the menu.
echo.
pause
set GIT_AVAILABLE=1
goto MENU


:: ============================================
:: EXIT
:: ============================================
:END
echo.
echo Goodbye!
exit
