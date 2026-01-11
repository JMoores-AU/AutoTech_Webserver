@ECHO OFF

REM Optional: enable "stay open" mode if launched with -debug
IF /I "%~1"=="-debug" (
    ECHO Debug mode active - window will persist on errors.
    SET "DEBUG_MODE=1"
)

REM Make sure both Extensions and Delayed Expansion are ON
SETLOCAL ENABLEEXTENSIONS ENABLEDELAYEDEXPANSION
CLS

REM Set console colors - Dark background with green text (mining theme)
COLOR 0F
MODE CON: COLS=95 LINES=35
POWERSHELL -Command "$console = $host.UI.RawUI; $console.BufferSize = New-Object System.Management.Automation.Host.Size(95, 600); $console.WindowSize = New-Object System.Management.Automation.Host.Size(95, 35)" 2>NUL

REM Auto-detect script location and set working directory
SET "SCRIPT_DIR=%~dp0"
REM Remove trailing backslash
SET "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

REM Check if we're in the bin folder, if so go up one level
FOR %%I in ("%SCRIPT_DIR%") DO SET "FOLDER_NAME=%%~nxI"
IF /I "%FOLDER_NAME%"=="bin" (
    FOR %%I in ("%SCRIPT_DIR%\..") DO SET "ROOT_DIR=%%~fI"
) ELSE (
    SET "ROOT_DIR=%SCRIPT_DIR%"
)

REM Change to the root directory
CD /D "%ROOT_DIR%"

REM ===============================================================================
REM  CONFIGURATION VARIABLES
REM ===============================================================================

SET "version=T1_Tools_v2.0_2025_Enhanced"
SET "datFile=bin\IP_list.dat"
SET "logFile=logs\tools_logfile.log"
SET "toolsDir=tools\"
SET "winDir=tools\WinSCP\"
SET "vncDir=tools\VNC\"
SET "truDir=tools\Topcon\"

REM Equipment Credentials
SET "screenUN=dlog"
SET "screenPW=gold"
SET "screenUN2=mms"
SET "screenPW2=modular"
SET "frPW=komatsu"
SET "frUN=administrator"
SET "aviUN=root"
SET "aviPW=root"
SET "gpsUN=modular"
SET "gpsPW=modular"

REM Port Configuration
SET /A vncPortNo=5900
SET /A proxyPortNo=5566
SET /A gps1PortNo=3333
SET /A gps2PortNo=3334

REM Initialize Arrays
SET arraySize=0

REM ===============================================================================
REM  ENHANCED INITIALIZATION WITH VISUAL FEEDBACK
REM ===============================================================================

CLS
ECHO T1 Tools Starting...
ECHO Type 'help' for commands
GOTO initialize

:initialize
    CALL :printHeader
    CALL :initializeSystem
    CALL :loadEquipmentList
    CALL :displayWelcome
    GOTO start

REM ===============================================================================
REM  ENHANCED MAIN COMMAND LOOP
REM ===============================================================================

:start
ECHO.
ECHO [%USERNAME%@AHS_GRM]

SET "command="
SET /P "command=T1> "

IF "!command!"=="" GOTO start
CALL :firstToken commandOne !command!

IF DEFINED DEBUG_MODE ECHO Processing command: !commandOne!

IF /I "!commandOne!"=="help" CALL :help
IF /I "!commandOne!"=="list" CALL :list
IF /I "!commandOne!"=="search" CALL :search
IF /I "!commandOne!"=="debug" CALL :debug
IF /I "!commandOne!"=="exit" CALL :exit
IF /I "!commandOne!"=="e" CALL :exit
IF /I "!commandOne!"=="import" CALL :import

REM PTX Commands
IF /I "!commandOne!"=="vnc" CALL :vnc
IF /I "!commandOne!"=="putty" CALL :putty
IF /I "!commandOne!"=="ping" CALL :ping
IF /I "!commandOne!"=="config" CALL :config
IF /I "!commandOne!"=="ptxr" CALL :ptxr
IF /I "!commandOne!"=="win" CALL :win
IF /I "!commandOne!"=="ptxlogs" CALL :ptxlogs
IF /I "!commandOne!"=="cache" CALL :cache
IF /I "!commandOne!"=="delcache" CALL :delcache

REM GNSS Commands
IF /I "!commandOne!"=="tru" CALL :tru
IF /I "!commandOne!"=="gnsslogs" CALL :gnsslogs

REM Flight Recorder Commands
IF /I "!commandOne!"=="atmon" CALL :atmon
IF /I "!commandOne!"=="frdownload" CALL :frdownload
IF /I "!commandOne!"=="frreset" CALL :frreset
IF /I "!commandOne!"=="frlogin" CALL :frlogin

REM AVI Commands
IF /I "!commandOne!"=="avi" CALL :avi
IF /I "!commandOne!"=="avilogs" CALL :avilogs

GOTO start

REM ===============================================================================
REM  VISUAL HELPER FUNCTIONS
REM ===============================================================================

:printHeader
    CLS
    ECHO.
    ECHO  ========================================================================
    ECHO                   T1 TOOLS - KOMATSU TIER 1 REMOTE ACCESS
    ECHO                        		Version 2.0
    ECHO  ========================================================================
    ECHO.
    GOTO :EOF
	
REM ===============================================================================
REM  SYSTEM INITIALIZATION FUNCTIONS
REM ===============================================================================

:initializeSystem
    REM Create required directories
    IF NOT EXIST "bin" MKDIR "bin"
    IF NOT EXIST "temp" MKDIR "temp"
    IF NOT EXIST "logs" MKDIR "logs"
    
    REM Initialize logging and trim if needed (once per session)
    IF NOT EXIST "!logFile!" (
        ECHO T1 Tools Log File - Created !DATE! !TIME! > "!logFile!"
        ECHO ============================================================ >> "!logFile!"
    ) ELSE (
        CALL :trimLogFile
    )
    
    REM Log session start
    ECHO. >> "!logFile!"
    ECHO [!DATE! !TIME!] SESSION START - User: !USERNAME! - Computer: !COMPUTERNAME! >> "!logFile!"
    
    REM Simple SSH check without calling other functions
    ssh -V >NUL 2>&1
    IF !ERRORLEVEL! EQU 0 (
        SET "SSH_AVAILABLE=1"
        ECHO Using SSH client. 
    ) ELSE (
        SET "SSH_AVAILABLE=0"
        ECHO Using putty client.
    )
    
    ECHO Initialization complete...
    GOTO :EOF

:loadEquipmentList
    IF EXIST "!datFile!" (
        ECHO Loading equipment list...
		ECHO.
        CALL :load
    ) ELSE (
        ECHO Equipment list not found: !datFile!
        ECHO Create manually or use the import command
        ECHO.
    )
    GOTO :EOF

:displayWelcome
    ECHO.                                                                  
    ECHO  Type 'help' for commands    
	ECHO.
	ECHO  Type 'list' to see all equipment
	ECHO.
    ECHO  Type 'search [equipID]' to find specific equipment (e.g., search RD190)
	ECHO.
    ECHO ================================================================================
    
    GOTO :EOF

REM ===============================================================================
REM  HELP SYSTEM
REM ===============================================================================

