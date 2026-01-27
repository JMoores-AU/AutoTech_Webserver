@echo off
REM AutoTech - Playback Tool launcher (runs locally on the client)
setlocal enabledelayedexpansion

set "TARGET_DIR=frontrunnerV3-3.7.0-076-full"
set "FOUND_DRIVE="

for %%D in (E D F G H I J K L M N O P Q R S T U V W X Y Z) do (
    if exist "%%D:\%TARGET_DIR%\bin\frontrunner.exe" (
        set "FOUND_DRIVE=%%D:"
        goto :found
    )
)

echo [ERROR] %TARGET_DIR% not found on any drive. Please mount the playback USB.
pause
exit /b 1

:found
pushd "%FOUND_DRIVE%\%TARGET_DIR%"
echo Launching playback from %CD%
.\bin\frontrunner start playback
popd
endlocal
