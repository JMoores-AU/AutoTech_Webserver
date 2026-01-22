@ECHO OFF
SETLOCAL ENABLEDELAYEDEXPANSION

SET "SCRIPTDIR=%~dp0"
SET "ROOTDIR=%SCRIPTDIR%.."
CD /D "%SCRIPTDIR%"

TITLE T1 Tools - PCN Version

:: General Variables ::
:: Directories ::
SET version=GRM_V1.4
SET datFile=%SCRIPTDIR%IP_list.dat
SET logFile=%ROOTDIR%\logs\tools_logfile.log
SET toolsDir=%ROOTDIR%\tools\
SET winDir=%ROOTDIR%\tools\WinSCP\
SET vncDir=%ROOTDIR%\tools\VNC\
SET truDir=%ROOTDIR%\tools\Topcon\
SET tempDir=%ROOTDIR%\temp
:: Access ::
SET screenUN=dlog
SET screenPW=gold
SET screenUN2=mms
SET screenPW2=modular
SET frPW=komatsu
SET frUN=administrator
SET aviUN=root
SET aviPW=root
SET gpsUN=modular
SET gpsPW=modular
SET command=START !version!
:: Ports ::
SET /A vncPortNo=5900
SET /A proxyPortNo=5566
SET /A gps1PortNo=3333
SET /A gps2PortNo=3334
SET watchDelay=10

SET arraySize=0
SET name[]=
SET ptxIP[]=
SET aviIP[]=

:: Load datFile ::
IF EXIST !datFile! (
    ECHO Loading IP List...
    
    REM Count lines first
    SET lineCount=0
    FOR /F "usebackq tokens=*" %%A IN (!datFile!) DO SET /A lineCount+=1
    
    CALL :load
    ECHO Loaded !lineCount! entries from IP List.
) ELSE (
    ECHO.
    ECHO !datFile! Not Found!
    ECHO Use import command to import vehicle list from server.
    ECHO.
)

ECHO Loaded... !version!
ECHO.
ECHO Welcome to T1 Tools. Type "help" for list of commands and use cases.  

:start
ECHO.
SET /P "command=> "
CALL :firstToken commandOne !command! 
:: Call Functions: 
IF !commandOne!==tru (
	CALL :tru !command!
	IF ERRORLEVEL 1 ECHO Command failed: tru
)	
IF !commandOne!==atmon (
	CALL :atmon !command!
	IF ERRORLEVEL 1 ECHO Command failed: atmon
)
IF !commandOne!==frdownload (
	CALL :frdownload !command!
	IF ERRORLEVEL 1 ECHO Command failed: frdownload
)
IF !commandOne!==frreset (
	CALL :frreset !command!
	IF ERRORLEVEL 1 ECHO Command failed: frreset
)
IF !commandOne!==frlogin (
	CALL :frlogin !command!
	IF ERRORLEVEL 1 ECHO Command failed: frlogin
)
IF !commandOne!==vnc (
	CALL :vnc !command!
	IF ERRORLEVEL 1 ECHO Command failed: vnc
)
IF !commandOne!==putty (
	CALL :putty !command!
	IF ERRORLEVEL 1 ECHO Command failed: putty
)
IF !commandOne!==ping (
	CALL :ping !command!
	IF ERRORLEVEL 1 ECHO Command failed: ping
)
IF !commandOne!==help (
	CALL :help !command!
	IF ERRORLEVEL 1 ECHO Command failed: help
)
IF !commandOne!==gnsslogs (
	CALL :gnsslogs !command!
	IF ERRORLEVEL 1 ECHO Command failed: gnsslogs
)
IF !commandOne!==ptxlogs (
	CALL :ptxlogs !command!
	IF ERRORLEVEL 1 ECHO Command failed: ptxlogs
)
IF !commandOne!==avi (
	CALL :avi !command!
	IF ERRORLEVEL 1 ECHO Command failed: avi
)
IF !commandOne!==avilogs (
	CALL :avilogs !command!
	IF ERRORLEVEL 1 ECHO Command failed: avilogs
)
IF !commandOne!==cache (
	CALL :cache !command!
	IF ERRORLEVEL 1 ECHO Command failed: cache
)
IF !commandOne!==delcache (
	CALL :delcache !command!
	IF ERRORLEVEL 1 ECHO Command failed: delcache
)
IF !commandOne!==ptxr (
	CALL :ptxr !command!
	IF ERRORLEVEL 1 ECHO Command failed: ptxr
)
IF !commandOne!==win (
	CALL :win !command!
	IF ERRORLEVEL 1 ECHO Command failed: win
)
IF !commandOne!==config (
	CALL :config !command!
	IF ERRORLEVEL 1 ECHO Command failed: config
)
IF !commandOne!==e (
	CALL :exit !command!
	IF ERRORLEVEL 1 ECHO Command failed: exit
)

GOTO start

ECHO FELL THROUGH!!!!
EXIT /B 1

:: Functions
:: AVI Scripts....................................................................................................................................................................................

:avilogs
	::open WinSCP to AVI Ip Address
	CALL :writeToLog Access AVI Log Files
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
		START "" "!toolsDir!HotKey.exe" /Force "!tempDir!\winscp.ahk"
		TIMEOUT /t 5 /nobreak > NUL
		TASKKILL /F /IM HotKey.exe > NUL 2>&1
		
		EXIT /B 0

