@ECHO OFF
REM ========================================
REM GIT SETUP FOR T1 TOOLS
REM ========================================
REM Run this ONCE to set up version control
REM ========================================

ECHO.
ECHO ========================================
ECHO  GIT SETUP FOR T1 TOOLS
ECHO ========================================
ECHO.

REM Check if Git is installed
git --version >nul 2>&1
IF ERRORLEVEL 1 (
    ECHO ❌ ERROR: Git is not installed!
    ECHO.
    ECHO Please install Git from: https://git-scm.com/download/win
    ECHO Then run this script again.
    PAUSE
    EXIT /B 1
)

ECHO ✅ Git is installed
ECHO.

REM Check if already initialized
IF EXIST .git (
    ECHO ⚠️  WARNING: Git repository already exists!
    ECHO.
    ECHO This folder is already using Git.
    ECHO No setup needed.
    PAUSE
    EXIT /B 0
)

ECHO Initializing Git repository...
git init

ECHO.
ECHO Creating .gitignore file...
(
ECHO # Python
ECHO __pycache__/
ECHO *.py[cod]
ECHO *.so
ECHO *.egg-info/
ECHO dist/
ECHO build/
ECHO.
ECHO # PyInstaller
ECHO *.spec
ECHO.
ECHO # Flask
ECHO instance/
ECHO .webassets-cache
ECHO.
ECHO # Environment
ECHO .env
ECHO venv/
ECHO ENV/
ECHO.
ECHO # IDE
ECHO .vscode/
ECHO .idea/
ECHO *.swp
ECHO *.swo
ECHO.
ECHO # OS
ECHO Thumbs.db
ECHO .DS_Store
ECHO.
ECHO # Logs
ECHO *.log
) > .gitignore

ECHO.
ECHO Adding all files to Git...
git add .

ECHO.
ECHO Creating initial commit...
git commit -m "Initial commit - Working T1 Tools version"

ECHO.
ECHO Creating backups directory...
IF NOT EXIST backups MKDIR backups

ECHO.
ECHO Creating backup of current main.py...
COPY main.py backups\main_WORKING_%DATE:~-4,4%-%DATE:~-10,2%-%DATE:~-7,2%.py

ECHO.
ECHO ========================================
ECHO  ✅ GIT SETUP COMPLETE!
ECHO ========================================
ECHO.
ECHO What was done:
ECHO   • Initialized Git repository
ECHO   • Created .gitignore file
ECHO   • Made initial commit
ECHO   • Created backups directory
ECHO   • Backed up current main.py
ECHO.
ECHO You can now use Git commands:
ECHO   git status        - See what changed
ECHO   git diff main.py  - See exact changes
ECHO   git commit -am "message"  - Save changes
ECHO   git log           - See history
ECHO.
ECHO Before making changes:
ECHO   git commit -am "Before adding feature X"
ECHO.
ECHO After making changes:
ECHO   python check_main.py main.py
ECHO   git diff main.py
ECHO   git commit -am "Added feature X"
ECHO.
ECHO To undo changes:
ECHO   git checkout main.py
ECHO.
PAUSE
