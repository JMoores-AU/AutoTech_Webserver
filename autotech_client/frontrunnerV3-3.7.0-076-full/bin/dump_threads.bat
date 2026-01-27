@echo off

goto MAIN


:SUB_HANDLE_PROC3

set IMAGE=%1
set PID=%2

exit /B


:SUB_HANDLE_PROC2

call :SUB_HANDLE_PROC3 %~1
@rem echo IMAGE:%IMAGE%  PID:%PID% --- %~1

if "%IMAGE%" == "cmd.exe" (
    echo ..........................................
    echo .... Command Shell: %~1
    echo ..........................................
) else if "%IMAGE%" == "java.exe" (
    echo ##########################################
    echo #### FULL THREAD DUMP: %~1
    echo ##########################################
    jstack %PID%
)

exit /B


:SUB_HANDLE_PROC1

set PROC1=%1
set PROC1=%PROC1:(=%
set PROC1=%PROC1:)=%
@rem echo PROC1=%PROC1%
call :SUB_HANDLE_PROC2 %PROC1%

exit /B


:MAIN

setlocal

set AHS_PROC_TMP=%TEMP%\ahs_process_list.txt
tasklist /V > %AHS_PROC_TMP%
for /F "delims=" %%f in (%AHS_PROC_TMP%) do (
    call :SUB_HANDLE_PROC1 "%%f"
)
del > %AHS_PROC_TMP%

endlocal


@echo on
