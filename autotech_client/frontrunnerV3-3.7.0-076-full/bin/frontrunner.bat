@echo off


set _REALPATH=%~dp0

rem Move to the drive where frontrunner is installed.
%~d0

rem config.ini has some relative paths to _REALPATH, so we need to cd into it to have them working properly
cd %_REALPATH%


SETLOCAL

rem setlocal makes all environment variables set applied only for the batch execution context

if "%2" == "embedded" (
    set JAVA_MEM_OPTIONS=-Xloggc:gc.log -Xms356m -Xmx356m -XX:NewSize=32m -XX:MaxNewSize=32m -XX:+UseConcMarkSweepGC -XX:SurvivorRatio=2 -XX:TargetSurvivorRatio=90 -XX:MaxTenuringThreshold=15
) else if "%2" == "playback" (
    set JAVA_MEM_OPTIONS=-Xms1024m -Xmx16G -XX:+UseG1GC -XX:MaxGCPauseMillis=50
) else (
    set JAVA_MEM_OPTIONS=-Xms1024m -Xmx2048m -XX:+UseG1GC -XX:MaxGCPauseMillis=50
)

if "%1" == "console" (
    set START_MODE=console
    call :start %*
) else if "%1" == "start" (
    call :start %*
) else if "%1" == "admin" (
    set START_MODE=console
    call :start console %*
) else if "%1" == "examples" (
    call :print_examples
) else if "%1" == "playback-examples" (
    call :print_playback_examples
) else if "%1" == "help" (
    call :print_help
) else if NOT "%1" == "" (
    call :print_invalid_usage
) else (
    call :print_usage
)

goto :eof

rem /////////////////////////////////////////////////////////////////////////
rem find_conf procedure
rem
:find_conf

    set CONF_DIR=%_REALPATH%..\work\%1
    set CONF_FILE=%CONF_DIR%\config.ini

    set SYSTEM_MODE=%1
    if "%1"=="controller"  (
        set SYSTEM_MODE=CLIENT
        set APP_NAME=_controller
    ) else  if "%1"=="mineview"  (
        set SYSTEM_MODE=CLIENT
        set APP_NAME=_mineview
    ) else  if "%1"=="super"  (
        set SYSTEM_MODE=CLIENT
        set APP_NAME=_super
    ) else  if "%1"=="playback"  (
        set SYSTEM_MODE=PLAYBACK
        set APP_NAME=_playback
    ) else  if "%1"=="server"  (
        set SYSTEM_MODE=SERVER
        set APP_NAME=_server
    ) else  if "%1"=="standalone"  (
        set SYSTEM_MODE=STANDALONE
    ) else  if "%1"=="embedded"  (
        set SYSTEM_MODE=CLIENT
        set APP_NAME=_minemobile
    ) else  if "%1"=="emergency"  (
        set SYSTEM_MODE=CLIENT
        set APP_NAME=_emergencyapp
   ) else  if "%1"=="gnssgs"  (
        set SYSTEM_MODE=NONE
        set APP_NAME=_gnssgs
   ) else  if "%1"=="gnssgm"  (
        set SYSTEM_MODE=NONE
        set APP_NAME=_gnssgm
   )
    if exist "%CONF_FILE%" goto :eof

    echo %CONF_FILE% not found.

    set CONF_FILE=

rem echo %1 not found.
goto :eof


rem /////////////////////////////////////////////////////////////////////////
rem start procedure
rem
rem Arguments:  %1="start" starts in a new window or "console" to start in the same window]
rem             %2=Application to start. There must exist a file at ..\conf\%2.conf
rem             %3=Java application arguments[]
rem
:start
if "%2"=="" (
    call :print_header
    echo. ERROR: Missing command argument!
    call :print_help_usage
    goto :eof
)

call :find_conf %2

if NOT exist "%CONF_FILE%" (
    call :print_header
    echo. ERROR: Invalid command argument: %2 !
    call :print_help_usage
    goto :eof
)

if "%1" == "console" (
    call setColor
)


rem parse java arguments
set JAVA_ARGS=
set count=1
for %%A IN (%*) DO (call :parseArgs %%A)


rem Mantis 0048455: [dev] If OutOfMemory errors happen the application MUST DIE
rem This property is being added to JAVA_OPTIONS instead going to MMS_LAUNCHER_WITH_ARGS, due to the use of double quotes in the parameter    
set _JAVA_OPTIONS=%_JAVA_OPTIONS% -XX:OnOutOfMemoryError="tskill %%p"

