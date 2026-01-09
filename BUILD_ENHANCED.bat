@echo off
:: ============================================
:: T1 Tools Web - Enhanced Build & Test Script
:: ============================================
:: Features:
::  - Git version control integration
::  - Pre-build verification (check_main.py)
::  - Automatic backups
::  - Version management
:: ============================================

title T1 Tools - Enhanced Build Script

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
echo    T1 TOOLS WEB - BUILD ^& TEST
echo ============================================
echo.
echo  DEVELOPMENT ^& TESTING
echo    1. Run Development Server (test changes)
echo    2. Verify Code (check_main.py)
echo    3. Run Tests ^& Show Git Status
echo.
echo  VERSION CONTROL (Git)
if %GIT_AVAILABLE%==1 (
    echo    4. Save Changes (Git Commit)
    echo    5. View Changes (Git Diff)
    echo    6. Undo Changes (Git Checkout)
    echo    7. View History (Git Log)
) else (
    echo    4-7. [Git not installed]
)
echo.
echo  BUILD ^& DEPLOYMENT
echo    8. Pre-Build Checklist
echo    9. Build Executable
echo    10. Test Executable
echo    11. Full Build Pipeline
echo.
echo  UTILITIES
echo    12. Create Backup
echo    13. Clean Build Folders
echo    14. Setup Git (first time)
echo    15. Exit
echo.
echo ============================================
set /p choice="Select option (1-15): "

if "%choice%"=="1" goto DEVSERVER
if "%choice%"=="2" goto VERIFY
if "%choice%"=="3" goto RUNTESTS
if "%choice%"=="4" goto GITCOMMIT
if "%choice%"=="5" goto GITDIFF
if "%choice%"=="6" goto GITCHECKOUT
if "%choice%"=="7" goto GITLOG
if "%choice%"=="8" goto PREBUILD
if "%choice%"=="9" goto BUILD
if "%choice%"=="10" goto TESTEXE
if "%choice%"=="11" goto FULLBUILD
if "%choice%"=="12" goto BACKUP
if "%choice%"=="13" goto CLEAN
if "%choice%"=="14" goto SETUPGIT
if "%choice%"=="15" goto END

echo Invalid option. Press any key to try again...
pause >nul
goto MENU

:: ============================================
:: DEVELOPMENT SERVER
:: ============================================
:DEVSERVER
cls
echo ============================================
echo  Starting Development Server...
echo ============================================
echo.
echo  Clearing Python cache...
if exist __pycache__ rmdir /s /q __pycache__
if exist tools\__pycache__ rmdir /s /q tools\__pycache__
echo.
echo  Access at: http://localhost:8888
echo  Password: komatsu
echo.
echo  Press Ctrl+C to stop
echo ============================================
echo.
python main.py
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
        echo   [WARNING] Missing components - run option 2 for details
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
        echo Run option 2 for details.
        pause
        goto MENU
    )
    echo [OK] Pre-build checks passed
    echo.
)

echo Building with PyInstaller...
python -m PyInstaller T1_Tools_Web.spec --noconfirm
echo.

if exist "dist\T1_Tools_Web.exe" (
    echo [SUCCESS] Build complete!
    echo Location: dist\T1_Tools_Web.exe
    
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
:: TEST EXECUTABLE
:: ============================================
:TESTEXE
cls
echo ============================================
echo  Testing Executable...
echo ============================================
echo.

if not exist "dist\T1_Tools_Web.exe" (
    echo [ERROR] Executable not found!
    echo Run option 9 to build first.
    pause
    goto MENU
)

echo Starting T1_Tools_Web.exe...
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
echo  Close the application window to return here.
echo ============================================
start /wait dist\T1_Tools_Web.exe
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
echo  Cleaning Build Folders...
echo ============================================
echo.

if exist "build" (
    rmdir /s /q build
    echo Removed: build\
)
if exist "dist" (
    rmdir /s /q dist
    echo Removed: dist\
)
if exist "__pycache__" (
    rmdir /s /q __pycache__
    echo Removed: __pycache__\
)
echo.
echo [DONE] Clean complete!
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

echo [1/7] Creating backup...
if not exist "backups" mkdir backups
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set backup_date=%%c-%%a-%%b)
copy main.py "backups\main_PREBUILD_%backup_date%.py" >nul
echo   [OK] Backup created
echo.

echo [2/7] Verifying code...
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

echo [3/7] Committing to Git...
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

echo [4/7] Cleaning old builds...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist
echo   [OK] Clean complete
echo.

echo [5/7] Building executable...
python -m PyInstaller T1_Tools_Web.spec --noconfirm
echo.

if not exist "dist\T1_Tools_Web.exe" (
    echo   [ERROR] Build failed!
    pause
    goto MENU
)
echo   [OK] Build complete
echo.

echo [6/7] Tagging build...
if %GIT_AVAILABLE%==1 (
    for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set build_date=%%c-%%a-%%b)
    for /f "tokens=1-2 delims=/:" %%a in ('time /t') do (set build_time=%%a%%b)
    git tag -a "build_%build_date%_%build_time%" -m "Auto-build %build_date% %build_time%" 2>nul
    echo   [OK] Tagged as build_%build_date%_%build_time%
) else (
    echo   [SKIP] Git not available
)
echo.

echo [7/7] Build summary...
echo.
echo ============================================
echo  BUILD SUCCESSFUL!
echo ============================================
echo.
echo  Executable: dist\T1_Tools_Web.exe
echo  Backup: backups\main_PREBUILD_%backup_date%.py
echo.
echo  NEXT STEPS:
echo  1. Run the executable (option 10)
echo  2. Test ALL pages visually
echo  3. Check browser console for errors (F12)
echo  4. Test with internet disabled
echo  5. Copy to USB for deployment
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
git commit -m "Initial commit - T1 Tools Web Dashboard"
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
echo You can now use Git options 4-7 in the menu.
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
