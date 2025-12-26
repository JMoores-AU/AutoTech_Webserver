@echo off
:: ============================================
:: T1 Tools Web - Build & Test Script
:: ============================================
:: Run this on your development laptop (with internet)
:: before deploying to the offline Win10 server
:: ============================================

title T1 Tools - Build Script

:MENU
cls
echo ============================================
echo    T1 TOOLS WEB - BUILD ^& TEST
echo ============================================
echo.
echo    1. Run Development Server (test changes)
echo    2. Build Executable
echo    3. Test Executable
echo    4. Clean Build Folders
echo    5. Full Build ^& Test
echo    6. Exit
echo.
echo ============================================
set /p choice="Select option (1-6): "

if "%choice%"=="1" goto DEVSERVER
if "%choice%"=="2" goto BUILD
if "%choice%"=="3" goto TESTEXE
if "%choice%"=="4" goto CLEAN
if "%choice%"=="5" goto FULLBUILD
if "%choice%"=="6" goto END

echo Invalid option. Press any key to try again...
pause >nul
goto MENU

:DEVSERVER
cls
echo ============================================
echo  Starting Development Server...
echo ============================================
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

:BUILD
cls
echo ============================================
echo  Building Executable...
echo ============================================
echo.
python -m PyInstaller T1_Tools_Web.spec --noconfirm
echo.
if exist "dist\T1_Tools_Web.exe" (
    echo [SUCCESS] Build complete!
    echo Location: dist\T1_Tools_Web.exe
) else (
    echo [ERROR] Build failed! Check errors above.
)
echo.
pause
goto MENU

:TESTEXE
cls
echo ============================================
echo  Testing Executable...
echo ============================================
echo.
if not exist "dist\T1_Tools_Web.exe" (
    echo [ERROR] Executable not found!
    echo Run option 2 to build first.
    pause
    goto MENU
)
echo Starting T1_Tools_Web.exe...
echo.
echo  Access at: http://localhost:8888
echo  Password: komatsu
echo.
echo  Close the application window to return here.
echo ============================================
start /wait dist\T1_Tools_Web.exe
goto MENU

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

:FULLBUILD
cls
echo ============================================
echo  Full Build ^& Test Process
echo ============================================
echo.
echo Step 1: Cleaning old builds...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist
echo [OK] Clean complete
echo.

echo Step 2: Building executable...
python -m PyInstaller T1_Tools_Web.spec --noconfirm
echo.

if not exist "dist\T1_Tools_Web.exe" (
    echo [ERROR] Build failed!
    pause
    goto MENU
)
echo [OK] Build complete
echo.

echo Step 3: Ready for testing
echo.
echo ============================================
echo  BUILD SUCCESSFUL!
echo ============================================
echo.
echo  Executable: dist\T1_Tools_Web.exe
echo.
echo  NEXT STEPS:
echo  1. Run the executable (option 3)
echo  2. Test ALL pages visually
echo  3. Check browser console for errors (F12)
echo  4. Test with internet disabled
echo  5. Copy to USB for deployment
echo.
echo ============================================
pause
goto MENU

:END
exit