rem echo Starting %2...
rem echo =========================================================
set OMSMTU=65536
set DUMP_HEAP="-XX:+HeapDumpOnOutOfMemoryError"
set JAVA_EXTRAS=" -Domsproperties.dir=%_REALPATH%/../conf -Djava.util.Arrays.useLegacyMergeSort=true -Dfile.encoding=UTF8 -Dsun.java2d.xrender=false -Dmariadb.logging.disable=true"
set JMX_ARGS=" -Djava.rmi.server.hostname=IP_GOES_HERE -Dcom.sun.management.jmxremote.local.only=false -Dcom.sun.management.jmxremote.ssl=false -Dcom.sun.management.jmxremote.port=30301 -Dcom.sun.management.jmxremote.authenticate=false"
set PATH=%_REALPATH%..\lib\win32;%PATH%
set EXTERNAL_LIBS=%_REALPATH%..\lib\java\jdom-1.1.jar;%_REALPATH%..\lib\java\jssc-2.8.0.jar;%_REALPATH%..\lib\java\libsocket-can-java-1.0.jar;%_REALPATH%..\lib\java\jdom-1.1.jar;%_REALPATH%..\lib\java\mms-extension-jaas-1.7.0-076.jar;%_REALPATH%..\lib\java\jsch-0.1.53.jar;%_REALPATH%..\lib\java\jPowerShell-1.9.1.jar
set BUNDLES=%_REALPATH%..\bundles\slf4j-api-1.7.25.jar;%_REALPATH%..\bundles\vertx-core-3.9.12.jar;%_REALPATH%..\bundles\vertx-auth-common-3.9.12.jar;%_REALPATH%..\bundles\vertx-web-3.9.12-mms-3.jar;%_REALPATH%..\bundles\netty-buffer-4.1.72.Final.jar;%_REALPATH%..\bundles\netty-codec-http-4.1.72.Final.jar;%_REALPATH%..\bundles\netty-codec-http2-4.1.72.Final.jar;%_REALPATH%..\bundles\netty-codec-dns-4.1.72.Final.jar;%_REALPATH%..\bundles\netty-handler-4.1.72.Final.jar;%_REALPATH%..\bundles\netty-codec-4.1.72.Final.jar;%_REALPATH%..\bundles\netty-common-4.1.72.Final.jar;%_REALPATH%..\bundles\netty-transport-4.1.72.Final.jar;%_REALPATH%..\bundles\netty-resolver-4.1.72.Final.jar;%_REALPATH%..\bundles\netty-resolver-dns-4.1.72.Final.jar
set MMS_LAUNCHER="-XX:-OmitStackTraceInFastThrow -Dfrontrunner.app.name=%APP_NAME% -classpath %_REALPATH%..\lib\java\org.eclipse.osgi-3.11.3.jar;%EXTERNAL_LIBS%;%BUNDLES% org.eclipse.core.runtime.adaptor.EclipseStarter"
set MMS_LAUNCHER_WITH_ARGS=%DUMP_HEAP% %REMOTE_DEBUG% %REMOTE_PROFILE%  %JAVA_EXTRAS% "%JAVA_ARGS% %JAVA_MEM_OPTIONS% -Dosgi.framework.activeThreadType=normal" "-Dosgi.noShutdown=true" "-Declipse.ignoreApp=true" "-Dmms.system.mode=%SYSTEM_MODE%" %MMS_LAUNCHER% "-configuration %CONF_DIR%"
set LOG_TO_CONSOLE="-Dlogback.configurationFile=%_REALPATH%..\conf\logback-console.xml"
set LOG_TO_FILE="-Dlogback.configurationFile=%_REALPATH%..\conf\logback.xml"
set WINDOW_TITLE=frontrunner@%2

if "%START_MODE%"=="console"  (
    TITLE %WINDOW_TITLE%
    starter %LOG_TO_CONSOLE% %MMS_LAUNCHER_WITH_ARGS%
    TITLE frontrunner
) else (
    start "%WINDOW_TITLE%" starter %LOG_TO_FILE% %MMS_LAUNCHER_WITH_ARGS%
)

goto :eof


rem /////////////////////////////////////////////////////////////////////////
rem parseArgs procedure
rem
:parseArgs
    if %count% LSS 3  (
       set /A count=count+1
       goto :eof
    )

    set temp=%~1
    if "%temp:~0,2%"=="-D" set JAVA_ARGS=%JAVA_ARGS% %temp%
    if "%temp:~0,6%"=="-debug" set REMOTE_DEBUG=-Xmx384M "-agentlib:jdwp=transport=dt_socket,address=30303,server=y,suspend=y" %temp%
    rem if "%temp:~0,8%"=="-profile" set REMOTE_PROFILE="-agentpath:%_REALPATH%../lib/deployed/jdk15/profilerinterface.dll=%_REALPATH%../lib/,5140" %temp%
    goto :eof


rem /////////////////////////////////////////////////////////////////////////
rem :print_help_usage
rem
:print_help_usage
echo.
echo. Run "frontrunner help" for more details.
goto :eof


rem /////////////////////////////////////////////////////////////////////////
rem print invalid usage
rem
:print_invalid_usage
call :print_header
echo.
echo ERROR: Invalid command! Run "frontrunner help" for more details.
goto :eof
rem /////////////////////////////////////////////////////////////////////////
rem print header
rem

:print_header
echo FrontRunner - Copyright 2010 Modular Mining System Incorporated.
echo.
goto :eof

rem /////////////////////////////////////////////////////////////////////////
rem print usage procedure
rem
:print_usage
call :print_header
echo Usage:
echo.  frontrunner command [application] [java args]
echo.
goto :eof

rem /////////////////////////////////////////////////////////////////////////
rem help procedure
rem
:print_help
call :print_usage
more %_REALPATH%\help.txt
goto :eof

:print_examples
call :print_header
more %_REALPATH%\examples.txt
goto :eof

:print_playback_examples
call : playback_help
more %_REALPATH%\playbackExamples.txt
goto :eof

:eof