:avi
	::get radio external IP address via PTXC and open chrome browser
	CALL :writeToLog Login to AVI Radio
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
	:: AVI IP Pre-check
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
	SET TempFile=!tempDir!\temp_errorlevel.txt
	TIMEOUT /T 2 > NUL
	START cmd /c "!toolsDir!plink.exe -v -batch -l dlog -pw gold !IP! 'ls /' & ECHO !ERRORLEVEL! > "!TempFile!""
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
	ECHO sleep 10; exit > !tempDir!\autoTunnelCloseCmd
	ECHO ifconfig mob1p1_1 ^| grep -E -o "inet addr:([0-9]{1,3}\.){3}[0-9]{1,3}" > !tempDir!\radIPCmd
    START !toolsDir!putty.exe -L !aviPortNo!:192.168.0.254:22 -l dlog -pw gold "!IP!" -m !tempDir!\autoTunnelCloseCmd
	TIMEOUT /t 2 /nobreak > NUL
    SET "aviIP=unknown"
    FOR /F "tokens=2 delims=:" %%a in ('echo yes ^| "!toolsDir!plink.exe" -batch -l root -pw root -P !aviPortNo! 127.0.0.1 -m !tempDir!\radIPCmd') DO (
        SET "aviIP=%%a"
    )
    ECHO Embedded AVI IP Address found: !aviIP!
	TASKKILL /F /IM putty.exe > NUL 2>&1
    GOTO :EOF

	:aviPTX10
    ECHO Attempting to obtain embedded via !IP!
    SET /A aviPortNo+=1
	ECHO sleep 10; exit > !tempDir!\autoTunnelCloseCmd
	ECHO ifconfig mob1p1_1 ^| grep -E -o "inet addr:([0-9]{1,3}\.){3}[0-9]{1,3}" > !tempDir!\radIPCmd
    START /min !toolsDir!putty.exe -L !aviPortNo!:192.168.0.254:22 -l mms -pw modular "!IP!" -m !tempDir!\autoTunnelCloseCmd
	TIMEOUT /t 2 /nobreak > NUL
    SET "aviIP=unknown"
    FOR /F "tokens=2 delims=:" %%a in ('echo yes ^| "!toolsDir!plink.exe" -batch -l root -pw root -P !aviPortNo! 127.0.0.1 -m !tempDir!\radIPCmd') DO (
        SET "aviIP=%%a"
    )
    ECHO Embedded AVI IP Address found: !aviIP!
	TASKKILL /F /IM putty.exe > NUL 2>&1
    GOTO :EOF
	
	:updateAVI
	SET tempFile=!tempDir!\tempIPList.dat
	IF !aviIP!==unknown (
    ECHO AVI IP is still unknown. Exiting.
    EXIT /B 1
	)
	IF NOT EXIST "!datFile!" (
    ECHO IP file not found: !datFile!
    EXIT /B 1
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
	GOTO start
	
:: MM2 Functions ::
	
:tru

	::use putty to open a tunnel to each of the GPS receivers
	CALL :writeToLog Access GNSS via TRU
	CALL :putkey
	CALL :topcon
	CALL :gpsencrypt
	IF !screenPW!==none SET /P "screenPW=enter PTXC Password: "
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
	SET TempFile=!tempDir!\temp_errorlevel.txt
	TIMEOUT /T 2 > NUL
	START cmd /c "!toolsDir!plink.exe -v -batch -l dlog -pw gold !IP! 'ls /' & ECHO !ERRORLEVEL! > "!TempFile!""
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
	:: Connect via PTXC
	START /min "!equipName! - GNSS 1" !toolsDir!plink.exe -v -batch -L !gps1PortNo!:192.168.0.101:8002 dlog@!IP! -pw gold -N
	START /min "!equipName! - GNSS 2" !toolsDir!plink.exe -v -batch -L !gps2PortNo!:192.168.0.102:8002 dlog@!IP! -pw gold -N		
	ECHO Tunnel to GNSS 1 and GNSS 2 open via PTXC, opening TRU. Please wait...
	TIMEOUT /t 4 /nobreak > NUL
	START "" "!truDir!TRU.exe" 
	TIMEOUT /t 2 /nobreak > NUL
	START "" "!toolsDir!HotKey.exe" /FORCE "!tempDir!\topcon.ahk"
	GOTO truFinish
	
	:: Connect via PTX10
	:truPTX10
		START /min "!equipName! - GNSS 1" !toolsDir!plink.exe -v -batch -L !gps1PortNo!:192.168.0.101:8002 mms@!IP! -pw modular -N
		START /min "!equipName! - GNSS 2" !toolsDir!plink.exe -v -batch -L !gps2PortNo!:192.168.0.102:8002 mms@!IP! -pw modular -N		
		ECHO Tunnel to GNSS 1 and GNSS 2 open via PTX10, opening TRU. Please wait...
		TIMEOUT /t 4 /nobreak > NUL
		START "" "!truDir!TRU.exe" 
		TIMEOUT /t 2 /nobreak > NUL
		START "" "!toolsDir!HotKey.exe" /FORCE "!tempDir!\topcon.ahk"
		GOTO truFinish
	
	:truFinish
	TASKKILL /F /IM HotKey.exe > NUL 2>&1
	EXIT /B 0
	
	
:gnsslogs

	::use putty to open SOCKS5 proxy to PTXC, then open a WinSCP connection to GNSS1 using the proxy
	CALL :writeToLog Access GNSS 1 logs
	CALL :putencrypt
	TIMEOUT /t 1 /nobreak > NUL
	SET /A proxyPortNo=!proxyPortNo! + 1
	IF gold==none SET /P "screenPW=enter PTXC Password: "
	IF !gpsPW!==none SET /P "gpsPW=enter GPS Password: "	
	CALL :secondToken equipName !command!
	CALL :toUCase equipName
	CALL :getEquipPTXAddress IP !equipName!
	IF !IP!==null (
		ECHO.
		ECHO Equipment !equipName! not found. Check spelling or use import if new equipment.
		GOTO start
	) 	
	:: Pre-Check
	PING -n 1 !IP! > NUL
	IF !ERRORLEVEL! NEQ 0 (
		ECHO.
		ECHO "Unable to reach !equipName! on !IP!, skipping WinSCP session."
		GOTO start 
	)
	CALL :hostkey
	SET TempFile=!tempDir!\temp_errorlevel.txt
	TIMEOUT /T 2 > NUL
	START cmd /c "!toolsDir!plink.exe -v -batch -l dlog -pw gold !IP! 'ls /' & ECHO !ERRORLEVEL! > "!TempFile!""
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
	START "" "!toolsDir!HotKey.exe" "!tempDir!\putty_key.ahk"
	TIMEOUT /t 2 /nobreak > NUL
	ECHO Tunnel to GNSS open via PTXC, Starting winSCP...
	TIMEOUT /t 2 /nobreak > NUL
	START !winDir!WinSCP.exe ftp://!gpsUN!:!gpsPW!@192.168.0.101 -rawsettings ProxyMethod=2 ProxyHost=127.0.0.1 ProxyPort=!proxyPortNo!
	START !winDir!WinSCP.exe ftp://!gpsUN!:!gpsPW!@192.168.0.102 -rawsettings ProxyMethod=2 ProxyHost=127.0.0.1 ProxyPort=!proxyPortNo!
	GOTO gnsslogsFinish
	
	:gnsslogsPTX10
		ECHO Equipment Online, !IP!
		START /min !toolsDir!putty.exe -D !proxyPortNo! mms@!IP! -pw modular -N
		START "" "!toolsDir!HotKey.exe" "!tempDir!\putty_key.ahk"
		TIMEOUT /t 2 /nobreak > NUL
		ECHO Tunnel to GNSS open va PTX10, Starting winSCP...
		TIMEOUT /t 2 /nobreak > NUL
		START !winDir!WinSCP.exe ftp://!gpsUN!:!gpsPW!@192.168.0.101 -rawsettings ProxyMethod=2 ProxyHost=127.0.0.1 ProxyPort=!proxyPortNo!
		START !winDir!WinSCP.exe ftp://!gpsUN!:!gpsPW!@192.168.0.102 -rawsettings ProxyMethod=2 ProxyHost=127.0.0.1 ProxyPort=!proxyPortNo!
		GOTO gnsslogsFinish
	
	:gnsslogsFinish
		TASKKILL /F /IM HotKey.exe > NUL 2>&1
		EXIT /B 0



:: ATmonitor Functions ::
:: Only applicable to 830E / 930E equipment
:atmon

	::use putty to open tunnel to Flight Recorder via PTXC for AT Monitor use
	CALL :writeToLog Load ATMonitor remotley.
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
	SET TempFile=!tempDir!\temp_errorlevel.txt
	TIMEOUT /T 2 > NUL
	START cmd /c "!toolsDir!plink.exe -v -batch -l dlog -pw gold !IP! 'ls /' & ECHO !ERRORLEVEL! > "!TempFile!""
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
	START "" "!toolsDir!HotKey.exe" "!tempDir!\putty_key.ahk"
	TIMEOUT /t 4 /nobreak > NUL
	START "" "!toolsDir!HotKey.exe" "!tempDir!\putty_encrypt.ahk"
	ECHO Tunnel created to FlightRecorder via PTXC...
	TIMEOUT /t 2 /nobreak > NUL
	IF defined FOUND (
		ECHO Opening %FOUND%. please wait...
		START "" "%FOUND%"
		START "" "!toolsDir!HotKey.exe" "!tempDir!\atmon.ahk"
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
			START "" "!toolsDir!HotKey.exe" "!tempDir!\putty_key.ahk"
			TIMEOUT /t 4 /nobreak > NUL
			START "" "!toolsDir!HotKey.exe" "!tempDir!\putty_encrypt.ahk"
			ECHO Tunnel created to FlightRecorder via PTX10
			TIMEOUT /t 2 /nobreak > NUL
			IF defined FOUND (
				ECHO Opening %FOUND%. please wait...
				START "" "%FOUND%"
				START "" "!toolsDir!HotKey.exe" "!tempDir!\atmon.ahk"
				TIMEOUT /t 4 /nobreak > NUL
				GOTO atmonFinish
			) ELSE (
				ECHO External program not found,
				ECHO Open ATMonitor 3.7.0 using port 127.0.0.1
				GOTO atmonFinish 
			)
	
	:atmonFinish
	TASKKILL /F /IM HotKey.exe > NUL 2>&1
	EXIT /B 0

:: FlightRecorder ::
:: Only applicable to 830E / 930E equipment

:frdownload

	::use putty to open SOCKS5 proxy to PTXC, then open a WinSCP connection to the Flight Recorder using the proxy
	::if -ssl switch is set use explicit TLS for the connection, required for Dash 5 trucks.
	CALL :writeToLog Access FlightRecorder data.
	SET ssl=
	SET /A proxyPortNo=!proxyPortNo! + 1
	IF !screenPW!==none SET /P "screenPW=enter PTXC Password: "
	IF !frPW!==none SET /P "frPW=enter Flight Recorder Password: "
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
	SET TempFile=!tempDir!\temp_errorlevel.txt
	TIMEOUT /T 2 > NUL
	START cmd /c "!toolsDir!plink.exe -v -batch -l dlog -pw gold !IP! 'ls /' & ECHO !ERRORLEVEL! > "!TempFile!""
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
	START "" "!toolsDir!HotKey.exe" /Force "!tempDir!\putty_key.ahk"
	TIMEOUT /t 2 /nobreak > NUL
	CALL :getFRIPAddress frIP !IP!
	ECHO Proxy opened to PTXC...
	START !winDir!WinSCP.exe ftp://!frUN!:!frPW!@!frIP! !ssl! -rawsettings ProxyMethod=2 ProxyHost=127.0.0.1 ProxyPort=!proxyPortNo!
	ECHO Opening winSCP... 
	GOTO frdownFinish 
		
		:frdownPTX10
			ECHO Equipment online, !IP!
			START /min !toolsDir!putty.exe -D !proxyPortNo! mms@!IP! -pw modular -N
			START "" "!toolsDir!HotKey.exe" /Force "!tempDir!\putty_key.ahk"
			TIMEOUT /t 2 /nobreak > NUL
			CALL :getFRIPAddress frIP !IP!
			ECHO Proxy opened to PTXC...
			START !winDir!WinSCP.exe ftp://!frUN!:!frPW!@!frIP! !ssl! -rawsettings ProxyMethod=2 ProxyHost=127.0.0.1 ProxyPort=!proxyPortNo!
			ECHO Opening winSCP... 
			GOTO :frdownFinish
		
	:frdownFinish
	DEL /f !tempDir!\putty_key.ahk
	EXIT /B 0

:frreset

	CALl :writeToLog Reset Flight Recorder remotley. 
	IF !screenPW!==none (
		SET /P "screenPW=enter PTXC Password: "
		CLS
	)
	::loop through arguments so multiple flight recorders can be reset at once
	FOR %%a in (!command!) DO (
		SET equipName=%%a
		CALL :toUCase equipName
		CALL :getEquipPTXAddress IP !equipName!
		IF !IP!==null (
		ECHO.
		ECHO Equipment !equipName! not found. Check spelling or use import if new equipment. 
		GOTO start
	) 	
	::shitty solution to not being able to easily strip the first token from the string in windows batch script
	IF %%a==frreset (
		ECHO.
		ECHO Begining Flight Recorder reset process for !equipName!
		CALL :getFRIPAddress frIP !IP!
		::create one liner command for putty to run on PTXC
		ECHO echo -e ^"e\ns\nq^" ^| timeout 10 nc -ti 2 !frIP! 23 ^& wait^; exit > frresetcmd
		!toolsDir!putty.exe -ssh !IP! -l dlog -pw gold -m frresetCmd
		DEL /f frresetCmd
	)

	EXIT /B 0

:frlogin

	CALL :writeToLog Access Flight Recorder via RDP. 
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
	SET TempFile=!tempDir!\temp_errorlevel.txt
	TIMEOUT /T 2 > NUL
	START cmd /c "!toolsDir!plink.exe -v -batch -l dlog -pw gold !IP! 'ls /' & ECHO !ERRORLEVEL! > "!TempFile!""
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
	START "" "!toolsDir!HotKey.exe" /Force "!tempDir!\putty_key.ahk"
	TIMEOUT /t 2 /nobreak > NUL
	ECHO Tunnel to FlightRecorder opened...
	ECHO Opening RDP Session to !frIP!
	START mstsc /v:127.0.0.1:!vncPortNo!
	TIMEOUT /t 2 /nobreak > NUL
	START "" "!toolsDir!HotKey.exe" /Force "!tempDir!\rdp_encrypt.ahk"
	TIMEOUT /t 4 /nobreak > NUL
	START "" "!toolsDir!HotKey.exe" /Force "!tempDir!\rdp_login.ahk"
	TIMEOUT /t 10 /nobreak > NUL
	GOTO frloginFinish
	
		:frloginPTX10
			ECHO Equipment online... !IP!
			CALL :getFRIPAddress frIP !IP!
			START /min !toolsDir!putty.exe -L !vncPortNo!:!frIP!:3389 mms@!IP! -pw modular -N
			START "" "!toolsDir!HotKey.exe" /Force "!tempDir!\putty_key.ahk"
			TIMEOUT /t 2 /nobreak > NUL
			ECHO Tunnel to FlightRecorder opened...
			ECHO Please wait, opening RDP Session...
			START mstsc /v:127.0.0.1:!vncPortNo!
			TIMEOUT /t 2 /nobreak > NUL
			START "" "!toolsDir!HotKey.exe" /Force "!tempDir!\rdp_encrypt.ahk"
			TIMEOUT /t 8 /nobreak > NUL
			START "" "!toolsDir!HotKey.exe" /Force "!tempDir!\rdp_login.ahk"
			TIMEOUT /t 10 /nobreak > NUL
			GOTO frloginFinish
			
	:frloginFinish
	TASKKILL /F /IM HotKey.exe > NUL 2>&1
	EXIT /B 0
	
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
	
:: WINSCP Functions ::
:: Retreive equipment/ server logs

:win

	::open winSCP connection to screen dlog (home)
	CALL :writeToLog Open WinSCP.
	CALL :winscp
	SET /A proxyPortNo=!proxyPortNo! + 1
	IF !screenPW!==none SET /P "screenPW=enter PTXC Password: "
	CALL :secondToken equipName !command!
	CALL :toUCase equipName
	CALL :getEquipPTXAddress IP !equipName!
	IF !IP!==null (
		ECHO.
		ECHO Equipment !equipName! not found. Check spelling or use import if new equipment.
		GOTO start
	) 		
	:: Pre-check
	PING -n 1 !IP! > NUL
	IF !ERRORLEVEL! NEQ 0 (
		ECHO.
		ECHO "Unable to reach !equipName! on !IP!, skipping WinSCP session."
		GOTO start
	)
	CALL :hostkey
	SET TempFile=!tempDir!\temp_errorlevel.txt
	TIMEOUT /T 2 > NUL
	START cmd /c "!toolsDir!plink.exe -v -batch -l dlog -pw gold !IP! 'ls /' & ECHO !ERRORLEVEL! > "!TempFile!""
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
	:: If Plink check passed, open WinSCP to PTXC
	ECHO Equipment online, !equipName! (!IP!)
	ECHO Opening winSCP connection to dlog/real_home
	START !toolsDir!\WinSCP\WinSCP.exe scp://dlog:gold@!IP!/home/dlog/real_home/
	GOTO winFinish
	
		:: If Plink check passed, open WinSCP to PTX10
		:winPTX10
			ECHO Equipment online, !equipName! (!IP!)
			ECHO Opening winSCP connection to /home/mms/
			START !toolsDir!\WinSCP\WinSCP.exe scp://mms:modular@!IP!/home/mms/
			GOTO winFinish

	:winFinish
	START "" "!toolsDir!HotKey.exe" /Force "!tempDir!\winscp.ahk"
	TIMEOUT /t 6 /nobreak > NUL
	TASKKILL /F /IM HotKey.exe > NUL 2>&1
	EXIT /B 0

:ptxlogs

	::open winSCP connection to screen for log downloads.
	CALL :writeToLog Access PTX logs via WinSCP.
	CALL :winscp
	SET /A proxyPortNo=!proxyPortNo! + 1
	IF !screenPW!==none SET /P "screenPW=enter PTXC Password: "
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
	SET TempFile=!tempDir!\temp_errorlevel.txt
	TIMEOUT /T 2 > NUL
	START cmd /c "!toolsDir!plink.exe -v -batch -l dlog -pw gold !IP! 'ls /' & ECHO !ERRORLEVEL! > "!TempFile!""
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
	:: If Plink check passed, open WinSCP to PTXC
	ECHO Equipment online, !equipName! (!IP!)
	ECHO Opening winSCP connection to /home/dlog/frontrunnerV3/logs
	START !winDir!WinSCP.exe scp://dlog:gold@!IP!/home/dlog/frontrunnerV3/logs/
	GOTO ptxlogsFinish
	:: If Plink check passed, open WinSCP to PTX10
		:ptxlogsPTX10
			ECHO Equipment online, !equipName! (!IP!)
			ECHO Opening winSCP connection to -
			ECHO /home/mms/frontrunnerV3-3.5.4-007-PTX10-1-ptx10/logs/
			START !winDir!WinSCP.exe scp://mms:modular@!IP!/home/mms/frontrunnerV3-3.5.4-007-PTX10-1-ptx10/logs/
			GOTO :ptxlogsFinish

	:ptxlogsFinish
	START "" "!toolsDir!HotKey.exe" /Force "!tempDir!\winscp.ahk"
	TIMEOUT /t 6 /nobreak > NUL
	TASKKILL /F /IM HotKey.exe > NUL 2>&1
	EXIT /B 0
	
:cache
	:: Only applicable to PTXC
	CALL :writeToLog Open cache folder via WinSCP.
	SET /A proxyPortNo=!proxyPortNo! + 1
	IF !screenPW!==none SET /P "screenPW=enter PTXC Password: "
	CALL :secondToken equipName !command!
	CALL :toUCase equipName
	CALL :getEquipPTXAddress IP !equipName!
	CALL :winscp
	SET TempFile=!tempDir!\ptx_auth.txt
	IF !IP!==null (
		ECHO.
		ECHO Equipment !equipName! not found.
		GOTO start 
	)
	PING -n 1 !IP! > NUL
	IF !ERRORLEVEL! NEQ 0 (
		ECHO.
		ECHO Unable to reach !equipName! on !IP!, skipping Cache session.
		GOTO start 
	)
	CALL :hostkey
	"!toolsDir!plink.exe" -v -batch -l dlog -pw gold !IP! "ls /" > "!TempFile!" 2>&1
	SET AUTH_STATUS=SUCCESS
	FOR /F "tokens=*" %%i IN ('FINDSTR /I "denied" "!TempFile!" 2^>NUL') DO SET AUTH_STATUS=FAILED
	
	IF "!AUTH_STATUS!"=="FAILED" (
		ECHO PTXC auth failed, swapping auth...
		GOTO cachePTX10 
		)
	
	GOTO cachePTXC
	
	:cachePTXC
		DEL "!TempFile!"
		ECHO Equipment online, !equipName! (!IP!)
		ECHO Opening winSCP connection to cache_client folder.
		START !winDir!WinSCP.exe scp://dlog:gold@!IP!/media/realroot/home/dlog/frontrunnerV3/cache_client/
		GOTO cacheFinish

	:cachePTX10
		ECHO Equipment online, !equipName! (!IP!)
		ECHO Opening winSCP connection to cache_client folder. 
		START !winDir!WinSCP.exe scp://mms:modular@!IP!/media/realroot/home/mms/frontrunnerV3-3.5.4-007-PTX10-1-ptx10/cache_client/
		GOTO cacheFinish

	:cacheFinish
		START "" "!toolsDir!HotKey.exe" /Force "!tempDir!\winscp.ahk"
		TIMEOUT /t 6 /nobreak > NUL
		TASKKILL /F /IM HotKey.exe > NUL 2>&1
		DEL "!TempFile!"
		EXIT /B 0

:: PTX Functions ::

:putty
	:: Connect to PTXC / PTX10 
	CALL :writeToLog Open PuTTY
	CALL :putkey
	CALL :secondToken equipName !command!
	CALL :toUCase equipName
	CALL :getEquipPTXAddress IP !equipName!
	SET TempFile=!tempDir!\ptx_auth.txt
	IF !IP!==null (
		ECHO.
		ECHO Equipment !equipName! not found. Check spelling or use import if new equipment.
		GOTO start 
	)
	PING -n 1 !IP! > NUL
	IF !ERRORLEVEL! NEQ 0 (
		ECHO.
		ECHO Unable to reach !equipName! on !IP!, skipping PuTTY session.
		GOTO start 
	)
	CALL :hostkey
	"!toolsDir!plink.exe" -v -batch -l dlog -pw gold !IP! "ls /" > "!TempFile!" 2>&1
	SET AUTH_STATUS=SUCCESS
	FOR /F "tokens=*" %%i IN ('FINDSTR /I "denied" "!TempFile!" 2^>NUL') DO SET AUTH_STATUS=FAILED
	
	IF "!AUTH_STATUS!"=="FAILED" (
		ECHO PTXC auth failed, swapping auth...
		GOTO puttyPTX10 
		)
	
	GOTO puttyPTXC
	
	:puttyPTXC
		ECHO !equipName! online, - !IP!
		ECHO Please wait, opening PuTTY...
		START !toolsDir!putty.exe -ssh dlog@!IP! -pw gold 
		TIMEOUT /t 1 /nobreak > NUL
		START "" "!toolsDir!HotKey.exe" /Force "!tempDir!\putty_key.ahk"
		TIMEOUT /t 1 /nobreak > NUL
		GOTO puttyFinish

	:puttyPTX10
		ECHO !equipName! online, - !IP!
		ECHO Please wait, opening putty. 
		START !toolsDir!putty.exe mms@!IP! -pw modular
		TIMEOUT /t 1 /nobreak > NUL
		START "" "!toolsDir!HotKey.exe" /Force "!tempDir!\putty_key.ahk"
		TIMEOUT /t 1 /nobreak > NUL
		GOTO puttyFinish

	:puttyFinish
		DEL "!TempFile!"
		TASKKILL /F /IM HotKey.exe > NUL 2>&1
		EXIT /B 0

:vnc
	CALL :writeToLog Open VNC Viewer
	SET /A vncPortNo=!vncPortNo! + 1
	CALL :secondToken equipName !command!
	CALL :toUCase equipName
	CALL :getEquipPTXAddress IP !equipName!
	SET TempFile=!tempDir!\ptx_auth.txt
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
	"!toolsDir!plink.exe" -v -batch -l dlog -pw gold !IP! "ls /" > "!TempFile!" 2>&1
	SET AUTH_STATUS=SUCCESS
	FOR /F "tokens=*" %%i IN ('FINDSTR /I "denied" "!TempFile!" 2^>NUL') DO SET AUTH_STATUS=FAILED
	
	IF "!AUTH_STATUS!"=="FAILED" (
		ECHO PTXC auth failed, swapping auth...
		GOTO vncPTX10 
		)
	
	GOTO vncPTXC
	
	:vncPTXC
		CALL :vncencrypt
		CALL :vncptxc
		TIMEOUT /t 1 /nobreak > NUL
		ECHO PTXC Online, !equipName! - !IP!
		ECHO Please wait, opening VNC Viewer.
		TIMEOUT /t 1 /nobreak > NUL
		START /min !toolsDir!plink.exe -v -ssh -l dlog -pw gold -L  !vncPortNo!:localhost:5900 !IP! -batch "vncserver && sleep 10"
		TIMEOUT /t 6 /nobreak > NUL
		START !vncDir!vncviewer_5.3.2.exe 127.0.0.1:!vncPortNo! 
		TIMEOUT /t 2 /nobreak > NUL
		START "" "!toolsDir!HotKey.exe" /Force "!tempDir!\vnc_encrypt.ahk"
		TIMEOUT /t 2 /nobreak > NUL
		START "" "!toolsDir!HotKey.exe" /Force "!tempDir!\vnc_ptxc.ahk"
		TIMEOUT /t 2 /nobreak > NUL
		GOTO vncFinish
	
	:vncPTX10
		CALL :vncencrypt
		CALL :vncptx10
		ECHO PTX10 Online, !equipName! - !IP!
		ECHO Please wait, opening VNC Viewer.
		TIMEOUT /t 1 /nobreak > NUL
		START /min !toolsDir!plink.exe -v -ssh -l mms -pw modular -L  !vncPortNo!:localhost:5900 !IP! -batch "vncserver && sleep 10"
		TIMEOUT /t 4 /nobreak > NUL
		START !vncDir!vncviewer_5.3.2.exe 127.0.0.1:!vncPortNo!
		TIMEOUT /t 3 /nobreak > NUL
		START "" "!toolsDir!HotKey.exe" /Force "!tempDir!\vnc_encrypt.ahk"
		TIMEOUT /t 2 /nobreak > NUL
		START "" "!toolsDir!HotKey.exe" /Force "!tempDir!\vnc_ptx10.ahk"
		TIMEOUT /t 2 /nobreak > NUL
		GOTO vncFinish

	:vncFinish
		TASKKILL /F /IM HotKey.exe > NUL 2>&1
		EXIT /B 0
	
:delcache

	CALL :writeToLog Delete cache folder and reboot PTX. 
	ECHO cd /media/realroot/home/dlog/frontrunnerV3/cache_client; rm -rf */ > !tempDir!\PTXCcachedel
	ECHO cd /media/realroot/home/mms/frontrunnerV3-3.5.4-007-PTX10-1-ptx10/cache_client; rm -rf */ > !tempDir!\PTX10cachedel
	ECHO sudo reboot > !tempDir!\reboot
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
		ECHO Unable to reach !equipName! on !IP!, skipping DELCACHE session.
		GOTO start 
	)
	CALL :hostkey
	"!toolsDir!plink.exe" -v -batch -l dlog -pw gold !IP! "ls /" > "!TempFile!" 2>&1
	SET AUTH_STATUS=SUCCESS
	FOR /F "tokens=*" %%i IN ('FINDSTR /I "denied" "!TempFile!" 2^>NUL') DO SET AUTH_STATUS=FAILED
	
	IF "!AUTH_STATUS!"=="FAILED" (
		ECHO PTXC auth failed, swapping auth...
		GOTO delcachePTX10 
		)
	
	GOTO delcachePTXC
	
	:delcachePTXC
	
		ECHO Equipment online, !equipName! (!IP!)
		ECHO (ENSURE EQUIPMENT STATUS "Not Enter AT") 
		SET /p answer=" Delete cache folder on !equipName! & Reboot PTXC ? (Y/N) "
		IF /i "!answer!"=="y" (
			START "Cache Delete" "!toolsDir!plink.exe" -batch dlog@!IP! -pw gold -m !tempDir!\PTXCcachedel -v
			PING 127.0.0.1 -n 5 > NUL
			START "PTX Reboot" "!toolsDir!plink.exe" -batch dlog@!IP! -pw gold -m !tempDir!\reboot -v
		) ELSE (
			ECHO "Operation Cancelled"
			GOTO delcacheFinish 
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
			START /min "!equipName! Reboot VNC" "!toolsDir!plink.exe" -v -ssh -l dlog -pw gold -L !vncPortNo!:localhost:5900 !IP! -batch "vncserver && sleep 10"
			TIMEOUT /t 6 /nobreak > NUL
			START "" "!toolsDir!HotKey.exe" /Force "!tempDir!\putty_key.ahk"
			TIMEOUT /t 1 /nobreak > NUL
			START "" "!toolsDir!HotKey.exe" /Force "!tempDir!\putty_encrypt.ahk"
			TIMEOUT /t 1 /nobreak > NUL
			START !vncDir!vncviewer_5.3.2.exe 127.0.0.1:!vncPortNo!
			TIMEOUT /t 1 /nobreak > NUL
			START "" "!toolsDir!HotKey.exe" /Force "!tempDir!\vnc_encrypt.ahk"
			TIMEOUT /t 2 /nobreak > NUL
			START "" "!toolsDir!HotKey.exe" /Force "!tempDir!\vnc_ptxc.ahk"
			TIMEOUT /t 6 /nobreak > NUL
			GOTO delcacheFinish
		) ELSE (
			ECHO "Cache delete complete, VNC session skipped."
			GOTO delcacheFinish 
		)

	:delcachePTX10
	
		ECHO Equipment online, !equipName! (!IP!)
		ECHO (ENSURE EQUIPMENT STATUS "Not Enter AT") 
		SET /p answer=" Delete cache folder on !equipName! & Reboot PTX10 ? (Y/N) "
		IF /i "!answer!"=="y" (
			START "Cache Delete" "!toolsDir!plink.exe" -batch mms@!IP! -pw modular -m !tempDir!\PTX10cachedel -v
			PING 127.0.0.1 -n 5 > NUL
			START "PTX Reboot" "!toolsDir!plink.exe" -batch mms@!IP! -pw modular -m !tempDir!\reboot -v
		) ELSE (
			ECHO "Operation Cancelled"
			GOTO delcacheFinish 
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
			START /min "!equipName! Reboot VNC" "!toolsDir!plink.exe" -v -ssh -l mms -pw modular -L !vncPortNo!:localhost:5900 !IP! -batch "vncserver && sleep 10"
			TIMEOUT /t 6 /nobreak > NUL
			START "" "!toolsDir!HotKey.exe" /Force "!tempDir!\putty_key.ahk"
			TIMEOUT /t 1 /nobreak > NUL
			START "" "!toolsDir!HotKey.exe" /Force "!tempDir!\putty_encrypt.ahk"
			TIMEOUT /t 1 /nobreak > NUL
			START !vncDir!vncviewer_5.3.2.exe 127.0.0.1:!vncPortNo!
			TIMEOUT /t 3 /nobreak > NUL
			START "" "!toolsDir!HotKey.exe" /Force "!tempDir!\vnc_encrypt.ahk"
			TIMEOUT /t 2 /nobreak > NUL
			START "" "!toolsDir!HotKey.exe" /Force "!tempDir!\vnc_ptx10.ahk"
			TIMEOUT /t 6 /nobreak > NUL
			GOTO delcacheFinish
		) ELSE (
			ECHO "Cache delete complete, VNC session skipped."
			GOTO delcacheFinish 
		)
	
	:delcacheFinish
	TIMEOUT /t 2 /nobreak > NUL
	TASKKILL /F /IM HotKey.exe > NUL 2>&1
	DEL "!TempFile!"
	EXIT /B 0
		
:ptxr

	CALL :writeToLog Reboot PTX via PuTTY.
	CALL :secondToken equipName !command!
	CALL :toUCase equipName
	CALL :getEquipPTXAddress IP !equipName!
	IF !IP!==null SET IP=!equipName!
	ECHO sudo reboot > !tempDir!\reboot
	IF !IP!==null (
		ECHO.
		ECHO Equipment !equipName! not found. Check spelling or use import if new equipment. 
		GOTO start
	) 	
	PING -n 1 !IP! > NUL
	IF !ERRORLEVEL! NEQ 0 (
		ECHO.
		ECHO "Unable to reach !equipName! on !IP!, skipping PTX reboot."
		DEL /f !tempDir!\reboot
		GOTO start
	)
	CALL :hostkey
	SET TempFile=!tempDir!\temp_errorlevel.txt
	TIMEOUT /T 2 > NUL
	START cmd /c "!toolsDir!plink.exe -v -batch -l dlog -pw gold !IP! 'ls /' & ECHO !ERRORLEVEL! > "!TempFile!""
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
	:: Reboot PTXC via putty
	ECHO Equipment online, !IP!
	ECHO (ENSURE EQUIPMENT STATUS "Not Enter AT")
	SET /p answer="Reboot !equipName! PTXC ? (Y/N) "
	IF /i "!answer!"=="y" (
		TIMEOUT /t 5 /nobreak
	START !toolsDir!plink.exe -batch dlog@!IP! -pw gold -m !tempDir!\reboot -v
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
		START /min "!equipName! Reboot VNC" "!toolsDir!plink.exe" -v -ssh -l dlog -pw gold -L !vncPortNo!:localhost:5900 !IP! -batch "vncserver && sleep 10"
		TIMEOUT /t 6 /nobreak > NUL
		START "" "!toolsDir!HotKey.exe" /Force "!tempDir!\putty_key.ahk"
		TIMEOUT /t 1 /nobreak > NUL
		START "" "!toolsDir!HotKey.exe" /Force "!tempDir!\putty_encrypt.ahk"
		TIMEOUT /t 1 /nobreak > NUL
		START !vncDir!vncviewer_5.3.2.exe 127.0.0.1:!vncPortNo!
		TIMEOUT /t 1 /nobreak > NUL
		START "" "!toolsDir!HotKey.exe" /Force "!tempDir!\vnc_encrypt.ahk"
		TIMEOUT /t 2 /nobreak > NUL
		START "" "!toolsDir!HotKey.exe" /Force "!tempDir!\vnc_ptxc.ahk"
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
			START !toolsDir!plink.exe -batch mms@!IP! -pw modular -m !tempDir!\reboot -v
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
			START /min "!equipName! Reboot VNC" "!toolsDir!plink.exe" -v -ssh -l mms -pw modular -L !vncPortNo!:localhost:5900 !IP! -batch "vncserver && sleep 15"
			TIMEOUT /t 6 /nobreak > NUL
			START "" "!toolsDir!HotKey.exe" /Force "!tempDir!\putty_key.ahk"
			TIMEOUT /t 1 /nobreak > NUL
			START "" "!toolsDir!HotKey.exe" /Force "!tempDir!\putty_encrypt.ahk"
			TIMEOUT /t 1 /nobreak > NUL
			START !vncDir!vncviewer_5.3.2.exe 127.0.0.1:!vncPortNo!
			TIMEOUT /t 1 /nobreak > NUL
			START "" "!toolsDir!HotKey.exe" /Force "!tempDir!\vnc_encrypt.ahk"
			TIMEOUT /t 2 /nobreak > NUL
			START "" "!toolsDir!HotKey.exe" /Force "!tempDir!\vnc_ptx10.ahk"
			TIMEOUT /t 6 /nobreak > NUL
			GOTO rebootFinish
			) ELSE (
				ECHO "PTX10 Reboot complete, VNC session skipped."
				GOTO rebootFinish 
			)
		
	:rebootFinish
	TIMEOUT /t 2 /nobreak > NUL
	TASKKILL /F /IM HotKey.exe > NUL 2>&1
	EXIT /B 0
	
:ping
	
	CALL :writeToLog Run embedded pings. 
	CALL :secondToken equipName !command!
	CALL :toUCase equipName
	CALL :getEquipPTXAddress IP !equipName!
	IF !IP!==null SET IP=!equipName!
	PING -n 3 !IP! > NUL
	IF !ERRORLEVEL! NEQ 0 (
	ECHO "Unable to reach !equipName! on !IP!, skipping Ping attempt.
	GOTO start
	)
	CALL :hostkey
	SET TempFile=!tempDir!\temp_errorlevel.txt
	TIMEOUT /T 2 > NUL
	START cmd /c "!toolsDir!plink.exe -v -batch -l dlog -pw gold !IP! 'ls /' & ECHO !ERRORLEVEL! > "!TempFile!""
	TIMEOUT /T 2 > NUL
	FOR /F "delims=" %%A in ('type "!TempFile!"') DO SET "ERRORLEV=%%A"
	ECHO.
	IF "!ERRORLEV!"=="0 " (
		ECHO PTXC
	) ELSE (
		ECHO PTX10
		GOTO pingPTX10
	)
	
	DEL "!TempFile!"
	:: If Plink check passed, PTXC Ping Function
	ECHO Machine online, !equipName! (!IP!)
	ECHO Please wait, pinging following devices...
	ECHO !equipName! PTXC to Server, GNSS 1, 2 and AVI.
	START "!equipName! PTXC to GNSS 1" !toolsDir!plink.exe -batch dlog@!IP! -pw gold "ping 192.168.0.101"
	START "!equipName! PTXC to GNSS 2" !toolsDir!plink.exe -batch dlog@!IP! -pw gold "ping 192.168.0.102"
	START "!equipName! PTXC to AVI" !toolsDir!plink.exe -batch dlog@!IP! -pw gold "ping 192.168.0.254"
	START "!equipName! PTXC to Server" !toolsDir!plink.exe -batch dlog@!IP! -pw gold "ping 10.110.19.16"
	GOTO pingFinish
	
	:: If Plink check failed, PTX10 Ping Function
	:pingPTX10
		ECHO Machine online, !equipName! (!IP!)
		ECHO Please wait, pinging following devices...
		ECHO !equipName! PTX10 to Server, GNSS 1, 2 and AVI.
		START "!equipName! PTX10 to GNSS 1" !toolsDir!plink.exe -batch mms@!IP! -pw modular "ping 192.168.0.101"
		START "!equipName! PTX10 to GNSS 2" !toolsDir!plink.exe -batch mms@!IP! -pw modular "ping 192.168.0.102"
		START "!equipName! PTX10 to AVI" !toolsDir!plink.exe -batch mms@!IP! -pw modular "ping 192.168.0.254"
		START "!equipName! PTX10 to Server" !toolsDir!plink.exe -batch mms@!IP! -pw modular "ping 10.110.19.16"
		GOTO pingFinish
	
	:pingFinish
	EXIT /B 0

:config
	
	CALL :writeToLog Run PTX config. 
	CALL :secondToken equipName !command!
	CALL :toUCase equipName
	CALL :getEquipPTXAddress IP !equipName!
	IF !IP!==null SET IP=!equipName!
	CALL :writeToLog Opening terminal to !equipName! on !IP!
	ECHO config > !tempDir!\config
	PING -n 1 !IP! > NUL
	IF !ERRORLEVEL! NEQ 0 (
		ECHO "Unable to reach !equipName! on !IP!, skipping Config attempt.
		GOTO start
	)
	CALL :hostkey
	SET TempFile=!tempDir!\temp_errorlevel.txt
	TIMEOUT /T 2 > NUL
	START cmd /c "!toolsDir!plink.exe -v -batch -l dlog -pw gold !IP! 'ls /' & ECHO !ERRORLEVEL! > "!TempFile!""
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
	:: If Plink check passed, PTXC Ping Function
	ECHO Machine online, !equipName! (!IP!)
	ECHO Please wait, running config via PuTTY...
	START /min !toolsDir!putty.exe -L !vncPortNo!:127.0.0.1:5900 dlog@!IP! -pw gold -m !tempDir!\config
	
	SET /p answer=" Open VNC session? (Y/N) "
	IF /i "!answer!"=="y" (
	ECHO Please wait, Opening VNC Session...
	CALL :putencrypt
	CALL :putkey
	CALL :vncencrypt
	CALL :vncptxc
	SET /A vncPortNo=!vncPortNo! + 1
	START /min "!equipName! Reboot VNC" "!toolsDir!plink.exe" -v -ssh -l dlog -pw gold -L !vncPortNo!:localhost:5900 !IP! -batch "vncserver && sleep 10"
	TIMEOUT /t 6 /nobreak > NUL
	START "" "!toolsDir!HotKey.exe" /Force "!tempDir!\putty_key.ahk"
	TIMEOUT /t 1 /nobreak > NUL
	START "" "!toolsDir!HotKey.exe" /Force "!tempDir!\putty_encrypt.ahk"
	TIMEOUT /t 1 /nobreak > NUL
	START !vncDir!vncviewer_5.3.2.exe 127.0.0.1:!vncPortNo!
	TIMEOUT /t 2 /nobreak > NUL
	START "" "!toolsDir!HotKey.exe" /Force "!tempDir!\vnc_encrypt.ahk"
	TIMEOUT /t 2 /nobreak > NUL
	START "" "!toolsDir!HotKey.exe" /Force "!tempDir!\vnc_ptxc.ahk"
	TIMEOUT /t 6 /nobreak > NUL
	) ELSE (
		ECHO VNC session not required...
	)
	
	TASKKILL /F /IM HotKey.exe > NUL 2>&1
	EXIT /B 0

:: General purpose subroutines ::

:: AutoHotKey Scripts

:atmon
	ECHO WinWait "Device Select" > !tempDir!\atmon.ahk
	ECHO If WinActive >> !tempDir!\atmon.ahk
	ECHO { >> !tempDir!\atmon.ahk
	ECHO ; WinActivate "Device Select" >> !tempDir!\atmon.ahk
	ECHO ControlClick "Ethernet" >> !tempDir!\atmon.ahk
	ECHO Sleep 1000 >> !tempDir!\atmon.ahk
	ECHO SendInput "{Enter}" >> !tempDir!\atmon.ahk
	ECHO } >> !tempDir!\atmon.ahk
	ECHO ExitApp >> !tempDir!\atmon.ahk
	
	GOTO :EOF
	
:gpsencrypt
	ECHO WinWait "PuTTY Security Alert" > !tempDir!\gps_encrypt.ahk
	ECHO If WinActive >> !tempDir!\gps_encrypt.ahk
	ECHO { >> !tempDir!\gps_encrypt.ahk
	ECHO ; WinActivate "PuTTY Security Alert" >> !tempDir!\gps_encrypt.ahk
	ECHO ControlClick "Yes" >> !tempDir!\gps_encrypt.ahk
	ECHO SendInput "{Enter}" >> !tempDir!\gps_encrypt.ahk
	ECHO } >> !tempDir!\gps_encrypt.ahk
	ECHO ExitApp >> !tempDir!\gps_encrypt.ahk
	
	GOTO :EOF
	
:putkey
	ECHO WinWait "PuTTY Security Alert" > !tempDir!\putty_key.ahk
	ECHO IF WinActive >> !tempDir!\putty_key.ahk
	ECHO { >> !tempDir!\putty_key.ahk
	ECHO ; WinActivate ("PuTTY Security Alert") >> !tempDir!\putty_key.ahk
	ECHO ControlClick "Accept" >> !tempDir!\putty_key.ahk
	ECHO SendInput "{Enter}" >> !tempDir!\putty_key.ahk
	ECHO } >> !tempDir!\putty_key.ahk
	ECHO ExitApp >> !tempDir!\putty_key.ahk

	GOTO :EOF

:putencrypt
	ECHO WinWait "PuTTY Security Alert" > !tempDir!\putty_encrypt.ahk
	ECHO IF WinActive >> !tempDir!\putty_encrypt.ahk
	ECHO { >> !tempDir!\putty_encrypt.ahk
	ECHO ; WinActivate ("PuTTY Security Alert") >> !tempDir!\putty_encrypt.ahk
	ECHO ControlClick "Yes" >> !tempDir!\putty_encrypt.ahk
	ECHO SendInput "{Enter}" >> !tempDir!\putty_encrypt.ahk
	ECHO } >> !tempDir!\putty_encrypt.ahk
	ECHO ExitApp >> !tempDir!\putty_encrypt.ahk
	
	GOTO :EOF
	
:topcon
	ECHO WinWait "Topcon Receiver Utility" > !tempDir!\topcon.ahk
	ECHO WinActivate ("Topcon Receiver Utility") >> !tempDir!\topcon.ahk
	ECHO ExitApp >> !tempDir!\topcon.ahk
	
	GOTO :EOF
	
:vncencrypt
	ECHO WinWait "Encryption" > !tempDir!\vnc_encrypt.ahk
	ECHO If WinActive >> !tempDir!\vnc_encrypt.ahk
	ECHO { >> !tempDir!\vnc_encrypt.ahk
	ECHO ; WinActivate ("Encryption") >> !tempDir!\vnc_encrypt.ahk
	ECHO ControlClick "Continue", "Encryption" >> !tempDir!\vnc_encrypt.ahk
	ECHO } >> !tempDir!\vnc_encrypt.ahk
	ECHO ExitApp >> !tempDir!\vnc_encrypt.ahk
	
	GOTO :EOF
	
:vncptxc
	ECHO WinWait "VNC Viewer" > !tempDir!\vnc_ptxc.ahk
	ECHO WinActivate "VNC Viewer" >> !tempDir!\vnc_ptxc.ahk
	ECHO SendInput "dlog" >> !tempDir!\vnc_ptxc.ahk
	ECHO SendInput "{Enter}" >> !tempDir!\vnc_ptxc.ahk
	ECHO SendInput "gold" >> !tempDir!\vnc_ptxc.ahk
	ECHO SendInput "{Enter}" >> !tempDir!\vnc_ptxc.ahk
	ECHO ExitApp >> !tempDir!\vnc_ptxc.ahk
	
	GOTO :EOF
	
:vncptx10
	ECHO WinWait "VNC Viewer" > !tempDir!\vnc_ptx10.ahk
	ECHO WinActivate "VNC Viewer" >> !tempDir!\vnc_ptx10.ahk
	ECHO SendInput "mms" >> !tempDir!\vnc_ptx10.ahk
	ECHO SendInput "{Enter}" >> !tempDir!\vnc_ptx10.ahk
	ECHO SendInput "modular" >> !tempDir!\vnc_ptx10.ahk
	ECHO SendInput "{Enter}" >> !tempDir!\vnc_ptx10.ahk
	ECHO ExitApp >> !tempDir!\vnc_ptx10.ahk
	
	GOTO :EOF
	
:winscp
	ECHO WinWait "Warning" > !tempDir!\winscp.ahk
	ECHO If WinActive >> !tempDir!\winscp.ahk
	ECHO { >> !tempDir!\winscp.ahk
	ECHO ; WinActivate "Warning" >> !tempDir!\winscp.ahk
	ECHO ControlClick "Yes" >> !tempDir!\winscp.ahk
	ECHO SendInput "{Enter}" >> !tempDir!\winscp.ahk
	ECHO } >> !tempDir!\winscp.ahk
	ECHO ExitApp >> !tempDir!\winscp.ahk
	
	GOTO :EOF
	
:rdpencrypt
	ECHO WinWait "Remote Desktop Connection" > !tempDir!\rdp_encrypt.ahk
	ECHO If WinActive >> !tempDir!\rdp_encrypt.ahk
	ECHO { >> !tempDir!\rdp_encrypt.ahk
	ECHO ; WinActivate "Remote Desktop Connection" >> !tempDir!\rdp_encrypt.ahk
	ECHO ControlClick "Yes" >> !tempDir!\rdp_encrypt.ahk
	ECHO SendInput "{Enter}" >> !tempDir!\rdp_encrypt.ahk
	ECHO } >> !tempDir!\rdp_encrypt.ahk
	ECHO ExitApp >> !tempDir!\rdp_encrypt.ahk
	
	GOTO :EOF
	
:rdpwarning
	ECHO WinWait "Remote Desktop Connection" > !tempDir!\rdp_warning.ahk
	ECHO If WinActive >> !tempDir!\rdp_warning.ahk
	ECHO { >> !tempDir!\rdp_warning.ahk
	ECHO ; WinActivate "Remote Desktop Connection" >> !tempDir!\rdp_warning.ahk
	ECHO ControlClick "Yes" >> !tempDir!\rdp_warning.ahk
	ECHO SendInput "{Enter}" >> !tempDir!\rdp_warning.ahk
	ECHO } >> !tempDir!\rdp_warning.ahk
	ECHO ExitApp >> !tempDir!\rdp_warning.ahk
	
	GOTO :EOF
	
:rdplogin
	ECHO WinWait "127.0.0.1:5901 - Remote Desktop Connection" > !tempDir!\rdp_login.ahk
	ECHO If WinActive >> !tempDir!\rdp_login.ahk
	ECHO { >> !tempDir!\rdp_login.ahk
	ECHO ; WinActivate "Log On to Windows" >> !tempDir!\rdp_login.ahk
	ECHO SendInput "administrator" >> !tempDir!\rdp_login.ahk
	ECHO Send "{Tab}" >> !tempDir!\rdp_login.ahk
	ECHO SendInput "komatsu" >> !tempDir!\rdp_login.ahk
	ECHO SendInput "{Enter}" >> !tempDir!\rdp_login.ahk
	ECHO } >> !tempDir!\rdp_login.ahk
	ECHO ExitApp >> !tempDir!\rdp_login.ahk
	
	GOTO :EOF

::FrontRunner stores the vehicle IPs as a decimal representation of the last two octets, this converts it back to octet representation
:: %1 is return variable, %2 is decimal IP

:decimcalToOctets

	SET %~1=0.0
	SET /A dec=%2
	SET /A "firstOct = (!dec! & 65280) / 256"
	SET /A "secondOct=!dec! & 255"
	SET %~1=!firstOct!.!secondOct!
	EXIT /B 0

:load

	SET /A recordToLoad=1
	FOR /F "delims=" %%a in (!datFile!) DO (
		CALL :firstToken nameIn %%a
		IF !recordToLoad! GTR 1 (
			CALL :secondToken ptxIPIn %%a
			CALL :thirdToken aviIPIn %%a
			SET name[!arraySize!]=!nameIn!
			SET ptxIP[!arraySize!]=!ptxIPIn!
			SET aviIP[!arraySize!]=!aviIPIn!
			SET /A arraySize += 1
		)
		SET /A recordToLoad += 1
 	)
	GOTO :EOF

:: %1 is return variable, %2 is truck name to find IP for

:getEquipPTXAddress

	SET %~1=null
	SET /A lastEntry= !arraySize! - 1
	FOR /L %%n in (0,1,!lastEntry!) do (
		IF !name[%%n]!==%2 SET %~1=!ptxIP[%%n]!
	)
	GOTO :EOF
	
:setEquipPTXAddress

	SET /A lastEntry= !arraySize! - 1
	FOR /L %%n in (0,1,!lastEntry!) do (
		IF !name[%%n]!==%1 (
			SET ptxIP[%%n]=%2
		)
	)
	GOTO :EOF
	
:getEquipAVIAddress

	SET %~1=null	
	SET /A lastEntry= !arraySize! - 1
	FOR /L %%n in (0,1,!lastEntry!) do (
		IF "!name[%%n]!"=="%2" SET %~1=!aviIP[%%n]!
	)
	GOTO :EOF

::%1 is return variable, %2 is IP to check

:upOrDown

	SET %~1=DOWN
	FOR /F "delims=" %%a in ('ping -n 1 %2') do (
		CALL :thirdToken responseFrom %%a
		IF !responseFrom!==%2: SET %~1=UP
	)
	GOTO :EOF

::%1 is return variable, %2 onwards is input string

:firstToken

	SET %~1=%2
	GOTO :EOF

::%1 is return variable, %2 onwards is input string

:secondToken

	SET %~1=%3
	GOTO :EOF

::%1 is return variable, %2 onwards are input string

:thirdToken

	SET %~1=%4
	GOTO :EOF

::%1 is return variable, %2 onwards are input string

:fourthToken

	SET %~1=%5
	GOTO :EOF

::%1 is string to write to log file

:writeToLog

	ECHO !DATE!!TIME! - %username% - !command! - %* >> !logFile!
	GOTO :EOF

::%1 is variable to change to upper case

:toUCase

    SET result=!%~1:a=A!
    SET result=!result:b=B!
    SET result=!result:c=C!
    SET result=!result:d=D!
    SET result=!result:e=E!
    SET result=!result:f=F!
    SET result=!result:g=G!
    SET result=!result:h=H!
    SET result=!result:i=I!
    SET result=!result:j=J!
    SET result=!result:k=K!
    SET result=!result:l=L!
    SET result=!result:m=M!
    SET result=!result:n=N!
    SET result=!result:o=O!
    SET result=!result:p=P!
    SET result=!result:q=Q!
    SET result=!result:r=R!
    SET result=!result:s=S!
    SET result=!result:t=T!
    SET result=!result:u=U!
    SET result=!result:v=V!
    SET result=!result:w=W!
    SET result=!result:x=X!
    SET result=!result:y=Y!
    SET result=!result:z=Z!
    SET %~1=!result!
    GOTO :EOF
	
:hostkey
	START /min !toolsDir!putty.exe "!IP!"
	TIMEOUT /t 2 /nobreak > NUL
	START "" "!toolsDir!HotKey.exe" "!tempDir!\putty_key.ahk"
	TIMEOUT /t 2 /nobreak > NUL
	TASKKILL /F /IM putty.exe > NUL 2>&1
	TASKKILL /F /IM HotKey.exe > NUL 2>&1
	GOTO :EOF
	
:help
  @echo off
  set "HelpFile=%SCRIPTDIR%T1_Tools_Help_Commands.html"

  >"%HelpFile%" echo ^<!DOCTYPE html^>
  >>"%HelpFile%" echo ^<html lang="en"^>
  >>"%HelpFile%" echo ^<head^>
  >>"%HelpFile%" echo   ^<meta charset="utf-8" /^>
  >>"%HelpFile%" echo   ^<meta name="viewport" content="width=device-width,initial-scale=1" /^>
  >>"%HelpFile%" echo   ^<title^>T1 Tools — Command Help^</title^>
  >>"%HelpFile%" echo   ^<style^>
  >>"%HelpFile%" echo     body{margin:0;background:#0f1115;color:#e6e6e6;font:15px/1.5 system-ui,-apple-system,Segoe UI,Roboto,Arial}
  >>"%HelpFile%" echo     .wrap{max-width:900px;margin:32px auto;padding:0 16px}
  >>"%HelpFile%" echo     h1{font-size:26px;margin:0 0 6px}
  >>"%HelpFile%" echo     .sub{color:#9aa4b2;font-size:12px;margin-bottom:18px}
  >>"%HelpFile%" echo     details{background:#111522;border:1px solid #2a3140;border-radius:10px;margin:12px 0;overflow:hidden}
  >>"%HelpFile%" echo     summary{list-style:none;cursor:pointer;padding:12px 14px;font-weight:600}
  >>"%HelpFile%" echo     summary::-webkit-details-marker{display:none}
  >>"%HelpFile%" echo     .chev{display:inline-block;transition:.15s transform;margin-right:8px}
  >>"%HelpFile%" echo     details[open] .chev{transform:rotate(90deg)}
  >>"%HelpFile%" echo     .section{border-top:1px solid #2a3140;padding:10px 14px 12px}
  >>"%HelpFile%" echo     ul{margin:6px 0 0 22px;padding:0}
  >>"%HelpFile%" echo     li{margin:8px 0}
  >>"%HelpFile%" echo     .cmd{font-weight:600;color:#a78bfa}
  >>"%HelpFile%" echo     code{background:#0b0d12;border:1px solid #2a3140;border-radius:6px;padding:2px 6px;font-family:Consolas,monospace;font-size:12px;color:#e5e7eb}
  >>"%HelpFile%" echo     .note{color:#9aa4b2;font-size:12px;margin-top:18px}
  >>"%HelpFile%" echo   ^</style^>
  >>"%HelpFile%" echo ^</head^>
  >>"%HelpFile%" echo ^<body^>^<div class="wrap"^>
  >>"%HelpFile%" echo   ^<h1^>T1 Tools — Command Help^</h1^>
  >>"%HelpFile%" echo   ^<div class="sub"^>Updated %date% %time%^</div^>

  rem ===== AVI =====
  >>"%HelpFile%" echo   ^<details open^>
  >>"%HelpFile%" echo     ^<summary^>^<span class="chev"^>▸^</span^>AVI^</summary^>
  >>"%HelpFile%" echo     ^<div class="section"^>
  >>"%HelpFile%" echo       ^<ul^>
  >>"%HelpFile%" echo         ^<li^>^<span class="cmd"^>avi^</span^> — Opens AVI web UI. ^<code^>avi "equipName"^</code^>^</li^>
  >>"%HelpFile%" echo         ^<li^>^<span class="cmd"^>avilogs^</span^> — Tunnel via PTX and open WinSCP to AVI logs. ^<code^>avilogs "equipName"^</code^>^</li^>
  >>"%HelpFile%" echo       ^</ul^>
  >>"%HelpFile%" echo     ^</div^>
  >>"%HelpFile%" echo   ^</details^>

  rem ===== AHT / Flight Recorder =====
  >>"%HelpFile%" echo   ^<details^>
  >>"%HelpFile%" echo     ^<summary^>^<span class="chev"^>▸^</span^>AHT / Flight Recorder^</summary^>
  >>"%HelpFile%" echo     ^<div class="section"^>
  >>"%HelpFile%" echo       ^<ul^>
  >>"%HelpFile%" echo         ^<li^>^<span class="cmd"^>atmon^</span^> — Tunnel to FR (port 50000) + launch ATMonitor. ^<code^>atmon "equipName"^</code^>^</li^>
  >>"%HelpFile%" echo         ^<li^>^<span class="cmd"^>frdownload^</span^> — Open FR in WinSCP; for Dash 5 use SSL. ^<code^>frdownload "equipName"^</code^>, ^<code^>frdownload -ssl "equipName"^</code^>^</li^>
  >>"%HelpFile%" echo         ^<li^>^<span class="cmd"^>frlogin^</span^> — Remote Desktop to FR. ^<code^>frlogin "equipName"^</code^>^</li^>
  >>"%HelpFile%" echo         ^<li^>^<span class="cmd"^>frreset^</span^> — Restart FR (multi-vehicle ok). ^<code^>frreset "equipName" [...]^</code^>^</li^>
  >>"%HelpFile%" echo       ^</ul^>
  >>"%HelpFile%" echo     ^</div^>
  >>"%HelpFile%" echo   ^</details^>

  rem ===== PTX =====
  >>"%HelpFile%" echo   ^<details^>
  >>"%HelpFile%" echo     ^<summary^>^<span class="chev"^>▸^</span^>PTX^</summary^>
  >>"%HelpFile%" echo     ^<div class="section"^>
  >>"%HelpFile%" echo       ^<ul^>
  >>"%HelpFile%" echo         ^<li^>^<span class="cmd"^>vnc^</span^> — VNC to Screen. ^<code^>vnc "equipName"^</code^>^</li^>
  >>"%HelpFile%" echo         ^<li^>^<span class="cmd"^>putty^</span^> — PTX shell in PuTTY. ^<code^>putty "equipName"^</code^>^</li^>
  >>"%HelpFile%" echo         ^<li^>^<span class="cmd"^>cache^</span^> — Open PTX cache in WinSCP. ^<code^>cache "equipName"^</code^>^</li^>
  >>"%HelpFile%" echo         ^<li^>^<span class="cmd"^>delcache^</span^> — Delete cache + reboot PTX. ^<code^>delcache "equipName"^</code^>^</li^>
  >>"%HelpFile%" echo         ^<li^>^<span class="cmd"^>ptxr^</span^> — Reboot PTX. ^<code^>ptxr "equipName"^</code^>^</li^>
  >>"%HelpFile%" echo         ^<li^>^<span class="cmd"^>win^</span^> — Open Screen home dir. ^<code^>win "equipName"^</code^>^</li^>
  >>"%HelpFile%" echo         ^<li^>^<span class="cmd"^>ptxlogs^</span^> — Open PTX logs in WinSCP. ^<code^>ptxlogs "equipName"^</code^>^</li^>
  >>"%HelpFile%" echo       ^</ul^>
  >>"%HelpFile%" echo     ^</div^>
  >>"%HelpFile%" echo   ^</details^>

  rem ===== GNSS =====
  >>"%HelpFile%" echo   ^<details^>
  >>"%HelpFile%" echo     ^<summary^>^<span class="chev"^>▸^</span^>GNSS^</summary^>
  >>"%HelpFile%" echo     ^<div class="section"^>
  >>"%HelpFile%" echo       ^<ul^>
  >>"%HelpFile%" echo         ^<li^>^<span class="cmd"^>tru^</span^> — Tunnels to both GNSS receivers + open TRU. ^<code^>tru "equipName"^</code^>^</li^>
  >>"%HelpFile%" echo         ^<li^>^<span class="cmd"^>gnsslogs^</span^> — Proxy to GNSS1/2 and pull logs. ^<code^>gnsslogs "equipName"^</code^>^</li^>
  >>"%HelpFile%" echo       ^</ul^>
  >>"%HelpFile%" echo     ^</div^>
  >>"%HelpFile%" echo   ^</details^>

  rem ===== MISC / Legacy =====
  >>"%HelpFile%" echo   ^<details^>
  >>"%HelpFile%" echo     ^<summary^>^<span class="chev"^>▸^</span^>Misc / Legacy^</summary^>
  >>"%HelpFile%" echo     ^<div class="section"^>
  >>"%HelpFile%" echo       ^<ul^>
  >>"%HelpFile%" echo         ^<li^>^<span class="cmd"^>import^</span^> — Legacy FR ≤3.7 equipment list sync. ^<code^>import^</code^>^</li^>
  >>"%HelpFile%" echo       ^</ul^>
  >>"%HelpFile%" echo     ^</div^>
  >>"%HelpFile%" echo   ^</details^>

  >>"%HelpFile%" echo   ^<div class="note"^>Tip: Check "Not Entered AT" in Equipment Status before reboots.^</div^>
  >>"%HelpFile%" echo ^</div^>^</body^>^</html^>

  where msedge >nul 2>&1 && start "" msedge "%HelpFile%" || start "" "%HelpFile%"
  EXIT /B 0

:exit 
	ECHO Exiting T1 Tools...
	EXIT /B 0