:help
    CALL :writeToLog "Help accessed"
    
    REM Create temporary HTML file
    SET "helpFile=%TEMP%\T1_Tools_Help.html"
    
    (
        ECHO ^<!DOCTYPE html^>
        ECHO ^<html^>^<head^>
        ECHO ^<title^>T1 TOOLS - COMMAND REFERENCE^</title^>
        ECHO ^<style^>
        ECHO body { font-family: 'Segoe UI', Arial, sans-serif; background-color: #f8f9fa; color: #333; margin: 30px; line-height: 1.6; }
        ECHO h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }
        ECHO h2 { color: #34495e; margin-top: 30px; margin-bottom: 15px; }
        ECHO .command { color: #e74c3c; font-weight: bold; font-family: 'Courier New', monospace; }
        ECHO .description { color: #555; margin-left: 20px; margin-bottom: 8px; }
        ECHO hr { border: none; height: 2px; background-color: #bdc3c7; margin: 20px 0; }
        ECHO .section { margin-bottom: 25px; }
        ECHO ^</style^>
        ECHO ^</head^>^<body^>
        ECHO ^<h1^>T1 TOOLS - COMMAND REFERENCE^</h1^>
        ECHO.
        ECHO ^<div class="section"^>
        ECHO ^<h2^>PTX COMMANDS^</h2^>
        ECHO ^<div class="command"^>vnc [equipment]^</div^>^<div class="description"^>Opens VNC connection with automatic login^</div^>
        ECHO ^<div class="command"^>putty [equipment]^</div^>^<div class="description"^>Opens PuTTY SSH terminal^</div^>
        ECHO ^<div class="command"^>ping [equipment]^</div^>^<div class="description"^>Tests connectivity to all components^</div^>
        ECHO ^<div class="command"^>config [equipment]^</div^>^<div class="description"^>Runs PTX configuration (PTXC only^)^</div^>
        ECHO ^<div class="command"^>ptxr [equipment]^</div^>^<div class="description"^>Reboots PTX system^</div^>
        ECHO ^<div class="command"^>win [equipment]^</div^>^<div class="description"^>Opens WinSCP to PTX filesystem^</div^>
        ECHO ^<div class="command"^>ptxlogs [equipment]^</div^>^<div class="description"^>Opens WinSCP to PTX log directory^</div^>
        ECHO ^<div class="command"^>cache [equipment]^</div^>^<div class="description"^>Opens WinSCP to cache directory^</div^>
        ECHO ^<div class="command"^>delcache [equipment]^</div^>^<div class="description"^>Deletes cache and reboots PTX^</div^>
        ECHO ^</div^>
        ECHO.
        ECHO ^<div class="section"^>
        ECHO ^<h2^>GNSS COMMANDS^</h2^>
        ECHO ^<div class="command"^>tru [equipment]^</div^>^<div class="description"^>Creates GNSS tunnels and opens TRU utility^</div^>
        ECHO ^<div class="command"^>gnsslogs [equipment]^</div^>^<div class="description"^>Opens WinSCP to GNSS log directories^</div^>
        ECHO ^</div^>
        ECHO.
        ECHO ^<div class="section"^>
        ECHO ^<h2^>FLIGHT RECORDER COMMANDS^</h2^>
        ECHO ^<div class="command"^>atmon [equipment]^</div^>^<div class="description"^>Creates tunnel and opens ATMonitor^</div^>
        ECHO ^<div class="command"^>frdownload [equipment]^</div^>^<div class="description"^>Opens WinSCP to Flight Recorder^</div^>
        ECHO ^<div class="command"^>frdownload -ssl [equipment]^</div^>^<div class="description"^>Same with SSL (for Dash 5 trucks^)^</div^>
        ECHO ^<div class="command"^>frreset [equipment]^</div^>^<div class="description"^>Resets Flight Recorder^</div^>
        ECHO ^<div class="command"^>frlogin [equipment]^</div^>^<div class="description"^>Opens RDP session to Flight Recorder^</div^>
        ECHO ^</div^>
        ECHO.
        ECHO ^<div class="section"^>
        ECHO ^<h2^>AVI COMMANDS^</h2^>
        ECHO ^<div class="command"^>avi [equipment]^</div^>^<div class="description"^>Opens browser to AVI radio interface^</div^>
        ECHO ^<div class="command"^>avilogs [equipment]^</div^>^<div class="description"^>Opens WinSCP to AVI log directory^</div^>
        ECHO ^</div^>
        ECHO.
        ECHO ^<div class="section"^>
        ECHO ^<h2^>SYSTEM COMMANDS^</h2^>
        ECHO ^<div class="command"^>help^</div^>^<div class="description"^>Shows this command reference^</div^>
        ECHO ^<div class="command"^>list^</div^>^<div class="description"^>Shows all loaded equipment (with optional filter^)^</div^>
        ECHO ^<div class="command"^>search [term]^</div^>^<div class="description"^>Searches equipment by name (e.g., search RD1^)^</div^>
        ECHO ^<div class="command"^>debug [equipment]^</div^>^<div class="description"^>Debug equipment lookup (e.g., debug RD190^)^</div^>
        ECHO ^<div class="command"^>import^</div^>^<div class="description"^>Import equipment list from server^</div^>
        ECHO ^<div class="command"^>exit^</div^>^<div class="description"^>Saves data and exits^</div^>
        ECHO ^</div^>
        ECHO ^</body^>^</html^>
    ) > "%helpFile%"
    
    REM Open in Edge
    START msedge "%helpFile%"
    
    ECHO Help opened in Microsoft Edge.
    GOTO :EOF

:search
    CALL :secondToken equipName !command!
    CALL :getEquipPTXAddress IP !equipName!
    CALL :getEquipAVIAddress aviIP !equipName!
    IF NOT "!IP!"=="null" (
        ECHO !equipName! - PTX: !IP! - AVI: !aviIP!
    ) ELSE (
        ECHO Equipment not found: !equipName!
    )
    GOTO :EOF
    
:debug
    CALL :secondToken equipName !command!
    IF "!equipName!"=="" (
        ECHO Error: Equipment name required for debug
        ECHO Usage: debug [equipment_name]
        ECHO Example: debug RD190
        GOTO :EOF
    )
    
    ECHO.
    ECHO DEBUG: Equipment lookup for "!equipName!"
    ECHO ================================================================================
    ECHO Input equipment name: !equipName!
    
    CALL :getEquipPTXAddress debugIP !equipName!
    CALL :getEquipAVIAddress debugAVI !equipName!
    
    ECHO PTX IP found: !debugIP!
    ECHO AVI IP found: !debugAVI!
    ECHO.
    
    ECHO Searching for exact matches in database:
    SET count=0
    SET /A lastEntry= !arraySize! - 1
    FOR /L %%n in (0,1,!lastEntry!) do (
        SET "dbName=!name[%%n]!"
        SET "testName=!equipName!"
        CALL :toUCase dbName
        CALL :toUCase testName
        ECHO Testing: "!dbName!" vs "!testName!"
        IF "!dbName!"=="!testName!" (
            ECHO MATCH FOUND: !name[%%n]! - PTX: !ptxIP[%%n]! - AVI: !aviIP[%%n]!
            SET /A count+=1
        )
    )
    
    IF !count! EQU 0 (
        ECHO No exact matches found. Try 'search !equipName!' for partial matches.
    )
    
    ECHO ================================================================================
	IF DEFINED DEBUG_MODE PAUSE
    GOTO :EOF

REM ===============================================================================
REM  EQUIPMENT MANAGEMENT FUNCTIONS
REM ===============================================================================

:load
    SET /A recordToLoad=1
    SET /A lineNumber=0
    FOR /F "usebackq tokens=*" %%a in ("!datFile!") do (
        SET /A lineNumber+=1
        SET "line=%%a"
        REM Skip empty lines and comment lines
        IF NOT "!line!"=="" (
            IF NOT "!line:~0,1!"=="#" (
                CALL :parseLine "!line!"
            )
        )
    )
    IF !arraySize! GTR 0 (
        ECHO Loaded !arraySize! equipment profiles
    ) ELSE (
        ECHO Warning: No valid equipment entries found in !datFile!
    )
    GOTO :EOF

:parseLine
    SET "line=%~1"
    SET "nameIn="
    SET "ptxIPIn="
    SET "aviIPIn="
    
    REM Parse the line manually
    FOR /F "tokens=1,2,3 delims= " %%A in ("!line!") DO (
        SET "nameIn=%%A"
        SET "ptxIPIn=%%B"
        SET "aviIPIn=%%C"
    )
    
    REM Skip header line
    IF /I "!nameIn!"=="Name" GOTO :EOF
    
    REM Validate we have at least name and PTX IP
    IF NOT "!nameIn!"=="" (
        IF NOT "!ptxIPIn!"=="" (
            IF "!aviIPIn!"=="" SET "aviIPIn=unknown"
            
            REM Check for duplicates
            SET "isDuplicate=0"
            SET /A lastEntry= !arraySize! - 1
            FOR /L %%n in (0,1,!lastEntry!) do (
                IF /I "!name[%%n]!"=="!nameIn!" SET "isDuplicate=1"
            )
            
            REM Only add if not duplicate
            IF "!isDuplicate!"=="0" (
                SET name[!arraySize!]=!nameIn!
                SET ptxIP[!arraySize!]=!ptxIPIn!
                SET aviIP[!arraySize!]=!aviIPIn!
                SET /A arraySize += 1
            )
        )
    )
    GOTO :EOF

:getEquipPTXAddress
    SET %~1=null
    SET /A lastEntry= !arraySize! - 1
    FOR /L %%n in (0,1,!lastEntry!) do (
        SET "equipName=!name[%%n]!"
        SET "searchName=%2"
        CALL :toUCase equipName
        CALL :toUCase searchName
        IF "!equipName!"=="!searchName!" (
            SET %~1=!ptxIP[%%n]!
            GOTO :EOF
        )
    )
    GOTO :EOF

:getEquipAVIAddress
    SET %~1=unknown    
    SET /A lastEntry= !arraySize! - 1
    FOR /L %%n in (0,1,!lastEntry!) do (
        SET "equipName=!name[%%n]!"
        SET "searchName=%2"
        CALL :toUCase equipName
        CALL :toUCase searchName
        IF "!equipName!"=="!searchName!" (
            SET %~1=!aviIP[%%n]!
            GOTO :EOF
        )
    )
    GOTO :EOF

:list
    ECHO.
    ECHO Equipment List (%arraySize% total units):
    ECHO ================================================================================
    
    IF !arraySize! EQU 0 (
        ECHO  No equipment loaded. Create bin\IP_list.dat file.
        ECHO.
        ECHO  Format: Name PTX_IP AVI_IP
        ECHO  Example: RD191 10.110.14.191 192.168.1.100
    ) ELSE (
        SET /A lastEntry= !arraySize! - 1
        FOR /L %%n in (0,1,!lastEntry!) do (
            ECHO  !name[%%n]! - PTX: !ptxIP[%%n]! - AVI: !aviIP[%%n]!
        )
    )
    
    ECHO ================================================================================
    GOTO :EOF

REM ===============================================================================
REM  AVI SCRIPTS
REM ===============================================================================

:avilogs
    CALL :writeToLog "Access AVI Log Files"
    CALL :winscp
    CALL :secondToken equipName !command!
    CALL :toUCase equipName
    CALL :getEquipPTXAddress IP !equipName!
    CALL :getEquipAVIAddress aviIP !equipName!
    IF !IP!==null (
        ECHO.
        ECHO Equipment !equipName! not found. Check spelling or use import if new equipment. 
        GOTO start
    ) 
    IF "!aviIP!"=="unknown" (
        ECHO AVI IP not found. Attempting to obtaining Embedded IP.
        CALL :getAVIIP
        CALL :updateAVI
        GOTO avilogsfinish
    ) ELSE (
        GOTO avilogsfinish 
    )

    :avilogsfinish  
        ECHO Opening WinSCP to !aviIP! log folder...
        START !winDir!WinSCP.exe scp://!aviUN!:!aviPW!@!aviIP!/mnt/bulk/
        START "" "!toolsDir!HotKey.exe" /Force "temp\winscp.ahk"
        TIMEOUT /t 5 /nobreak > NUL
        TASKKILL /F /IM HotKey.exe > NUL 2>&1
        
        GOTO :EOF

:avi
    CALL :writeToLog "Login to AVI Radio"
    CALL :secondToken equipName !command!
    CALL :toUCase equipName
    CALL :getEquipPTXAddress IP !equipName!
    CALL :getEquipAVIAddress aviIP !equipName!
    CALL :putkey
    IF !IP!==null (
        ECHO.
        ECHO Equipment !equipName! not found. Check spelling or use import if new equipment. 
        GOTO start
    ) 
    REM AVI IP Pre-check
    IF "!aviIP!"=="unknown" (
        ECHO AVI IP not found. Attempting to obtain Embedded IP.
        CALL :getAviIP
        IF EXIST "%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe" (
            ECHO Opening Edge browser... 
            START msedge !aviIP! 
            GOTO aviFinish 
        )
        IF EXIST "%ProgramFiles%\Google\Chrome\Application\chrome.exe" (
            ECHO Opening Chrome browser...
            START chrome !aviIP!
            GOTO aviFinish
        )
        CALL :updateAVI
        GOTO aviFinish
    ) ELSE (
        ECHO The AVI IP for !equipName! is: !aviIP!
        PING -n 1 !aviIP! > NUL
        IF !ERRORLEVEL! NEQ 0 (
            ECHO.
            ECHO "Unable to reach !equipName! via !aviIP!, AVI Radio is offline."
            GOTO start 
        )
        IF EXIST "%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe" (
            ECHO Opening Edge browser... 
            START msedge !aviIP! 
            GOTO aviFinish 
        )
        IF EXIST "%ProgramFiles%\Google\Chrome\Application\chrome.exe" (
            ECHO Opening Chrome browser...
            START chrome !aviIP!
            GOTO aviFinish
        )
    )

    :getAviIP
    PING -n 1 !IP! > NUL
    IF !ERRORLEVEL! NEQ 0 (
        ECHO "Unable to reach PTX on !equipName! !IP!, equipment is offline."
        GOTO start 
    )
    ECHO Equip Online... !IP!
    CALL :hostkey
    SET TempFile=temp\temp_errorlevel.txt
    TIMEOUT /T 2 > NUL
    START cmd /c "!toolsDir!%PLINK_PATH% -v -batch -l dlog -pw gold !IP! 'ls /' & ECHO !ERRORLEVEL! > "!TempFile!""
    TIMEOUT /T 2 > NUL
    FOR /F "delims=" %%A in ('type "!TempFile!"') DO SET "ERRORLEV=%%A"
    ECHO.
    IF "!ERRORLEV!"=="0 " (
        ECHO PTXC
    ) ELSE (
        ECHO PTX10
        GOTO aviPTX10
    )
    
    DEL "!TempFile!"
    ECHO Attempting to obtain embedded via !IP!
    SET /A aviPortNo+=1
    ECHO sleep 10; exit > temp\autoTunnelCloseCmd
    ECHO ifconfig mob1p1_1 ^| grep -E -o "inet addr:([0-9]{1,3}\.){3}[0-9]{1,3}" > temp\radIPCmd
    START !toolsDir!putty.exe -L !aviPortNo!:192.168.0.254:22 -l dlog -pw gold "!IP!" -m temp\autoTunnelCloseCmd
    TIMEOUT /t 2 /nobreak > NUL
    SET "aviIP=unknown"
    FOR /F "tokens=2 delims=:" %%a in ('echo yes ^| "!toolsDir!%PLINK_PATH%" -batch -l root -pw root -P !aviPortNo! 127.0.0.1 -m temp\radIPCmd') DO (
        SET "aviIP=%%a"
    )
    ECHO Embedded AVI IP Address found: !aviIP!
    TASKKILL /F /IM putty.exe > NUL 2>&1
    GOTO :EOF

    :aviPTX10
    ECHO Attempting to obtain embedded via !IP!
    SET /A aviPortNo+=1
    ECHO sleep 10; exit > temp\autoTunnelCloseCmd
    ECHO ifconfig mob1p1_1 ^| grep -E -o "inet addr:([0-9]{1,3}\.){3}[0-9]{1,3}" > temp\radIPCmd
    START /min !toolsDir!putty.exe -L !aviPortNo!:192.168.0.254:22 -l mms -pw modular "!IP!" -m temp\autoTunnelCloseCmd
    TIMEOUT /t 2 /nobreak > NUL
    SET "aviIP=unknown"
    FOR /F "tokens=2 delims=:" %%a in ('echo yes ^| "!toolsDir!%PLINK_PATH%" -batch -l root -pw root -P !aviPortNo! 127.0.0.1 -m temp\radIPCmd') DO (
        SET "aviIP=%%a"
    )
    ECHO Embedded AVI IP Address found: !aviIP!
    TASKKILL /F /IM putty.exe > NUL 2>&1
    GOTO :EOF
    
    :updateAVI
    SET tempFile=temp\tempIPList.dat
    IF !aviIP!==unknown (
        ECHO AVI IP is still unknown. Exiting.
        GOTO :EOF
    )
    IF NOT EXIST "!datFile!" (
        ECHO IP file not found: !datFile!
        GOTO :EOF
    )
    > "!tempFile!" (
        FOR /F "tokens=1,2,3" %%A IN ('type "!datFile!"') DO (
            IF "%%A"=="!equipName!" (
                ECHO %%A %%B !aviIP!
            ) ELSE (
                ECHO %%A %%B %%C
            )
        )
    )
    MOVE /Y "!tempFile!" "!datFile!" > NUL 2>&1 
    IF EXIST "!tempFile!" DEL "!tempFile!"
    ECHO Updating and reloading .dat file...
    CALL :load
    GOTO :EOF
    
    :aviFinish
    TASKKILL /F /IM putty.exe > NUL 2>&1
    TASKKILL /F /IM HotKey.exe > NUL 2>&1  
    
    GOTO :EOF

REM ===============================================================================
REM  GNSS COMMANDS
REM ===============================================================================

:tru
    CALL :writeToLog "Access GNSS via TRU"
    CALL :putkey
    CALL :topcon
    CALL :gpsencrypt
    CALL :secondToken equipName !command!
    CALL :toUCase equipName
    CALL :getEquipPTXAddress IP !equipName!
    IF !IP!==null (
        ECHO.
        ECHO Equipment !equipName! not found. Check spelling or use import if new equipment. 
        GOTO start
    ) 
    PING -n 1 !IP! > NUL
    IF !ERRORLEVEL! NEQ 0 (
        ECHO.
        ECHO "Unable to reach !equipName! on !IP!, skipping TRU session."
        GOTO start
    )
    ECHO.
    CALL :hostkey
    ECHO Equipment Online "!IP!"
    SET TempFile=temp\temp_errorlevel.txt
    TIMEOUT /T 2 > NUL
    START cmd /c "!toolsDir!%PLINK_PATH% -v -batch -l dlog -pw gold !IP! 'ls /' & ECHO !ERRORLEVEL! > "!TempFile!""
    TIMEOUT /T 2 > NUL
    FOR /F "delims=" %%A in ('type "!TempFile!"') DO SET "ERRORLEV=%%A"
    ECHO.
    IF "!ERRORLEV!"=="0 " (
        ECHO PTXC
    ) ELSE (
        ECHO PTX10
        GOTO truPTX10
    )
    
    DEL "!TempFile!"
    REM Connect via PTXC
    START /min "!equipName! - GNSS 1" !toolsDir!%PLINK_PATH% -v -batch -L !gps1PortNo!:192.168.0.101:8002 dlog@!IP! -pw gold -N
    START /min "!equipName! - GNSS 2" !toolsDir!%PLINK_PATH% -v -batch -L !gps2PortNo!:192.168.0.102:8002 dlog@!IP! -pw gold -N      
    ECHO Tunnel to GNSS 1 and GNSS 2 open via PTXC, opening TRU. Please wait...
    TIMEOUT /t 4 /nobreak > NUL
    START "" "!truDir!TRU.exe" 
    TIMEOUT /t 2 /nobreak > NUL
    START "" "!toolsDir!HotKey.exe" /FORCE "temp\topcon.ahk"
    GOTO truFinish
    
    REM Connect via PTX10
    :truPTX10
        START /min "!equipName! - GNSS 1" !toolsDir!%PLINK_PATH% -v -batch -L !gps1PortNo!:192.168.0.101:8002 mms@!IP! -pw modular -N
        START /min "!equipName! - GNSS 2" !toolsDir!%PLINK_PATH% -v -batch -L !gps2PortNo!:192.168.0.102:8002 mms@!IP! -pw modular -N      
        ECHO Tunnel to GNSS 1 and GNSS 2 open via PTX10, opening TRU. Please wait...
        TIMEOUT /t 4 /nobreak > NUL
        START "" "!truDir!TRU.exe" 
        TIMEOUT /t 2 /nobreak > NUL
        START "" "!toolsDir!HotKey.exe" /FORCE "temp\topcon.ahk"
        GOTO truFinish
    
    :truFinish
    TASKKILL /F /IM HotKey.exe > NUL 2>&1
    GOTO :EOF

:gnsslogs
    CALL :writeToLog "Access GNSS 1 logs"
    CALL :putencrypt
    TIMEOUT /t 1 /nobreak > NUL
    SET /A proxyPortNo=!proxyPortNo! + 1
    CALL :secondToken equipName !command!
    CALL :toUCase equipName
    CALL :getEquipPTXAddress IP !equipName!
    IF !IP!==null (
        ECHO.
        ECHO Equipment !equipName! not found. Check spelling or use import if new equipment.
        GOTO start
    ) 
    REM Pre-Check
    PING -n 1 !IP! > NUL
    IF !ERRORLEVEL! NEQ 0 (
        ECHO.
        ECHO "Unable to reach !equipName! on !IP!, skipping WinSCP session."
        GOTO start 
    )
    CALL :hostkey
    SET TempFile=temp\temp_errorlevel.txt
    TIMEOUT /T 2 > NUL
    START cmd /c "!toolsDir!%PLINK_PATH% -v -batch -l dlog -pw gold !IP! 'ls /' & ECHO !ERRORLEVEL! > "!TempFile!""
    TIMEOUT /T 2 > NUL
    FOR /F "delims=" %%A in ('type "!TempFile!"') DO SET "ERRORLEV=%%A"
    ECHO.
    IF "!ERRORLEV!"=="0 " (
        ECHO PTXC
    ) ELSE (
        ECHO PTX10
        GOTO gnsslogsPTX10
    )
    
    DEL "!TempFile!"
    ECHO Equipment Online, !IP!
    START /min !toolsDir!putty.exe -D !proxyPortNo! dlog@!IP! -pw gold -N
    START "" "!toolsDir!HotKey.exe" "temp\putty_key.ahk"
    TIMEOUT /t 2 /nobreak > NUL
    ECHO Tunnel to GNSS open via PTXC, Starting winSCP...
    TIMEOUT /t 2 /nobreak > NUL
    START !winDir!WinSCP.exe ftp://!gpsUN!:!gpsPW!@192.168.0.101 -rawsettings ProxyMethod=2 ProxyHost=127.0.0.1 ProxyPort=!proxyPortNo!
    START !winDir!WinSCP.exe ftp://!gpsUN!:!gpsPW!@192.168.0.102 -rawsettings ProxyMethod=2 ProxyHost=127.0.0.1 ProxyPort=!proxyPortNo!
    GOTO gnsslogsFinish
    
    :gnsslogsPTX10
        ECHO Equipment Online, !IP!
        START /min !toolsDir!putty.exe -D !proxyPortNo! mms@!IP! -pw modular -N
        START "" "!toolsDir!HotKey.exe" "temp\putty_key.ahk"
        TIMEOUT /t 2 /nobreak > NUL
        ECHO Tunnel to GNSS open va PTX10, Starting winSCP...
        TIMEOUT /t 2 /nobreak > NUL
        START !winDir!WinSCP.exe ftp://!gpsUN!:!gpsPW!@192.168.0.101 -rawsettings ProxyMethod=2 ProxyHost=127.0.0.1 ProxyPort=!proxyPortNo!
        START !winDir!WinSCP.exe ftp://!gpsUN!:!gpsPW!@192.168.0.102 -rawsettings ProxyMethod=2 ProxyHost=127.0.0.1 ProxyPort=!proxyPortNo!
        GOTO gnsslogsFinish
    
    :gnsslogsFinish
        TASKKILL /F /IM HotKey.exe > NUL 2>&1
        GOTO :EOF

REM ===============================================================================
REM  ATMONITOR SCRIPTS
REM ===============================================================================

:atmon
    CALL :writeToLog "Load ATMonitor remotley."
    CALL :putkey
    CALL :atmon
    CALL :putencrypt
    SET PROGRAMNAME=ATMonitor.exe
    SET FOUND=
    FOR /f "tokens=1" %%D in ('wmic logicaldisk where drivetype^=2 get DeviceID 2^>nul ^| find ":"') DO (
        SET DRIVE=%%D
        FOR /f "delims=" %%F in ('dir !DRIVE!\%PROGRAMNAME% /s /b /a:-d 2^>nul') DO (
        SET FOUND=%%F
        )
    )
    CALL :secondToken equipName !command!
    CALL :toUCase equipName
    CALL :getEquipPTXAddress IP !equipName!
    IF !IP!==null (
        ECHO.
        ECHO Equipment !equipName! not found. Check spelling or use import if new equipment. 
        GOTO start
    ) 
    PING -n 1 !IP! > NUL
    IF !ERRORLEVEL! NEQ 0 (
        ECHO.
        ECHO "Unable to reach !equipName! on !IP!, aborting connection."
        GOTO start 
    )
    CALL :hostkey
    SET TempFile=temp\temp_errorlevel.txt
    TIMEOUT /T 2 > NUL
    START cmd /c "!toolsDir!%PLINK_PATH% -v -batch -l dlog -pw gold !IP! 'ls /' & ECHO !ERRORLEVEL! > "!TempFile!""
    TIMEOUT /T 2 > NUL
    FOR /F "delims=" %%A in ('type "!TempFile!"') DO SET "ERRORLEV=%%A"
    ECHO.
    IF "!ERRORLEV!"=="0 " (
        ECHO PTXC
    ) ELSE (
        ECHO PTX10
        GOTO atmonPTX10
    )
    
    DEL "!TempFile!"
    
    ECHO Equipment online, !IP!
    CALL :getFRIPAddress frIP !IP!
    TIMEOUT /t 1 /nobreak > NUL
    ECHO FlightRecorder IP: !frIP!
    START /min !toolsDir!putty.exe -L 50000:!frIP!:50000 dlog@!IP! -pw gold -N
    START "" "!toolsDir!HotKey.exe" "temp\putty_key.ahk"
    TIMEOUT /t 4 /nobreak > NUL
    START "" "!toolsDir!HotKey.exe" "temp\putty_encrypt.ahk"
    ECHO Tunnel created to FlightRecorder via PTXC...
    TIMEOUT /t 2 /nobreak > NUL
    IF defined FOUND (
        ECHO Opening %FOUND%. please wait...
        START "" "%FOUND%"
        START "" "!toolsDir!HotKey.exe" "temp\atmon.ahk"
        TIMEOUT /t 4 /nobreak > NUL
        TASKKILL /F /IM HotKey.exe > NUL 2>&1
        GOTO atmonFinish
    ) ELSE (
        ECHO External program not found,
        ECHO Open ATMonitor 3.7.0 using port 127.0.0.1
        GOTO atmonFinish 
    )
            
        :atmonPTX10
            ECHO Equipment online, !IP!
            CALL :getFRIPAddress frIP !IP!
            ECHO FlightRecorder IP: !frIP!
            START /min !toolsDir!putty.exe -L 50000:!frIP!:50000 mms@!IP! -pw modular -N
            TIMEOUT /t 1 /nobreak > NUL
            START "" "!toolsDir!HotKey.exe" "temp\putty_key.ahk"
            TIMEOUT /t 4 /nobreak > NUL
            START "" "!toolsDir!HotKey.exe" "temp\putty_encrypt.ahk"
            ECHO Tunnel created to FlightRecorder via PTX10
            TIMEOUT /t 2 /nobreak > NUL
            IF defined FOUND (
                ECHO Opening %FOUND%. please wait...
                START "" "%FOUND%"
                START "" "!toolsDir!HotKey.exe" "temp\atmon.ahk"
                TIMEOUT /t 4 /nobreak > NUL
                GOTO atmonFinish
            ) ELSE (
                ECHO External program not found,
                ECHO Open ATMonitor 3.7.0 using port 127.0.0.1
                GOTO atmonFinish 
            )
    
    :atmonFinish
    TASKKILL /F /IM HotKey.exe > NUL 2>&1
    GOTO :EOF

REM ===============================================================================
REM  FLIGHT RECORDER SCRIPTS
REM ===============================================================================

:frdownload
    CALL :writeToLog "Access FlightRecorder data."
    SET ssl=
    SET /A proxyPortNo=!proxyPortNo! + 1
    CALL :secondToken equipName !command!
    CALL :toUCase equipName
    CALL :putkey

    IF !equipName!==-SSL (
        SET ssl=-explicittls
        CALL :thirdToken equipName !command!
        CALL :toUCase equipName
    )
    CALL :getEquipPTXAddress IP !equipName!
    IF !IP!==null (
        ECHO.
        ECHO Equipment !equipName! not found. Check spelling or use import if new equipment. 
        GOTO start
    ) 
    PING -n 1 !IP! > NUL
    IF !ERRORLEVEL! NEQ 0 (
        ECHO.
        ECHO "Unable to reach !equipName! on !IP!, skipping WinSCP session."
        GOTO start 
    )
    CALL :hostkey
    SET TempFile=temp\temp_errorlevel.txt
    TIMEOUT /T 2 > NUL
    START cmd /c "!toolsDir!%PLINK_PATH% -v -batch -l dlog -pw gold !IP! 'ls /' & ECHO !ERRORLEVEL! > "!TempFile!""
    TIMEOUT /T 2 > NUL
    FOR /F "delims=" %%A in ('type "!TempFile!"') DO SET "ERRORLEV=%%A"
    ECHO.
    IF "!ERRORLEV!"=="0 " (
        ECHO PTXC
    ) ELSE (
        ECHO PTX10
        GOTO frdownPTX10
    )
    
    DEL "!TempFile!"
    ECHO Equipment online, !IP!
    START /min !toolsDir!putty.exe -D !proxyPortNo! dlog@!IP! -pw gold -N
    START "" "!toolsDir!HotKey.exe" /Force "temp\putty_key.ahk"
    TIMEOUT /t 2 /nobreak > NUL
    CALL :getFRIPAddress frIP !IP!
    ECHO Proxy opened to PTXC...
    START !winDir!WinSCP.exe ftp://!frUN!:!frPW!@!frIP! !ssl! -rawsettings ProxyMethod=2 ProxyHost=127.0.0.1 ProxyPort=!proxyPortNo!
    ECHO Opening winSCP... 
    GOTO frdownFinish 
        
        :frdownPTX10
            ECHO Equipment online, !IP!
            START /min !toolsDir!putty.exe -D !proxyPortNo! mms@!IP! -pw modular -N
            START "" "!toolsDir!HotKey.exe" /Force "temp\putty_key.ahk"
            TIMEOUT /t 2 /nobreak > NUL
            CALL :getFRIPAddress frIP !IP!
            ECHO Proxy opened to PTXC...
            START !winDir!WinSCP.exe ftp://!frUN!:!frPW!@!frIP! !ssl! -rawsettings ProxyMethod=2 ProxyHost=127.0.0.1 ProxyPort=!proxyPortNo!
            ECHO Opening winSCP... 
            GOTO :frdownFinish
        
    :frdownFinish
    DEL /f temp\putty_key.ahk
    GOTO :EOF

:frreset
    CALL :writeToLog "Reset Flight Recorder remotley."
    REM loop through arguments so multiple flight recorders can be reset at once
    FOR %%a in (!command!) DO (
        SET equipName=%%a
        CALL :toUCase equipName
        CALL :getEquipPTXAddress IP !equipName!
        IF !IP!==null (
            ECHO.
            ECHO Equipment !equipName! not found. Check spelling or use import if new equipment. 
            GOTO start
        ) 
        REM shitty solution to not being able to easily strip the first token from the string in windows batch script
        IF NOT %%a==frreset (
            ECHO.
            ECHO Begining Flight Recorder reset process for !equipName!
            CALL :getFRIPAddress frIP !IP!
            REM create one liner command for putty to run on PTXC
            ECHO echo -e ^"e\ns\nq^" ^| timeout 10 nc -ti 2 !frIP! 23 ^& wait^; exit > frresetcmd
            !toolsDir!putty.exe -ssh !IP! -l dlog -pw gold -m frresetCmd
            DEL /f frresetCmd
        )
    )
    GOTO :EOF

:frlogin
    CALL :writeToLog "Access Flight Recorder via RDP."
    SET /A vncPortNo=!vncPortNo! + 1
    CALL :rdplogin
    CALL :putkey
    CALL :rdpencrypt
    CALL :secondToken equipName !command!
    CALL :toUCase equipName
    CALL :getEquipPTXAddress IP !equipName!
    IF !IP!==null (
        ECHO.
        ECHO Equipment !equipName! not found. Check spelling or use import if new equipment. 
        GOTO start
    ) 
    PING -n 1 !IP! > NUL
    IF !ERRORLEVEL! NEQ 0 (
        ECHO.
        ECHO "Unable to reach !equipName! on !IP!, skipping RDP session."
        GOTO start
    )
    CALL :hostkey
    SET TempFile=temp\temp_errorlevel.txt
    TIMEOUT /T 2 > NUL
    START cmd /c "!toolsDir!%PLINK_PATH% -v -batch -l dlog -pw gold !IP! 'ls /' & ECHO !ERRORLEVEL! > "!TempFile!""
    TIMEOUT /T 2 > NUL
    FOR /F "delims=" %%A in ('type "!TempFile!"') DO SET "ERRORLEV=%%A"
    ECHO.
    IF "!ERRORLEV!"=="0 " (
        ECHO PTXC
    ) ELSE (
        ECHO PTX10
        GOTO frloginPTX10
    )
    
    DEL "!TempFile!"
    ECHO Equipment online... !IP!  
    CALL :getFRIPAddress frIP !IP!
    START /min !toolsDir!putty.exe -L !vncPortNo!:!frIP!:3389 dlog@!IP! -pw gold -N
    TIMEOUT /t 1 /nobreak > NUL
    START "" "!toolsDir!HotKey.exe" /Force "temp\putty_key.ahk"
    TIMEOUT /t 2 /nobreak > NUL
    ECHO Tunnel to FlightRecorder opened...
    ECHO Opening RDP Session to !frIP!
    START mstsc /v:127.0.0.1:!vncPortNo!
    TIMEOUT /t 2 /nobreak > NUL
    START "" "!toolsDir!HotKey.exe" /Force "temp\rdp_encrypt.ahk"
    TIMEOUT /t 4 /nobreak > NUL
    START "" "!toolsDir!HotKey.exe" /Force "temp\rdp_login.ahk"
    TIMEOUT /t 10 /nobreak > NUL
    GOTO frloginFinish
    
        :frloginPTX10
            ECHO Equipment online... !IP!
            CALL :getFRIPAddress frIP !IP!
            START /min !toolsDir!putty.exe -L !vncPortNo!:!frIP!:3389 mms@!IP! -pw modular -N
            START "" "!toolsDir!HotKey.exe" /Force "temp\putty_key.ahk"
            TIMEOUT /t 2 /nobreak > NUL
            ECHO Tunnel to FlightRecorder opened...
            ECHO Please wait, opening RDP Session...
            START mstsc /v:127.0.0.1:!vncPortNo!
            TIMEOUT /t 2 /nobreak > NUL
            START "" "!toolsDir!HotKey.exe" /Force "temp\rdp_encrypt.ahk"
            TIMEOUT /t 8 /nobreak > NUL
            START "" "!toolsDir!HotKey.exe" /Force "temp\rdp_login.ahk"
            TIMEOUT /t 10 /nobreak > NUL
            GOTO frloginFinish
            
    :frloginFinish
    TASKKILL /F /IM HotKey.exe > NUL 2>&1
    GOTO :EOF

:getFRIPAddress
    SET IPspaced=%2
    SET IPspaced=!IPspaced:.= !
    CALL :firstToken truckFirstOct !IPspaced!
    CALL :secondToken truckSecondOct !IPspaced!
    CALL :thirdToken truckThirdOct !IPspaced!
    CALL :fourthToken truckFourthOct !IPspaced!
    SET /A frFourthOct = truckFourthOct + 1
    SET flightRecIP=!truckFirstOct!.!truckSecondOct!.!truckThirdOct!.!FrFourthOct!
    SET %~1=!flightRecIP!
    GOTO :EOF

REM ===============================================================================
REM  PTX COMMANDS (COMPLETE IMPLEMENTATIONS)
REM ===============================================================================

:vnc
    CALL :writeToLog "Open VNC Viewer"
    SET /A vncPortNo=!vncPortNo! + 1
    CALL :secondToken equipName !command!
    CALL :toUCase equipName
    CALL :getEquipPTXAddress IP !equipName!
    IF !IP!==null (
        ECHO.
        ECHO Equipment !equipName! not found. Check spelling or use import if new equipment.
        GOTO start 
    )
    
    PING -n 1 !IP! > NUL
    IF !ERRORLEVEL! NEQ 0 (
        ECHO.
        ECHO Unable to reach !equipName! on !IP!, skipping VNC session.
        GOTO start 
    )
    
    CALL :hostkey
    SET TempFile=temp\temp_errorlevel.txt
    TIMEOUT /T 2 > NUL
    START cmd /c "!toolsDir!%PLINK_PATH% -v -batch -l dlog -pw gold !IP! 'ls /' & ECHO !ERRORLEVEL! > "!TempFile!""
    TIMEOUT /T 2 > NUL
    FOR /F "delims=" %%A in ('type "!TempFile!"') DO SET "ERRORLEV=%%A"
    ECHO.
    IF "!ERRORLEV!"=="0 " (
        ECHO PTXC
    ) ELSE (
        ECHO PTX10
        GOTO vncPTX10
    )
    
    DEL "!TempFile!"
    REM If Plink check passed, open VNC to PTXC
    CALL :vncencrypt
    CALL :vncptxc
    ECHO Equipment online, !equipName! (!IP!)
    TIMEOUT /t 1 /nobreak > NUL
    ECHO Please wait, opening VNC Viewer.
    TIMEOUT /t 1 /nobreak > NUL
    START /min !toolsDir!%PLINK_PATH% -v -ssh -l dlog -pw gold -L  !vncPortNo!:localhost:5900 !IP! -batch "vncserver && sleep 10"
    TIMEOUT /t 6 /nobreak > NUL
    START !vncDir!vncviewer.exe 127.0.0.1:!vncPortNo! 
    TIMEOUT /t 2 /nobreak > NUL
    START "" "!toolsDir!HotKey.exe" /Force "temp\vnc_encrypt.ahk"
    TIMEOUT /t 2 /nobreak > NUL
    START "" "!toolsDir!HotKey.exe" /Force "temp\vnc_ptxc.ahk"
    TIMEOUT /t 2 /nobreak > NUL
    GOTO vncFinish
    
    REM If Plink check failed, open VNC to PTX10
    :vncPTX10
        CALL :vncencrypt
        CALL :vncptx10
        ECHO Equipment online, !equipName! (!IP!)
        TIMEOUT /t 1 /nobreak > NUL
        ECHO Please wait, opening VNC Viewer.
        TIMEOUT /t 1 /nobreak > NUL
        START /min !toolsDir!%PLINK_PATH% -v -ssh -l mms -pw modular -L  !vncPortNo!:localhost:5900 !IP! -batch "vncserver && sleep 10"
        TIMEOUT /t 4 /nobreak > NUL
        START !vncDir!vncviewer.exe 127.0.0.1:!vncPortNo!
        TIMEOUT /t 3 /nobreak > NUL
        START "" "!toolsDir!HotKey.exe" /Force "temp\vnc_encrypt.ahk"
        TIMEOUT /t 2 /nobreak > NUL
        START "" "!toolsDir!HotKey.exe" /Force "temp\vnc_ptx10.ahk"
        TIMEOUT /t 2 /nobreak > NUL
        GOTO vncFinish

    :vncFinish
    TASKKILL /F /IM HotKey.exe > NUL 2>&1
    GOTO :EOF

:putty
    CALL :writeToLog "Open PuTTY/SSH Terminal"
    CALL :secondToken equipName !command!
    CALL :toUCase equipName
    CALL :getEquipPTXAddress IP !equipName!
    IF !IP!==null SET IP=!equipName!
    
    PING -n 1 !IP! > NUL
    IF !ERRORLEVEL! NEQ 0 (
        ECHO.
        ECHO "Unable to reach !equipName! on !IP!, skipping connection attempt."
        GOTO start
    )
    
    ECHO Machine online, (!IP!)
    
    REM Check system type using new wrapper function
    CALL :checkSystemType !IP! systemType
    
    IF "!systemType!"=="PTXC" (
        ECHO PTXC detected - Please wait, opening terminal...
        CALL :sshInteractive dlog !IP! gold
    ) ELSE (
        ECHO PTX10 detected - Please wait, opening terminal...
        CALL :sshInteractive mms !IP! modular
    )
    
    GOTO :EOF

:ping
    CALL :writeToLog "Run connectivity tests"
    CALL :secondToken equipName !command!
    CALL :toUCase equipName
    CALL :getEquipPTXAddress IP !equipName!
    IF !IP!==null SET IP=!equipName!
    
    PING -n 3 !IP! > NUL
    IF !ERRORLEVEL! NEQ 0 (
        ECHO "Unable to reach !equipName! on !IP!, skipping connectivity tests."
        GOTO start
    )
    
    ECHO Machine online, !equipName! (!IP!)
    ECHO Please wait, testing connectivity to all components...
    
    REM Check system type
    CALL :checkSystemType !IP! systemType
    
    IF "!systemType!"=="PTXC" (
        ECHO !equipName! PTXC to Server, GNSS 1, 2 and AVI.
        CALL :sshConnect dlog !IP! gold "ping -c 3 192.168.0.101"
        CALL :sshConnect dlog !IP! gold "ping -c 3 192.168.0.102" 
        CALL :sshConnect dlog !IP! gold "ping -c 3 192.168.0.254"
        CALL :sshConnect dlog !IP! gold "ping -c 3 10.110.19.16"
    ) ELSE (
        ECHO !equipName! PTX10 to Server, GNSS 1, 2 and AVI.
        CALL :sshConnect mms !IP! modular "ping -c 3 192.168.0.101"
        CALL :sshConnect mms !IP! modular "ping -c 3 192.168.0.102"
        CALL :sshConnect mms !IP! modular "ping -c 3 192.168.0.254" 
        CALL :sshConnect mms !IP! modular "ping -c 3 10.110.19.16"
    )
    
    GOTO :EOF

:config
    CALL :writeToLog "Run PTX config."
    CALL :secondToken equipName !command!
    CALL :toUCase equipName
    CALL :getEquipPTXAddress IP !equipName!
    IF !IP!==null SET IP=!equipName!
    CALL :writeToLog "Opening terminal to !equipName! on !IP!"
    ECHO config > temp\config
    PING -n 1 !IP! > NUL
    IF !ERRORLEVEL! NEQ 0 (
        ECHO "Unable to reach !equipName! on !IP!, skipping Config attempt.
        GOTO start
    )
    CALL :hostkey
    SET TempFile=temp\temp_errorlevel.txt
    TIMEOUT /T 2 > NUL
    START cmd /c "!toolsDir!%PLINK_PATH% -v -batch -l dlog -pw gold !IP! 'ls /' & ECHO !ERRORLEVEL! > "!TempFile!""
    TIMEOUT /T 2 > NUL
    FOR /F "delims=" %%A in ('type "!TempFile!"') DO SET "ERRORLEV=%%A"
    ECHO.
    IF "!ERRORLEV!"=="0 " (
        ECHO PTXC
    ) ELSE (
        ECHO PTX10, config unavailable.
        GOTO start
    )
    
    DEL "!TempFile!"
    REM If Plink check passed, PTXC Config Function
    ECHO Machine online, !equipName! (!IP!)
    ECHO Please wait, running config via PuTTY...
    START /min !toolsDir!putty.exe -L !vncPortNo!:127.0.0.1:5900 dlog@!IP! -pw gold -m temp\config
    
    SET /p answer=" Open VNC session? (Y/N) "
    IF /i "!answer!"=="y" (
        ECHO Please wait, Opening VNC Session...
        CALL :putencrypt
        CALL :putkey
        CALL :vncencrypt
        CALL :vncptxc
        SET /A vncPortNo=!vncPortNo! + 1
        START /min "!equipName! Config VNC" "!toolsDir!%PLINK_PATH%" -v -ssh -l dlog -pw gold -L !vncPortNo!:localhost:5900 !IP! -batch "vncserver && sleep 10"
        TIMEOUT /t 6 /nobreak > NUL
        START "" "!toolsDir!HotKey.exe" /Force "temp\putty_key.ahk"
        TIMEOUT /t 1 /nobreak > NUL
        START "" "!toolsDir!HotKey.exe" /Force "temp\putty_encrypt.ahk"
        TIMEOUT /t 1 /nobreak > NUL
        START !vncDir!vncviewer.exe 127.0.0.1:!vncPortNo!
        TIMEOUT /t 2 /nobreak > NUL
        START "" "!toolsDir!HotKey.exe" /Force "temp\vnc_encrypt.ahk"
        TIMEOUT /t 2 /nobreak > NUL
        START "" "!toolsDir!HotKey.exe" /Force "temp\vnc_ptxc.ahk"
        TIMEOUT /t 6 /nobreak > NUL
    ) ELSE (
        ECHO VNC session not required...
    )
    
    TASKKILL /F /IM HotKey.exe > NUL 2>&1
    GOTO :EOF

:ptxr
    CALL :writeToLog "Reboot PTX via PuTTY."
    CALL :secondToken equipName !command!
    CALL :toUCase equipName
    CALL :getEquipPTXAddress IP !equipName!
    IF !IP!==null SET IP=!equipName!
    ECHO sudo reboot > temp\reboot
    IF !IP!==null (
        ECHO.
        ECHO Equipment !equipName! not found. Check spelling or use import if new equipment. 
        GOTO start
    ) 
    PING -n 1 !IP! > NUL
    IF !ERRORLEVEL! NEQ 0 (
        ECHO.
        ECHO "Unable to reach !equipName! on !IP!, skipping PTX reboot."
        DEL /f temp\reboot
        GOTO start
    )
    CALL :hostkey
    SET TempFile=temp\temp_errorlevel.txt
    TIMEOUT /T 2 > NUL
    START cmd /c "!toolsDir!%PLINK_PATH% -v -batch -l dlog -pw gold !IP! 'ls /' & ECHO !ERRORLEVEL! > "!TempFile!""
    TIMEOUT /T 2 > NUL
    FOR /F "delims=" %%A in ('type "!TempFile!"') DO SET "ERRORLEV=%%A"
    ECHO.
    IF "!ERRORLEV!"=="0 " (
        ECHO PTXC
    ) ELSE (
        ECHO PTX10
        GOTO rebootPTX10
    )
    
    DEL "!TempFile!"
    REM Reboot PTXC via putty
    ECHO Equipment online, !IP!
    ECHO (ENSURE EQUIPMENT STATUS "Not Enter AT")
    SET /p answer="Reboot !equipName! PTXC ? (Y/N) "
    IF /i "!answer!"=="y" (
        TIMEOUT /t 5 /nobreak
        START !toolsDir!%PLINK_PATH% -batch dlog@!IP! -pw gold -m temp\reboot -v
    ) ELSE (
        ECHO "Operation Cancelled"
        GOTO rebootFinish 
    )
    
    ECHO.
    SET /p answer=" Confirm operation via VNC session? (Y/N) "
    IF /i "!answer!"=="y" (
        ECHO Allowing time for reboot to complete...
        TIMEOUT /t 20 /nobreak
        ECHO Please wait, Opening VNC Session...
        CALL :putencrypt
        CALL :putkey
        CALL :vncencrypt
        CALL :vncptxc
        SET /A vncPortNo=!vncPortNo! + 1
        TIMEOUT /t 1 /nobreak > NUL
        START /min "!equipName! Reboot VNC" "!toolsDir!%PLINK_PATH%" -v -ssh -l dlog -pw gold -L !vncPortNo!:localhost:5900 !IP! -batch "vncserver && sleep 10"
        TIMEOUT /t 6 /nobreak > NUL
        START "" "!toolsDir!HotKey.exe" /Force "temp\putty_key.ahk"
        TIMEOUT /t 1 /nobreak > NUL
        START "" "!toolsDir!HotKey.exe" /Force "temp\putty_encrypt.ahk"
        TIMEOUT /t 1 /nobreak > NUL
        START !vncDir!vncviewer.exe 127.0.0.1:!vncPortNo!
        TIMEOUT /t 1 /nobreak > NUL
        START "" "!toolsDir!HotKey.exe" /Force "temp\vnc_encrypt.ahk"
        TIMEOUT /t 2 /nobreak > NUL
        START "" "!toolsDir!HotKey.exe" /Force "temp\vnc_ptxc.ahk"
        TIMEOUT /t 6 /nobreak > NUL
        GOTO rebootFinish
    ) ELSE (
        ECHO "PTXC Reboot complete, VNC session skipped."
        GOTO rebootFinish 
    )
        
        :rebootPTX10
            ECHO Equipment online, !IP!
            ECHO (ENSURE EQUIPMENT STATUS "Not Enter AT")
            SET /p answer="Reboot !equipName! PTX10 ? (Y/N) "
            IF /i "!answer!"=="y" (
                TIMEOUT /t 5 /nobreak
                START !toolsDir!%PLINK_PATH% -batch mms@!IP! -pw modular -m temp\reboot -v
            ) ELSE (
                ECHO "Operation Cancelled"
                GOTO rebootFinish 
            )
    
            ECHO.
            SET /p answer=" Confirm operation via VNC session? (Y/N) "
            IF /i "!answer!"=="y" (
                ECHO Allowing time for reboot to complete...
                TIMEOUT /t 20 /nobreak
                ECHO Please wait, Opening VNC Session...
                CALL :putencrypt
                CALL :putkey
                CALL :vncencrypt
                CALL :vncptx10
                SET /A vncPortNo=!vncPortNo! + 1
                TIMEOUT /t 1 /nobreak > NUL
                START /min "!equipName! Reboot VNC" "!toolsDir!%PLINK_PATH%" -v -ssh -l mms -pw modular -L !vncPortNo!:localhost:5900 !IP! -batch "vncserver && sleep 15"
                TIMEOUT /t 6 /nobreak > NUL
                START "" "!toolsDir!HotKey.exe" /Force "temp\putty_key.ahk"
                TIMEOUT /t 1 /nobreak > NUL
                START "" "!toolsDir!HotKey.exe" /Force "temp\putty_encrypt.ahk"
                TIMEOUT /t 1 /nobreak > NUL
                START !vncDir!vncviewer.exe 127.0.0.1:!vncPortNo!
                TIMEOUT /t 1 /nobreak > NUL
                START "" "!toolsDir!HotKey.exe" /Force "temp\vnc_encrypt.ahk"
                TIMEOUT /t 2 /nobreak > NUL
                START "" "!toolsDir!HotKey.exe" /Force "temp\vnc_ptx10.ahk"
                TIMEOUT /t 6 /nobreak > NUL
                GOTO rebootFinish
            ) ELSE (
                ECHO "PTX10 Reboot complete, VNC session skipped."
                GOTO rebootFinish 
            )
        
    :rebootFinish
    TIMEOUT /t 2 /nobreak > NUL
    TASKKILL /F /IM HotKey.exe > NUL 2>&1
    GOTO :EOF

:win
    CALL :writeToLog "Open WinSCP."
    CALL :winscp
    SET /A proxyPortNo=!proxyPortNo! + 1
    CALL :secondToken equipName !command!
    CALL :toUCase equipName
    CALL :getEquipPTXAddress IP !equipName!
    IF !IP!==null (
        ECHO.
        ECHO Equipment !equipName! not found. Check spelling or use import if new equipment.
        GOTO start
    )     
    REM Pre-check
    PING -n 1 !IP! > NUL
    IF !ERRORLEVEL! NEQ 0 (
        ECHO.
        ECHO "Unable to reach !equipName! on !IP!, skipping WinSCP session."
        GOTO start
    )
    CALL :hostkey
    SET TempFile=temp\temp_errorlevel.txt
    TIMEOUT /T 2 > NUL
    START cmd /c "!toolsDir!%PLINK_PATH% -v -batch -l dlog -pw gold !IP! 'ls /' & ECHO !ERRORLEVEL! > "!TempFile!""
    TIMEOUT /T 2 > NUL
    FOR /F "delims=" %%A in ('type "!TempFile!"') DO SET "ERRORLEV=%%A"
    ECHO.
    IF "!ERRORLEV!"=="0 " (
        ECHO PTXC
    ) ELSE (
        ECHO PTX10
        GOTO winPTX10
    )
    
    DEL "!TempFile!"
    REM If Plink check passed, open WinSCP to PTXC
    ECHO Equipment online, !equipName! (!IP!)
    ECHO Opening winSCP connection to dlog/real_home
    START !toolsDir!\WinSCP\WinSCP.exe scp://dlog:gold@!IP!/home/dlog/real_home/
    GOTO winFinish
    
        REM If Plink check passed, open WinSCP to PTX10
        :winPTX10
            ECHO Equipment online, !equipName! (!IP!)
            ECHO Opening winSCP connection to /home/mms/
            START !toolsDir!\WinSCP\WinSCP.exe scp://mms:modular@!IP!/home/mms/
            GOTO winFinish

    :winFinish
    START "" "!toolsDir!HotKey.exe" /Force "temp\winscp.ahk"
    TIMEOUT /t 6 /nobreak > NUL
    TASKKILL /F /IM HotKey.exe > NUL 2>&1
    GOTO :EOF

:ptxlogs
    CALL :writeToLog "Access PTX logs via WinSCP."
    CALL :winscp
    SET /A proxyPortNo=!proxyPortNo! + 1
    CALL :secondToken equipName !command!
    CALL :toUCase equipName
    CALL :getEquipPTXAddress IP !equipName!
    IF !IP!==null (
        ECHO.
        ECHO Equipment !equipName! not found. Check spelling or use import if new equipment. 
        GOTO start
    ) 
    PING -n 1 !IP! > NUL
    IF !ERRORLEVEL! NEQ 0 (
        ECHO.
        ECHO "Unable to reach !equipName! on !IP!, skipping WinSCP session."
        GOTO start
    )
    CALL :hostkey
    SET TempFile=temp\temp_errorlevel.txt
    TIMEOUT /T 2 > NUL
    START cmd /c "!toolsDir!%PLINK_PATH% -v -batch -l dlog -pw gold !IP! 'ls /' & ECHO !ERRORLEVEL! > "!TempFile!""
    TIMEOUT /T 2 > NUL
    FOR /F "delims=" %%A in ('type "!TempFile!"') DO SET "ERRORLEV=%%A"
    ECHO.
    IF "!ERRORLEV!"=="0 " (
        ECHO PTXC
    ) ELSE (
        ECHO PTX10
        GOTO ptxlogsPTX10
    )
    
    DEL "!TempFile!"
    REM If Plink check passed, open WinSCP to PTXC
    ECHO Equipment online, !equipName! (!IP!)
    ECHO Opening winSCP connection to /home/dlog/frontrunnerV3/logs
    START !winDir!WinSCP.exe scp://dlog:gold@!IP!/home/dlog/frontrunnerV3/logs/
    GOTO ptxlogsFinish
    REM If Plink check passed, open WinSCP to PTX10
        :ptxlogsPTX10
            ECHO Equipment online, !equipName! (!IP!)
            ECHO Opening winSCP connection to -
            ECHO /home/mms/frontrunnerV3-3.5.4-007-PTX10-1-ptx10/logs/
            START !winDir!WinSCP.exe scp://mms:modular@!IP!/home/mms/frontrunnerV3-3.5.4-007-PTX10-1-ptx10/logs/
            GOTO ptxlogsFinish

    :ptxlogsFinish
    START "" "!toolsDir!HotKey.exe" /Force "temp\winscp.ahk"
    TIMEOUT /t 6 /nobreak > NUL
    TASKKILL /F /IM HotKey.exe > NUL 2>&1
    GOTO :EOF

:cache
    CALL :writeToLog "Open cache folder via WinSCP."
    SET /A proxyPortNo=!proxyPortNo! + 1
    CALL :secondToken equipName !command!
    CALL :toUCase equipName
    CALL :getEquipPTXAddress IP !equipName!
    CALL :winscp
    IF !IP!==null (
        ECHO.
        ECHO Equipment !equipName! not found. Check spelling or use import if new equipment.
        GOTO start
    ) 
    PING -n 1 !IP! > NUL
    IF !ERRORLEVEL! NEQ 0 (
        ECHO.
        ECHO "Unable to reach !equipName! on !IP!, skipping WinSCP session."
        GOTO start
    )
    CALL :hostkey
    SET TempFile=temp\temp_errorlevel.txt
    TIMEOUT /T 2 > NUL
    START cmd /c "!toolsDir!%PLINK_PATH% -v -batch -l dlog -pw gold !IP! 'ls /' & ECHO !ERRORLEVEL! > "!TempFile!""
    TIMEOUT /T 2 > NUL
    FOR /F "delims=" %%A in ('type "!TempFile!"') DO SET "ERRORLEV=%%A"
    ECHO.
    IF "!ERRORLEV!"=="0 " (
        ECHO PTXC
    ) ELSE (
        ECHO PTX10
        GOTO cachePTX10
    )
    
    DEL "!TempFile!"
    REM If Plink check passed, open WinSCP to PTXC
    ECHO Equipment online, !equipName! (!IP!)
    ECHO Opening winSCP connection to cache_client folder.
    START !winDir!WinSCP.exe scp://dlog:gold@!IP!/media/realroot/home/dlog/frontrunnerV3/cache_client/
    GOTO cacheFinish
    
    REM If Plink check passed, open WinSCP to PTX10
        :cachePTX10
        ECHO Equipment online, !equipName! (!IP!)
        ECHO Opening winSCP connection to cache_client folder. 
        START !winDir!WinSCP.exe scp://mms:modular@!IP!/media/realroot/home/mms/frontrunnerV3-3.5.4-007-PTX10-1-ptx10/cache_client/
        GOTO cacheFinish

    :cacheFinish
        START "" "!toolsDir!HotKey.exe" /Force "temp\winscp.ahk"
        TIMEOUT /t 6 /nobreak > NUL
        TASKKILL /F /IM HotKey.exe > NUL 2>&1
        GOTO :EOF

:delcache
    CALL :writeToLog "Delete cache folder and reboot PTX."
    ECHO cd /media/realroot/home/dlog/frontrunnerV3/cache_client; rm -rf */ > temp\PTXCcachedel
    ECHO cd /media/realroot/home/mms/frontrunnerV3-3.5.4-007-PTX10-1-ptx10/cache_client; rm -rf */ > temp\PTX10cachedel
    ECHO sudo reboot > temp\reboot
    CALL :secondToken equipName !command!
    CALL :toUCase equipName
    CALL :getEquipPTXAddress IP !equipName!
    PING -n 1 !IP! > NUL
    IF !ERRORLEVEL! NEQ 0 (
        ECHO.
        ECHO "Unable to reach !equipName! on !IP!, skipping Cache delete/Reboot."
        GOTO start 
    )
    CALL :hostkey
    SET TempFile=temp\temp_errorlevel.txt
    TIMEOUT /T 2 > NUL
    START cmd /c "!toolsDir!%PLINK_PATH% -v -batch -l dlog -pw gold !IP! 'ls /' & ECHO !ERRORLEVEL! > "!TempFile!""
    TIMEOUT /T 2 > NUL
    FOR /F "delims=" %%A in ('type "!TempFile!"') DO SET "ERRORLEV=%%A"
    ECHO.
    IF "!ERRORLEV!"=="0 " (
        ECHO PTXC
    ) ELSE (
        ECHO PTX10
        GOTO delcachePTX10
    )
    
    DEL "!TempFile!"
    REM If Plink check passed, open Plink to PTXC
    ECHO Equipment online, !equipName! (!IP!)
    ECHO (ENSURE EQUIPMENT STATUS "Not Enter AT") 
    SET /p answer=" Delete cache folder on !equipName! & Reboot PTXC ? (Y/N) "
    IF /i "!answer!"=="y" (
        START "Cache Delete" "!toolsDir!%PLINK_PATH%" -batch dlog@!IP! -pw gold -m temp\PTXCcachedel -v
        PING 127.0.0.1 -n 5 > NUL
        START "PTX Reboot" "!toolsDir!%PLINK_PATH%" -batch dlog@!IP! -pw gold -m temp\reboot -v
    ) ELSE (
        ECHO "Operation Cancelled"
        GOTO delFinish 
    )
    ECHO.
    SET /p answer=" Confirm operation via VNC session? (Y/N) "
    IF /i "!answer!"=="y" (
        ECHO Allowing time for reboot to complete...
        TIMEOUT /t 20 /nobreak
        ECHO Please wait, Opening VNC Session...
        SET /A vncPortNo=!vncPortNo! + 1
        CALL :putencrypt
        CALL :putkey
        CALL :vncencrypt
        CALL :vncptxc
        TIMEOUT /t 1 /nobreak > NUL
        START /min "!equipName! Reboot VNC" "!toolsDir!%PLINK_PATH%" -v -ssh -l dlog -pw gold -L !vncPortNo!:localhost:5900 !IP! -batch "vncserver && sleep 10"
        TIMEOUT /t 6 /nobreak > NUL
        START "" "!toolsDir!HotKey.exe" /Force "temp\putty_key.ahk"
        TIMEOUT /t 1 /nobreak > NUL
        START "" "!toolsDir!HotKey.exe" /Force "temp\putty_encrypt.ahk"
        TIMEOUT /t 1 /nobreak > NUL
        START !vncDir!vncviewer.exe 127.0.0.1:!vncPortNo!
        TIMEOUT /t 1 /nobreak > NUL
        START "" "!toolsDir!HotKey.exe" /Force "temp\vnc_encrypt.ahk"
        TIMEOUT /t 2 /nobreak > NUL
        START "" "!toolsDir!HotKey.exe" /Force "temp\vnc_ptxc.ahk"
        TIMEOUT /t 6 /nobreak > NUL
        GOTO delFinish
    ) ELSE (
        ECHO "Cache delete complete, VNC session skipped."
        GOTO delFinish 
    )

    REM If Plink check failed, open Plink to PTX10
        :delcachePTX10
            ECHO Equipment online, !equipName! (!IP!)
            ECHO (ENSURE EQUIPMENT STATUS "Not Enter AT") 
            SET /p answer=" Delete cache folder on !equipName! & Reboot PTX10 ? (Y/N) "
            IF /i "!answer!"=="y" (
                START "Cache Delete" "!toolsDir!%PLINK_PATH%" -batch mms@!IP! -pw modular -m temp\PTX10cachedel -v
                PING 127.0.0.1 -n 5 > NUL
                START "PTX Reboot" "!toolsDir!%PLINK_PATH%" -batch mms@!IP! -pw modular -m temp\reboot -v
            ) ELSE (
                ECHO "Operation Cancelled"
                GOTO delFinish 
            )
            ECHO.
        SET /p answer=" Confirm operation via VNC session? (Y/N) "
        IF /i "!answer!"=="y" (
            ECHO Allowing time for reboot to complete...
            TIMEOUT /t 20 /nobreak
            ECHO Please wait, Opening VNC Session...
            SET /A vncPortNo=!vncPortNo! + 1
            CALL :putencrypt
            CALL :putkey
            CALL :vncencrypt
            CALL :vncptx10
            TIMEOUT /t 1 /nobreak > NUL
            START /min "!equipName! Reboot VNC" "!toolsDir!%PLINK_PATH%" -v -ssh -l mms -pw modular -L !vncPortNo!:localhost:5900 !IP! -batch "vncserver && sleep 10"
            TIMEOUT /t 6 /nobreak > NUL
            START "" "!toolsDir!HotKey.exe" /Force "temp\putty_key.ahk"
            TIMEOUT /t 1 /nobreak > NUL
            START "" "!toolsDir!HotKey.exe" /Force "temp\putty_encrypt.ahk"
            TIMEOUT /t 1 /nobreak > NUL
            START !vncDir!vncviewer.exe 127.0.0.1:!vncPortNo!
            TIMEOUT /t 3 /nobreak > NUL
            START "" "!toolsDir!HotKey.exe" /Force "temp\vnc_encrypt.ahk"
            TIMEOUT /t 2 /nobreak > NUL
            START "" "!toolsDir!HotKey.exe" /Force "temp\vnc_ptx10.ahk"
            TIMEOUT /t 6 /nobreak > NUL
            GOTO delFinish
        ) ELSE (
            ECHO "Cache delete complete, VNC session skipped."
            GOTO delFinish 
        )
    
    :delFinish
    TIMEOUT /t 2 /nobreak > NUL
    TASKKILL /F /IM HotKey.exe > NUL 2>&1
    GOTO :EOF

REM ===============================================================================
REM  IMPORT FUNCTION
REM ===============================================================================

:import
    CALL :writeToLog "Import equipment list"
    ECHO.
    ECHO Import function placeholder - would connect to server and import equipment list
    ECHO This would typically:
    ECHO  1. Connect to FrontRunner server
    ECHO  2. Query equipment database
    ECHO  3. Update local IP_list.dat file
    ECHO.
    ECHO For now, create bin\IP_list.dat manually with format:
    ECHO Name PTX_IP AVI_IP
    ECHO RD191 10.110.14.191 192.168.1.100
    ECHO.
    GOTO :EOF

REM ===============================================================================
REM  SSH/PUTTY WRAPPER FUNCTIONS
REM ===============================================================================

:sshConnect
    REM Usage: CALL :sshConnect [user] [host] [password] [command] [returnVar]
    SET "sshUser=%1"
    SET "sshHost=%2" 
    SET "sshPass=%3"
    SET "sshCmd=%4"
    
    IF "!SSH_AVAILABLE!"=="1" (
        REM Use native SSH with sshpass if available, otherwise interactive
        WHERE sshpass >NUL 2>&1
        IF !ERRORLEVEL! EQU 0 (
            sshpass -p "!sshPass!" ssh -o StrictHostKeyChecking=no !sshUser!@!sshHost! "!sshCmd!"
        ) ELSE (
            REM SSH available but no sshpass - use expect-like approach or interactive
            ssh -o StrictHostKeyChecking=no !sshUser!@!sshHost! "!sshCmd!"
        )
    ) ELSE (
        REM Fallback to PuTTY plink
        "!toolsDir!%PLINK_PATH%" -ssh -batch -pw "!sshPass!" !sshUser!@!sshHost! "!sshCmd!"
    )
    GOTO :EOF

:sshTunnel
    REM Usage: CALL :sshTunnel [user] [host] [password] [localPort] [remoteHost] [remotePort]
    SET "sshUser=%1"
    SET "sshHost=%2"
    SET "sshPass=%3" 
    SET "localPort=%4"
    SET "remoteHost=%5"
    SET "remotePort=%6"
    
    IF "!SSH_AVAILABLE!"=="1" (
        WHERE sshpass >NUL 2>&1
        IF !ERRORLEVEL! EQU 0 (
            START /min sshpass -p "!sshPass!" ssh -o StrictHostKeyChecking=no -L !localPort!:!remoteHost!:!remotePort! -N !sshUser!@!sshHost!
        ) ELSE (
            START /min ssh -o StrictHostKeyChecking=no -L !localPort!:!remoteHost!:!remotePort! -N !sshUser!@!sshHost!
        )
    ) ELSE (
        REM Fallback to PuTTY
        START /min "!toolsDir!putty.exe" -ssh -L !localPort!:!remoteHost!:!remotePort! -pw "!sshPass!" !sshUser!@!sshHost! -N
    )
    GOTO :EOF

:sshInteractive
    REM Usage: CALL :sshInteractive [user] [host] [password]
    SET "sshUser=%1"
    SET "sshHost=%2"
    SET "sshPass=%3"
    
    IF "!SSH_AVAILABLE!"=="1" (
        WHERE sshpass >NUL 2>&1
        IF !ERRORLEVEL! EQU 0 (
            sshpass -p "!sshPass!" ssh -o StrictHostKeyChecking=no !sshUser!@!sshHost!
        ) ELSE (
            ssh -o StrictHostKeyChecking=no !sshUser!@!sshHost!
        )
    ) ELSE (
        REM Fallback to PuTTY
        START "!toolsDir!putty.exe" -ssh -pw "!sshPass!" !sshUser!@!sshHost!
    )
    GOTO :EOF

:checkSystemType
    REM Usage: CALL :checkSystemType [IP] [returnVar]
    SET "checkIP=%1"
    SET "resultVar=%2"
    
    IF "!SSH_AVAILABLE!"=="1" (
        WHERE sshpass >NUL 2>&1
        IF !ERRORLEVEL! EQU 0 (
            sshpass -p "gold" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 dlog@!checkIP! "ls /" >NUL 2>&1
        ) ELSE (
            ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 dlog@!checkIP! "ls /" >NUL 2>&1
        )
        IF !ERRORLEVEL! EQU 0 (
            SET "%~2=PTXC"
        ) ELSE (
            SET "%~2=PTX10"
        )
    ) ELSE (
        REM Fallback to PuTTY method
        SET TempFile=temp\temp_errorlevel.txt
        START /wait cmd /c "!toolsDir!%PLINK_PATH% -ssh -batch -pw gold dlog@!checkIP! "ls /" & ECHO !ERRORLEVEL! > "!TempFile!""
        FOR /F "delims=" %%A in ('type "!TempFile!"') DO SET "ERRORLEV=%%A"
        IF "!ERRORLEV!"=="0 " (
            SET "%~2=PTXC"
        ) ELSE (
            SET "%~2=PTX10"
        )
        DEL "!TempFile!" >NUL 2>&1
    )
    GOTO :EOF

:atmon
    ECHO WinWait "Device Select" > temp\atmon.ahk
    ECHO If WinActive >> temp\atmon.ahk
    ECHO { >> temp\atmon.ahk
    ECHO ; WinActivate "Device Select" >> temp\atmon.ahk
    ECHO ControlClick "Ethernet" >> temp\atmon.ahk
    ECHO Sleep 1000 >> temp\atmon.ahk
    ECHO SendInput "{Enter}" >> temp\atmon.ahk
    ECHO } >> temp\atmon.ahk
    ECHO ExitApp >> temp\atmon.ahk
    GOTO :EOF
    
:gpsencrypt
    ECHO WinWait "PuTTY Security Alert" > temp\gps_encrypt.ahk
    ECHO If WinActive >> temp\gps_encrypt.ahk
    ECHO { >> temp\gps_encrypt.ahk
    ECHO ; WinActivate "PuTTY Security Alert" >> temp\gps_encrypt.ahk
    ECHO ControlClick "Yes" >> temp\gps_encrypt.ahk
    ECHO SendInput "{Enter}" >> temp\gps_encrypt.ahk
    ECHO } >> temp\gps_encrypt.ahk
    ECHO ExitApp >> temp\gps_encrypt.ahk
    GOTO :EOF
    
:putkey
    ECHO WinWait "PuTTY Security Alert" > temp\putty_key.ahk
    ECHO IF WinActive >> temp\putty_key.ahk
    ECHO { >> temp\putty_key.ahk
    ECHO ; WinActivate ("PuTTY Security Alert") >> temp\putty_key.ahk
    ECHO ControlClick "Accept" >> temp\putty_key.ahk
    ECHO SendInput "{Enter}" >> temp\putty_key.ahk
    ECHO } >> temp\putty_key.ahk
    ECHO ExitApp >> temp\putty_key.ahk
    GOTO :EOF

:putencrypt
    ECHO WinWait "PuTTY Security Alert" > temp\putty_encrypt.ahk
    ECHO IF WinActive >> temp\putty_encrypt.ahk
    ECHO { >> temp\putty_encrypt.ahk
    ECHO ; WinActivate ("PuTTY Security Alert") >> temp\putty_encrypt.ahk
    ECHO ControlClick "Yes" >> temp\putty_encrypt.ahk
    ECHO SendInput "{Enter}" >> temp\putty_encrypt.ahk
    ECHO } >> temp\putty_encrypt.ahk
    ECHO ExitApp >> temp\putty_encrypt.ahk
    GOTO :EOF
    
:topcon
    ECHO WinWait "Topcon Receiver Utility" > temp\topcon.ahk
    ECHO WinActivate ("Topcon Receiver Utility") >> temp\topcon.ahk
    ECHO ExitApp >> temp\topcon.ahk
    GOTO :EOF
    
:vncencrypt
    ECHO WinWait "Encryption" > temp\vnc_encrypt.ahk
    ECHO If WinActive >> temp\vnc_encrypt.ahk
    ECHO { >> temp\vnc_encrypt.ahk
    ECHO ; WinActivate ("Encryption") >> temp\vnc_encrypt.ahk
    ECHO ControlClick "Continue", "Encryption" >> temp\vnc_encrypt.ahk
    ECHO } >> temp\vnc_encrypt.ahk
    ECHO ExitApp >> temp\vnc_encrypt.ahk
    GOTO :EOF
    
:vncptxc
    ECHO WinWait "VNC Viewer" > temp\vnc_ptxc.ahk
    ECHO WinActivate "VNC Viewer" >> temp\vnc_ptxc.ahk
    ECHO SendInput "dlog" >> temp\vnc_ptxc.ahk
    ECHO SendInput "{Enter}" >> temp\vnc_ptxc.ahk
    ECHO SendInput "gold" >> temp\vnc_ptxc.ahk
    ECHO SendInput "{Enter}" >> temp\vnc_ptxc.ahk
    ECHO ExitApp >> temp\vnc_ptxc.ahk
    GOTO :EOF
    
:vncptx10
    ECHO WinWait "VNC Viewer" > temp\vnc_ptx10.ahk
    ECHO WinActivate "VNC Viewer" >> temp\vnc_ptx10.ahk
    ECHO SendInput "mms" >> temp\vnc_ptx10.ahk
    ECHO SendInput "{Enter}" >> temp\vnc_ptx10.ahk
    ECHO SendInput "modular" >> temp\vnc_ptx10.ahk
    ECHO SendInput "{Enter}" >> temp\vnc_ptx10.ahk
    ECHO ExitApp >> temp\vnc_ptx10.ahk
    GOTO :EOF
    
:winscp
    ECHO WinWait "Warning" > temp\winscp.ahk
    ECHO If WinActive >> temp\winscp.ahk
    ECHO { >> temp\winscp.ahk
    ECHO ; WinActivate "Warning" >> temp\winscp.ahk
    ECHO ControlClick "Yes" >> temp\winscp.ahk
    ECHO SendInput "{Enter}" >> temp\winscp.ahk
    ECHO } >> temp\winscp.ahk
    ECHO ExitApp >> temp\winscp.ahk
    GOTO :EOF
    
:rdpencrypt
    ECHO WinWait "Remote Desktop Connection" > temp\rdp_encrypt.ahk
    ECHO If WinActive >> temp\rdp_encrypt.ahk
    ECHO { >> temp\rdp_encrypt.ahk
    ECHO ; WinActivate "Remote Desktop Connection" >> temp\rdp_encrypt.ahk
    ECHO ControlClick "Yes" >> temp\rdp_encrypt.ahk
    ECHO SendInput "{Enter}" >> temp\rdp_encrypt.ahk
    ECHO } >> temp\rdp_encrypt.ahk
    ECHO ExitApp >> temp\rdp_encrypt.ahk
    GOTO :EOF
    
:rdpwarning
    ECHO WinWait "Remote Desktop Connection" > temp\rdp_warning.ahk
    ECHO If WinActive >> temp\rdp_warning.ahk
    ECHO { >> temp\rdp_warning.ahk
    ECHO ; WinActivate "Remote Desktop Connection" >> temp\rdp_warning.ahk
    ECHO ControlClick "Yes" >> temp\rdp_warning.ahk
    ECHO SendInput "{Enter}" >> temp\rdp_warning.ahk
    ECHO } >> temp\rdp_warning.ahk
    ECHO ExitApp >> temp\rdp_warning.ahk
    GOTO :EOF
    
:rdplogin
    ECHO WinWait "127.0.0.1:5901 - Remote Desktop Connection" > temp\rdp_login.ahk
    ECHO If WinActive >> temp\rdp_login.ahk
    ECHO { >> temp\rdp_login.ahk
    ECHO ; WinActivate "Log On to Windows" >> temp\rdp_login.ahk
    ECHO SendInput "administrator" >> temp\rdp_login.ahk
    ECHO Send "{Tab}" >> temp\rdp_login.ahk
    ECHO SendInput "komatsu" >> temp\rdp_login.ahk
    ECHO SendInput "{Enter}" >> temp\rdp_login.ahk
    ECHO } >> temp\rdp_login.ahk
    ECHO ExitApp >> temp\rdp_login.ahk
    GOTO :EOF

REM ===============================================================================
REM  UTILITY FUNCTIONS
REM ===============================================================================

:decimcalToOctets
    SET %~1=0.0
    SET /A dec=%2
    SET /A "firstOct = (!dec! & 65280) / 256"
    SET /A "secondOct=!dec! & 255"
    SET %~1=!firstOct!.!secondOct!
    GOTO :EOF

:upOrDown
    SET %~1=DOWN
    FOR /F "delims=" %%a in ('ping -n 1 %2') do (
        CALL :thirdToken responseFrom %%a
        IF !responseFrom!==%2: SET %~1=UP
    )
    GOTO :EOF

:firstToken
    SET %~1=%2
    GOTO :EOF

:secondToken
    SET %~1=%3
    GOTO :EOF

:thirdToken
    SET %~1=%4
    GOTO :EOF

:fourthToken
    SET %~1=%5
    GOTO :EOF

:writeToLog
    ECHO [!DATE! !TIME!] !USERNAME! - !command! - %* >> "!logFile!"
    GOTO :EOF

:trimLogFile
    SET "tempLog=logs\temp_log.tmp"
    IF EXIST "!logFile!" (
        FOR /F %%A in ('TYPE "!logFile!" ^| FIND /C /V ""') DO SET lineCount=%%A
        IF !lineCount! GTR 1000 (
            ECHO Trimming log file...
            FOR /F "skip=200 delims=" %%A in ('TYPE "!logFile!"') DO ECHO %%A >> "!tempLog!"
            MOVE "!tempLog!" "!logFile!" >NUL 2>&1
        )
    )
    GOTO :EOF

:toUCase
    SET "temp=!%~1!"
    SET "temp=!temp:a=A!"
    SET "temp=!temp:b=B!"
    SET "temp=!temp:c=C!"
    SET "temp=!temp:d=D!"
    SET "temp=!temp:e=E!"
    SET "temp=!temp:f=F!"
    SET "temp=!temp:g=G!"
    SET "temp=!temp:h=H!"
    SET "temp=!temp:i=I!"
    SET "temp=!temp:j=J!"
    SET "temp=!temp:k=K!"
    SET "temp=!temp:l=L!"
    SET "temp=!temp:m=M!"
    SET "temp=!temp:n=N!"
    SET "temp=!temp:o=O!"
    SET "temp=!temp:p=P!"
    SET "temp=!temp:q=Q!"
    SET "temp=!temp:r=R!"
    SET "temp=!temp:s=S!"
    SET "temp=!temp:t=T!"
    SET "temp=!temp:u=U!"
    SET "temp=!temp:v=V!"
    SET "temp=!temp:w=W!"
    SET "temp=!temp:x=X!"
    SET "temp=!temp:y=Y!"
    SET "temp=!temp:z=Z!"
    SET %~1=!temp!
    GOTO :EOF
    
:hostkey
    START /min !toolsDir!putty.exe "!IP!"
    START "" "!toolsDir!HotKey.exe" "temp\putty_key.ahk"
    TIMEOUT /t 1 /nobreak > NUL
    TASKKILL /F /IM putty.exe > NUL 2>&1
    TASKKILL /F /IM HotKey.exe > NUL 2>&1
    GOTO :EOF

REM ===============================================================================
REM  EXIT FUNCTION
REM ===============================================================================

:exit
    ECHO [!DATE! !TIME!] SESSION END - User: !USERNAME! >> "!logFile!"
    ECHO Saving configuration...
    
    REM Save equipment list
    IF !arraySize! GTR 0 (
        ECHO Name PTX_IP AVI_IP > "!datFile!"
        SET /A lastEntry= !arraySize! - 1
        FOR /L %%n in (0,1,!lastEntry!) do (
            ECHO !name[%%n]! !ptxIP[%%n]! !aviIP[%%n]! >> "!datFile!"
        )
    )
    
    ECHO.
    ECHO ================================================================================
    ECHO                        T1 TOOLS SESSION COMPLETE                             
    ECHO                                                                               
    ECHO  Configuration saved successfully                                             
    ECHO  Session logged to: !logFile!                                   
    ECHO                                                                               
    ECHO  Thank you for using T1 Tools V2.0                            
    ECHO ================================================================================
    ECHO.
    
    REM Only pause if not in debug mode or if there was an error
    IF NOT DEFINED DEBUG_MODE (
        PAUSE
    ) ELSE (
        ECHO Debug mode - press any key to exit or close window
        PAUSE >NUL
    )
    EXIT

REM ===============================================================================
REM  END OF SCRIPT
REM ===============================================================================