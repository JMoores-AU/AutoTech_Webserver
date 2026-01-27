@echo off
REM AutoTech - CamStudio launcher (runs locally on the client)
setlocal enabledelayedexpansion

set "CANDIDATES=CamStudioPortable\\CamStudioPortable.exe CamStudio\\CamStudio.exe CamStudio\\Recorder.exe"
set "FOUND_DRIVE="
set "FOUND_PATH="

for %%D in (E D F G H I J K L M N O P Q R S T U V W X Y Z) do (
    for %%P in (%CANDIDATES%) do (
        if exist "%%D:\\%%P" (
            set "FOUND_DRIVE=%%D:"
            set "FOUND_PATH=%%D:\\%%P"
            goto :found
        )
    )
)

echo [ERROR] CamStudio not found on any drive. Please mount the USB that contains CamStudioPortable.
pause
exit /b 1

:found
echo Launching CamStudio from %FOUND_PATH%
start "" "%FOUND_PATH%"
endlocal
