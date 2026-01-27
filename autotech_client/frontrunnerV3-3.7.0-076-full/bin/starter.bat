@echo off
call setColor
set RESTART_COUNT=0

:start
echo java %~1 %~2 %~3 %~4 %~5 %~6 %~7 %~8 %~9 
java %~1 %~2 %~3 %~4 %~5 %~6 %~7 %~8 %~9 
if not "%AUTO_RESTARTS%" == "" (
    if not "%RESTART_COUNT%" == "%AUTO_RESTARTS%" (
        set /A RESTART_COUNT=RESTART_COUNT+1
        rem 234 frontrunner gui code to avoid autorestarts!!
        if "%ERRORLEVEL%" == "234" (
           goto :eof
        )
        rem ctrl+c
        if "%ERRORLEVEL%" == "130" (
           goto :eof
        )
        rem class not found
        if "%ERRORLEVEL%" == "1" (
           goto :eof
        )
        
        echo Restarting...
        goto :start
    )
)

:eof
