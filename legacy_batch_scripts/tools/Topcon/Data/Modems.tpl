<?xml version="1.0"?>
<!-- *******  Topcon Positioning Systems  *******        -->
<!--  Cellular module management templates file          -->
<!--                                                     -->
<!--  This file includes templates for:                  -->
<!--  1.Digital UHF modem with Wavecom GSM module        -->
<!--  2.Digital UHF modem with Motorola GSM module       -->
<!--  3.Satel 3AS OEM11 modem with Motorola GSM module   -->
<!--  4.Digital UHF II modem with Motorola GSM module    -->
<!--  5.Digital UHF II modem with Motorola HSDPA module  -->
<!--  6.FH915+ modem with Motorola GSM module            -->
<!--  7.FH915+ modem with Motorola HSDPA module          -->
<!--  8.FH915+ modem with Motorola CDMA module           -->
<!--  9.Digital UHF modem with Motorola CDMA module      -->
<!-- 10.Digital UHF modem with Wavecom CDMA module       -->
<!-- 11.Digital UHF II modem with Motorola CDMA module   -->
<!-- 12.Digital UHF II modem with Wavecom GSM module     -->
<!-- 13.Digital UHF II modem with Wavecom CDMA module    -->
<!-- 14.Satel 3AS OEM11 modem with Motorola HSDPA module -->
<!-- 15.HiPer SR Plus with Cinterion PHS8 module         -->
<!-- 16.Digital UHF II modem with H24 Replacement Card   -->

<templates-list schema="1.1">
<version>1.2</version>

<template name="ArWest|AW401;Wavecom|Q24/G">
<id>[$$dev.port$$];ArWest|AW401@[$$radio.rate$$];Wavecom|Q24/G@[$$cell.rate$$]</id>
<version>1.3</version>
<description>Digital UHF modem with Wavecom Q24 GSM module</description>
<compat-version>1</compat-version>

<profiles-list>
<profile name="internet">
	<description>Connect to Internet using GPRS by cellular modem</description>
	<block id="1" type="script" script="checkgsm">
		<branch from="0" to="0" id="3"></branch>

		<branch from="1" to="1" id="9"></branch>

		<branch from="2" to="15" id="2">
			<try times="1" id="1"></try></branch>
	</block>
	<block id="2" type="script" script="togsm">
		<branch from="0" to="0" id="3"></branch>

		<branch from="1" to="1" id="9"></branch>

		<branch from="2" to="15" id="2"></branch>
	</block>
	<block id="3" type="script" script="initgsm">
		<branch from="0" to="0" id="4"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="2">
			<try times="30" id="3"></try></branch>
	</block>
	<block id="4" type="script" script="setpin">
		<branch from="0" to="0" id="10"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="2" id="1">
			<try times="2" id="4"></try></branch>
		<branch from="3" to="3" id="3">
			<try times="10" id="4"></try></branch>
		<branch from="4" to="15" id="5"></branch>
	</block>
	<block id="5" type="script" script="setgprs">
		<branch from="0" to="0" id="6"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="3">
			<try times="10" id="5"></try></branch>
	</block>
	<block id="6" type="script" script="setppp">
		<branch from="0" to="0" id="7"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="5">
			<try times="30" id="6"></try></branch>
	</block>
	<block id="7" type="ppp" script="runppp">
		<branch from="0" to="0" id="6"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="6"></branch>
	</block>
	<block id="8" type="script" script="hangup">
		<branch from="0" to="1" id="9"></branch>

		<branch from="2" to="2" id="9">
			<try times="5" id="8"></try></branch>
		<branch from="3" to="15" id="9"></branch>
	</block>
	<block id="9" type="script" script="touhf">
		<branch from="0" to="0" id="0"></branch>
		<branch from="2" to="2" id="0">
			<try times="5" id="9"></try></branch>
		<branch from="3" to="3" id="0"></branch>
		<branch from="4" to="15" id="0">
			<try times="5" id="9"></try></branch>
	</block>
	<block id="10" type="script" script="error">
		<branch from="0" to="0" id="10"></branch>

		<branch from="1" to="15" id="8"></branch>
	</block>
</profile>

<profile name="c-master">
	<description>Start outgoing cellular data connection</description>
	<block id="1" type="script" script="checkgsm">
		<branch from="0" to="0" id="3"></branch>

		<branch from="1" to="1" id="9"></branch>

		<branch from="2" to="15" id="2">
			<try times="1" id="1"></try></branch>
	</block>
	<block id="2" type="script" script="togsm">
		<branch from="0" to="0" id="3"></branch>

		<branch from="1" to="1" id="9"></branch>

		<branch from="2" to="15" id="2"></branch>
	</block>
	<block id="3" type="script" script="initgsm">
		<branch from="0" to="0" id="4"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="2">
			<try times="30" id="3"></try></branch>
	</block>
	<block id="4" type="script" script="setpin">
		<branch from="0" to="0" id="10"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="2" id="1">
			<try times="2" id="4"></try></branch>
		<branch from="3" to="3" id="3">
			<try times="10" id="4"></try></branch>
		<branch from="4" to="15" id="5"></branch>
	</block>
	<block id="5" type="script" script="setgsm">
		<branch from="0" to="0" id="6"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="3">
			<try times="10" id="5"></try></branch>
	</block>
	<block id="6" type="script" script="setgsmm">
		<branch from="0" to="0" id="7"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="5">
			<try times="30" id="6"></try></branch>
	</block>
	<block id="7" type="direct" script="rungsm">
		<branch from="0" to="0" id="6"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="5"></branch>
	</block>
	<block id="8" type="script" script="hangup">
		<branch from="0" to="1" id="9"></branch>

		<branch from="2" to="2" id="9">
			<try times="5" id="8"></try></branch>
		<branch from="3" to="15" id="9"></branch>
	</block>
	<block id="9" type="script" script="touhf">
		<branch from="0" to="0" id="0"></branch>

		<branch from="2" to="15" id="0">
			<try times="5" id="9"></try></branch>
	</block>
	<block id="10" type="script" script="error">
		<branch from="0" to="0" id="10"></branch>

		<branch from="1" to="15" id="8"></branch>
	</block>
</profile>

<profile name="c-slave">
	<description>Wait for incoming cellular data call</description>
	<block id="1" type="script" script="checkgsm">
		<branch from="0" to="0" id="3"></branch>

		<branch from="1" to="1" id="9"></branch>

		<branch from="2" to="15" id="2">
			<try times="1" id="1"></try></branch>
	</block>
	<block id="2" type="script" script="togsm">
		<branch from="0" to="0" id="3"></branch>

		<branch from="1" to="1" id="9"></branch>

		<branch from="2" to="15" id="2"></branch>
	</block>
	<block id="3" type="script" script="initgsm">
		<branch from="0" to="0" id="4"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="2">
			<try times="30" id="3"></try></branch>
	</block>
	<block id="4" type="script" script="setpin">
		<branch from="0" to="0" id="10"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="2" id="1">
			<try times="2" id="4"></try></branch>
		<branch from="3" to="3" id="3">
			<try times="10" id="4"></try></branch>
		<branch from="4" to="15" id="5"></branch>
	</block>
	<block id="5" type="script" script="setgsm">
		<branch from="0" to="0" id="6"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="3">
			<try times="10" id="5"></try></branch>
	</block>
	<block id="6" type="script" script="setgsms">
		<branch from="0" to="0" id="7"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="2" id="5">
			<try times="30" id="6"></try></branch>
		<branch from="3" to="3" id="7"></branch>

		<branch from="4" to="15" id="5">
			<try times="3" id="6"></try></branch>
	</block>
	<block id="7" type="direct" script="rungsm">
		<branch from="0" to="0" id="6"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="5"></branch>
	</block>
	<block id="8" type="script" script="hangup">
		<branch from="0" to="1" id="9"></branch>

		<branch from="2" to="2" id="9">
			<try times="5" id="8"></try></branch>
		<branch from="3" to="15" id="9"></branch>
	</block>
	<block id="9" type="script" script="touhf">
		<branch from="0" to="0" id="0"></branch>

		<branch from="2" to="15" id="0">
			<try times="5" id="9"></try></branch>
	</block>
	<block id="10" type="script" script="error">
		<branch from="0" to="0" id="10"></branch>

		<branch from="1" to="15" id="8"></branch>
	</block>
</profile>

</profiles-list>

<scripts-list>
<script name="checkgsm">
<![CDATA[$ABORT||$ENDLINE|\r|$TIMEOUT|15|$REPORT|M105#Looking for modem|$DAISY|OFF||dm\r\n\p%%|RE002%%|%%dm,[$$dev.port$$]|RE|%%set,/par[$$dev.port$$]/rate,[$$cell.rate$$]|RE||$DAISY|[$$dev.port$$]|$TIMEOUT|10||AT|OK-AT-OK-AT-OK]]>
</script>

<script name="togsm">
<![CDATA[$ABORT||$ENDLINE|\r|$TIMEOUT|15|$DAISY|OFF||dm\r\n\p%%|RE002%%|%%dm,[$$dev.port$$]|RE||$REPORT|M106#Configuring modem||%%set,/par[$$dev.port$$]/rate,[$$radio.rate$$]|RE|%%set,/par[$$dev.port$$]/rtscts,off|RE||$DAISY|[$$dev.port$$]|$TIMEOUT|15||++++\p|@00-++++-@01|ATI|Topcon||@00|LINK RFSW 1|@00|\p\pDATAMODE|$WAIT|10|$DAISY|OFF||dm\r\n\p%%|RE002%%|%%set,/par[$$dev.port$$]/rate,[$$cell.rate$$]|RE|%%set,/par[$$dev.port$$]/rtscts,on|RE||$DAISY|[$$dev.port$$]|]]>
</script>

<script name="initgsm">
<![CDATA[$ABORT|ERROR|$ENDLINE|\r|$TIMEOUT|10||AT|OK||$TIMEOUT|20|$REPORT|M106#Configuring modem||ATV1&D0|OK|ATE0S0=0|OK|AT+CMEE=0|OK|AT+WIND=0|OK]]>
</script>

<script name="setpin">
<![CDATA[$ABORT|ERROR|$ENDLINE|\r|$TIMEOUT|10||AT|OK||$REPORT|M107#Checking SIM card|$ABORT|ERROR:READY||AT+CPIN?|+CPIN\:||SIM PIN||OK-AT-OK||$TIMEOUT|30|$REPORT|M108#Entering PIN|$ABORT|||\pAT+CPIN="[$$cell.pin$$]"|OK:ERROR||$ABORT|#---#:READY||AT+CPIN?|+CPIN\:||SIM||$REPORT|E101#Wrong PIN|]]>
</script>

<script name="setgprs">
<![CDATA[$ABORT||$TIMEOUT|10|$REPORT|M101#Registering||\p+++\p\pATH|OK:ERROR|AT+CREG=0|OK|AT+CGREG=0|OK|AT+COPS=3,0|OK|]]>
</script>

<script name="setppp">
<![CDATA[$ABORT||$TIMEOUT|20||AT+CREG?|+CREG\:||[$$cell.roam$$]||OK|AT+CSQ|+CSQ\:||$9,||OK|AT+COPS?|+COPS\:||,"||[$$cell.op.name$$]"||OK|AT+CGDCONT=1,"IP","[$$cell.gprs.apn$$]"|OK||$ABORT|NO CARRIER:BUSY:NO ANSWER:ERROR|$REPORT|M102#Dialing||ATD[$$cell.gprs.dial$$]|$TIMEOUT|400|CONNECT||]]>
</script>

<script name="setgsm">
<![CDATA[$ABORT||$TIMEOUT|10|$REPORT|M101#Registering||\p+++\p\pATH|OK:ERROR|ATGH|OK:ERROR|AT+CREG=0|OK|AT+COPS=3,0|OK|AT+CSQ|+CSQ\:||$9,||OK|AT+COPS?|+COPS\:||,"||[$$cell.op.name$$]"||OK|]]>
</script>

<script name="setgsmm">
<![CDATA[$ABORT||$TIMEOUT|10||AT+CREG?|+CREG\:||[$$cell.roam$$]||OK|AT+CSQ|+CSQ\:||$9,||OK|AT+COPS?|+COPS\:||,"||[$$cell.op.name$$]"||OK|AT+CBST=[$$cell.csd.cbst$$]|OK:ERROR||$ABORT|NO CARRIER:BUSY:NO ANSWER:ERROR|$REPORT|M102#Dialing||ATD[$$cell.csd.dial$$]|$TIMEOUT|400|CONNECT||]]>
</script>

<script name="setgsms">
<![CDATA[$ABORT|CONNECT:NO CARRIER|$TIMEOUT|10||AT+CREG?|+CREG\:||[$$cell.roam$$]||OK|AT+CSQ|+CSQ\:||$9,||OK|AT+COPS?|+COPS\:||,"||[$$cell.op.name$$]"||OK|ATS0=2|OK|AT+CBST=[$$cell.csd.cbst$$]|OK:ERROR||$TIMEOUT|3000|$REPORT|M103#Awaiting call|RING|ATA|$TIMEOUT|200|CONNECT||]]>
</script>

<script name="hangup">
<![CDATA[$ABORT||$TIMEOUT|20||\p+++\p\p|OK-+++AT\p\p-OK-ATH-OK:ERROR|ATH|OK:ERROR|ATS0=0|OK|]]>
</script>

<script name="touhf">
<![CDATA[$ABORT||$TIMEOUT|20|$DAISY|OFF|$REPORT|M106#Configuring modem||dm\r\n\p%%|RE002%%|%%set,/par[$$dev.port$$]/rate,[$$radio.rate$$]|RE|%%set,/par[$$dev.port$$]/rtscts,off|RE||$ABORT|%1%||%[$$cell.offmode$$]%|RE||%0%:%%||$ABORT||$DAISY|[$$dev.port$$]|$TIMEOUT|15||++++\p|@00-++++-@01|ATI|Topcon||@00|LINK RFSW 0|@00|\p\pDATAMODE|$WAIT|10|$DAISY|OFF]]>
</script>

<script name="rungsm">
<![CDATA[$TIMEOUT|[$$cell.csd.idle$$]|$ABORT|NO CARRIER:ERROR:RING]]>
</script>

<script name="runppp">
<![CDATA[[$$dev.port$$]|[$$cell.rate$$]|[$$ppp.ip$$]|novj|novjccomp|lcp-echo-interval:15|lcp-echo-failure:3|lcp-restart:5|ipcp-accept-local|ipcp-accept-remote|ipcp-max-failure:3|ipcp-max-configure:10|usepeerdns|noipdefault|noproxyarp|idle:[$$ppp.idle$$]|name:[$$ppp.name$$]|password:[$$ppp.password$$]]]>
</script>

<script name="error">
<![CDATA[$ABORT||$WAIT|10|]]>
</script>

</scripts-list>

<vars-list>
<var name="dev.port" type="enum" default="3">
<ui>Port</ui>
<description>Name of hardware serial port that is connected to modem</description>
<enum_list>
	<enum index="1">
		<value>/dev/ser/a</value>
	</enum>
	<enum index="2">
		<value>/dev/ser/b</value>
	</enum>
	<enum index="3">
		<value>/dev/ser/c</value>
	</enum>
	<enum index="4">
		<value>/dev/ser/d</value>
	</enum>
</enum_list>
</var>

<var name="radio.rate" type="enum" default="6">
<ui>Baud Rate</ui>
<description>Baud rate of modem serial interface</description>
<enum_list>
	<enum index="1">
		<value>1200</value>
	</enum>
	<enum index="2">
		<value>2400</value>
	</enum>
	<enum index="3">
		<value>4800</value>
	</enum>
	<enum index="4">
		<value>9600</value>
	</enum>
	<enum index="5">
		<value>19200</value>
	</enum>
	<enum index="6">
		<value>38400</value>
	</enum>
	<enum index="7">
		<value>57600</value>
	</enum>
	<enum index="8">
		<value>115200</value>
	</enum>
</enum_list>
</var>

<var name="cell.rate" type="enum" default="6">
<ui>Baud Rate</ui>
<description>Baud rate of cellular module</description>
<enum_list>
	<enum index="1">
		<value>1200</value>
	</enum>
	<enum index="2">
		<value>2400</value>
	</enum>
	<enum index="3">
		<value>4800</value>
	</enum>
	<enum index="4">
		<value>9600</value>
	</enum>
	<enum index="5">
		<value>19200</value>
	</enum>
	<enum index="6">
		<value>38400</value>
	</enum>
	<enum index="7">
		<value>57600</value>
	</enum>
	<enum index="8">
		<value>115200</value>
	</enum>
</enum_list>
</var>

<var name="cell.pin" type="string" default="0000">
<ui>PIN Code</ui>
<description>SIM PIN code</description>
<uvar>0</uvar>
</var>

<var name="cell.gprs.dial" type="string" default="*99***1#">
<ui>GPRS Dial</ui>
<description>GPRS Dial Number</description>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="cell.gprs.apn" type="string" default="">
<ui>APN</ui>
<description>GPRS APN</description>
<uvar>1</uvar>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="ppp.name" type="string" default="">
<ui>User</ui>
<description>GPRS User Name</description>
<uvar>2</uvar>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="ppp.password" type="string" default="">
<ui>Password</ui>
<description>GPRS Password</description>
<uvar>3</uvar>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="ppp.ip" type="string" default="">
<ui>IP address</ui>
<description>Static PPP address</description>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="ppp.idle" type="numeric" default="0">
<ui>Timeout</ui>
<description>GPRS Reconnection Timeout if datalink is lost</description>
<range min="0" max="9999">
<uifactor>0.1</uifactor>
</range>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="cell.roam" type="enum" default="1">
<ui>Roaming</ui>
<description>Allow network roaming</description>
<profiles>
	<name>internet</name>
	<name>c-master</name>
	<name>c-slave</name>
</profiles>
<enum_list>
	<enum index="1">
		<value>,1:,5</value>
		<ui>Enabled</ui>
	</enum>
	<enum index="2">
		<value>,1</value>
		<ui>Disabled</ui>
	</enum>
</enum_list>
</var>

<var name="cell.csd.cbst" type="enum" default="1">
<ui>Data Call Type</ui>
<description>Bearer type for outgoing and incoming data calls</description>
<uvar>6</uvar>
<profiles>
	<name>c-master</name>
	<name>c-slave</name>
</profiles>
<enum_list>
	<enum index="1">
		<value>0</value>
		<ui>Automatic</ui>
	</enum>
	<enum index="2">
		<value>7</value>
		<ui>Analog V.32</ui>
	</enum>
	<enum index="3">
		<value>71</value>
		<ui>Digital V.110</ui>
	</enum>
</enum_list>
</var>

<var name="cell.csd.dial" type="string" default="">
<ui>Dial Number</ui>
<description>CSD Base Phone Number</description>
<uvar>5</uvar>
<profiles>
	<name>c-master</name>
</profiles>
</var>

<var name="cell.csd.idle" type="numeric" default="300">
<ui>CSD Timeout</ui>
<description>Hangup CSD if no data is received within timeout threshold</description>
<range min="0" max="9999">
<uifactor>0.1</uifactor>
</range>
<profiles>
	<name>c-master</name>
	<name>c-slave</name>
</profiles>
</var>

<var name="cell.op.name" type="string" default="">
<ui>Cellular Operator Name</ui>
<description>Operator Name (read only)</description>
<uvar>7</uvar>
</var>

<var name="cell.offmode" type="string" default="0">
<ui>Keep Cellular Powered</ui>
<description>Flag to Keep cellular module powered when turning profile off</description>
<uvar>8</uvar>
</var>

<var name="cell.sq" type="string" default="">
<ui>Cellular Signal Quality</ui>
<description>Signal Quality (read only)</description>
<uvar>9</uvar>
</var>

</vars-list>
</template>

<template name="ArWest|AW401;Motorola|G24">
<id>[$$dev.port$$];ArWest|AW401@[$$radio.rate$$];Motorola|G24@[$$cell.rate$$]</id>
<version>1.3</version>
<description>Digital UHF modem with Motorola G20/G24 GSM module</description>
<compat-version>1</compat-version>

<profiles-list>
<profile name="internet">
	<description>Connect to Internet using GPRS by cellular modem</description>
	<block id="1" type="script" script="checkgsm">
		<branch from="0" to="0" id="3"></branch>

		<branch from="1" to="1" id="9"></branch>

		<branch from="2" to="15" id="2">
			<try times="1" id="1"></try></branch>
	</block>
	<block id="2" type="script" script="togsm">
		<branch from="0" to="0" id="3"></branch>

		<branch from="1" to="1" id="9"></branch>

		<branch from="2" to="15" id="2"></branch>
	</block>
	<block id="3" type="script" script="initgsm">
		<branch from="0" to="0" id="4"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="2">
			<try times="30" id="3"></try></branch>
	</block>
	<block id="4" type="script" script="setpin">
		<branch from="0" to="0" id="10"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="2" id="1">
			<try times="2" id="4"></try></branch>
		<branch from="3" to="3" id="3">
			<try times="10" id="4"></try></branch>
		<branch from="4" to="15" id="5"></branch>
	</block>
	<block id="5" type="script" script="setgprs">
		<branch from="0" to="0" id="6"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="3">
			<try times="10" id="5"></try></branch>
	</block>
	<block id="6" type="script" script="setppp">
		<branch from="0" to="0" id="7"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="5">
			<try times="30" id="6"></try></branch>
	</block>
	<block id="7" type="ppp" script="runppp">
		<branch from="0" to="0" id="6"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="6"></branch>
	</block>
	<block id="8" type="script" script="hangup">
		<branch from="0" to="1" id="9"></branch>

		<branch from="2" to="2" id="9">
			<try times="5" id="8"></try></branch>
		<branch from="3" to="15" id="9"></branch>
	</block>
	<block id="9" type="script" script="touhf">
		<branch from="0" to="0" id="0"></branch>
		<branch from="2" to="2" id="0">
			<try times="5" id="9"></try></branch>
		<branch from="3" to="3" id="0"></branch>
		<branch from="4" to="15" id="0">
			<try times="5" id="9"></try></branch>
	</block>
	<block id="10" type="script" script="error">
		<branch from="0" to="0" id="10"></branch>

		<branch from="1" to="15" id="8"></branch>
	</block>
</profile>

<profile name="c-master">
	<description>Start outgoing cellular data connection</description>
	<block id="1" type="script" script="checkgsm">
		<branch from="0" to="0" id="3"></branch>

		<branch from="1" to="1" id="9"></branch>

		<branch from="2" to="15" id="2">
			<try times="1" id="1"></try></branch>
	</block>
	<block id="2" type="script" script="togsm">
		<branch from="0" to="0" id="3"></branch>

		<branch from="1" to="1" id="9"></branch>

		<branch from="2" to="15" id="2"></branch>
	</block>
	<block id="3" type="script" script="initgsm">
		<branch from="0" to="0" id="4"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="2">
			<try times="30" id="3"></try></branch>
	</block>
	<block id="4" type="script" script="setpin">
		<branch from="0" to="0" id="10"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="2" id="1">
			<try times="2" id="4"></try></branch>
		<branch from="3" to="3" id="3">
			<try times="10" id="4"></try></branch>
		<branch from="4" to="15" id="5"></branch>
	</block>
	<block id="5" type="script" script="setgsm">
		<branch from="0" to="0" id="6"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="3">
			<try times="10" id="5"></try></branch>
	</block>
	<block id="6" type="script" script="setgsmm">
		<branch from="0" to="0" id="7"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="5">
			<try times="30" id="6"></try></branch>
	</block>
	<block id="7" type="direct" script="rungsm">
		<branch from="0" to="0" id="6"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="5"></branch>
	</block>
	<block id="8" type="script" script="hangup">
		<branch from="0" to="1" id="9"></branch>

		<branch from="2" to="2" id="9">
			<try times="5" id="8"></try></branch>
		<branch from="3" to="15" id="9"></branch>
	</block>
	<block id="9" type="script" script="touhf">
		<branch from="0" to="0" id="0"></branch>

		<branch from="2" to="15" id="0">
			<try times="5" id="9"></try></branch>
	</block>
	<block id="10" type="script" script="error">
		<branch from="0" to="0" id="10"></branch>

		<branch from="1" to="15" id="8"></branch>
	</block>
</profile>

<profile name="c-slave">
	<description>Wait for incoming cellular data call</description>
	<block id="1" type="script" script="checkgsm">
		<branch from="0" to="0" id="3"></branch>

		<branch from="1" to="1" id="9"></branch>

		<branch from="2" to="15" id="2">
			<try times="1" id="1"></try></branch>
	</block>
	<block id="2" type="script" script="togsm">
		<branch from="0" to="0" id="3"></branch>

		<branch from="1" to="1" id="9"></branch>

		<branch from="2" to="15" id="2"></branch>
	</block>
	<block id="3" type="script" script="initgsm">
		<branch from="0" to="0" id="4"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="2">
			<try times="30" id="3"></try></branch>
	</block>
	<block id="4" type="script" script="setpin">
		<branch from="0" to="0" id="10"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="2" id="1">
			<try times="2" id="4"></try></branch>
		<branch from="3" to="3" id="3">
			<try times="10" id="4"></try></branch>
		<branch from="4" to="15" id="5"></branch>
	</block>
	<block id="5" type="script" script="setgsm">
		<branch from="0" to="0" id="6"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="3">
			<try times="10" id="5"></try></branch>
	</block>
	<block id="6" type="script" script="setgsms">
		<branch from="0" to="0" id="7"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="2" id="5">
			<try times="30" id="6"></try></branch>
		<branch from="3" to="3" id="7"></branch>

		<branch from="4" to="15" id="5">
			<try times="3" id="6"></try></branch>
	</block>
	<block id="7" type="direct" script="rungsm">
		<branch from="0" to="0" id="6"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="5"></branch>
	</block>
	<block id="8" type="script" script="hangup">
		<branch from="0" to="1" id="9"></branch>

		<branch from="2" to="2" id="9">
			<try times="5" id="8"></try></branch>
		<branch from="3" to="15" id="9"></branch>
	</block>
	<block id="9" type="script" script="touhf">
		<branch from="0" to="0" id="0"></branch>

		<branch from="2" to="15" id="0">
			<try times="5" id="9"></try></branch>
	</block>
	<block id="10" type="script" script="error">
		<branch from="0" to="0" id="10"></branch>

		<branch from="1" to="15" id="8"></branch>
	</block>
</profile>

</profiles-list>

<scripts-list>
<script name="checkgsm">
<![CDATA[$ABORT||$ENDLINE|\r|$TIMEOUT|15|$REPORT|M105#Looking for modem|$DAISY|OFF||dm\r\n\p%%|RE002%%|%%dm,[$$dev.port$$]|RE|%%set,/par[$$dev.port$$]/rate,[$$cell.rate$$]|RE|%%set,/par[$$dev.port$$]/rtscts,off|RE|%%set,/par[$$dev.port$$]/rts,on|RE||$DAISY|[$$dev.port$$]|$TIMEOUT|10||AT|OK-AT-OK-AT-OK]]>
</script>

<script name="togsm">
<![CDATA[$ABORT||$ENDLINE|\r|$TIMEOUT|15|$DAISY|OFF||dm\r\n\p%%|RE002%%|%%dm,[$$dev.port$$]|RE||$REPORT|M106#Configuring modem||%%set,/par[$$dev.port$$]/rate,[$$radio.rate$$]|RE|%%set,/par[$$dev.port$$]/rtscts,off|RE||$DAISY|[$$dev.port$$]|$TIMEOUT|15||++++\p|@00-++++-@01|ATI|Topcon||@00|\p\pLINK RFSW 1|@00|\p\pDATAMODE|$WAIT|15|$DAISY|OFF||dm\r\n\p%%|RE002%%|%%set,/par[$$dev.port$$]/rate,[$$cell.rate$$]|RE|%%set,/par[$$dev.port$$]/rtscts,off|RE|%%set,/par[$$dev.port$$]/rts,on|RE||$DAISY|[$$dev.port$$]|]]>
</script>

<script name="initgsm">
<![CDATA[$ABORT|ERROR|$ENDLINE|\r|$TIMEOUT|10||AT|OK||$TIMEOUT|20|$REPORT|M106#Configuring modem||ATV1&D0|OK|ATE0S0=0|OK|AT+CMEE=0|OK]]>
</script>

<script name="setpin">
<![CDATA[$ABORT|ERROR|$ENDLINE|\r|$TIMEOUT|10||AT|OK||$REPORT|M107#Checking SIM card|$ABORT|ERROR:READY||AT+CPIN?|+CPIN\:||SIM PIN||OK-AT-OK||$TIMEOUT|30|$REPORT|M108#Entering PIN|$ABORT|||\pAT+CPIN="[$$cell.pin$$]"|OK:ERROR||$ABORT|#---#:READY||AT+CPIN?|+CPIN\:||SIM||$REPORT|E101#Wrong PIN|]]>
</script>

<script name="setgprs">
<![CDATA[$ABORT||$TIMEOUT|10|$REPORT|M101#Registering||\p+++\p\pATH|OK:ERROR|AT+CREG=0|OK|AT+CGREG=0|OK|AT+COPS=3,0|OK|AT+CGATT?|+CGATT\:||1-AT+CGATT=0]]>
</script>

<script name="setppp">
<![CDATA[$ABORT||$TIMEOUT|10||AT+CREG?|+CREG\:||[$$cell.roam$$]||OK|AT+CGATT?|+CGATT\: 1-AT+CGATT=1-OK|AT+CGREG?|+CGREG\:||[$$cell.roam$$]||OK|AT+CSQ|+CSQ\:||$9,||OK|AT+COPS?|+COPS\:||,"||[$$cell.op.name$$]"||OK|AT+CGDCONT=1,"IP","[$$cell.gprs.apn$$]"|OK||$ABORT|NO CARRIER:BUSY:NO ANSWER:ERROR|$REPORT|M102#Dialing||ATD[$$cell.gprs.dial$$]|$TIMEOUT|400|CONNECT||]]>
</script>

<script name="setgsm">
<![CDATA[$ABORT||$TIMEOUT|10|$REPORT|M101#Registering||\p+++\p\pATH|OK:ERROR|AT+CREG=0|OK|AT+COPS=3,0|OK|AT+CSQ|+CSQ\:||$9,||OK|AT+COPS?|+COPS\:||,"||[$$cell.op.name$$]"||OK|]]>
</script>

<script name="setgsmm">
<![CDATA[$ABORT||$TIMEOUT|10||AT+CREG?|+CREG\:||[$$cell.roam$$]||OK|AT+CSQ|+CSQ\:||$9,||OK|AT+COPS?|+COPS\:||,"||[$$cell.op.name$$]"||OK|AT+CBST=[$$cell.csd.cbst$$]|OK:ERROR||$ABORT|NO CARRIER:BUSY:NO ANSWER:ERROR|$REPORT|M102#Dialing||ATD[$$cell.csd.dial$$]|$TIMEOUT|400|CONNECT||]]>
</script>

<script name="setgsms">
<![CDATA[$ABORT|CONNECT:NO CARRIER|$TIMEOUT|10||AT+CREG?|+CREG\:||[$$cell.roam$$]||OK|AT+CSQ|+CSQ\:||$9,||OK|AT+COPS?|+COPS\:||,"||[$$cell.op.name$$]"||OK|ATS0=2|OK|AT+CBST=[$$cell.csd.cbst$$]|OK:ERROR||$TIMEOUT|3000|$REPORT|M103#Awaiting call|RING|ATA|$TIMEOUT|200|CONNECT||]]>
</script>

<script name="hangup">
<![CDATA[$ABORT||$TIMEOUT|20||\p+++\p\p|OK-+++AT\p\p-OK-ATH-OK:ERROR|ATH|OK:ERROR|ATS0=0|OK|]]>
</script>

<script name="touhf">
<![CDATA[$ABORT||$TIMEOUT|20|$DAISY|OFF|$REPORT|M106#Configuring modem||dm\r\n\p%%|RE002%%|%%set,/par[$$dev.port$$]/rate,[$$radio.rate$$]|RE|%%set,/par[$$dev.port$$]/rtscts,off|RE||$ABORT|%1%||%[$$cell.offmode$$]%|RE||%0%:%%||$ABORT||$DAISY|[$$dev.port$$]|$TIMEOUT|15||++++\p|@00-++++-@01|ATI|Topcon||@00|LINK RFSW 0|@00|\p\pDATAMODE|$WAIT|10|$DAISY|OFF]]>
</script>

<script name="rungsm">
<![CDATA[$TIMEOUT|[$$cell.csd.idle$$]|$ABORT|NO CARRIER:ERROR:RING]]>
</script>

<script name="runppp">
<![CDATA[[$$dev.port$$]|[$$cell.rate$$]|[$$ppp.ip$$]|novj|novjccomp|lcp-echo-interval:15|lcp-echo-failure:3|lcp-restart:5|ipcp-accept-local|ipcp-accept-remote|ipcp-max-failure:3|ipcp-max-configure:10|usepeerdns|noipdefault|noproxyarp|idle:[$$ppp.idle$$]|name:[$$ppp.name$$]|password:[$$ppp.password$$]]]>
</script>

<script name="error">
<![CDATA[$ABORT||$WAIT|10|]]>
</script>

</scripts-list>

<vars-list>
<var name="dev.port" type="enum" default="3">
<ui>Port</ui>
<description>Name of hardware serial port that is connected to modem</description>
<enum_list>
	<enum index="1">
		<value>/dev/ser/a</value>
	</enum>
	<enum index="2">
		<value>/dev/ser/b</value>
	</enum>
	<enum index="3">
		<value>/dev/ser/c</value>
	</enum>
	<enum index="4">
		<value>/dev/ser/d</value>
	</enum>
</enum_list>
</var>

<var name="radio.rate" type="enum" default="6">
<ui>Baud Rate</ui>
<description>Baud rate of modem serial interface</description>
<enum_list>
	<enum index="1">
		<value>1200</value>
	</enum>
	<enum index="2">
		<value>2400</value>
	</enum>
	<enum index="3">
		<value>4800</value>
	</enum>
	<enum index="4">
		<value>9600</value>
	</enum>
	<enum index="5">
		<value>19200</value>
	</enum>
	<enum index="6">
		<value>38400</value>
	</enum>
	<enum index="7">
		<value>57600</value>
	</enum>
	<enum index="8">
		<value>115200</value>
	</enum>
</enum_list>
</var>

<var name="cell.rate" type="enum" default="6">
<ui>Baud Rate</ui>
<description>Baud rate of cellular module</description>
<enum_list>
	<enum index="1">
		<value>1200</value>
	</enum>
	<enum index="2">
		<value>2400</value>
	</enum>
	<enum index="3">
		<value>4800</value>
	</enum>
	<enum index="4">
		<value>9600</value>
	</enum>
	<enum index="5">
		<value>19200</value>
	</enum>
	<enum index="6">
		<value>38400</value>
	</enum>
	<enum index="7">
		<value>57600</value>
	</enum>
	<enum index="8">
		<value>115200</value>
	</enum>
</enum_list>
</var>

<var name="cell.pin" type="string" default="0000">
<ui>PIN Code</ui>
<description>SIM PIN code</description>
<uvar>0</uvar>
</var>

<var name="cell.gprs.dial" type="string" default="*99***1#">
<ui>GPRS Dial</ui>
<description>GPRS Dial Number</description>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="cell.gprs.apn" type="string" default="">
<ui>APN</ui>
<description>GPRS APN</description>
<uvar>1</uvar>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="ppp.name" type="string" default="">
<ui>User</ui>
<description>GPRS User Name</description>
<uvar>2</uvar>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="ppp.password" type="string" default="">
<ui>Password</ui>
<description>GPRS Password</description>
<uvar>3</uvar>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="ppp.ip" type="string" default="">
<ui>IP address</ui>
<description>Static PPP address</description>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="ppp.idle" type="numeric" default="0">
<ui>Timeout</ui>
<description>GPRS Reconnection Timeout if datalink is lost</description>
<range min="0" max="9999">
<uifactor>0.1</uifactor>
</range>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="cell.roam" type="enum" default="1">
<ui>Roaming</ui>
<description>Allow network roaming</description>
<profiles>
	<name>internet</name>
	<name>c-master</name>
	<name>c-slave</name>
</profiles>
<enum_list>
	<enum index="1">
		<value>,001:,005</value>
		<ui>Enabled</ui>
	</enum>
	<enum index="2">
		<value>,001</value>
		<ui>Disabled</ui>
	</enum>
</enum_list>
</var>

<var name="cell.csd.cbst" type="enum" default="1">
<ui>Data Call Type</ui>
<description>Bearer type for outgoing and incoming data calls</description>
<uvar>6</uvar>
<profiles>
	<name>c-master</name>
	<name>c-slave</name>
</profiles>
<enum_list>
	<enum index="1">
		<value>0</value>
		<ui>Automatic</ui>
	</enum>
	<enum index="2">
		<value>7</value>
		<ui>Analog V.32</ui>
	</enum>
	<enum index="3">
		<value>71</value>
		<ui>Digital V.110</ui>
	</enum>
</enum_list>
</var>

<var name="cell.csd.dial" type="string" default="">
<ui>Dial Number</ui>
<description>CSD Base Phone Number</description>
<uvar>5</uvar>
<profiles>
	<name>c-master</name>
</profiles>
</var>

<var name="cell.csd.idle" type="numeric" default="300">
<ui>CSD Timeout</ui>
<description>Hangup CSD if no data is received within timeout threshold</description>
<range min="0" max="9999">
<uifactor>0.1</uifactor>
</range>
<profiles>
	<name>c-master</name>
	<name>c-slave</name>
</profiles>
</var>

<var name="cell.op.name" type="string" default="">
<ui>Cellular Operator Name</ui>
<description>Operator Name (read only)</description>
<uvar>7</uvar>
</var>

<var name="cell.offmode" type="string" default="0">
<ui>Keep Cellular Powered</ui>
<description>Flag to Keep cellular module powered when turning profile off</description>
<uvar>8</uvar>
</var>

<var name="cell.sq" type="string" default="">
<ui>Cellular Signal Quality</ui>
<description>Signal Quality (read only)</description>
<uvar>9</uvar>
</var>

</vars-list>
</template>

<template name="Satel|SATELLINE-3AS;Motorola|G24">
<id>[$$dev.port$$];Satel|SATELLINE-3AS@[$$radio.rate$$];Motorola|G24@[$$cell.rate$$]</id>
<version>1.4</version>
<description>Satel UHF modem with Motorola G24 GSM/GPRS module</description>
<compat-version>1</compat-version>

<profiles-list>
<profile name="internet">
	<description>Connect to Internet using GPRS by cellular modem</description>
	<block id="1" type="script" script="checkgsm">
		<branch from="0" to="0" id="3"></branch>

		<branch from="1" to="1" id="9"></branch>

		<branch from="2" to="15" id="2">
			<try times="1" id="1"></try></branch>
	</block>
	<block id="2" type="script" script="togsm">
		<branch from="0" to="0" id="3"></branch>

		<branch from="1" to="1" id="9"></branch>

		<branch from="2" to="15" id="2"></branch>
	</block>
	<block id="3" type="script" script="initgsm">
		<branch from="0" to="0" id="4"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="2">
			<try times="30" id="3"></try></branch>
	</block>
	<block id="4" type="script" script="setpin">
		<branch from="0" to="0" id="10"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="2" id="1">
			<try times="2" id="4"></try></branch>
		<branch from="3" to="3" id="3">
			<try times="10" id="4"></try></branch>
		<branch from="4" to="15" id="5"></branch>
	</block>
	<block id="5" type="script" script="setgprs">
		<branch from="0" to="0" id="6"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="3">
			<try times="10" id="5"></try></branch>
	</block>
	<block id="6" type="script" script="setppp">
		<branch from="0" to="0" id="7"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="5">
			<try times="30" id="6"></try></branch>
	</block>
	<block id="7" type="ppp" script="runppp">
		<branch from="0" to="0" id="6"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="6"></branch>
	</block>
	<block id="8" type="script" script="hangup">
		<branch from="0" to="1" id="9"></branch>

		<branch from="2" to="2" id="9">
			<try times="5" id="8"></try></branch>
		<branch from="3" to="15" id="9"></branch>
	</block>
	<block id="9" type="script" script="touhf">
		<branch from="0" to="0" id="0"></branch>
		<branch from="2" to="2" id="0">
			<try times="5" id="9"></try></branch>
		<branch from="3" to="3" id="0"></branch>
		<branch from="4" to="15" id="0">
			<try times="5" id="9"></try></branch>
	</block>
	<block id="10" type="script" script="error">
		<branch from="0" to="0" id="10"></branch>

		<branch from="1" to="15" id="8"></branch>
	</block>
</profile>

<profile name="c-master">
	<description>Start outgoing cellular data connection</description>
	<block id="1" type="script" script="checkgsm">
		<branch from="0" to="0" id="3"></branch>

		<branch from="1" to="1" id="9"></branch>

		<branch from="2" to="15" id="2">
			<try times="1" id="1"></try></branch>
	</block>
	<block id="2" type="script" script="togsm">
		<branch from="0" to="0" id="3"></branch>

		<branch from="1" to="1" id="9"></branch>

		<branch from="2" to="15" id="2"></branch>
	</block>
	<block id="3" type="script" script="initgsm">
		<branch from="0" to="0" id="4"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="2">
			<try times="30" id="3"></try></branch>
	</block>
	<block id="4" type="script" script="setpin">
		<branch from="0" to="0" id="10"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="2" id="1">
			<try times="2" id="4"></try></branch>
		<branch from="3" to="3" id="3">
			<try times="10" id="4"></try></branch>
		<branch from="4" to="15" id="5"></branch>
	</block>
	<block id="5" type="script" script="setgsm">
		<branch from="0" to="0" id="6"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="3">
			<try times="10" id="5"></try></branch>
	</block>
	<block id="6" type="script" script="setgsmm">
		<branch from="0" to="0" id="7"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="5">
			<try times="30" id="6"></try></branch>
	</block>
	<block id="7" type="direct" script="rungsm">
		<branch from="0" to="0" id="6"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="5"></branch>
	</block>
	<block id="8" type="script" script="hangup">
		<branch from="0" to="1" id="9"></branch>

		<branch from="2" to="2" id="9">
			<try times="5" id="8"></try></branch>
		<branch from="3" to="15" id="9"></branch>
	</block>
	<block id="9" type="script" script="touhf">
		<branch from="0" to="0" id="0"></branch>

		<branch from="2" to="15" id="0">
			<try times="5" id="9"></try></branch>
	</block>
	<block id="10" type="script" script="error">
		<branch from="0" to="0" id="10"></branch>

		<branch from="1" to="15" id="8"></branch>
	</block>
</profile>

<profile name="c-slave">
	<description>Wait for incoming cellular data call</description>
	<block id="1" type="script" script="checkgsm">
		<branch from="0" to="0" id="3"></branch>

		<branch from="1" to="1" id="9"></branch>

		<branch from="2" to="15" id="2">
			<try times="1" id="1"></try></branch>
	</block>
	<block id="2" type="script" script="togsm">
		<branch from="0" to="0" id="3"></branch>

		<branch from="1" to="1" id="9"></branch>

		<branch from="2" to="15" id="2"></branch>
	</block>
	<block id="3" type="script" script="initgsm">
		<branch from="0" to="0" id="4"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="2">
			<try times="30" id="3"></try></branch>
	</block>
	<block id="4" type="script" script="setpin">
		<branch from="0" to="0" id="10"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="2" id="1">
			<try times="2" id="4"></try></branch>
		<branch from="3" to="3" id="3">
			<try times="10" id="4"></try></branch>
		<branch from="4" to="15" id="5"></branch>
	</block>
	<block id="5" type="script" script="setgsm">
		<branch from="0" to="0" id="6"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="3">
			<try times="10" id="5"></try></branch>
	</block>
	<block id="6" type="script" script="setgsms">
		<branch from="0" to="0" id="7"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="2" id="5">
			<try times="30" id="6"></try></branch>
		<branch from="3" to="3" id="7"></branch>

		<branch from="4" to="15" id="5">
			<try times="3" id="6"></try></branch>
	</block>
	<block id="7" type="direct" script="rungsm">
		<branch from="0" to="0" id="6"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="5"></branch>
	</block>
	<block id="8" type="script" script="hangup">
		<branch from="0" to="1" id="9"></branch>

		<branch from="2" to="2" id="9">
			<try times="5" id="8"></try></branch>
		<branch from="3" to="15" id="9"></branch>
	</block>
	<block id="9" type="script" script="touhf">
		<branch from="0" to="0" id="0"></branch>

		<branch from="2" to="15" id="0">
			<try times="5" id="9"></try></branch>
	</block>
	<block id="10" type="script" script="error">
		<branch from="0" to="0" id="10"></branch>

		<branch from="1" to="15" id="8"></branch>
	</block>
</profile>

</profiles-list>

<scripts-list>
<script name="checkgsm">
<![CDATA[$ABORT||$ENDLINE|\r|$TIMEOUT|15|$REPORT|M105#Looking for modem|$DAISY|OFF||dm\r\n\p%%|RE002%%|%%dm,[$$dev.port$$]|RE|%%set,/par[$$dev.port$$]/rate,[$$cell.rate$$]|RE||$DAISY|[$$dev.port$$]|$TIMEOUT|5||AT|OK-AT-OK]]>
</script>

<script name="togsm">
<![CDATA[$ABORT||$ENDLINE|\r|$TIMEOUT|15|$DAISY|OFF||dm\r\n\p%%|RE002%%|%%dm,[$$dev.port$$]|RE||$REPORT|M106#Configuring modem||%%set,/par[$$dev.port$$]/rtscts,off|RE|%%set,/par[$$dev.port$$]/rate,[$$radio.rate$$]|RE||$DAISY|[$$dev.port$$]|$TIMEOUT|15||SL+++|OK-SL+++-OK-SL+++-OK-SL+++-OK-SL!V?-3AS-+++\p\pSL@G=0-OK|\pSL@G=1\p||SL@G=1|$WAIT|10|$DAISY|OFF||dm\r\n\p%%|RE002%%|%%set,/par[$$dev.port$$]/rate,[$$cell.rate$$]|RE|%%set,/par[$$dev.port$$]/rtscts,on|RE||$DAISY|[$$dev.port$$]|]]>
</script>

<script name="initgsm">
<![CDATA[$ABORT|ERROR|$ENDLINE|\r|$TIMEOUT|10||AT|OK||$TIMEOUT|20|$REPORT|M106#Configuring modem||ATV1&D0|OK|ATE0S0=0|OK|AT+CMEE=0|OK]]>
</script>

<script name="setpin">
<![CDATA[$ABORT|ERROR|$ENDLINE|\r|$TIMEOUT|10||AT|OK||$REPORT|M107#Checking SIM card|$ABORT|ERROR:READY||AT+CPIN?|+CPIN\:||SIM PIN||OK-AT-OK||$TIMEOUT|30|$REPORT|M108#Entering PIN|$ABORT|||\pAT+CPIN="[$$cell.pin$$]"|OK:ERROR||$ABORT|#---#:READY||AT+CPIN?|+CPIN\:||SIM||$REPORT|E101#Wrong PIN|]]>
</script>

<script name="setgprs">
<![CDATA[$ABORT||$TIMEOUT|10|$REPORT|M101#Registering||\p+++\p\pATH|OK:ERROR|AT+CREG=0|OK|AT+CGREG=0|OK|AT+COPS=3,0|OK|AT+CGATT=0|OK]]>
</script>

<script name="setppp">
<![CDATA[$ABORT||$TIMEOUT|10||AT+CREG?|+CREG\:||[$$cell.roam$$]||OK|AT+CGATT?|+CGATT\: 1-AT+CGATT=1-OK|AT+CGREG?|+CGREG\:||[$$cell.roam$$]||OK|AT+CSQ|+CSQ\:||$9,||OK|AT+COPS?|+COPS\:||,"||[$$cell.op.name$$]"||OK|AT+CGDCONT=1,"IP","[$$cell.gprs.apn$$]"|OK||$ABORT|NO CARRIER:BUSY:NO ANSWER:ERROR|$REPORT|M102#Dialing||ATD[$$cell.gprs.dial$$]|$TIMEOUT|400|CONNECT||]]>
</script>

<script name="setgsm">
<![CDATA[$ABORT||$TIMEOUT|10|$REPORT|M101#Registering||\p+++\p\pATH|OK:ERROR|AT+CREG=0|OK|AT+COPS=3,0|OK|AT+CSQ|+CSQ\:||$9,||OK|AT+COPS?|+COPS\:||,"||[$$cell.op.name$$]"||OK|]]>
</script>

<script name="setgsmm">
<![CDATA[$ABORT||$TIMEOUT|10||AT+CREG?|+CREG\:||[$$cell.roam$$]||OK|AT+CSQ|+CSQ\:||$9,||OK|AT+COPS?|+COPS\:||,"||[$$cell.op.name$$]"||OK|AT+CBST=[$$cell.csd.cbst$$]|OK:ERROR||$ABORT|NO CARRIER:BUSY:NO ANSWER:ERROR|$REPORT|M102#Dialing||ATD[$$cell.csd.dial$$]|$TIMEOUT|400|CONNECT||]]>
</script>

<script name="setgsms">
<![CDATA[$ABORT|CONNECT:NO CARRIER|$TIMEOUT|10||AT+CREG?|+CREG\:||[$$cell.roam$$]||OK|AT+CSQ|+CSQ\:||$9,||OK|AT+COPS?|+COPS\:||,"||[$$cell.op.name$$]"||OK|ATS0=2|OK|AT+CBST=[$$cell.csd.cbst$$]|OK:ERROR||$TIMEOUT|3000|$REPORT|M103#Awaiting call|RING|ATA|$TIMEOUT|200|CONNECT||]]>
</script>

<script name="hangup">
<![CDATA[$ABORT||$TIMEOUT|20||\p+++\p\p|OK-+++AT\p\p-OK-ATH-OK:ERROR|ATH|OK:ERROR|ATS0=0|OK|]]>
</script>

<script name="touhf">
<![CDATA[$ABORT||$TIMEOUT|20|$DAISY|OFF|$REPORT|M106#Configuring modem||dm\r\n\p%%|RE002%%|%%set,/par[$$dev.port$$]/rate,[$$radio.rate$$]|RE|%%set,/par[$$dev.port$$]/rtscts,off|RE||$ABORT|%1%||%[$$cell.offmode$$]%|RE||%0%:%%||$ABORT||$DAISY|[$$dev.port$$]|$TIMEOUT|80||+++\p\pSL@G=0|OK||$TIMEOUT|10||AT+CGMI?|Satel-SL!V?-3AS|SL++O|OK-SL++O||$WAIT|10|$DAISY|OFF]]>
</script>

<script name="rungsm">
<![CDATA[$TIMEOUT|[$$cell.csd.idle$$]|$ABORT|NO CARRIER:ERROR:RING]]>
</script>

<script name="runppp">
<![CDATA[[$$dev.port$$]|[$$cell.rate$$]|[$$ppp.ip$$]|novj|novjccomp|lcp-echo-interval:15|lcp-echo-failure:3|lcp-restart:5|ipcp-accept-local|ipcp-accept-remote|ipcp-max-failure:3|ipcp-max-configure:10|usepeerdns|noipdefault|noproxyarp|idle:[$$ppp.idle$$]|name:[$$ppp.name$$]|password:[$$ppp.password$$]]]>
</script>

<script name="error">
<![CDATA[$ABORT||$WAIT|10|]]>
</script>

</scripts-list>

<vars-list>
<var name="dev.port" type="enum" default="3">
<ui>Port</ui>
<description>Name of hardware serial port that is connected to modem</description>
<enum_list>
	<enum index="1">
		<value>/dev/ser/a</value>
	</enum>
	<enum index="2">
		<value>/dev/ser/b</value>
	</enum>
	<enum index="3">
		<value>/dev/ser/c</value>
	</enum>
	<enum index="4">
		<value>/dev/ser/d</value>
	</enum>
</enum_list>
</var>

<var name="radio.rate" type="enum" default="6">
<ui>Baud Rate</ui>
<description>Baud rate of modem serial interface</description>
<enum_list>
	<enum index="1">
		<value>1200</value>
	</enum>
	<enum index="2">
		<value>2400</value>
	</enum>
	<enum index="3">
		<value>4800</value>
	</enum>
	<enum index="4">
		<value>9600</value>
	</enum>
	<enum index="5">
		<value>19200</value>
	</enum>
	<enum index="6">
		<value>38400</value>
	</enum>
	<enum index="7">
		<value>57600</value>
	</enum>
	<enum index="8">
		<value>115200</value>
	</enum>
</enum_list>
</var>

<var name="cell.rate" type="enum" default="6">
<ui>Baud Rate</ui>
<description>Baud rate of cellular module</description>
<enum_list>
	<enum index="1">
		<value>1200</value>
	</enum>
	<enum index="2">
		<value>2400</value>
	</enum>
	<enum index="3">
		<value>4800</value>
	</enum>
	<enum index="4">
		<value>9600</value>
	</enum>
	<enum index="5">
		<value>19200</value>
	</enum>
	<enum index="6">
		<value>38400</value>
	</enum>
	<enum index="7">
		<value>57600</value>
	</enum>
	<enum index="8">
		<value>115200</value>
	</enum>
</enum_list>
</var>

<var name="cell.pin" type="string" default="0000">
<ui>PIN Code</ui>
<description>SIM PIN code</description>
<uvar>0</uvar>
</var>

<var name="cell.gprs.dial" type="string" default="*99***1#">
<ui>GPRS Dial string</ui>
<description>GPRS Dial Number</description>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="cell.gprs.apn" type="string" default="">
<ui>APN</ui>
<description>GPRS APN</description>
<uvar>1</uvar>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="ppp.name" type="string" default="">
<ui>User</ui>
<description>GPRS User Name</description>
<uvar>2</uvar>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="ppp.password" type="string" default="">
<ui>Password</ui>
<description>GPRS Password</description>
<uvar>3</uvar>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="ppp.ip" type="string" default="">
<ui>IP address</ui>
<description>Static PPP address</description>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="ppp.idle" type="numeric" default="0">
<ui>Timeout</ui>
<description>GPRS Reconnection Timeout if datalink is lost</description>
<range min="0" max="9999">
<uifactor>0.1</uifactor>
</range>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="cell.roam" type="enum" default="1">
<ui>Roaming</ui>
<description>Allow network roaming</description>
<profiles>
	<name>internet</name>
	<name>c-master</name>
	<name>c-slave</name>
</profiles>
<enum_list>
	<enum index="1">
		<value>,001:,1:,005:,5</value>
		<ui>Enabled</ui>
	</enum>
	<enum index="2">
		<value>,001:,1</value>
		<ui>Disabled</ui>
	</enum>
</enum_list>
</var>

<var name="cell.csd.cbst" type="enum" default="1">
<ui>Data Call Type</ui>
<description>Bearer type for outgoing and incoming data calls</description>
<uvar>6</uvar>
<profiles>
	<name>c-master</name>
	<name>c-slave</name>
</profiles>
<enum_list>
	<enum index="1">
		<value>0</value>
		<ui>Automatic</ui>
	</enum>
	<enum index="2">
		<value>7</value>
		<ui>Analog V.32</ui>
	</enum>
	<enum index="3">
		<value>71</value>
		<ui>Digital V.110</ui>
	</enum>
</enum_list>
</var>

<var name="cell.csd.dial" type="string" default="">
<ui>Dial Number</ui>
<description>CSD Base Phone Number</description>
<uvar>5</uvar>
<profiles>
	<name>c-master</name>
</profiles>
</var>

<var name="cell.csd.idle" type="numeric" default="300">
<ui>CSD Timeout</ui>
<description>Hangup CSD if no data is received within timeout threshold</description>
<range min="0" max="9999">
<uifactor>0.1</uifactor>
</range>
<profiles>
	<name>c-master</name>
	<name>c-slave</name>
</profiles>
</var>

<var name="cell.op.name" type="string" default="">
<ui>Cellular Operator Name</ui>
<description>Operator Name (read only)</description>
<uvar>7</uvar>
</var>

<var name="cell.offmode" type="string" default="0">
<ui>Keep Cellular Powered</ui>
<description>Flag to Keep cellular module powered when turning profile off</description>
<uvar>8</uvar>
</var>

<var name="cell.sq" type="string" default="">
<ui>Cellular Signal Quality</ui>
<description>Signal Quality (read only)</description>
<uvar>9</uvar>
</var>

</vars-list>
</template>

<template name="Topcon|DUHF2;Motorola|G24">
<id>[$$dev.port$$];Topcon|DUHF2@[$$radio.rate$$];Motorola|G24@[$$cell.rate$$]</id>
<version>1.3</version>
<description>Digital UHF 2 modem with Motorola G20/G24 GSM module</description>
<compat-version>1</compat-version>

<profiles-list>
<profile name="internet">
	<description>Connect to Internet using GPRS by cellular modem</description>
	<block id="1" type="script" script="checkgsm">
		<branch from="0" to="0" id="3"></branch>

		<branch from="1" to="1" id="9"></branch>

		<branch from="2" to="15" id="2">
			<try times="1" id="1"></try></branch>
	</block>
	<block id="2" type="script" script="togsm">
		<branch from="0" to="0" id="3"></branch>

		<branch from="1" to="1" id="9"></branch>

		<branch from="2" to="15" id="2"></branch>
	</block>
	<block id="3" type="script" script="initgsm">
		<branch from="0" to="0" id="4"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="2">
			<try times="30" id="3"></try></branch>
	</block>
	<block id="4" type="script" script="setpin">
		<branch from="0" to="0" id="10"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="2" id="1">
			<try times="2" id="4"></try></branch>
		<branch from="3" to="3" id="3">
			<try times="10" id="4"></try></branch>
		<branch from="4" to="15" id="5"></branch>
	</block>
	<block id="5" type="script" script="setgprs">
		<branch from="0" to="0" id="6"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="3">
			<try times="10" id="5"></try></branch>
	</block>
	<block id="6" type="script" script="setppp">
		<branch from="0" to="0" id="7"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="5">
			<try times="30" id="6"></try></branch>
	</block>
	<block id="7" type="ppp" script="runppp">
		<branch from="0" to="0" id="6"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="6"></branch>
	</block>
	<block id="8" type="script" script="hangup">
		<branch from="0" to="1" id="9"></branch>

		<branch from="2" to="2" id="9">
			<try times="5" id="8"></try></branch>
		<branch from="3" to="15" id="9"></branch>
	</block>
	<block id="9" type="script" script="touhf">
		<branch from="0" to="0" id="0"></branch>
		<branch from="2" to="2" id="0">
			<try times="5" id="9"></try></branch>
		<branch from="3" to="3" id="0"></branch>
		<branch from="4" to="15" id="0">
			<try times="5" id="9"></try></branch>
	</block>
	<block id="10" type="script" script="error">
		<branch from="0" to="0" id="10"></branch>

		<branch from="1" to="15" id="8"></branch>
	</block>
</profile>

<profile name="c-master">
	<description>Start outgoing cellular data connection</description>
	<block id="1" type="script" script="checkgsm">
		<branch from="0" to="0" id="3"></branch>

		<branch from="1" to="1" id="9"></branch>

		<branch from="2" to="15" id="2">
			<try times="1" id="1"></try></branch>
	</block>
	<block id="2" type="script" script="togsm">
		<branch from="0" to="0" id="3"></branch>

		<branch from="1" to="1" id="9"></branch>

		<branch from="2" to="15" id="2"></branch>
	</block>
	<block id="3" type="script" script="initgsm">
		<branch from="0" to="0" id="4"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="2">
			<try times="30" id="3"></try></branch>
	</block>
	<block id="4" type="script" script="setpin">
		<branch from="0" to="0" id="10"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="2" id="1">
			<try times="2" id="4"></try></branch>
		<branch from="3" to="3" id="3">
			<try times="10" id="4"></try></branch>
		<branch from="4" to="15" id="5"></branch>
	</block>
	<block id="5" type="script" script="setgsm">
		<branch from="0" to="0" id="6"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="3">
			<try times="10" id="5"></try></branch>
	</block>
	<block id="6" type="script" script="setgsmm">
		<branch from="0" to="0" id="7"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="5">
			<try times="30" id="6"></try></branch>
	</block>
	<block id="7" type="direct" script="rungsm">
		<branch from="0" to="0" id="6"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="5"></branch>
	</block>
	<block id="8" type="script" script="hangup">
		<branch from="0" to="1" id="9"></branch>

		<branch from="2" to="2" id="9">
			<try times="5" id="8"></try></branch>
		<branch from="3" to="15" id="9"></branch>
	</block>
	<block id="9" type="script" script="touhf">
		<branch from="0" to="0" id="0"></branch>

		<branch from="2" to="15" id="0">
			<try times="5" id="9"></try></branch>
	</block>
	<block id="10" type="script" script="error">
		<branch from="0" to="0" id="10"></branch>

		<branch from="1" to="15" id="8"></branch>
	</block>
</profile>

<profile name="c-slave">
	<description>Wait for incoming cellular data call</description>
	<block id="1" type="script" script="checkgsm">
		<branch from="0" to="0" id="3"></branch>

		<branch from="1" to="1" id="9"></branch>

		<branch from="2" to="15" id="2">
			<try times="1" id="1"></try></branch>
	</block>
	<block id="2" type="script" script="togsm">
		<branch from="0" to="0" id="3"></branch>

		<branch from="1" to="1" id="9"></branch>

		<branch from="2" to="15" id="2"></branch>
	</block>
	<block id="3" type="script" script="initgsm">
		<branch from="0" to="0" id="4"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="2">
			<try times="30" id="3"></try></branch>
	</block>
	<block id="4" type="script" script="setpin">
		<branch from="0" to="0" id="10"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="2" id="1">
			<try times="2" id="4"></try></branch>
		<branch from="3" to="3" id="3">
			<try times="10" id="4"></try></branch>
		<branch from="4" to="15" id="5"></branch>
	</block>
	<block id="5" type="script" script="setgsm">
		<branch from="0" to="0" id="6"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="3">
			<try times="10" id="5"></try></branch>
	</block>
	<block id="6" type="script" script="setgsms">
		<branch from="0" to="0" id="7"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="2" id="5">
			<try times="30" id="6"></try></branch>
		<branch from="3" to="3" id="7"></branch>

		<branch from="4" to="15" id="5">
			<try times="3" id="6"></try></branch>
	</block>
	<block id="7" type="direct" script="rungsm">
		<branch from="0" to="0" id="6"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="5"></branch>
	</block>
	<block id="8" type="script" script="hangup">
		<branch from="0" to="1" id="9"></branch>

		<branch from="2" to="2" id="9">
			<try times="5" id="8"></try></branch>
		<branch from="3" to="15" id="9"></branch>
	</block>
	<block id="9" type="script" script="touhf">
		<branch from="0" to="0" id="0"></branch>

		<branch from="2" to="15" id="0">
			<try times="5" id="9"></try></branch>
	</block>
	<block id="10" type="script" script="error">
		<branch from="0" to="0" id="10"></branch>

		<branch from="1" to="15" id="8"></branch>
	</block>
</profile>

</profiles-list>

<scripts-list>
<script name="checkgsm">
<![CDATA[$ABORT||$ENDLINE|\r|$TIMEOUT|15|$REPORT|M105#Looking for modem|$DAISY|OFF||dm\r\n\p%%|RE002%%|%%dm,[$$dev.port$$]|RE|%%set,/par[$$dev.port$$]/rate,[$$cell.rate$$]|RE||$DAISY|[$$dev.port$$]|$TIMEOUT|10||AT|OK-AT-OK-AT-OK]]>
</script>

<script name="togsm">
<![CDATA[$ABORT||$ENDLINE|\r|$TIMEOUT|15|$DAISY|OFF||dm\r\n\p%%|RE002%%|%%dm,[$$dev.port$$]|RE||$REPORT|M106#Configuring modem||%%set,/par[$$dev.port$$]/rate,[$$radio.rate$$]|RE|%%set,/par[$$dev.port$$]/rtscts,off|RE||$DAISY|[$$dev.port$$]|$TIMEOUT|15||++++\p|@00-++++-@01|ATI|Topcon||@00|LINK RFSW 1|@00|\p\pDATAMODE|$WAIT|10|$DAISY|OFF||dm\r\n\p%%|RE002%%|%%set,/par[$$dev.port$$]/rate,[$$cell.rate$$]|RE|%%set,/par[$$dev.port$$]/rtscts,on|RE||$DAISY|[$$dev.port$$]|]]>
</script>

<script name="initgsm">
<![CDATA[$ABORT|ERROR|$ENDLINE|\r|$TIMEOUT|10||AT|OK||$TIMEOUT|20|$REPORT|M106#Configuring modem||ATV1&D0|OK|ATE0S0=0|OK|AT+CMEE=0|OK]]>
</script>

<script name="setpin">
<![CDATA[$ABORT|ERROR|$ENDLINE|\r|$TIMEOUT|10||AT|OK||$REPORT|M107#Checking SIM card|$ABORT|ERROR:READY||AT+CPIN?|+CPIN\:||SIM PIN||OK-AT-OK||$TIMEOUT|30|$REPORT|M108#Entering PIN|$ABORT|||\pAT+CPIN="[$$cell.pin$$]"|OK:ERROR||$ABORT|#---#:READY||AT+CPIN?|+CPIN\:||SIM||$REPORT|E101#Wrong PIN|]]>
</script>

<script name="setgprs">
<![CDATA[$ABORT||$TIMEOUT|10|$REPORT|M101#Registering||\p+++\p\pATH|OK:ERROR|AT+CREG=0|OK|AT+CGREG=0|OK|AT+COPS=3,0|OK|AT+CGATT?|+CGATT\:||1-AT+CGATT=0]]>
</script>

<script name="setppp">
<![CDATA[$ABORT||$TIMEOUT|10||AT+CREG?|+CREG\:||[$$cell.roam$$]||OK|AT+CGATT?|+CGATT\: 1-AT+CGATT=1-OK|AT+CGREG?|+CGREG\:||[$$cell.roam$$]||OK|AT+CSQ|+CSQ\:||$9,||OK|AT+COPS?|+COPS\:||,"||[$$cell.op.name$$]"||OK|AT+CGDCONT=1,"IP","[$$cell.gprs.apn$$]"|OK||$ABORT|NO CARRIER:BUSY:NO ANSWER:ERROR|$REPORT|M102#Dialing||ATD[$$cell.gprs.dial$$]|$TIMEOUT|400|CONNECT||]]>
</script>

<script name="setgsm">
<![CDATA[$ABORT||$TIMEOUT|10|$REPORT|M101#Registering||\p+++\p\pATH|OK:ERROR|AT+CREG=0|OK|AT+COPS=3,0|OK|AT+CSQ|+CSQ\:||$9,||OK|AT+COPS?|+COPS\:||,"||[$$cell.op.name$$]"||OK|]]>
</script>

<script name="setgsmm">
<![CDATA[$ABORT||$TIMEOUT|10||AT+CREG?|+CREG\:||[$$cell.roam$$]||OK|AT+CSQ|+CSQ\:||$9,||OK|AT+COPS?|+COPS\:||,"||[$$cell.op.name$$]"||OK|AT+CBST=[$$cell.csd.cbst$$]|OK:ERROR||$ABORT|NO CARRIER:BUSY:NO ANSWER:ERROR|$REPORT|M102#Dialing||ATD[$$cell.csd.dial$$]|$TIMEOUT|400|CONNECT||]]>
</script>

<script name="setgsms">
<![CDATA[$ABORT|CONNECT:NO CARRIER|$TIMEOUT|10||AT+CREG?|+CREG\:||[$$cell.roam$$]||OK|AT+CSQ|+CSQ\:||$9,||OK|AT+COPS?|+COPS\:||,"||[$$cell.op.name$$]"||OK|ATS0=2|OK|AT+CBST=[$$cell.csd.cbst$$]|OK:ERROR||$TIMEOUT|3000|$REPORT|M103#Awaiting call|RING|ATA|$TIMEOUT|200|CONNECT||]]>
</script>

<script name="hangup">
<![CDATA[$ABORT||$TIMEOUT|20||\p+++\p\p|OK-+++AT\p\p-OK-ATH-OK:ERROR|ATH|OK:ERROR|ATS0=0|OK|]]>
</script>

<script name="touhf">
<![CDATA[$ABORT||$TIMEOUT|20|$DAISY|OFF|$REPORT|M106#Configuring modem||dm\r\n\p%%|RE002%%|%%set,/par[$$dev.port$$]/rate,[$$radio.rate$$]|RE|%%set,/par[$$dev.port$$]/rtscts,off|RE||$ABORT|%1%||%[$$cell.offmode$$]%|RE||%0%:%%||$ABORT||$DAISY|[$$dev.port$$]|$TIMEOUT|15||++++\p|@00-++++-@01|ATI|Topcon||@00|LINK RFSW 0|@00|\p\pDATAMODE|$WAIT|10|$DAISY|OFF]]>
</script>

<script name="rungsm">
<![CDATA[$TIMEOUT|[$$cell.csd.idle$$]|$ABORT|NO CARRIER:ERROR:RING]]>
</script>

<script name="runppp">
<![CDATA[[$$dev.port$$]|[$$cell.rate$$]|[$$ppp.ip$$]|novj|novjccomp|lcp-echo-interval:15|lcp-echo-failure:3|lcp-restart:5|ipcp-accept-local|ipcp-accept-remote|ipcp-max-failure:3|ipcp-max-configure:10|usepeerdns|noipdefault|noproxyarp|idle:[$$ppp.idle$$]|name:[$$ppp.name$$]|password:[$$ppp.password$$]]]>
</script>

<script name="error">
<![CDATA[$ABORT||$WAIT|10|]]>
</script>

</scripts-list>

<vars-list>
<var name="dev.port" type="enum" default="3">
<ui>Port</ui>
<description>Name of hardware serial port that is connected to modem</description>
<enum_list>
	<enum index="1">
		<value>/dev/ser/a</value>
	</enum>
	<enum index="2">
		<value>/dev/ser/b</value>
	</enum>
	<enum index="3">
		<value>/dev/ser/c</value>
	</enum>
	<enum index="4">
		<value>/dev/ser/d</value>
	</enum>
</enum_list>
</var>

<var name="radio.rate" type="enum" default="6">
<ui>Baud Rate</ui>
<description>Baud rate of modem serial interface</description>
<enum_list>
	<enum index="1">
		<value>1200</value>
	</enum>
	<enum index="2">
		<value>2400</value>
	</enum>
	<enum index="3">
		<value>4800</value>
	</enum>
	<enum index="4">
		<value>9600</value>
	</enum>
	<enum index="5">
		<value>19200</value>
	</enum>
	<enum index="6">
		<value>38400</value>
	</enum>
	<enum index="7">
		<value>57600</value>
	</enum>
	<enum index="8">
		<value>115200</value>
	</enum>
</enum_list>
</var>

<var name="cell.rate" type="enum" default="6">
<ui>Baud Rate</ui>
<description>Baud rate of cellular module</description>
<enum_list>
	<enum index="1">
		<value>1200</value>
	</enum>
	<enum index="2">
		<value>2400</value>
	</enum>
	<enum index="3">
		<value>4800</value>
	</enum>
	<enum index="4">
		<value>9600</value>
	</enum>
	<enum index="5">
		<value>19200</value>
	</enum>
	<enum index="6">
		<value>38400</value>
	</enum>
	<enum index="7">
		<value>57600</value>
	</enum>
	<enum index="8">
		<value>115200</value>
	</enum>
</enum_list>
</var>

<var name="cell.pin" type="string" default="0000">
<ui>PIN Code</ui>
<description>SIM PIN code</description>
<uvar>0</uvar>
</var>

<var name="cell.gprs.dial" type="string" default="*99***1#">
<ui>GPRS Dial</ui>
<description>GPRS Dial Number</description>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="cell.gprs.apn" type="string" default="">
<ui>APN</ui>
<description>GPRS APN</description>
<uvar>1</uvar>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="ppp.name" type="string" default="">
<ui>User</ui>
<description>GPRS User Name</description>
<uvar>2</uvar>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="ppp.password" type="string" default="">
<ui>Password</ui>
<description>GPRS Password</description>
<uvar>3</uvar>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="ppp.ip" type="string" default="">
<ui>IP address</ui>
<description>Static PPP address</description>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="ppp.idle" type="numeric" default="0">
<ui>Timeout</ui>
<description>GPRS Reconnection Timeout if datalink is lost</description>
<range min="0" max="9999">
<uifactor>0.1</uifactor>
</range>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="cell.roam" type="enum" default="1">
<ui>Roaming</ui>
<description>Allow network roaming</description>
<profiles>
	<name>internet</name>
	<name>c-master</name>
	<name>c-slave</name>
</profiles>
<enum_list>
	<enum index="1">
		<value>,001:,005</value>
		<ui>Enabled</ui>
	</enum>
	<enum index="2">
		<value>,001</value>
		<ui>Disabled</ui>
	</enum>
</enum_list>
</var>

<var name="cell.csd.cbst" type="enum" default="1">
<ui>Data Call Type</ui>
<description>Bearer type for outgoing and incoming data calls</description>
<uvar>6</uvar>
<profiles>
	<name>c-master</name>
	<name>c-slave</name>
</profiles>
<enum_list>
	<enum index="1">
		<value>0</value>
		<ui>Automatic</ui>
	</enum>
	<enum index="2">
		<value>7</value>
		<ui>Analog V.32</ui>
	</enum>
	<enum index="3">
		<value>71</value>
		<ui>Digital V.110</ui>
	</enum>
</enum_list>
</var>

<var name="cell.csd.dial" type="string" default="">
<ui>Dial Number</ui>
<description>CSD Base Phone Number</description>
<uvar>5</uvar>
<profiles>
	<name>c-master</name>
</profiles>
</var>

<var name="cell.csd.idle" type="numeric" default="300">
<ui>CSD Timeout</ui>
<description>Hangup CSD if no data is received within timeout threshold</description>
<range min="0" max="9999">
<uifactor>0.1</uifactor>
</range>
<profiles>
	<name>c-master</name>
	<name>c-slave</name>
</profiles>
</var>

<var name="cell.op.name" type="string" default="">
<ui>Cellular Operator Name</ui>
<description>Operator Name (read only)</description>
<uvar>7</uvar>
</var>

<var name="cell.offmode" type="string" default="0">
<ui>Keep Cellular Powered</ui>
<description>Flag to Keep cellular module powered when turning profile off</description>
<uvar>8</uvar>
</var>

<var name="cell.sq" type="string" default="">
<ui>Cellular Signal Quality</ui>
<description>Signal Quality (read only)</description>
<uvar>9</uvar>
</var>

</vars-list>
</template>

<template name="Topcon|DUHF2;Motorola|H24">
<id>[$$dev.port$$];Topcon|DUHF2@[$$radio.rate$$];Motorola|H24@[$$cell.rate$$]</id>
<version>1.3</version>
<description>Digital UHF 2 modem with Motorola H24 3G module</description>
<compat-version>1</compat-version>

<profiles-list>
<profile name="internet">
	<description>Connect to Internet using GPRS by cellular modem</description>
	<block id="1" type="script" script="checkgsm">
		<branch from="0" to="0" id="3"></branch>

		<branch from="1" to="1" id="9"></branch>

		<branch from="2" to="15" id="2">
			<try times="1" id="1"></try></branch>
	</block>
	<block id="2" type="script" script="togsm">
		<branch from="0" to="0" id="3"></branch>

		<branch from="1" to="1" id="9"></branch>

		<branch from="2" to="15" id="2"></branch>
	</block>
	<block id="3" type="script" script="initgsm">
		<branch from="0" to="0" id="4"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="2" id="2">
			<try times="30" id="3"></try></branch>
		<branch from="3" to="15" id="4"></branch>
	</block>
	<block id="4" type="script" script="setpin">
		<branch from="0" to="0" id="10"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="2" id="1">
			<try times="2" id="4"></try></branch>
		<branch from="3" to="3" id="11">
			<try times="20" id="4"></try></branch>
		<branch from="4" to="15" id="5"></branch>
	</block>
	<block id="5" type="script" script="setgprs">
		<branch from="0" to="0" id="6"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="3">
			<try times="10" id="5"></try></branch>
	</block>
	<block id="6" type="script" script="setppp">
		<branch from="0" to="0" id="7"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="2" id="11">
			<try times="20" id="6"></try></branch>
		<branch from="3" to="15" id="5">
			<try times="30" id="6"></try></branch>
	</block>
	<block id="7" type="ppp" script="runppp">
		<branch from="0" to="0" id="6"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="6"></branch>
	</block>
	<block id="8" type="script" script="hangup">
		<branch from="0" to="1" id="9"></branch>

		<branch from="2" to="2" id="9">
			<try times="5" id="8"></try></branch>
		<branch from="3" to="15" id="9"></branch>
	</block>
	<block id="9" type="script" script="touhf">
		<branch from="0" to="0" id="0"></branch>
		<branch from="2" to="2" id="0">
			<try times="5" id="9"></try></branch>
		<branch from="3" to="3" id="0"></branch>
		<branch from="4" to="15" id="0">
			<try times="5" id="9"></try></branch>
	</block>
	<block id="10" type="script" script="error">
		<branch from="0" to="0" id="10"></branch>

		<branch from="1" to="15" id="8"></branch>
	</block>
	<block id="11" type="script" script="simreset">
		<branch from="0" to="0" id="3"></branch>
		<branch from="1" to="1" id="8"></branch>
		<branch from="2" to="2" id="3"></branch>
		<branch from="3" to="15" id="3"></branch>
	</block>
</profile>

<profile name="c-master">
	<description>Start outgoing cellular data connection</description>
	<block id="1" type="script" script="checkgsm">
		<branch from="0" to="0" id="3"></branch>

		<branch from="1" to="1" id="9"></branch>

		<branch from="2" to="15" id="2">
			<try times="1" id="1"></try></branch>
	</block>
	<block id="2" type="script" script="togsm">
		<branch from="0" to="0" id="3"></branch>

		<branch from="1" to="1" id="9"></branch>

		<branch from="2" to="15" id="2"></branch>
	</block>
	<block id="3" type="script" script="initgsm">
		<branch from="0" to="0" id="4"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="2" id="2">
			<try times="30" id="3"></try></branch>
		<branch from="3" to="15" id="4"></branch>
	</block>
	<block id="4" type="script" script="setpin">
		<branch from="0" to="0" id="10"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="2" id="1">
			<try times="2" id="4"></try></branch>
		<branch from="3" to="3" id="11">
			<try times="20" id="4"></try></branch>
		<branch from="4" to="15" id="5"></branch>
	</block>
	<block id="5" type="script" script="setgsm">
		<branch from="0" to="0" id="6"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="3">
			<try times="10" id="5"></try></branch>
	</block>
	<block id="6" type="script" script="setgsmm">
		<branch from="0" to="0" id="7"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="2" id="11">
			<try times="30" id="6"></try></branch>
		<branch from="3" to="15" id="5">
			<try times="30" id="6"></try></branch>
	</block>
	<block id="7" type="direct" script="rungsm">
		<branch from="0" to="0" id="6"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="5"></branch>
	</block>
	<block id="8" type="script" script="hangup">
		<branch from="0" to="1" id="9"></branch>

		<branch from="2" to="2" id="9">
			<try times="5" id="8"></try></branch>
		<branch from="3" to="15" id="9"></branch>
	</block>
	<block id="9" type="script" script="touhf">
		<branch from="0" to="0" id="0"></branch>

		<branch from="2" to="15" id="0">
			<try times="5" id="9"></try></branch>
	</block>
	<block id="10" type="script" script="error">
		<branch from="0" to="0" id="10"></branch>

		<branch from="1" to="15" id="8"></branch>
	</block>
	<block id="11" type="script" script="simreset">
		<branch from="0" to="0" id="3"></branch>
		<branch from="1" to="1" id="8"></branch>
		<branch from="2" to="2" id="3"></branch>
		<branch from="3" to="15" id="3"></branch>
	</block> 
</profile>

<profile name="c-slave">
	<description>Wait for incoming cellular data call</description>
	<block id="1" type="script" script="checkgsm">
		<branch from="0" to="0" id="3"></branch>

		<branch from="1" to="1" id="9"></branch>

		<branch from="2" to="15" id="2">
			<try times="1" id="1"></try></branch>
	</block>
	<block id="2" type="script" script="togsm">
		<branch from="0" to="0" id="3"></branch>

		<branch from="1" to="1" id="9"></branch>

		<branch from="2" to="15" id="2"></branch>
	</block>
	<block id="3" type="script" script="initgsm">
		<branch from="0" to="0" id="4"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="2" id="2">
			<try times="30" id="3"></try></branch>
		<branch from="3" to="15" id="4"></branch>
	</block>
	<block id="4" type="script" script="setpin">
		<branch from="0" to="0" id="10"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="2" id="1">
			<try times="2" id="4"></try></branch>
		<branch from="3" to="3" id="11">
			<try times="20" id="4"></try></branch>
		<branch from="4" to="15" id="5"></branch>
	</block>
	<block id="5" type="script" script="setgsm">
		<branch from="0" to="0" id="6"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="3">
			<try times="10" id="5"></try></branch>
	</block>
	<block id="6" type="script" script="setgsms">
		<branch from="0" to="0" id="7"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="2" id="5">
			<try times="30" id="6"></try></branch>
		<branch from="3" to="3" id="7"></branch>

		<branch from="4" to="15" id="5">
			<try times="3" id="6"></try></branch>
	</block>
	<block id="7" type="direct" script="rungsm">
		<branch from="0" to="0" id="6"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="5"></branch>
	</block>
	<block id="8" type="script" script="hangup">
		<branch from="0" to="1" id="9"></branch>

		<branch from="2" to="2" id="9">
			<try times="5" id="8"></try></branch>
		<branch from="3" to="15" id="9"></branch>
	</block>
	<block id="9" type="script" script="touhf">
		<branch from="0" to="0" id="0"></branch>

		<branch from="2" to="15" id="0">
			<try times="5" id="9"></try></branch>
	</block>
	<block id="10" type="script" script="error">
		<branch from="0" to="0" id="10"></branch>

		<branch from="1" to="15" id="8"></branch>
	</block>
	<block id="11" type="script" script="simreset">
		<branch from="0" to="0" id="3"></branch>
		<branch from="1" to="1" id="8"></branch>
		<branch from="2" to="2" id="3"></branch>
		<branch from="3" to="15" id="3"></branch>
	</block>
</profile>

</profiles-list>

<scripts-list>
<script name="checkgsm">
<![CDATA[$ABORT||$ENDLINE|\r|$TIMEOUT|15|$REPORT|M105#Looking for modem|$DAISY|OFF||dm\r\n\p%%|RE002%%|%%dm,[$$dev.port$$]|RE|%%set,/par[$$dev.port$$]/rate,[$$cell.rate$$]|RE||$DAISY|[$$dev.port$$]|$TIMEOUT|10||AT|OK-AT-OK-AT-OK]]>
</script>

<script name="togsm">
<![CDATA[$ABORT||$ENDLINE|\r|$TIMEOUT|15|$DAISY|OFF||dm\r\n\p%%|RE002%%|%%dm,[$$dev.port$$]|RE||$REPORT|M106#Configuring modem||%%set,/par[$$dev.port$$]/rate,[$$radio.rate$$]|RE|%%set,/par[$$dev.port$$]/rtscts,off|RE||$DAISY|[$$dev.port$$]|$TIMEOUT|15||++++\p|@00-++++-@01|ATI|Topcon||@00|LINK RFSW|0-LINK RFSW 0\n\p\pDATAMODE\n\p\p\p\p\p-@00|LINK RFSW 1|@00|\p\pDATAMODE|$WAIT|10|$DAISY|OFF||dm\r\n\p%%|RE002%%|%%set,/par[$$dev.port$$]/rate,[$$cell.rate$$]|RE|%%set,/par[$$dev.port$$]/rtscts,on|RE||$DAISY|[$$dev.port$$]|]]>
</script>

<script name="initgsm">
<![CDATA[$ABORT|ERROR|$ENDLINE|\r|$TIMEOUT|10||AT|OK||$TIMEOUT|20|$REPORT|M106#Configuring modem||ATV1&D0|OK|ATE0S0=0|OK|AT+CMEE=0|OK||$ABORT|+MCONN\: 3||AT+MCONN?|OK|AT+MCONN=3|OK|AT+MRST|OK|\pAT|OK]]>
</script>

<script name="setpin">
<![CDATA[$ABORT|ERROR|$ENDLINE|\r|$TIMEOUT|10||AT|OK|AT+CMEE=2|OK||$REPORT|M107#Checking SIM card|$ABORT|SIM busy:READY|$WAIT|5||AT+CPIN?|+CPIN\:||SIM PIN||OK-AT-OK||$TIMEOUT|30|$REPORT|M108#Entering PIN|$ABORT|||\pAT+CPIN="[$$cell.pin$$]"|OK:ERROR||$ABORT|#---#:READY||AT+CPIN?|+CPIN\:||SIM||$REPORT|E101#Wrong PIN|]]>
</script>

<script name="setgprs">
<![CDATA[$ABORT||$TIMEOUT|10|$REPORT|M101#Registering||\p+++\p\pATH|OK:ERROR|AT+CMEE=0|OK|AT+CREG=0|OK|AT+CGREG=0|OK||$ABORT|ERROR|$TIMEOUT|300||AT+COPS=[$$cell.3g.enable$$]|OK||$TIMEOUT|10||AT+WS46?|12:22:25||OK]]>
</script>

<script name="setppp">
<![CDATA[$ABORT|99,99|$TIMEOUT|10||AT+CREG?|+CREG\:||[$$cell.roam$$]||OK|AT+CSQ|+CSQ\:||OK|AT+CSQ|+CSQ\:||$9,||OK|AT+COPS?|+COPS\:||,"||[$$cell.op.name$$]"||OK|AT+CGDCONT=1,"IP","[$$cell.gprs.apn$$]"|OK||$ABORT|NO CARRIER:BUSY:NO ANSWER:ERROR|$REPORT|M102#Dialing||ATD[$$cell.gprs.dial$$]|$TIMEOUT|400|CONNECT||]]>
</script>

<script name="setgsm">
<![CDATA[$ABORT||$TIMEOUT|10|$REPORT|M101#Registering||\p+++\p\pATH|OK:ERROR|AT+CMEE=0|OK|AT+CREG=0|OK||$ABORT|ERROR|$TIMEOUT|300||AT+COPS=,0,,0|OK||$TIMEOUT|10||AT+WS46?|12||OK|AT+CSQ|+CSQ\:||$9,||OK|AT+COPS?|+COPS\:||,"||[$$cell.op.name$$]"||OK|]]>
</script>

<script name="setgsmm">
<![CDATA[$ABORT|99,99|$TIMEOUT|10||AT+CREG?|+CREG\:||[$$cell.roam$$]||OK|AT+CSQ|+CSQ\:||OK|AT+CSQ|+CSQ\:||$9,||OK|AT+COPS?|+COPS\:||,"||[$$cell.op.name$$]"||OK|AT+CBST=7|OK|AT+CBST=[$$cell.csd.cbst$$]|OK:ERROR||$ABORT|NO CARRIER:BUSY:NO ANSWER:ERROR|$REPORT|M102#Dialing||ATD[$$cell.csd.dial$$]|$TIMEOUT|400|CONNECT||]]>
</script>

<script name="setgsms">
<![CDATA[$ABORT|CONNECT:NO CARRIER:99,99|$TIMEOUT|10||AT+CREG?|+CREG\:||[$$cell.roam$$]||OK|AT+CSQ|+CSQ\:||OK|AT+CSQ|+CSQ\:||$9,||OK|AT+COPS?|+COPS\:||,"||[$$cell.op.name$$]"||OK|ATS0=2|OK||$TIMEOUT|3000|$REPORT|M103#Awaiting call|RING|ATA|$TIMEOUT|200|CONNECT||]]>
</script>

<script name="hangup">
<![CDATA[$ABORT|Topcon:Error|$TIMEOUT|20||\p+++\p\p|OK-AT-OK|ATI|OK:ERROR|ATH|OK:ERROR|ATS0=0|OK|]]>
</script>

<script name="touhf">
<![CDATA[$ABORT||$TIMEOUT|20|$DAISY|OFF|$REPORT|M106#Configuring modem||dm\r\n\p%%|RE002%%|%%set,/par[$$dev.port$$]/rate,[$$radio.rate$$]|RE|%%set,/par[$$dev.port$$]/rtscts,off|RE||$ABORT|%1%||%[$$cell.offmode$$]%|RE||%0%:%%||$ABORT||$DAISY|[$$dev.port$$]|$TIMEOUT|15||++++\p|@00-++++-@01|ATI|Topcon||@00|LINK RFSW 0|@00|\p\pDATAMODE|$WAIT|10|$DAISY|OFF]]>
</script>

<script name="rungsm">
<![CDATA[$TIMEOUT|[$$cell.csd.idle$$]|$ABORT|NO CARRIER:ERROR:RING]]>
</script>

<script name="runppp">
<![CDATA[[$$dev.port$$]|[$$cell.rate$$]|[$$ppp.ip$$]:192.168.255.1|novj|novjccomp|lcp-echo-interval:15|lcp-echo-failure:2|lcp-restart:5|ipcp-accept-local|ipcp-accept-remote|ipcp-max-failure:3|ipcp-max-configure:10|usepeerdns|noipdefault|noproxyarp|idle:[$$ppp.idle$$]|name:[$$ppp.name$$]|password:[$$ppp.password$$]]]>
</script>

<script name="error">
<![CDATA[$ABORT||$WAIT|10|]]>
</script>

<script name="simreset">
<![CDATA[$ABORT|AT+MRST:SIM PIN|$TIMEOUT|20||AT+CPIN?|SIM busy-AT+MGSMSIM?-MGSMSIM\: 0|AT+CPIN?|SIM busy-AT+MGSMSIM=1-OK|ATE1|OK|AT+CPIN?|SIM busy-AT+MRST-OK|AT+MGSMSIM=0|OK|\pAT+MRST|OK]]>
</script>

</scripts-list>

<vars-list>
<var name="dev.port" type="enum" default="3">
<ui>Port</ui>
<description>Name of hardware serial port that is connected to modem</description>
<enum_list>
	<enum index="1">
		<value>/dev/ser/a</value>
	</enum>
	<enum index="2">
		<value>/dev/ser/b</value>
	</enum>
	<enum index="3">
		<value>/dev/ser/c</value>
	</enum>
	<enum index="4">
		<value>/dev/ser/d</value>
	</enum>
</enum_list>
</var>

<var name="radio.rate" type="enum" default="6">
<ui>Baud Rate</ui>
<description>Baud rate of modem serial interface</description>
<enum_list>
	<enum index="1">
		<value>1200</value>
	</enum>
	<enum index="2">
		<value>2400</value>
	</enum>
	<enum index="3">
		<value>4800</value>
	</enum>
	<enum index="4">
		<value>9600</value>
	</enum>
	<enum index="5">
		<value>19200</value>
	</enum>
	<enum index="6">
		<value>38400</value>
	</enum>
	<enum index="7">
		<value>57600</value>
	</enum>
	<enum index="8">
		<value>115200</value>
	</enum>
</enum_list>
</var>

<var name="cell.rate" type="enum" default="6">
<ui>Baud Rate</ui>
<description>Baud rate of cellular module</description>
<enum_list>
	<enum index="1">
		<value>1200</value>
	</enum>
	<enum index="2">
		<value>2400</value>
	</enum>
	<enum index="3">
		<value>4800</value>
	</enum>
	<enum index="4">
		<value>9600</value>
	</enum>
	<enum index="5">
		<value>19200</value>
	</enum>
	<enum index="6">
		<value>38400</value>
	</enum>
	<enum index="7">
		<value>57600</value>
	</enum>
	<enum index="8">
		<value>115200</value>
	</enum>
</enum_list>
</var>

<var name="cell.pin" type="string" default="0000">
<ui>PIN Code</ui>
<description>SIM PIN code</description>
<uvar>0</uvar>
</var>

<var name="cell.gprs.dial" type="string" default="*99***1#">
<ui>GPRS Dial</ui>
<description>GPRS Dial Number</description>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="cell.gprs.apn" type="string" default="">
<ui>APN</ui>
<description>GPRS APN</description>
<uvar>1</uvar>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="ppp.name" type="string" default="">
<ui>User</ui>
<description>GPRS User Name</description>
<uvar>2</uvar>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="ppp.password" type="string" default="">
<ui>Password</ui>
<description>GPRS Password</description>
<uvar>3</uvar>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="ppp.ip" type="string" default="">
<ui>IP address</ui>
<description>Static PPP address</description>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="ppp.idle" type="numeric" default="0">
<ui>Timeout</ui>
<description>GPRS Reconnection Timeout if datalink is lost</description>
<range min="0" max="9999">
<uifactor>0.1</uifactor>
</range>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="cell.roam" type="enum" default="1">
<ui>Roaming</ui>
<description>Allow network roaming</description>
<profiles>
	<name>internet</name>
	<name>c-master</name>
	<name>c-slave</name>
</profiles>
<enum_list>
	<enum index="1">
		<value>,1:,5</value>
		<ui>Enabled</ui>
	</enum>
	<enum index="2">
		<value>,1</value>
		<ui>Disabled</ui>
	</enum>
</enum_list>
</var>

<var name="cell.csd.cbst" type="enum" default="1">
<ui>Data Call Type</ui>
<description>Bearer type for outgoing and incoming data calls</description>
<uvar>6</uvar>
<profiles>
	<name>c-master</name>
	<name>c-slave</name>
</profiles>
<enum_list>
	<enum index="1">
		<value>0</value>
		<ui>Automatic</ui>
	</enum>
	<enum index="2">
		<value>7</value>
		<ui>Analog V.32</ui>
	</enum>
	<enum index="3">
		<value>71</value>
		<ui>Digital V.110</ui>
	</enum>
</enum_list>
</var>

<var name="cell.csd.dial" type="string" default="">
<ui>Dial Number</ui>
<description>CSD Base Phone Number</description>
<uvar>5</uvar>
<profiles>
	<name>c-master</name>
</profiles>
</var>

<var name="cell.csd.idle" type="numeric" default="300">
<ui>CSD Timeout</ui>
<description>Hangup CSD if no data is received within timeout threshold</description>
<range min="0" max="9999">
<uifactor>0.1</uifactor>
</range>
<profiles>
	<name>c-master</name>
	<name>c-slave</name>
</profiles>
</var>

<var name="cell.3g.enable" type="enum" default="1">
<ui>3G Mode</ui>
<description>Use 3G technology for Internet access</description>
<enum_list>
	<enum index="1">
		<value>0,0,,</value>
		<ui>Automatic</ui>
	</enum>
	<enum index="2">
		<value>,0,,0</value>
		<ui>2G only</ui>
	</enum>
	<enum index="3">
		<value>,0,,2</value>
		<ui>3G only</ui>
	</enum>
</enum_list>
</var>

<var name="cell.op.name" type="string" default="">
<ui>Cellular Operator Name</ui>
<description>Operator Name (read only)</description>
<uvar>7</uvar>
</var>

<var name="cell.offmode" type="string" default="0">
<ui>Keep Cellular Powered</ui>
<description>Flag to Keep cellular module powered when turning profile off</description>
<uvar>8</uvar>
</var>

<var name="cell.sq" type="string" default="">
<ui>Cellular Signal Quality</ui>
<description>Signal Quality (read only)</description>
<uvar>9</uvar>
</var>

</vars-list>
</template>

<template name="Topcon|FH915+;Motorola|G24">
<id>[$$dev.port$$];Topcon|FH915+@[$$radio.rate$$];Motorola|G24@[$$radio.rate$$]</id>
<version>1.3</version>
<description>TPS FH915+ Modem with Motorola G20/G24 GSM module</description>
<compat-version>1</compat-version>

<profiles-list>
<profile name="internet">
	<description>Connect to Internet using GPRS by cellular modem</description>
	<block id="1" type="script" script="checkgsm">
		<branch from="0" to="0" id="3"></branch>

		<branch from="1" to="1" id="9"></branch>

		<branch from="2" to="15" id="2">
			<try times="1" id="1"></try></branch>
	</block>
	<block id="2" type="script" script="togsm">
		<branch from="0" to="0" id="3"></branch>

		<branch from="1" to="1" id="9"></branch>

		<branch from="2" to="15" id="2"></branch>
	</block>
	<block id="3" type="script" script="initgsm">
		<branch from="0" to="0" id="4"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="2">
			<try times="30" id="3"></try></branch>
	</block>
	<block id="4" type="script" script="setpin">
		<branch from="0" to="0" id="10"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="2" id="1">
			<try times="2" id="4"></try></branch>
		<branch from="3" to="3" id="3">
			<try times="10" id="4"></try></branch>
		<branch from="4" to="15" id="5"></branch>
	</block>
	<block id="5" type="script" script="setgprs">
		<branch from="0" to="0" id="6"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="3">
			<try times="10" id="5"></try></branch>
	</block>
	<block id="6" type="script" script="setppp">
		<branch from="0" to="0" id="7"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="5">
			<try times="30" id="6"></try></branch>
	</block>
	<block id="7" type="ppp" script="runppp">
		<branch from="0" to="0" id="6"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="6"></branch>
	</block>
	<block id="8" type="script" script="hangup">
		<branch from="0" to="1" id="9"></branch>

		<branch from="2" to="2" id="9">
			<try times="5" id="8"></try></branch>
		<branch from="3" to="15" id="9"></branch>
	</block>
	<block id="9" type="script" script="touhf">
		<branch from="0" to="0" id="0"></branch>
		<branch from="2" to="2" id="0">
			<try times="5" id="9"></try></branch>
		<branch from="3" to="3" id="0"></branch>
		<branch from="4" to="15" id="0">
			<try times="5" id="9"></try></branch>
	</block>
	<block id="10" type="script" script="error">
		<branch from="0" to="0" id="10"></branch>

		<branch from="1" to="15" id="8"></branch>
	</block>
</profile>

<profile name="c-master">
	<description>Start outgoing cellular data connection</description>
	<block id="1" type="script" script="checkgsm">
		<branch from="0" to="0" id="3"></branch>

		<branch from="1" to="1" id="9"></branch>

		<branch from="2" to="15" id="2">
			<try times="1" id="1"></try></branch>
	</block>
	<block id="2" type="script" script="togsm">
		<branch from="0" to="0" id="3"></branch>

		<branch from="1" to="1" id="9"></branch>

		<branch from="2" to="15" id="2"></branch>
	</block>
	<block id="3" type="script" script="initgsm">
		<branch from="0" to="0" id="4"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="2">
			<try times="30" id="3"></try></branch>
	</block>
	<block id="4" type="script" script="setpin">
		<branch from="0" to="0" id="10"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="2" id="1">
			<try times="2" id="4"></try></branch>
		<branch from="3" to="3" id="3">
			<try times="10" id="4"></try></branch>
		<branch from="4" to="15" id="5"></branch>
	</block>
	<block id="5" type="script" script="setgsm">
		<branch from="0" to="0" id="6"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="3">
			<try times="10" id="5"></try></branch>
	</block>
	<block id="6" type="script" script="setgsmm">
		<branch from="0" to="0" id="7"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="5">
			<try times="30" id="6"></try></branch>
	</block>
	<block id="7" type="direct" script="rungsm">
		<branch from="0" to="0" id="6"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="11"></branch>
	</block>
	<block id="8" type="script" script="hangup">
		<branch from="0" to="1" id="9"></branch>

		<branch from="2" to="2" id="9">
			<try times="5" id="8"></try></branch>
		<branch from="3" to="15" id="9"></branch>
	</block>
	<block id="9" type="script" script="touhf">
		<branch from="0" to="0" id="0"></branch>

		<branch from="2" to="15" id="0">
			<try times="5" id="9"></try></branch>
	</block>
	<block id="10" type="script" script="error">
		<branch from="0" to="0" id="10"></branch>

		<branch from="1" to="15" id="8"></branch>
	</block>
	<block id="11" type="script" script="resetgsm">
		<branch from="0" to="0" id="5"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="2" id="2">
			<try times="5" id="11"></try></branch>
		<branch from="3" to="15" id="2"></branch>
	</block> 
</profile>

<profile name="c-slave">
	<description>Wait for incoming cellular data call</description>
	<block id="1" type="script" script="checkgsm">
		<branch from="0" to="0" id="3"></branch>

		<branch from="1" to="1" id="9"></branch>

		<branch from="2" to="15" id="2">
			<try times="1" id="1"></try></branch>
	</block>
	<block id="2" type="script" script="togsm">
		<branch from="0" to="0" id="3"></branch>

		<branch from="1" to="1" id="9"></branch>

		<branch from="2" to="15" id="2"></branch>
	</block>
	<block id="3" type="script" script="initgsm">
		<branch from="0" to="0" id="4"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="2">
			<try times="30" id="3"></try></branch>
	</block>
	<block id="4" type="script" script="setpin">
		<branch from="0" to="0" id="10"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="2" id="1">
			<try times="2" id="4"></try></branch>
		<branch from="3" to="3" id="3">
			<try times="10" id="4"></try></branch>
		<branch from="4" to="15" id="5"></branch>
	</block>
	<block id="5" type="script" script="setgsm">
		<branch from="0" to="0" id="6"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="3">
			<try times="10" id="5"></try></branch>
	</block>
	<block id="6" type="script" script="setgsms">
		<branch from="0" to="0" id="7"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="2" id="5">
			<try times="30" id="6"></try></branch>
		<branch from="3" to="3" id="7"></branch>

		<branch from="4" to="15" id="5">
			<try times="3" id="6"></try></branch>
	</block>
	<block id="7" type="direct" script="rungsm">
		<branch from="0" to="0" id="6"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="11"></branch>
	</block>
	<block id="8" type="script" script="hangup">
		<branch from="0" to="1" id="9"></branch>

		<branch from="2" to="2" id="9">
			<try times="5" id="8"></try></branch>
		<branch from="3" to="15" id="9"></branch>
	</block>
	<block id="9" type="script" script="touhf">
		<branch from="0" to="0" id="0"></branch>

		<branch from="2" to="15" id="0">
			<try times="5" id="9"></try></branch>
	</block>
	<block id="10" type="script" script="error">
		<branch from="0" to="0" id="10"></branch>

		<branch from="1" to="15" id="8"></branch>
	</block>
	<block id="11" type="script" script="resetgsm">
		<branch from="0" to="0" id="5"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="2" id="2">
			<try times="5" id="11"></try></branch>
		<branch from="3" to="15" id="2"></branch>
	</block> 
</profile>

</profiles-list>

<scripts-list>
<script name="checkgsm">
<![CDATA[$ABORT||$ENDLINE|\r|$TIMEOUT|15|$REPORT|M105#Looking for modem|$DAISY|OFF||dm\r\n\p%%|RE002%%|%%dm,[$$dev.port$$]|RE|%%set,/par[$$dev.port$$]/rate,[$$radio.rate$$]|RE||$DAISY|[$$dev.port$$]|$TIMEOUT|10||AT|OK-AT-OK-AT-OK]]>
</script>

<script name="togsm">
<![CDATA[$ABORT||$ENDLINE|\r|$TIMEOUT|15|$DAISY|OFF||dm\r\n\p%%|RE002%%|%%dm,[$$dev.port$$]|RE||$REPORT|M106#Configuring modem||%%set,/par[$$dev.port$$]/rtscts,off|RE|%%set,/par[$$dev.port$$]/rts,on|RE|%%set,/par[$$dev.port$$]/rate,[$$radio.rate$$]|RE||$DAISY|[$$dev.port$$]|$TIMEOUT|15||++++|OK-++++-OK-++++-OK|ati|Topcon|%GSM1%set,modem/fh/gsmmode,3|%GSM1%||OK-%GSM2%set,modem/uhf/gsmmode,3-OK|\pato|OK||$WAIT|10|$DAISY|OFF||dm\r\n\p%%|RE002%%|%%set,/par[$$dev.port$$]/rate,[$$radio.rate$$]|RE|%%set,/par[$$dev.port$$]/rtscts,on|RE||$DAISY|[$$dev.port$$]|]]>
</script>

<script name="initgsm">
<![CDATA[$ABORT|ERROR|$ENDLINE|\r|$TIMEOUT|10||AT|OK||$TIMEOUT|20|$REPORT|M106#Configuring modem||ATV1&D0|OK|ATE0S0=0|OK|AT+CMEE=0|OK]]>
</script>

<script name="setpin">
<![CDATA[$ABORT|ERROR|$ENDLINE|\r|$TIMEOUT|10||AT|OK||$REPORT|M107#Checking SIM card|$ABORT|ERROR:READY||AT+CPIN?|+CPIN\:||SIM PIN||OK-AT-OK||$TIMEOUT|30|$REPORT|M108#Entering PIN|$ABORT|||\pAT+CPIN="[$$cell.pin$$]"|OK:ERROR||$ABORT|#---#:READY||AT+CPIN?|+CPIN\:||SIM||$REPORT|E101#Wrong PIN|]]>
</script>

<script name="setgprs">
<![CDATA[$ABORT||$TIMEOUT|10|$REPORT|M101#Registering||ATH|OK:ERROR|AT+CREG=0|OK|AT+CGREG=0|OK|AT+COPS=3,0|OK|AT+CGATT=0|OK|]]>
</script>

<script name="setppp">
<![CDATA[$ABORT||$TIMEOUT|10||AT+CREG?|+CREG\:||[$$cell.roam$$]||OK|AT+CGATT?|+CGATT\: 1-AT+CGATT=1-OK|AT+CGREG?|+CGREG\:||[$$cell.roam$$]||OK|AT+CSQ|+CSQ\:||$9,||OK|AT+COPS?|+COPS\:||,"||[$$cell.op.name$$]"||OK|AT+CGDCONT=1,"IP","[$$cell.gprs.apn$$]"|OK||$ABORT|NO CARRIER:BUSY:NO ANSWER:ERROR|$REPORT|M102#Dialing||ATD[$$cell.gprs.dial$$]|$TIMEOUT|400|CONNECT||]]>
</script>

<script name="setgsm">
<![CDATA[$ABORT||$TIMEOUT|10|$REPORT|M101#Registering||ATH|OK:ERROR|AT+CREG=0|OK|AT+COPS=3,0|OK|AT+CSQ|+CSQ\:||$9,||OK|AT+COPS?|+COPS\:||,"||[$$cell.op.name$$]"||OK|]]>
</script>

<script name="setgsmm">
<![CDATA[$ABORT||$TIMEOUT|10||AT+CREG?|+CREG\:||[$$cell.roam$$]||OK|AT+CSQ|+CSQ\:||$9,||OK|AT+COPS?|+COPS\:||,"||[$$cell.op.name$$]"||OK|AT+CBST=[$$cell.csd.cbst$$]|OK:ERROR||$ABORT|NO CARRIER:BUSY:NO ANSWER:ERROR|$REPORT|M102#Dialing||ATD[$$cell.csd.dial$$]|$TIMEOUT|400|CONNECT||]]>
</script>

<script name="setgsms">
<![CDATA[$ABORT|CONNECT:NO CARRIER|$TIMEOUT|10||AT+CREG?|+CREG\:||[$$cell.roam$$]||OK|AT+CSQ|+CSQ\:||$9,||OK|AT+COPS?|+COPS\:||,"||[$$cell.op.name$$]"||OK|ATS0=2|OK|AT+CBST=[$$cell.csd.cbst$$]|OK:ERROR||$TIMEOUT|3000|$REPORT|M103#Awaiting call|RING|ATA|$TIMEOUT|200|CONNECT||]]>
</script>

<script name="hangup">
<![CDATA[$ABORT|Topcon:Error|$TIMEOUT|20||\p+++\p\p|OK-AT-OK|ATI|OK:ERROR|ATH|OK:ERROR|ATS0=0|OK|]]>
</script>

<script name="touhf">
<![CDATA[$ABORT||$TIMEOUT|20|$DAISY|OFF|$REPORT|M106#Configuring modem||dm\r\n\p%%|RE002%%|%%set,/par[$$dev.port$$]/rate,[$$radio.rate$$]|RE|%%set,/par[$$dev.port$$]/rtscts,off|RE||$ABORT|%1%||%[$$cell.offmode$$]%|RE||%0%:%%||$ABORT||$DAISY|[$$dev.port$$]|$TIMEOUT|15||++++|OK-++++-OK-++++-OK|ati|Topcon|%GSM1%set,modem/fh/gsmmode,0|%GSM1%||OK-%GSM2%set,modem/uhf/gsmmode,0-OK|\pato|OK||$WAIT|10|$DAISY|OFF]]>
</script>

<script name="rungsm">
<![CDATA[$TIMEOUT|[$$cell.csd.idle$$]|$ABORT|NO CARRIER:ERROR:RING]]>
</script>

<script name="runppp">
<![CDATA[[$$dev.port$$]|[$$radio.rate$$]|[$$ppp.ip$$]|novj|novjccomp|lcp-echo-interval:15|lcp-echo-failure:3|lcp-restart:5|ipcp-accept-local|ipcp-accept-remote|ipcp-max-failure:3|ipcp-max-configure:10|usepeerdns|noipdefault|noproxyarp|idle:[$$ppp.idle$$]|name:[$$ppp.name$$]|password:[$$ppp.password$$]]]>
</script>

<script name="error">
<![CDATA[$ABORT||$WAIT|10|]]>
</script>

<script name="resetgsm">
<![CDATA[$ABORT|Topcon:Error|$TIMEOUT|60||\p+++\p\p|OK-AT-OK||$TIMEOUT|10||ATI|OK|AT+CGMI|Motorola||OK]]>
</script>

</scripts-list>

<vars-list>
<var name="dev.port" type="enum" default="3">
<ui>Port</ui>
<description>Name of hardware serial port that is connected to modem</description>
<enum_list>
	<enum index="1">
		<value>/dev/ser/a</value>
	</enum>
	<enum index="2">
		<value>/dev/ser/b</value>
	</enum>
	<enum index="3">
		<value>/dev/ser/c</value>
	</enum>
	<enum index="4">
		<value>/dev/ser/d</value>
	</enum>
</enum_list>
</var>

<var name="radio.rate" type="enum" default="6">
<ui>Baud Rate</ui>
<description>Baud rate of modem serial interface</description>
<enum_list>
	<enum index="1">
		<value>1200</value>
	</enum>
	<enum index="2">
		<value>2400</value>
	</enum>
	<enum index="3">
		<value>4800</value>
	</enum>
	<enum index="4">
		<value>9600</value>
	</enum>
	<enum index="5">
		<value>19200</value>
	</enum>
	<enum index="6">
		<value>38400</value>
	</enum>
	<enum index="7">
		<value>57600</value>
	</enum>
	<enum index="8">
		<value>115200</value>
	</enum>
</enum_list>
</var>

<var name="cell.pin" type="string" default="0000">
<ui>PIN Code</ui>
<description>SIM PIN code</description>
<uvar>0</uvar>
</var>

<var name="cell.gprs.dial" type="string" default="*99***1#">
<ui>GPRS Dial</ui>
<description>GPRS Dial Number</description>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="cell.gprs.apn" type="string" default="">
<ui>APN</ui>
<description>GPRS APN</description>
<uvar>1</uvar>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="ppp.name" type="string" default="">
<ui>User</ui>
<description>GPRS User Name</description>
<uvar>2</uvar>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="ppp.password" type="string" default="">
<ui>Password</ui>
<description>GPRS Password</description>
<uvar>3</uvar>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="ppp.ip" type="string" default="">
<ui>IP address</ui>
<description>Static PPP address</description>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="ppp.idle" type="numeric" default="0">
<ui>Timeout</ui>
<description>GPRS Reconnection Timeout if datalink is lost</description>
<range min="0" max="9999">
<uifactor>0.1</uifactor>
</range>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="cell.roam" type="enum" default="1">
<ui>Roaming</ui>
<description>Allow network roaming</description>
<profiles>
	<name>internet</name>
	<name>c-master</name>
	<name>c-slave</name>
</profiles>
<enum_list>
	<enum index="1">
		<value>,001:,1:,005:,5</value>
		<ui>Enabled</ui>
	</enum>
	<enum index="2">
		<value>,001:,1</value>
		<ui>Disabled</ui>
	</enum>
</enum_list>
</var>

<var name="cell.csd.cbst" type="enum" default="1">
<ui>Data Call Type</ui>
<description>Bearer type for outgoing and incoming data calls</description>
<uvar>6</uvar>
<profiles>
	<name>c-master</name>
	<name>c-slave</name>
</profiles>
<enum_list>
	<enum index="1">
		<value>0</value>
		<ui>Automatic</ui>
	</enum>
	<enum index="2">
		<value>7</value>
		<ui>Analog V.32</ui>
	</enum>
	<enum index="3">
		<value>71</value>
		<ui>Digital V.110</ui>
	</enum>
</enum_list>
</var>
<var name="cell.csd.dial" type="string" default="">
<ui>Dial Number</ui>
<description>CSD Base Phone Number</description>
<uvar>5</uvar>
<profiles>
	<name>c-master</name>
</profiles>
</var>

<var name="cell.csd.idle" type="numeric" default="300">
<ui>CSD Timeout</ui>
<description>Hangup CSD if no data is received within timeout threshold</description>
<range min="0" max="9999">
<uifactor>0.1</uifactor>
</range>
<profiles>
	<name>c-master</name>
	<name>c-slave</name>
</profiles>
</var>

<var name="cell.op.name" type="string" default="">
<ui>Cellular Operator Name</ui>
<description>Operator Name (read only)</description>
<uvar>7</uvar>
</var>

<var name="cell.offmode" type="string" default="0">
<ui>Keep Cellular Powered</ui>
<description>Flag to Keep cellular module powered when turning profile off</description>
<uvar>8</uvar>
</var>

<var name="cell.sq" type="string" default="">
<ui>Cellular Signal Quality</ui>
<description>Signal Quality (read only)</description>
<uvar>9</uvar>
</var>

</vars-list>
</template>

<template name="Topcon|FH915+;Motorola|H24">
<id>[$$dev.port$$];Topcon|FH915+@[$$radio.rate$$];Motorola|H24@[$$radio.rate$$]</id>
<version>1.3</version>
<description>TPS FH915+ Modem with Motorola H24 3G module</description>
<compat-version>1</compat-version>

<profiles-list>
<profile name="internet">
	<description>Connect to Internet using GPRS by cellular modem</description>
	<block id="1" type="script" script="checkgsm">
		<branch from="0" to="0" id="3"></branch>

		<branch from="1" to="1" id="9"></branch>

		<branch from="2" to="15" id="2">
			<try times="1" id="1"></try></branch>
	</block>
	<block id="2" type="script" script="togsm">
		<branch from="0" to="0" id="3"></branch>

		<branch from="1" to="1" id="9"></branch>

		<branch from="2" to="15" id="2"></branch>
	</block>
	<block id="3" type="script" script="initgsm">
		<branch from="0" to="0" id="4"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="2" id="2">
			<try times="30" id="3"></try></branch>
		<branch from="3" to="15" id="4"></branch>
	</block>
	<block id="4" type="script" script="setpin">
		<branch from="0" to="0" id="10"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="2" id="1">
			<try times="2" id="4"></try></branch>
		<branch from="3" to="3" id="11">
			<try times="20" id="4"></try></branch>
		<branch from="4" to="15" id="5"></branch>
	</block>
	<block id="5" type="script" script="setgprs">
		<branch from="0" to="0" id="6"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="3">
			<try times="10" id="5"></try></branch>
	</block>
	<block id="6" type="script" script="setppp">
		<branch from="0" to="0" id="7"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="2" id="11">
			<try times="20" id="6"></try></branch>
		<branch from="3" to="15" id="5">
			<try times="30" id="6"></try></branch>
	</block>
	<block id="7" type="ppp" script="runppp">
		<branch from="0" to="0" id="6"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="6"></branch>
	</block>
	<block id="8" type="script" script="hangup">
		<branch from="0" to="1" id="9"></branch>

		<branch from="2" to="2" id="9">
			<try times="5" id="8"></try></branch>
		<branch from="3" to="15" id="9"></branch>
	</block>
	<block id="9" type="script" script="touhf">
		<branch from="0" to="0" id="0"></branch>
		<branch from="2" to="2" id="0">
			<try times="5" id="9"></try></branch>
		<branch from="3" to="3" id="0"></branch>
		<branch from="4" to="15" id="0">
			<try times="5" id="9"></try></branch>
	</block>
	<block id="10" type="script" script="error">
		<branch from="0" to="0" id="10"></branch>

		<branch from="1" to="15" id="8"></branch>
	</block>
	<block id="11" type="script" script="simreset">
		<branch from="0" to="0" id="3"></branch>
		<branch from="1" to="1" id="8"></branch>
		<branch from="2" to="2" id="3"></branch>
		<branch from="3" to="15" id="3"></branch>
	</block>
</profile>
<profile name="c-master">
	<description>Start outgoing cellular data connection</description>
	<block id="1" type="script" script="checkgsm">
		<branch from="0" to="0" id="3"></branch>

		<branch from="1" to="1" id="9"></branch>

		<branch from="2" to="15" id="2">
			<try times="1" id="1"></try></branch>
	</block>
	<block id="2" type="script" script="togsm">
		<branch from="0" to="0" id="3"></branch>

		<branch from="1" to="1" id="9"></branch>

		<branch from="2" to="15" id="2"></branch>
	</block>
	<block id="3" type="script" script="initgsm">
		<branch from="0" to="0" id="4"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="2" id="2">
			<try times="30" id="3"></try></branch>
		<branch from="3" to="15" id="4"></branch>
	</block>
	<block id="4" type="script" script="setpin">
		<branch from="0" to="0" id="10"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="2" id="1">
			<try times="2" id="4"></try></branch>
		<branch from="3" to="3" id="12">
			<try times="20" id="4"></try></branch>
		<branch from="4" to="15" id="5"></branch>
	</block>
	<block id="5" type="script" script="setgsm">
		<branch from="0" to="0" id="6"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="3">
			<try times="10" id="5"></try></branch>
	</block>
	<block id="6" type="script" script="setgsmm">
		<branch from="0" to="0" id="7"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="2" id="12">
			<try times="30" id="6"></try></branch>
		<branch from="3" to="15" id="5">
			<try times="30" id="6"></try></branch>

	</block>
	<block id="7" type="direct" script="rungsm">
		<branch from="0" to="0" id="6"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="11"></branch>
	</block>
	<block id="8" type="script" script="hangup">
		<branch from="0" to="1" id="9"></branch>

		<branch from="2" to="2" id="9">
			<try times="5" id="8"></try></branch>
		<branch from="3" to="15" id="9"></branch>
	</block>
	<block id="9" type="script" script="touhf">
		<branch from="0" to="0" id="0"></branch>

		<branch from="2" to="15" id="0">
			<try times="5" id="9"></try></branch>
	</block>
	<block id="10" type="script" script="error">
		<branch from="0" to="0" id="10"></branch>

		<branch from="1" to="15" id="8"></branch>
	</block>
	<block id="11" type="script" script="resetgsm">
		<branch from="0" to="0" id="5"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="2" id="2">
			<try times="5" id="11"></try></branch>
		<branch from="3" to="15" id="2"></branch>
	</block>
	<block id="12" type="script" script="simreset">
		<branch from="0" to="0" id="3"></branch>
		<branch from="1" to="1" id="8"></branch>
		<branch from="2" to="2" id="3"></branch>
		<branch from="3" to="15" id="3"></branch>
	</block> 
</profile>

<profile name="c-slave">
	<description>Wait for incoming cellular data call</description>
	<block id="1" type="script" script="checkgsm">
		<branch from="0" to="0" id="3"></branch>

		<branch from="1" to="1" id="9"></branch>

		<branch from="2" to="15" id="2">
			<try times="1" id="1"></try></branch>
	</block>
	<block id="2" type="script" script="togsm">
		<branch from="0" to="0" id="3"></branch>

		<branch from="1" to="1" id="9"></branch>

		<branch from="2" to="15" id="2"></branch>
	</block>
	<block id="3" type="script" script="initgsm">
		<branch from="0" to="0" id="4"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="2" id="2">
			<try times="30" id="3"></try></branch>
		<branch from="3" to="15" id="4"></branch>
	</block>
	<block id="4" type="script" script="setpin">
		<branch from="0" to="0" id="10"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="2" id="1">
			<try times="2" id="4"></try></branch>
		<branch from="3" to="3" id="12">
			<try times="20" id="4"></try></branch>
		<branch from="4" to="15" id="5"></branch>
	</block>
	<block id="5" type="script" script="setgsm">
		<branch from="0" to="0" id="6"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="3">
			<try times="10" id="5"></try></branch>
	</block>
	<block id="6" type="script" script="setgsms">
		<branch from="0" to="0" id="7"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="2" id="5">
			<try times="30" id="6"></try></branch>
		<branch from="3" to="3" id="7"></branch>

		<branch from="4" to="15" id="5">
			<try times="3" id="6"></try></branch>
	</block>
	<block id="7" type="direct" script="rungsm">
		<branch from="0" to="0" id="6"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="11"></branch>
	</block>
	<block id="8" type="script" script="hangup">
		<branch from="0" to="1" id="9"></branch>

		<branch from="2" to="2" id="9">
			<try times="5" id="8"></try></branch>
		<branch from="3" to="15" id="9"></branch>
	</block>
	<block id="9" type="script" script="touhf">
		<branch from="0" to="0" id="0"></branch>

		<branch from="2" to="15" id="0">
			<try times="5" id="9"></try></branch>
	</block>
	<block id="10" type="script" script="error">
		<branch from="0" to="0" id="10"></branch>

		<branch from="1" to="15" id="8"></branch>
	</block>
	<block id="11" type="script" script="resetgsm">
		<branch from="0" to="0" id="5"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="2" id="2">
			<try times="5" id="11"></try></branch>
		<branch from="3" to="15" id="2"></branch>
	</block> 
	<block id="12" type="script" script="simreset">
		<branch from="0" to="0" id="3"></branch>
		<branch from="1" to="1" id="8"></branch>
		<branch from="2" to="2" id="3"></branch>
		<branch from="3" to="15" id="3"></branch>
	</block>
</profile>

</profiles-list>

<scripts-list>
<script name="checkgsm">
<![CDATA[$ABORT||$ENDLINE|\r|$TIMEOUT|15|$REPORT|M105#Looking for modem|$DAISY|OFF||dm\r\n\p%%|RE002%%|%%dm,[$$dev.port$$]|RE|%%set,/par[$$dev.port$$]/rate,[$$radio.rate$$]|RE||$DAISY|[$$dev.port$$]|$TIMEOUT|10||AT|OK-AT-OK-AT-OK]]>
</script>

<script name="togsm">
<![CDATA[$ABORT||$ENDLINE|\r|$TIMEOUT|15|$DAISY|OFF||dm\r\n\p%%|RE002%%|%%dm,[$$dev.port$$]|RE||$REPORT|M106#Configuring modem||%%set,/par[$$dev.port$$]/rtscts,off|RE|%%set,/par[$$dev.port$$]/rts,on|RE|%%set,/par[$$dev.port$$]/rate,[$$radio.rate$$]|RE||$DAISY|[$$dev.port$$]|$TIMEOUT|15||++++|OK-++++-OK-++++-OK|ati|Topcon|%GSM1%set,modem/fh/gsmmode,3|%GSM1%||OK-%GSM2%set,modem/uhf/gsmmode,3-OK|\pato|OK||$WAIT|10|$DAISY|OFF||dm\r\n\p%%|RE002%%|%%set,/par[$$dev.port$$]/rate,[$$radio.rate$$]|RE|%%set,/par[$$dev.port$$]/rtscts,on|RE||$DAISY|[$$dev.port$$]|]]>
</script>

<script name="initgsm">
<![CDATA[$ABORT|ERROR|$ENDLINE|\r|$TIMEOUT|10||AT|OK||$TIMEOUT|20|$REPORT|M106#Configuring modem||ATV1&D0|OK|ATE0S0=0|OK|AT+CMEE=0|OK||$ABORT|+MCONN\: 3||AT+MCONN?|OK|AT+MCONN=3|OK|AT+MRST|OK|\pAT|OK]]>
</script>

<script name="setpin">
<![CDATA[$ABORT|ERROR|$ENDLINE|\r|$TIMEOUT|10||AT|OK|AT+CMEE=2|OK||$REPORT|M107#Checking SIM card|$ABORT|SIM busy:READY|$WAIT|5||AT+CPIN?|+CPIN\:||SIM PIN||OK-AT-OK||$TIMEOUT|30|$REPORT|M108#Entering PIN|$ABORT|||\pAT+CPIN="[$$cell.pin$$]"|OK:ERROR||$ABORT|#---#:READY||AT+CPIN?|+CPIN\:||SIM||$REPORT|E101#Wrong PIN|]]>
</script>

<script name="setgprs">
<![CDATA[$ABORT||$TIMEOUT|10|$REPORT|M101#Registering||AT+CMEE=0|OK|ATH|OK:ERROR|AT+CREG=0|OK|AT+CGREG=0|OK||$ABORT|ERROR|$TIMEOUT|300||AT+COPS=[$$cell.3g.enable$$]|OK||$TIMEOUT|10||AT+WS46?|12:22:25||OK]]>
</script>

<script name="setppp">
<![CDATA[$ABORT|99,99|$TIMEOUT|10||AT+CREG?|+CREG\:||[$$cell.roam$$]||OK|AT+CSQ|+CSQ\:||OK|AT+CSQ|+CSQ\:||$9,||OK|AT+COPS?|+COPS\:||,"||[$$cell.op.name$$]"||OK|AT+CGDCONT=1,"IP","[$$cell.gprs.apn$$]"|OK||$ABORT|NO CARRIER:BUSY:NO ANSWER:ERROR|$REPORT|M102#Dialing||ATD[$$cell.gprs.dial$$]|$TIMEOUT|400|CONNECT||]]>
</script>

<script name="setgsm">
<![CDATA[$ABORT||$TIMEOUT|10|$REPORT|M101#Registering||AT+CMEE=0|OK|ATH|OK:ERROR|AT+CREG=0|OK||$ABORT|ERROR|$TIMEOUT|300||AT+COPS=,0,,0|OK||$TIMEOUT|10||AT+WS46?|12||OK|AT+CSQ|+CSQ\:||$9,||OK|AT+COPS?|+COPS\:||,"||[$$cell.op.name$$]"||OK|]]>
</script>

<script name="setgsmm">
<![CDATA[$ABORT|99,99|$TIMEOUT|10||AT+CREG?|+CREG\:||[$$cell.roam$$]||OK|AT+CSQ|+CSQ\:||OK|AT+CSQ|+CSQ\:||$9,||OK|AT+COPS?|+COPS\:||,"||[$$cell.op.name$$]"||OK|AT+CBST=7|OK|AT+CBST=[$$cell.csd.cbst$$]|OK:ERROR||$ABORT|NO CARRIER:BUSY:NO ANSWER:ERROR|$REPORT|M102#Dialing||ATD[$$cell.csd.dial$$]|$TIMEOUT|400|CONNECT||]]>
</script>

<script name="setgsms">
<![CDATA[$ABORT|CONNECT:NO CARRIER:99,99|$TIMEOUT|10||AT+CREG?|+CREG\:||[$$cell.roam$$]||OK|AT+CSQ|+CSQ\:||OK|AT+CSQ|+CSQ\:||$9,||OK|AT+COPS?|+COPS\:||,"||[$$cell.op.name$$]"||OK|ATS0=2|OK||$TIMEOUT|3000|$REPORT|M103#Awaiting call|RING|ATA|$TIMEOUT|200|CONNECT||]]>
</script>

<script name="hangup">
<![CDATA[$ABORT|Topcon:Error|$TIMEOUT|20||\p+++\p\p|OK-AT-OK|ATI|OK:ERROR|ATH|OK:ERROR|ATS0=0|OK|]]>
</script>

<script name="touhf">
<![CDATA[$ABORT||$TIMEOUT|20|$DAISY|OFF|$REPORT|M106#Configuring modem||dm\r\n\p%%|RE002%%|%%set,/par[$$dev.port$$]/rate,[$$radio.rate$$]|RE|%%set,/par[$$dev.port$$]/rtscts,off|RE||$ABORT|%1%||%[$$cell.offmode$$]%|RE||%0%:%%||$ABORT||$DAISY|[$$dev.port$$]|$TIMEOUT|15||++++|OK-++++-OK-++++-OK|ati|Topcon|%GSM1%set,modem/fh/gsmmode,0|%GSM1%||OK-%GSM2%set,modem/uhf/gsmmode,0-OK|\pato|OK||$WAIT|10|$DAISY|OFF]]>
</script>

<script name="rungsm">
<![CDATA[$TIMEOUT|[$$cell.csd.idle$$]|$ABORT|NO CARRIER:ERROR:RING]]>
</script>

<script name="runppp">
<![CDATA[[$$dev.port$$]|[$$radio.rate$$]|[$$ppp.ip$$]:192.168.255.1|novj|novjccomp|lcp-echo-interval:15|lcp-echo-failure:2|lcp-restart:5|ipcp-accept-local|ipcp-accept-remote|ipcp-max-failure:3|ipcp-max-configure:10|usepeerdns|noipdefault|noproxyarp|idle:[$$ppp.idle$$]|name:[$$ppp.name$$]|password:[$$ppp.password$$]]]>
</script>

<script name="error">
<![CDATA[$ABORT||$WAIT|10|]]>
</script>

<script name="resetgsm">
<![CDATA[$ABORT|Topcon:Error|$TIMEOUT|60||\p+++\p\p|OK-AT-OK||$TIMEOUT|10||ATI|OK:ERROR|AT+CGMI|Motorola||OK]]>
</script>

<script name="simreset">
<![CDATA[$ABORT|AT+MRST:SIM PIN|$TIMEOUT|20||AT+CPIN?|SIM busy-AT+MGSMSIM?-MGSMSIM\: 0|AT+CPIN?|SIM busy-AT+MGSMSIM=1-OK|ATE1|OK|AT+CPIN?|SIM busy-AT+MRST-OK|AT+MGSMSIM=0|OK|\pAT+MRST|OK]]>
</script>

</scripts-list>

<vars-list>
<var name="dev.port" type="enum" default="3">
<ui>Port</ui>
<description>Name of hardware serial port that is connected to modem</description>
<enum_list>
	<enum index="1">
		<value>/dev/ser/a</value>
	</enum>
	<enum index="2">
		<value>/dev/ser/b</value>
	</enum>
	<enum index="3">
		<value>/dev/ser/c</value>
	</enum>
	<enum index="4">
		<value>/dev/ser/d</value>
	</enum>
</enum_list>
</var>

<var name="radio.rate" type="enum" default="6">
<ui>Baud Rate</ui>
<description>Baud rate of modem serial interface</description>
<enum_list>
	<enum index="1">
		<value>1200</value>
	</enum>
	<enum index="2">
		<value>2400</value>
	</enum>
	<enum index="3">
		<value>4800</value>
	</enum>
	<enum index="4">
		<value>9600</value>
	</enum>
	<enum index="5">
		<value>19200</value>
	</enum>
	<enum index="6">
		<value>38400</value>
	</enum>
	<enum index="7">
		<value>57600</value>
	</enum>
	<enum index="8">
		<value>115200</value>
	</enum>
</enum_list>
</var>

<var name="cell.pin" type="string" default="0000">
<ui>PIN Code</ui>
<description>SIM PIN code</description>
<uvar>0</uvar>
</var>

<var name="cell.gprs.dial" type="string" default="*99***1#">
<ui>GPRS Dial</ui>
<description>GPRS Dial Number</description>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="cell.gprs.apn" type="string" default="">
<ui>APN</ui>
<description>GPRS APN</description>
<uvar>1</uvar>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="ppp.name" type="string" default="">
<ui>User</ui>
<description>GPRS User Name</description>
<uvar>2</uvar>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="ppp.password" type="string" default="">
<ui>Password</ui>
<description>GPRS Password</description>
<uvar>3</uvar>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="ppp.ip" type="string" default="">
<ui>IP address</ui>
<description>Static PPP address</description>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="ppp.idle" type="numeric" default="0">
<ui>Timeout</ui>
<description>GPRS Reconnection Timeout if datalink is lost</description>
<range min="0" max="9999">
<uifactor>0.1</uifactor>
</range>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="cell.roam" type="enum" default="1">
<ui>Roaming</ui>
<description>Allow network roaming</description>
<profiles>
	<name>internet</name>
	<name>c-master</name>
	<name>c-slave</name>
</profiles>
<enum_list>
	<enum index="1">
		<value>,1:,5</value>
		<ui>Enabled</ui>
	</enum>
	<enum index="2">
		<value>,1</value>
		<ui>Disabled</ui>
	</enum>
</enum_list>
</var>

<var name="cell.csd.cbst" type="enum" default="1">
<ui>Data Call Type</ui>
<description>Bearer type for outgoing and incoming data calls</description>
<uvar>6</uvar>
<profiles>
	<name>c-master</name>
	<name>c-slave</name>
</profiles>
<enum_list>
	<enum index="1">
		<value>0</value>
		<ui>Automatic</ui>
	</enum>
	<enum index="2">
		<value>7</value>
		<ui>Analog V.32</ui>
	</enum>
	<enum index="3">
		<value>71</value>
		<ui>Digital V.110</ui>
	</enum>
</enum_list>
</var>

<var name="cell.csd.dial" type="string" default="">
<ui>Dial Number</ui>
<description>CSD Base Phone Number</description>
<uvar>5</uvar>
<profiles>
	<name>c-master</name>
</profiles>
</var>

<var name="cell.csd.idle" type="numeric" default="300">
<ui>CSD Timeout</ui>
<description>Hangup CSD if no data is received within timeout threshold</description>
<range min="0" max="9999">
<uifactor>0.1</uifactor>
</range>
<profiles>
	<name>c-master</name>
	<name>c-slave</name>
</profiles>
</var>

<var name="cell.3g.enable" type="enum" default="1">
<ui>3G Mode</ui>
<description>Use 3G technology for Internet access</description>
<enum_list>
	<enum index="1">
		<value>0,0,,</value>
		<ui>Automatic</ui>
	</enum>
	<enum index="2">
		<value>,0,,0</value>
		<ui>2G only</ui>
	</enum>
	<enum index="3">
		<value>,0,,2</value>
		<ui>3G only</ui>
	</enum>
</enum_list>
</var>

<var name="cell.op.name" type="string" default="">
<ui>Cellular Operator Name</ui>
<description>Operator Name (read only)</description>
<uvar>7</uvar>
</var>

<var name="cell.offmode" type="string" default="0">
<ui>Keep Cellular Powered</ui>
<description>Flag to Keep cellular module powered when turning profile off</description>
<uvar>8</uvar>
</var>

<var name="cell.sq" type="string" default="">
<ui>Cellular Signal Quality</ui>
<description>Signal Quality (read only)</description>
<uvar>9</uvar>
</var>

</vars-list>
</template>

<template name="Topcon|FH915+;Motorola|C24">
<id>[$$dev.port$$];Topcon|FH915+@[$$radio.rate$$];Motorola|C24@[$$radio.rate$$]</id>
<version>1.2</version>
<description>TPS FH915+ Modem with Motorola C24 CDMA module</description>
<compat-version>1</compat-version>

<profiles-list>
<profile name="internet">
	<description>Connect to Internet using CDMA modem</description>
	<block id="1" type="script" script="checkmod">
		<branch from="0" to="0" id="3"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="2">
			<try times="1" id="1"></try></branch>
	</block>
	<block id="2" type="script" script="tocdma">
		<branch from="0" to="0" id="3"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="2"></branch>
	</block>
	<block id="3" type="script" script="initcdma">
		<branch from="0" to="0" id="4"></branch>

		<branch from="1" to="1" id="7"></branch>

		<branch from="2" to="15" id="2">
			<try times="30" id="3"></try></branch>
	</block>
	<block id="4" type="script" script="setcdma">
		<branch from="0" to="0" id="5"></branch>

		<branch from="1" to="1" id="7"></branch>

		<branch from="2" to="15" id="3">
			<try times="10" id="4"></try></branch>
	</block>
	<block id="5" type="script" script="setppp">
		<branch from="0" to="0" id="6"></branch>

		<branch from="1" to="1" id="7"></branch>

		<branch from="2" to="15" id="4">
			<try times="30" id="5"></try></branch>
	</block>
	<block id="6" type="ppp" script="runppp">
		<branch from="0" to="0" id="5"></branch>

		<branch from="1" to="1" id="7"></branch>

		<branch from="2" to="15" id="5"></branch>
	</block>
	<block id="7" type="script" script="hangup">
		<branch from="0" to="1" id="8"></branch>

		<branch from="2" to="2" id="8">
			<try times="5" id="7"></try></branch>
		<branch from="3" to="15" id="8"></branch>
	</block>
	<block id="8" type="script" script="touhf">
		<branch from="0" to="0" id="0"></branch>
		<branch from="2" to="2" id="0">
			<try times="5" id="8"></try></branch>
		<branch from="3" to="3" id="0"></branch>
		<branch from="4" to="15" id="0">
			<try times="5" id="8"></try></branch>
	</block>
</profile>

</profiles-list>

<scripts-list>
<script name="checkmod">
<![CDATA[$ABORT||$ENDLINE|\r|$TIMEOUT|15|$REPORT|M105#Looking for modem|$DAISY|OFF||dm\r\n\p%%|RE002%%|%%dm,[$$dev.port$$]|RE|%%set,/par[$$dev.port$$]/rate,[$$radio.rate$$]|RE||$DAISY|[$$dev.port$$]|$TIMEOUT|10||AT|OK-AT-OK-AT-OK]]>
</script>

<script name="tocdma">
<![CDATA[$ABORT||$ENDLINE|\r|$TIMEOUT|15|$DAISY|OFF||dm\r\n\p%%|RE002%%|%%dm,[$$dev.port$$]|RE||$REPORT|M106#Configuring modem||%%set,/par[$$dev.port$$]/rtscts,off|RE|%%set,/par[$$dev.port$$]/rts,on|RE|%%set,/par[$$dev.port$$]/rate,[$$radio.rate$$]|RE||$DAISY|[$$dev.port$$]|$TIMEOUT|15||++++|OK-++++-OK-++++-OK|ati|Topcon|%GSM1%set,modem/fh/gsmmode,3|%GSM1%||OK-%GSM2%set,modem/uhf/gsmmode,3-OK|\pato|OK||$WAIT|10|$DAISY|OFF||dm\r\n\p%%|RE002%%|%%set,/par[$$dev.port$$]/rate,[$$radio.rate$$]|RE|%%set,/par[$$dev.port$$]/rtscts,on|RE||$DAISY|[$$dev.port$$]|]]>
</script>

<script name="initcdma">
<![CDATA[$ABORT|ERROR|$ENDLINE|\r|$TIMEOUT|10||AT|OK||$TIMEOUT|20|$REPORT|M106#Configuring modem||ATV1&D0|OK|ATE0S0=0|OK|AT+CMEE=0|OK]]>
</script>

<script name="setcdma">
<![CDATA[$ABORT||$TIMEOUT|10|$REPORT|M101#Registering||ATH|OK:ERROR|AT+CREG=0|OK|]]>
</script>

<script name="setppp">
<![CDATA[$ABORT||$TIMEOUT|10||AT+CREG?|+CREG\:||,||,||[$$cell.roam$$]||OK|AT+CSQ|+CSQ\:||$9,||OK||$ABORT|NO CARRIER:BUSY:NO ANSWER:ERROR|$REPORT|M102#Dialing||ATD[$$cell.cdma.dial$$]|$TIMEOUT|400|CONNECT||]]>
</script>

<script name="hangup">
<![CDATA[$ABORT|Topcon:Error|$TIMEOUT|20||\p+++\p\p|OK-AT-OK|ATI|OK:ERROR|ATH|OK:ERROR|ATS0=0|OK|]]>
</script>

<script name="touhf">
<![CDATA[$ABORT||$TIMEOUT|20|$DAISY|OFF|$REPORT|M106#Configuring modem||dm\r\n\p%%|RE002%%|%%set,/par[$$dev.port$$]/rate,[$$radio.rate$$]|RE|%%set,/par[$$dev.port$$]/rtscts,off|RE||$ABORT|%1%||%[$$cell.offmode$$]%|RE||%0%:%%||$ABORT||$DAISY|[$$dev.port$$]|$TIMEOUT|15||++++|OK-++++-OK-++++-OK|ati|Topcon|%GSM1%set,modem/fh/gsmmode,0|%GSM1%||OK-%GSM2%set,modem/uhf/gsmmode,0-OK|\pato|OK||$WAIT|10|$DAISY|OFF]]>
</script>

<script name="runppp">
<![CDATA[[$$dev.port$$]|[$$radio.rate$$]|[$$ppp.ip$$]|novj|novjccomp|lcp-echo-interval:15|lcp-echo-failure:3|lcp-restart:5|ipcp-accept-local|ipcp-accept-remote|ipcp-max-failure:3|ipcp-max-configure:10|usepeerdns|noipdefault|noproxyarp|idle:[$$ppp.idle$$]|name:[$$ppp.name$$]|password:[$$ppp.password$$]]]>
</script>

</scripts-list>

<vars-list>
<var name="dev.port" type="enum" default="3">
<ui>Port</ui>
<description>Name of hardware serial port that is connected to modem</description>
<enum_list>
	<enum index="1">
		<value>/dev/ser/a</value>
	</enum>
	<enum index="2">
		<value>/dev/ser/b</value>
	</enum>
	<enum index="3">
		<value>/dev/ser/c</value>
	</enum>
	<enum index="4">
		<value>/dev/ser/d</value>
	</enum>
</enum_list>
</var>

<var name="radio.rate" type="enum" default="6">
<ui>Baud Rate</ui>
<description>Baud rate of modem serial interface</description>
<enum_list>
	<enum index="1">
		<value>1200</value>
	</enum>
	<enum index="2">
		<value>2400</value>
	</enum>
	<enum index="3">
		<value>4800</value>
	</enum>
	<enum index="4">
		<value>9600</value>
	</enum>
	<enum index="5">
		<value>19200</value>
	</enum>
	<enum index="6">
		<value>38400</value>
	</enum>
	<enum index="7">
		<value>57600</value>
	</enum>
	<enum index="8">
		<value>115200</value>
	</enum>
</enum_list>
</var>

<var name="cell.cdma.dial" type="string" default="#777">
<ui>CDMA Dial</ui>
<description>CDMA Dial Number</description>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="ppp.name" type="string" default="">
<ui>User</ui>
<description>CDMA User Name</description>
<uvar>2</uvar>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="ppp.password" type="string" default="">
<ui>Password</ui>
<description>CDMA Password</description>
<uvar>3</uvar>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="ppp.ip" type="string" default="">
<ui>IP address</ui>
<description>Static PPP address</description>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="ppp.idle" type="numeric" default="0">
<ui>Timeout</ui>
<description>PPP Reconnection Timeout if datalink is lost</description>
<range min="0" max="9999">
<uifactor>0.1</uifactor>
</range>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="cell.roam" type="enum" default="1">
<ui>Roaming</ui>
<description>Allow network roaming</description>
<profiles>
	<name>internet</name>
</profiles>
<enum_list>
	<enum index="1">
		<value>,1:,5</value>
		<ui>Enabled</ui>
	</enum>
	<enum index="2">
		<value>,1</value>
		<ui>Disabled</ui>
	</enum>
</enum_list>
</var>

<var name="cell.offmode" type="string" default="0">
<ui>Keep Cellular Powered</ui>
<description>Flag to Keep cellular module powered when turning profile off</description>
<uvar>8</uvar>
</var>

<var name="cell.sq" type="string" default="">
<ui>Cellular Signal Quality</ui>
<description>Signal Quality (read only)</description>
<uvar>9</uvar>
</var>

</vars-list>
</template>

<template name="ArWest|AW401;Motorola|C24">
<id>[$$dev.port$$];ArWest|AW401@[$$radio.rate$$];Motorola|C24@[$$cell.rate$$]</id>
<version>1.2</version>
<description>Digital UHF modem with Motorola C24 CDMA module</description>
<compat-version>1</compat-version>

<profiles-list>
<profile name="internet">
	<description>Connect to Internet using CDMA modem</description>
	<block id="1" type="script" script="checkmod">
		<branch from="0" to="0" id="3"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="2">
			<try times="1" id="1"></try></branch>
	</block>
	<block id="2" type="script" script="tocdma">
		<branch from="0" to="0" id="3"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="2"></branch>
	</block>
	<block id="3" type="script" script="initcdma">
		<branch from="0" to="0" id="4"></branch>

		<branch from="1" to="1" id="7"></branch>

		<branch from="2" to="15" id="2">
			<try times="30" id="3"></try></branch>
	</block>
	<block id="4" type="script" script="setcdma">
		<branch from="0" to="0" id="5"></branch>

		<branch from="1" to="1" id="7"></branch>

		<branch from="2" to="15" id="3">
			<try times="10" id="4"></try></branch>
	</block>
	<block id="5" type="script" script="setppp">
		<branch from="0" to="0" id="6"></branch>

		<branch from="1" to="1" id="7"></branch>

		<branch from="2" to="15" id="4">
			<try times="30" id="5"></try></branch>
	</block>
	<block id="6" type="ppp" script="runppp">
		<branch from="0" to="0" id="5"></branch>

		<branch from="1" to="1" id="7"></branch>

		<branch from="2" to="15" id="5"></branch>
	</block>
	<block id="7" type="script" script="hangup">
		<branch from="0" to="1" id="8"></branch>

		<branch from="2" to="2" id="8">
			<try times="5" id="7"></try></branch>
		<branch from="3" to="15" id="8"></branch>
	</block>
	<block id="8" type="script" script="touhf">
		<branch from="0" to="0" id="0"></branch>
		<branch from="2" to="2" id="0">
			<try times="5" id="8"></try></branch>
		<branch from="3" to="3" id="0"></branch>
		<branch from="4" to="15" id="0">
			<try times="5" id="8"></try></branch>
	</block>
</profile>

</profiles-list>

<scripts-list>
<script name="checkmod">
<![CDATA[$ABORT||$ENDLINE|\r|$TIMEOUT|15|$REPORT|M105#Looking for modem|$DAISY|OFF||dm\r\n\p%%|RE002%%|%%dm,[$$dev.port$$]|RE|%%set,/par[$$dev.port$$]/rate,[$$cell.rate$$]|RE|%%set,/par[$$dev.port$$]/rtscts,off|RE|%%set,/par[$$dev.port$$]/rts,on|RE||$DAISY|[$$dev.port$$]|$TIMEOUT|10||AT|OK-AT-OK-AT-OK]]>
</script>

<script name="tocdma">
<![CDATA[$ABORT||$ENDLINE|\r|$TIMEOUT|15|$DAISY|OFF||dm\r\n\p%%|RE002%%|%%dm,[$$dev.port$$]|RE||$REPORT|M106#Configuring modem||%%set,/par[$$dev.port$$]/rate,[$$radio.rate$$]|RE|%%set,/par[$$dev.port$$]/rtscts,off|RE||$DAISY|[$$dev.port$$]|$TIMEOUT|15||++++\p|@00-++++-@01|ATI|Topcon||@00|\p\pLINK RFSW 1|@00|\p\pDATAMODE|$WAIT|20|$DAISY|OFF||dm\r\n\p%%|RE002%%|%%set,/par[$$dev.port$$]/rate,[$$cell.rate$$]|RE|%%set,/par[$$dev.port$$]/rtscts,off|RE|%%set,/par[$$dev.port$$]/rts,on|RE||$DAISY|[$$dev.port$$]|]]>
</script>

<script name="initcdma">
<![CDATA[$ABORT|ERROR|$ENDLINE|\r|$TIMEOUT|10||AT|OK||$TIMEOUT|20|$REPORT|M106#Configuring modem||ATV1&D0|OK|ATE0S0=0|OK|AT+CMEE=0|OK]]>
</script>

<script name="setcdma">
<![CDATA[$ABORT||$TIMEOUT|10|$REPORT|M101#Registering||\p+++\p\pATH|OK:ERROR|AT+CREG=0|OK|]]>
</script>

<script name="setppp">
<![CDATA[$ABORT||$TIMEOUT|10||AT+CREG?|+CREG\:||,||,||[$$cell.roam$$]||OK|AT+CSQ|+CSQ\:||$9,||OK||$ABORT|NO CARRIER:BUSY:NO ANSWER:ERROR|$REPORT|M102#Dialing||ATD[$$cell.cdma.dial$$]|$TIMEOUT|400|CONNECT||]]>
</script>

<script name="hangup">
<![CDATA[$ABORT||$TIMEOUT|20||\p+++\p\p|OK-+++AT\p\p-OK-ATH-OK:ERROR|ATH|OK:ERROR|ATS0=0|OK|]]>
</script>

<script name="touhf">
<![CDATA[$ABORT||$TIMEOUT|20|$DAISY|OFF|$REPORT|M106#Configuring modem||dm\r\n\p%%|RE002%%|%%set,/par[$$dev.port$$]/rate,[$$radio.rate$$]|RE|%%set,/par[$$dev.port$$]/rtscts,off|RE||$ABORT|%1%||%[$$cell.offmode$$]%|RE||%0%:%%||$ABORT||$DAISY|[$$dev.port$$]|$TIMEOUT|15||++++\p|@00-++++-@01|ATI|Topcon||@00|LINK RFSW 0|@00|\p\pDATAMODE|$WAIT|20|$DAISY|OFF]]>
</script>

<script name="runppp">
<![CDATA[[$$dev.port$$]|[$$cell.rate$$]|[$$ppp.ip$$]|novj|novjccomp|lcp-echo-interval:15|lcp-echo-failure:3|lcp-restart:5|ipcp-accept-local|ipcp-accept-remote|ipcp-max-failure:3|ipcp-max-configure:10|usepeerdns|noipdefault|noproxyarp|idle:[$$ppp.idle$$]|name:[$$ppp.name$$]|password:[$$ppp.password$$]]]>
</script>

</scripts-list>

<vars-list>
<var name="dev.port" type="enum" default="3">
<ui>Port</ui>
<description>Name of hardware serial port that is connected to modem</description>
<enum_list>
	<enum index="1">
		<value>/dev/ser/a</value>
	</enum>
	<enum index="2">
		<value>/dev/ser/b</value>
	</enum>
	<enum index="3">
		<value>/dev/ser/c</value>
	</enum>
	<enum index="4">
		<value>/dev/ser/d</value>
	</enum>
</enum_list>
</var>

<var name="radio.rate" type="enum" default="6">
<ui>Baud Rate</ui>
<description>Baud rate of modem serial interface</description>
<enum_list>
	<enum index="1">
		<value>1200</value>
	</enum>
	<enum index="2">
		<value>2400</value>
	</enum>
	<enum index="3">
		<value>4800</value>
	</enum>
	<enum index="4">
		<value>9600</value>
	</enum>
	<enum index="5">
		<value>19200</value>
	</enum>
	<enum index="6">
		<value>38400</value>
	</enum>
	<enum index="7">
		<value>57600</value>
	</enum>
	<enum index="8">
		<value>115200</value>
	</enum>
</enum_list>
</var>

<var name="cell.rate" type="enum" default="6">
<ui>Baud Rate</ui>
<description>Baud rate of cellular module</description>
<enum_list>
	<enum index="1">
		<value>1200</value>
	</enum>
	<enum index="2">
		<value>2400</value>
	</enum>
	<enum index="3">
		<value>4800</value>
	</enum>
	<enum index="4">
		<value>9600</value>
	</enum>
	<enum index="5">
		<value>19200</value>
	</enum>
	<enum index="6">
		<value>38400</value>
	</enum>
	<enum index="7">
		<value>57600</value>
	</enum>
	<enum index="8">
		<value>115200</value>
	</enum>
</enum_list>
</var>

<var name="cell.cdma.dial" type="string" default="#777">
<ui>CDMA Dial</ui>
<description>CDMA Dial Number</description>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="ppp.name" type="string" default="">
<ui>User</ui>
<description>CDMA User Name</description>
<uvar>2</uvar>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="ppp.password" type="string" default="">
<ui>Password</ui>
<description>CDMA Password</description>
<uvar>3</uvar>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="ppp.ip" type="string" default="">
<ui>IP address</ui>
<description>Static PPP address</description>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="ppp.idle" type="numeric" default="0">
<ui>Timeout</ui>
<description>PPP Reconnection Timeout if datalink is lost</description>
<range min="0" max="9999">
<uifactor>0.1</uifactor>
</range>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="cell.roam" type="enum" default="1">
<ui>Roaming</ui>
<description>Allow network roaming</description>
<profiles>
	<name>internet</name>
</profiles>
<enum_list>
	<enum index="1">
		<value>,1:,5</value>
		<ui>Enabled</ui>
	</enum>
	<enum index="2">
		<value>,1</value>
		<ui>Disabled</ui>
	</enum>
</enum_list>
</var>

<var name="cell.offmode" type="string" default="0">
<ui>Keep Cellular Powered</ui>
<description>Flag to Keep cellular module powered when turning profile off</description>
<uvar>8</uvar>
</var>

<var name="cell.sq" type="string" default="">
<ui>Cellular Signal Quality</ui>
<description>Signal Quality (read only)</description>
<uvar>9</uvar>
</var>

</vars-list>
</template>

<template name="ArWest|AW401;Wavecom|Q24/C">
<id>[$$dev.port$$];ArWest|AW401@[$$radio.rate$$];Wavecom|Q24/C@[$$cell.rate$$]</id>
<version>1.2</version>
<description>Digital UHF modem with Wavecom Q24 CDMA module</description>
<compat-version>1</compat-version>

<profiles-list>
<profile name="internet">
	<description>Connect to Internet using CDMA modem</description>
	<block id="1" type="script" script="checkmod">
		<branch from="0" to="0" id="3"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="2">
			<try times="1" id="1"></try></branch>
	</block>
	<block id="2" type="script" script="tocdma">
		<branch from="0" to="0" id="3"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="2"></branch>
	</block>
	<block id="3" type="script" script="initcdma">
		<branch from="0" to="0" id="4"></branch>

		<branch from="1" to="1" id="7"></branch>

		<branch from="2" to="15" id="2">
			<try times="30" id="3"></try></branch>
	</block>
	<block id="4" type="script" script="setcdma">
		<branch from="0" to="0" id="5"></branch>

		<branch from="1" to="1" id="7"></branch>

		<branch from="2" to="15" id="3">
			<try times="10" id="4"></try></branch>
	</block>
	<block id="5" type="script" script="setppp">
		<branch from="0" to="0" id="6"></branch>

		<branch from="1" to="1" id="7"></branch>

		<branch from="2" to="15" id="4">
			<try times="30" id="5"></try></branch>
	</block>
	<block id="6" type="ppp" script="runppp">
		<branch from="0" to="0" id="5"></branch>

		<branch from="1" to="1" id="7"></branch>

		<branch from="2" to="15" id="5"></branch>
	</block>
	<block id="7" type="script" script="hangup">
		<branch from="0" to="1" id="8"></branch>

		<branch from="2" to="2" id="8">
			<try times="5" id="7"></try></branch>
		<branch from="3" to="15" id="8"></branch>
	</block>
	<block id="8" type="script" script="touhf">
		<branch from="0" to="0" id="0"></branch>
		<branch from="2" to="2" id="0">
			<try times="5" id="8"></try></branch>
		<branch from="3" to="3" id="0"></branch>
		<branch from="4" to="15" id="0">
			<try times="5" id="8"></try></branch>
	</block>
</profile>

</profiles-list>

<scripts-list>
<script name="checkmod">
<![CDATA[$ABORT||$ENDLINE|\r|$TIMEOUT|15|$REPORT|M105#Looking for modem|$DAISY|OFF||dm\r\n\p%%|RE002%%|%%dm,[$$dev.port$$]|RE|%%set,/par[$$dev.port$$]/rate,[$$cell.rate$$]|RE||$DAISY|[$$dev.port$$]|$TIMEOUT|10||AT|OK-AT-OK-AT-OK]]>
</script>

<script name="tocdma">
<![CDATA[$ABORT||$ENDLINE|\r|$TIMEOUT|15|$DAISY|OFF||dm\r\n\p%%|RE002%%|%%dm,[$$dev.port$$]|RE||$REPORT|M106#Configuring modem||%%set,/par[$$dev.port$$]/rate,[$$radio.rate$$]|RE|%%set,/par[$$dev.port$$]/rtscts,off|RE||$DAISY|[$$dev.port$$]|$TIMEOUT|15||++++\p|@00-++++-@01|ATI|Topcon||@00|LINK RFSW 1|@00|\p\pDATAMODE|$WAIT|10|$DAISY|OFF||dm\r\n\p%%|RE002%%|%%set,/par[$$dev.port$$]/rate,[$$cell.rate$$]|RE|%%set,/par[$$dev.port$$]/rtscts,on|RE||$DAISY|[$$dev.port$$]|]]>
</script>

<script name="initcdma">
<![CDATA[$ABORT|ERROR|$ENDLINE|\r|$TIMEOUT|10||AT|OK||$TIMEOUT|20|$REPORT|M106#Configuring modem||ATV1&D0|OK|ATE0S0=0|OK|AT+CMEE=0|OK]]>
</script>

<script name="setcdma">
<![CDATA[$ABORT||$TIMEOUT|10|$REPORT|M101#Registering||\p+++\p\pATH|OK:ERROR|AT+CREG=0|OK|]]>
</script>

<script name="setppp">
<![CDATA[$ABORT||$TIMEOUT|10||AT+CREG?|+CREG\:||[$$cell.roam$$]||OK|AT+CSQ|+CSQ\:||$9,||OK||$ABORT|NO CARRIER:BUSY:NO ANSWER:ERROR|$REPORT|M102#Dialing||ATD[$$cell.cdma.dial$$]|$TIMEOUT|400|CONNECT||]]>
</script>

<script name="hangup">
<![CDATA[$ABORT||$TIMEOUT|20||\p+++\p\p|OK-+++AT\p\p-OK-ATH-OK:ERROR|ATH|OK:ERROR|ATS0=0|OK|]]>
</script>

<script name="touhf">
<![CDATA[$ABORT||$TIMEOUT|20|$DAISY|OFF|$REPORT|M106#Configuring modem||dm\r\n\p%%|RE002%%|%%set,/par[$$dev.port$$]/rate,[$$radio.rate$$]|RE|%%set,/par[$$dev.port$$]/rtscts,off|RE||$ABORT|%1%||%[$$cell.offmode$$]%|RE||%0%:%%||$ABORT||$DAISY|[$$dev.port$$]|$TIMEOUT|15||++++\p|@00-++++-@01|ATI|Topcon||@00|LINK RFSW 0|@00|\p\pDATAMODE|$WAIT|10|$DAISY|OFF]]>
</script>

<script name="runppp">
<![CDATA[[$$dev.port$$]|[$$cell.rate$$]|[$$ppp.ip$$]|novj|novjccomp|lcp-echo-interval:0|lcp-echo-failure:0|default-asyncmap|lcp-restart:5|ipcp-accept-local|ipcp-accept-remote|ipcp-max-failure:3|ipcp-max-configure:10|usepeerdns|noipdefault|noproxyarp|idle:[$$ppp.idle$$]|name:[$$ppp.name$$]|password:[$$ppp.password$$]]]>
</script>

</scripts-list>

<vars-list>
<var name="dev.port" type="enum" default="3">
<ui>Port</ui>
<description>Name of hardware serial port that is connected to modem</description>
<enum_list>
	<enum index="1">
		<value>/dev/ser/a</value>
	</enum>
	<enum index="2">
		<value>/dev/ser/b</value>
	</enum>
	<enum index="3">
		<value>/dev/ser/c</value>
	</enum>
	<enum index="4">
		<value>/dev/ser/d</value>
	</enum>
</enum_list>
</var>

<var name="radio.rate" type="enum" default="6">
<ui>Baud Rate</ui>
<description>Baud rate of modem serial interface</description>
<enum_list>
	<enum index="1">
		<value>1200</value>
	</enum>
	<enum index="2">
		<value>2400</value>
	</enum>
	<enum index="3">
		<value>4800</value>
	</enum>
	<enum index="4">
		<value>9600</value>
	</enum>
	<enum index="5">
		<value>19200</value>
	</enum>
	<enum index="6">
		<value>38400</value>
	</enum>
	<enum index="7">
		<value>57600</value>
	</enum>
	<enum index="8">
		<value>115200</value>
	</enum>
</enum_list>
</var>

<var name="cell.rate" type="enum" default="6">
<ui>Baud Rate</ui>
<description>Baud rate of cellular module</description>
<enum_list>
	<enum index="1">
		<value>1200</value>
	</enum>
	<enum index="2">
		<value>2400</value>
	</enum>
	<enum index="3">
		<value>4800</value>
	</enum>
	<enum index="4">
		<value>9600</value>
	</enum>
	<enum index="5">
		<value>19200</value>
	</enum>
	<enum index="6">
		<value>38400</value>
	</enum>
	<enum index="7">
		<value>57600</value>
	</enum>
	<enum index="8">
		<value>115200</value>
	</enum>
</enum_list>
</var>

<var name="cell.cdma.dial" type="string" default="#777">
<ui>CDMA Dial</ui>
<description>CDMA Dial Number</description>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="ppp.name" type="string" default="">
<ui>User</ui>
<description>CDMA User Name</description>
<uvar>2</uvar>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="ppp.password" type="string" default="">
<ui>Password</ui>
<description>CDMA Password</description>
<uvar>3</uvar>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="ppp.ip" type="string" default="">
<ui>IP address</ui>
<description>Static PPP address</description>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="ppp.idle" type="numeric" default="0">
<ui>Timeout</ui>
<description>PPP Reconnection Timeout if datalink is lost</description>
<range min="0" max="9999">
<uifactor>0.1</uifactor>
</range>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="cell.roam" type="enum" default="1">
<ui>Roaming</ui>
<description>Allow network roaming</description>
<profiles>
	<name>internet</name>
</profiles>
<enum_list>
	<enum index="1">
		<value>,1:,5</value>
		<ui>Enabled</ui>
	</enum>
	<enum index="2">
		<value>,1</value>
		<ui>Disabled</ui>
	</enum>
</enum_list>
</var>

<var name="cell.offmode" type="string" default="0">
<ui>Keep Cellular Powered</ui>
<description>Flag to Keep cellular module powered when turning profile off</description>
<uvar>8</uvar>
</var>

<var name="cell.sq" type="string" default="">
<ui>Cellular Signal Quality</ui>
<description>Signal Quality (read only)</description>
<uvar>9</uvar>
</var>

</vars-list>
</template>

<template name="Topcon|DUHF2;Motorola|C24">
<id>[$$dev.port$$];Topcon|DUHF2@[$$radio.rate$$];Motorola|C24@[$$cell.rate$$]</id>
<version>1.2</version>
<description>Digital UHF 2 modem with Motorola C24 CDMA module</description>
<compat-version>1</compat-version>

<profiles-list>
<profile name="internet">
	<description>Connect to Internet using CDMA modem</description>
	<block id="1" type="script" script="checkmod">
		<branch from="0" to="0" id="3"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="2">
			<try times="1" id="1"></try></branch>
	</block>
	<block id="2" type="script" script="tocdma">
		<branch from="0" to="0" id="3"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="2"></branch>
	</block>
	<block id="3" type="script" script="initcdma">
		<branch from="0" to="0" id="4"></branch>

		<branch from="1" to="1" id="7"></branch>

		<branch from="2" to="15" id="2">
			<try times="30" id="3"></try></branch>
	</block>
	<block id="4" type="script" script="setcdma">
		<branch from="0" to="0" id="5"></branch>

		<branch from="1" to="1" id="7"></branch>

		<branch from="2" to="15" id="3">
			<try times="10" id="4"></try></branch>
	</block>
	<block id="5" type="script" script="setppp">
		<branch from="0" to="0" id="6"></branch>

		<branch from="1" to="1" id="7"></branch>

		<branch from="2" to="15" id="4">
			<try times="30" id="5"></try></branch>
	</block>
	<block id="6" type="ppp" script="runppp">
		<branch from="0" to="0" id="5"></branch>

		<branch from="1" to="1" id="7"></branch>

		<branch from="2" to="15" id="5"></branch>
	</block>
	<block id="7" type="script" script="hangup">
		<branch from="0" to="1" id="8"></branch>

		<branch from="2" to="2" id="8">
			<try times="5" id="7"></try></branch>
		<branch from="3" to="15" id="8"></branch>
	</block>
	<block id="8" type="script" script="touhf">
		<branch from="0" to="0" id="0"></branch>
		<branch from="2" to="2" id="0">
			<try times="5" id="8"></try></branch>
		<branch from="3" to="3" id="0"></branch>
		<branch from="4" to="15" id="0">
			<try times="5" id="8"></try></branch>
	</block>
</profile>

</profiles-list>

<scripts-list>
<script name="checkmod">
<![CDATA[$ABORT||$ENDLINE|\r|$TIMEOUT|15|$REPORT|M105#Looking for modem|$DAISY|OFF||dm\r\n\p%%|RE002%%|%%dm,[$$dev.port$$]|RE|%%set,/par[$$dev.port$$]/rate,[$$cell.rate$$]|RE||$DAISY|[$$dev.port$$]|$TIMEOUT|10||AT|OK-AT-OK-AT-OK]]>
</script>

<script name="tocdma">
<![CDATA[$ABORT||$ENDLINE|\r|$TIMEOUT|15|$DAISY|OFF||dm\r\n\p%%|RE002%%|%%dm,[$$dev.port$$]|RE||$REPORT|M106#Configuring modem||%%set,/par[$$dev.port$$]/rate,[$$radio.rate$$]|RE|%%set,/par[$$dev.port$$]/rtscts,off|RE||$DAISY|[$$dev.port$$]|$TIMEOUT|15||++++\p|@00-++++-@01|ATI|Topcon||@00|LINK RFSW 1|@00|\p\pDATAMODE|$WAIT|10|$DAISY|OFF||dm\r\n\p%%|RE002%%|%%set,/par[$$dev.port$$]/rate,[$$cell.rate$$]|RE|%%set,/par[$$dev.port$$]/rtscts,on|RE||$DAISY|[$$dev.port$$]|]]>
</script>

<script name="initcdma">
<![CDATA[$ABORT|ERROR|$ENDLINE|\r|$TIMEOUT|10||AT|OK||$TIMEOUT|20|$REPORT|M106#Configuring modem||ATV1&D0|OK|ATE0S0=0|OK|AT+CMEE=0|OK]]>
</script>

<script name="setcdma">
<![CDATA[$ABORT||$TIMEOUT|10|$REPORT|M101#Registering||\p+++\p\pATH|OK:ERROR|AT+CREG=0|OK|]]>
</script>

<script name="setppp">
<![CDATA[$ABORT||$TIMEOUT|10||AT+CREG?|+CREG\:||,||,||[$$cell.roam$$]||OK|AT+CSQ|+CSQ\:||$9,||OK||$ABORT|NO CARRIER:BUSY:NO ANSWER:ERROR|$REPORT|M102#Dialing||ATD[$$cell.cdma.dial$$]|$TIMEOUT|400|CONNECT||]]>
</script>

<script name="hangup">
<![CDATA[$ABORT||$TIMEOUT|20||\p+++\p\p|OK-+++AT\p\p-OK-ATH-OK:ERROR|ATH|OK:ERROR|ATS0=0|OK|]]>
</script>

<script name="touhf">
<![CDATA[$ABORT||$TIMEOUT|20|$DAISY|OFF|$REPORT|M106#Configuring modem||dm\r\n\p%%|RE002%%|%%set,/par[$$dev.port$$]/rate,[$$radio.rate$$]|RE|%%set,/par[$$dev.port$$]/rtscts,off|RE||$ABORT|%1%||%[$$cell.offmode$$]%|RE||%0%:%%||$ABORT||$DAISY|[$$dev.port$$]|$TIMEOUT|15||++++\p|@00-++++-@01|ATI|Topcon||@00|LINK RFSW 0|@00|\p\pDATAMODE|$WAIT|10|$DAISY|OFF]]>
</script>

<script name="runppp">
<![CDATA[[$$dev.port$$]|[$$cell.rate$$]|[$$ppp.ip$$]|novj|novjccomp|lcp-echo-interval:15|lcp-echo-failure:3|lcp-restart:5|ipcp-accept-local|ipcp-accept-remote|ipcp-max-failure:3|ipcp-max-configure:10|usepeerdns|noipdefault|noproxyarp|idle:[$$ppp.idle$$]|name:[$$ppp.name$$]|password:[$$ppp.password$$]]]>
</script>

</scripts-list>

<vars-list>
<var name="dev.port" type="enum" default="3">
<ui>Port</ui>
<description>Name of hardware serial port that is connected to modem</description>
<enum_list>
	<enum index="1">
		<value>/dev/ser/a</value>
	</enum>
	<enum index="2">
		<value>/dev/ser/b</value>
	</enum>
	<enum index="3">
		<value>/dev/ser/c</value>
	</enum>
	<enum index="4">
		<value>/dev/ser/d</value>
	</enum>
</enum_list>
</var>

<var name="radio.rate" type="enum" default="6">
<ui>Baud Rate</ui>
<description>Baud rate of modem serial interface</description>
<enum_list>
	<enum index="1">
		<value>1200</value>
	</enum>
	<enum index="2">
		<value>2400</value>
	</enum>
	<enum index="3">
		<value>4800</value>
	</enum>
	<enum index="4">
		<value>9600</value>
	</enum>
	<enum index="5">
		<value>19200</value>
	</enum>
	<enum index="6">
		<value>38400</value>
	</enum>
	<enum index="7">
		<value>57600</value>
	</enum>
	<enum index="8">
		<value>115200</value>
	</enum>
</enum_list>
</var>

<var name="cell.rate" type="enum" default="6">
<ui>Baud Rate</ui>
<description>Baud rate of cellular module</description>
<enum_list>
	<enum index="1">
		<value>1200</value>
	</enum>
	<enum index="2">
		<value>2400</value>
	</enum>
	<enum index="3">
		<value>4800</value>
	</enum>
	<enum index="4">
		<value>9600</value>
	</enum>
	<enum index="5">
		<value>19200</value>
	</enum>
	<enum index="6">
		<value>38400</value>
	</enum>
	<enum index="7">
		<value>57600</value>
	</enum>
	<enum index="8">
		<value>115200</value>
	</enum>
</enum_list>
</var>

<var name="cell.cdma.dial" type="string" default="#777">
<ui>CDMA Dial</ui>
<description>CDMA Dial Number</description>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="ppp.name" type="string" default="">
<ui>User</ui>
<description>CDMA User Name</description>
<uvar>2</uvar>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="ppp.password" type="string" default="">
<ui>Password</ui>
<description>CDMA Password</description>
<uvar>3</uvar>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="ppp.ip" type="string" default="">
<ui>IP address</ui>
<description>Static PPP address</description>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="ppp.idle" type="numeric" default="0">
<ui>Timeout</ui>
<description>PPP Reconnection Timeout if datalink is lost</description>
<range min="0" max="9999">
<uifactor>0.1</uifactor>
</range>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="cell.roam" type="enum" default="1">
<ui>Roaming</ui>
<description>Allow network roaming</description>
<profiles>
	<name>internet</name>
</profiles>
<enum_list>
	<enum index="1">
		<value>,1:,5</value>
		<ui>Enabled</ui>
	</enum>
	<enum index="2">
		<value>,1</value>
		<ui>Disabled</ui>
	</enum>
</enum_list>
</var>

<var name="cell.offmode" type="string" default="0">
<ui>Keep Cellular Powered</ui>
<description>Flag to Keep cellular module powered when turning profile off</description>
<uvar>8</uvar>
</var>

<var name="cell.sq" type="string" default="">
<ui>Cellular Signal Quality</ui>
<description>Signal Quality (read only)</description>
<uvar>9</uvar>
</var>

</vars-list>
</template>

<template name="Topcon|DUHF2;Wavecom|Q24/G">
<id>[$$dev.port$$];Topcon|DUHF2@[$$radio.rate$$];Wavecom|Q24/G@[$$cell.rate$$]</id>
<version>1.3</version>
<description>Digital UHF 2 modem with Wavecom Q24 GSM module</description>
<compat-version>1</compat-version>

<profiles-list>
<profile name="internet">
	<description>Connect to Internet using GPRS by cellular modem</description>
	<block id="1" type="script" script="checkgsm">
		<branch from="0" to="0" id="3"></branch>

		<branch from="1" to="1" id="9"></branch>

		<branch from="2" to="15" id="2">
			<try times="1" id="1"></try></branch>
	</block>
	<block id="2" type="script" script="togsm">
		<branch from="0" to="0" id="3"></branch>

		<branch from="1" to="1" id="9"></branch>

		<branch from="2" to="15" id="2"></branch>
	</block>
	<block id="3" type="script" script="initgsm">
		<branch from="0" to="0" id="4"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="2">
			<try times="30" id="3"></try></branch>
	</block>
	<block id="4" type="script" script="setpin">
		<branch from="0" to="0" id="10"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="2" id="1">
			<try times="2" id="4"></try></branch>
		<branch from="3" to="3" id="3">
			<try times="10" id="4"></try></branch>
		<branch from="4" to="15" id="5"></branch>
	</block>
	<block id="5" type="script" script="setgprs">
		<branch from="0" to="0" id="6"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="3">
			<try times="10" id="5"></try></branch>
	</block>
	<block id="6" type="script" script="setppp">
		<branch from="0" to="0" id="7"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="5">
			<try times="30" id="6"></try></branch>
	</block>
	<block id="7" type="ppp" script="runppp">
		<branch from="0" to="0" id="6"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="6"></branch>
	</block>
	<block id="8" type="script" script="hangup">
		<branch from="0" to="1" id="9"></branch>

		<branch from="2" to="2" id="9">
			<try times="5" id="8"></try></branch>
		<branch from="3" to="15" id="9"></branch>
	</block>
	<block id="9" type="script" script="touhf">
		<branch from="0" to="0" id="0"></branch>
		<branch from="2" to="2" id="0">
			<try times="5" id="9"></try></branch>
		<branch from="3" to="3" id="0"></branch>
		<branch from="4" to="15" id="0">
			<try times="5" id="9"></try></branch>
	</block>
	<block id="10" type="script" script="error">
		<branch from="0" to="0" id="10"></branch>

		<branch from="1" to="15" id="8"></branch>
	</block>
</profile>

<profile name="c-master">
	<description>Start outgoing cellular data connection</description>
	<block id="1" type="script" script="checkgsm">
		<branch from="0" to="0" id="3"></branch>

		<branch from="1" to="1" id="9"></branch>

		<branch from="2" to="15" id="2">
			<try times="1" id="1"></try></branch>
	</block>
	<block id="2" type="script" script="togsm">
		<branch from="0" to="0" id="3"></branch>

		<branch from="1" to="1" id="9"></branch>

		<branch from="2" to="15" id="2"></branch>
	</block>
	<block id="3" type="script" script="initgsm">
		<branch from="0" to="0" id="4"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="2">
			<try times="30" id="3"></try></branch>
	</block>
	<block id="4" type="script" script="setpin">
		<branch from="0" to="0" id="10"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="2" id="1">
			<try times="2" id="4"></try></branch>
		<branch from="3" to="3" id="3">
			<try times="10" id="4"></try></branch>
		<branch from="4" to="15" id="5"></branch>
	</block>
	<block id="5" type="script" script="setgsm">
		<branch from="0" to="0" id="6"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="3">
			<try times="10" id="5"></try></branch>
	</block>
	<block id="6" type="script" script="setgsmm">
		<branch from="0" to="0" id="7"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="5">
			<try times="30" id="6"></try></branch>
	</block>
	<block id="7" type="direct" script="rungsm">
		<branch from="0" to="0" id="6"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="5"></branch>
	</block>
	<block id="8" type="script" script="hangup">
		<branch from="0" to="1" id="9"></branch>

		<branch from="2" to="2" id="9">
			<try times="5" id="8"></try></branch>
		<branch from="3" to="15" id="9"></branch>
	</block>
	<block id="9" type="script" script="touhf">
		<branch from="0" to="0" id="0"></branch>

		<branch from="2" to="15" id="0">
			<try times="5" id="9"></try></branch>
	</block>
	<block id="10" type="script" script="error">
		<branch from="0" to="0" id="10"></branch>

		<branch from="1" to="15" id="8"></branch>
	</block>
</profile>

<profile name="c-slave">
	<description>Wait for incoming cellular data call</description>
	<block id="1" type="script" script="checkgsm">
		<branch from="0" to="0" id="3"></branch>

		<branch from="1" to="1" id="9"></branch>

		<branch from="2" to="15" id="2">
			<try times="1" id="1"></try></branch>
	</block>
	<block id="2" type="script" script="togsm">
		<branch from="0" to="0" id="3"></branch>

		<branch from="1" to="1" id="9"></branch>

		<branch from="2" to="15" id="2"></branch>
	</block>
	<block id="3" type="script" script="initgsm">
		<branch from="0" to="0" id="4"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="2">
			<try times="30" id="3"></try></branch>
	</block>
	<block id="4" type="script" script="setpin">
		<branch from="0" to="0" id="10"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="2" id="1">
			<try times="2" id="4"></try></branch>
		<branch from="3" to="3" id="3">
			<try times="10" id="4"></try></branch>
		<branch from="4" to="15" id="5"></branch>
	</block>
	<block id="5" type="script" script="setgsm">
		<branch from="0" to="0" id="6"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="3">
			<try times="10" id="5"></try></branch>
	</block>
	<block id="6" type="script" script="setgsms">
		<branch from="0" to="0" id="7"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="2" id="5">
			<try times="30" id="6"></try></branch>
		<branch from="3" to="3" id="7"></branch>

		<branch from="4" to="15" id="5">
			<try times="3" id="6"></try></branch>
	</block>
	<block id="7" type="direct" script="rungsm">
		<branch from="0" to="0" id="6"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="5"></branch>
	</block>
	<block id="8" type="script" script="hangup">
		<branch from="0" to="1" id="9"></branch>

		<branch from="2" to="2" id="9">
			<try times="5" id="8"></try></branch>
		<branch from="3" to="15" id="9"></branch>
	</block>
	<block id="9" type="script" script="touhf">
		<branch from="0" to="0" id="0"></branch>

		<branch from="2" to="15" id="0">
			<try times="5" id="9"></try></branch>
	</block>
	<block id="10" type="script" script="error">
		<branch from="0" to="0" id="10"></branch>

		<branch from="1" to="15" id="8"></branch>
	</block>
</profile>

</profiles-list>

<scripts-list>
<script name="checkgsm">
<![CDATA[$ABORT||$ENDLINE|\r|$TIMEOUT|15|$REPORT|M105#Looking for modem|$DAISY|OFF||dm\r\n\p%%|RE002%%|%%dm,[$$dev.port$$]|RE|%%set,/par[$$dev.port$$]/rate,[$$cell.rate$$]|RE||$DAISY|[$$dev.port$$]|$TIMEOUT|10||AT|OK-AT-OK-AT-OK]]>
</script>

<script name="togsm">
<![CDATA[$ABORT||$ENDLINE|\r|$TIMEOUT|15|$DAISY|OFF||dm\r\n\p%%|RE002%%|%%dm,[$$dev.port$$]|RE||$REPORT|M106#Configuring modem||%%set,/par[$$dev.port$$]/rate,[$$radio.rate$$]|RE|%%set,/par[$$dev.port$$]/rtscts,off|RE||$DAISY|[$$dev.port$$]|$TIMEOUT|15||++++\p|@00-++++-@01|ATI|Topcon||@00|LINK RFSW 1|@00|\p\pDATAMODE|$WAIT|10|$DAISY|OFF||dm\r\n\p%%|RE002%%|%%set,/par[$$dev.port$$]/rate,[$$cell.rate$$]|RE|%%set,/par[$$dev.port$$]/rtscts,on|RE||$DAISY|[$$dev.port$$]|]]>
</script>

<script name="initgsm">
<![CDATA[$ABORT|ERROR|$ENDLINE|\r|$TIMEOUT|10||AT|OK||$TIMEOUT|20|$REPORT|M106#Configuring modem||ATV1&D0|OK|ATE0S0=0|OK|AT+CMEE=0|OK|AT+WIND=0|OK]]>
</script>

<script name="setpin">
<![CDATA[$ABORT|ERROR|$ENDLINE|\r|$TIMEOUT|10||AT|OK||$REPORT|M107#Checking SIM card|$ABORT|ERROR:READY||AT+CPIN?|+CPIN\:||SIM PIN||OK-AT-OK||$TIMEOUT|30|$REPORT|M108#Entering PIN|$ABORT|||\pAT+CPIN="[$$cell.pin$$]"|OK:ERROR||$ABORT|#---#:READY||AT+CPIN?|+CPIN\:||SIM||$REPORT|E101#Wrong PIN|]]>
</script>

<script name="setgprs">
<![CDATA[$ABORT||$TIMEOUT|10|$REPORT|M101#Registering||\p+++\p\pATH|OK:ERROR|AT+CREG=0|OK|AT+CGREG=0|OK|AT+COPS=3,0|OK|]]>
</script>

<script name="setppp">
<![CDATA[$ABORT||$TIMEOUT|20||AT+CREG?|+CREG\:||[$$cell.roam$$]||OK|AT+CSQ|+CSQ\:||OK|AT+CSQ|+CSQ\:||$9,||OK|AT+COPS?|+COPS\:||,"||[$$cell.op.name$$]"||OK|AT+CGDCONT=1,"IP","[$$cell.gprs.apn$$]"|OK||$ABORT|NO CARRIER:BUSY:NO ANSWER:ERROR|$REPORT|M102#Dialing||ATD[$$cell.gprs.dial$$]|$TIMEOUT|400|CONNECT||]]>
</script>

<script name="setgsm">
<![CDATA[$ABORT||$TIMEOUT|10|$REPORT|M101#Registering||\p+++\p\pATH|OK:ERROR|ATGH|OK:ERROR|AT+CREG=0|OK|AT+COPS=3,0|OK|AT+CSQ|+CSQ\:||$9,||OK|AT+COPS?|+COPS\:||,"||[$$cell.op.name$$]"||OK|]]>
</script>

<script name="setgsmm">
<![CDATA[$ABORT||$TIMEOUT|10||AT+CREG?|+CREG\:||[$$cell.roam$$]||OK|AT+CSQ|+CSQ\:||$9,||OK|AT+COPS?|+COPS\:||,"||[$$cell.op.name$$]"||OK|AT+CBST=[$$cell.csd.cbst$$]|OK:ERROR||$ABORT|NO CARRIER:BUSY:NO ANSWER:ERROR|$REPORT|M102#Dialing||ATD[$$cell.csd.dial$$]|$TIMEOUT|400|CONNECT||]]>
</script>

<script name="setgsms">
<![CDATA[$ABORT|CONNECT:NO CARRIER|$TIMEOUT|10||AT+CREG?|+CREG\:||[$$cell.roam$$]||OK|AT+CSQ|+CSQ\:||$9,||OK|AT+COPS?|+COPS\:||,"||[$$cell.op.name$$]"||OK|ATS0=2|OK|AT+CBST=[$$cell.csd.cbst$$]|OK:ERROR||$TIMEOUT|3000|$REPORT|M103#Awaiting call|RING|ATA|$TIMEOUT|200|CONNECT||]]>
</script>

<script name="hangup">
<![CDATA[$ABORT||$TIMEOUT|20||\p+++\p\p|OK-+++AT\p\p-OK-ATH-OK:ERROR|ATH|OK:ERROR|ATS0=0|OK|]]>
</script>

<script name="touhf">
<![CDATA[$ABORT||$TIMEOUT|20|$DAISY|OFF|$REPORT|M106#Configuring modem||dm\r\n\p%%|RE002%%|%%set,/par[$$dev.port$$]/rate,[$$radio.rate$$]|RE|%%set,/par[$$dev.port$$]/rtscts,off|RE||$ABORT|%1%||%[$$cell.offmode$$]%|RE||%0%:%%||$ABORT||$DAISY|[$$dev.port$$]|$TIMEOUT|15||++++\p|@00-++++-@01|ATI|Topcon||@00|LINK RFSW 0|@00|\p\pDATAMODE|$WAIT|10|$DAISY|OFF]]>
</script>

<script name="rungsm">
<![CDATA[$TIMEOUT|[$$cell.csd.idle$$]|$ABORT|NO CARRIER:ERROR:RING]]>
</script>

<script name="runppp">
<![CDATA[[$$dev.port$$]|[$$cell.rate$$]|[$$ppp.ip$$]|novj|novjccomp|lcp-echo-interval:15|lcp-echo-failure:3|lcp-restart:5|ipcp-accept-local|ipcp-accept-remote|ipcp-max-failure:3|ipcp-max-configure:10|usepeerdns|noipdefault|noproxyarp|idle:[$$ppp.idle$$]|name:[$$ppp.name$$]|password:[$$ppp.password$$]]]>
</script>

<script name="error">
<![CDATA[$ABORT||$WAIT|10|]]>
</script>

</scripts-list>

<vars-list>
<var name="dev.port" type="enum" default="3">
<ui>Port</ui>
<description>Name of hardware serial port that is connected to modem</description>
<enum_list>
	<enum index="1">
		<value>/dev/ser/a</value>
	</enum>
	<enum index="2">
		<value>/dev/ser/b</value>
	</enum>
	<enum index="3">
		<value>/dev/ser/c</value>
	</enum>
	<enum index="4">
		<value>/dev/ser/d</value>
	</enum>
</enum_list>
</var>

<var name="radio.rate" type="enum" default="6">
<ui>Baud Rate</ui>
<description>Baud rate of modem serial interface</description>
<enum_list>
	<enum index="1">
		<value>1200</value>
	</enum>
	<enum index="2">
		<value>2400</value>
	</enum>
	<enum index="3">
		<value>4800</value>
	</enum>
	<enum index="4">
		<value>9600</value>
	</enum>
	<enum index="5">
		<value>19200</value>
	</enum>
	<enum index="6">
		<value>38400</value>
	</enum>
	<enum index="7">
		<value>57600</value>
	</enum>
	<enum index="8">
		<value>115200</value>
	</enum>
</enum_list>
</var>

<var name="cell.rate" type="enum" default="6">
<ui>Baud Rate</ui>
<description>Baud rate of cellular module</description>
<enum_list>
	<enum index="1">
		<value>1200</value>
	</enum>
	<enum index="2">
		<value>2400</value>
	</enum>
	<enum index="3">
		<value>4800</value>
	</enum>
	<enum index="4">
		<value>9600</value>
	</enum>
	<enum index="5">
		<value>19200</value>
	</enum>
	<enum index="6">
		<value>38400</value>
	</enum>
	<enum index="7">
		<value>57600</value>
	</enum>
	<enum index="8">
		<value>115200</value>
	</enum>
</enum_list>
</var>

<var name="cell.pin" type="string" default="0000">
<ui>PIN Code</ui>
<description>SIM PIN code</description>
<uvar>0</uvar>
</var>

<var name="cell.gprs.dial" type="string" default="*99***1#">
<ui>GPRS Dial</ui>
<description>GPRS Dial Number</description>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="cell.gprs.apn" type="string" default="">
<ui>APN</ui>
<description>GPRS APN</description>
<uvar>1</uvar>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="ppp.name" type="string" default="">
<ui>User</ui>
<description>GPRS User Name</description>
<uvar>2</uvar>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="ppp.password" type="string" default="">
<ui>Password</ui>
<description>GPRS Password</description>
<uvar>3</uvar>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="ppp.ip" type="string" default="">
<ui>IP address</ui>
<description>Static PPP address</description>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="ppp.idle" type="numeric" default="0">
<ui>Timeout</ui>
<description>GPRS Reconnection Timeout if datalink is lost</description>
<range min="0" max="9999">
<uifactor>0.1</uifactor>
</range>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="cell.roam" type="enum" default="1">
<ui>Roaming</ui>
<description>Allow network roaming</description>
<profiles>
	<name>internet</name>
	<name>c-master</name>
	<name>c-slave</name>
</profiles>
<enum_list>
	<enum index="1">
		<value>,1:,5</value>
		<ui>Enabled</ui>
	</enum>
	<enum index="2">
		<value>,1</value>
		<ui>Disabled</ui>
	</enum>
</enum_list>
</var>

<var name="cell.csd.cbst" type="enum" default="1">
<ui>Data Call Type</ui>
<description>Bearer type for outgoing and incoming data calls</description>
<uvar>6</uvar>
<profiles>
	<name>c-master</name>
	<name>c-slave</name>
</profiles>
<enum_list>
	<enum index="1">
		<value>0</value>
		<ui>Automatic</ui>
	</enum>
	<enum index="2">
		<value>7</value>
		<ui>Analog V.32</ui>
	</enum>
	<enum index="3">
		<value>71</value>
		<ui>Digital V.110</ui>
	</enum>
</enum_list>
</var>

<var name="cell.csd.dial" type="string" default="">
<ui>Dial Number</ui>
<description>CSD Base Phone Number</description>
<uvar>5</uvar>
<profiles>
	<name>c-master</name>
</profiles>
</var>

<var name="cell.csd.idle" type="numeric" default="300">
<ui>CSD Timeout</ui>
<description>Hangup CSD if no data is received within timeout threshold</description>
<range min="0" max="9999">
<uifactor>0.1</uifactor>
</range>
<profiles>
	<name>c-master</name>
	<name>c-slave</name>
</profiles>
</var>

<var name="cell.op.name" type="string" default="">
<ui>Cellular Operator Name</ui>
<description>Operator Name (read only)</description>
<uvar>7</uvar>
</var>

<var name="cell.offmode" type="string" default="0">
<ui>Keep Cellular Powered</ui>
<description>Flag to Keep cellular module powered when turning profile off</description>
<uvar>8</uvar>
</var>

<var name="cell.sq" type="string" default="">
<ui>Cellular Signal Quality</ui>
<description>Signal Quality (read only)</description>
<uvar>9</uvar>
</var>

</vars-list>
</template>

<template name="Topcon|DUHF2;Wavecom|Q24/C">
<id>[$$dev.port$$];Topcon|DUHF2@[$$radio.rate$$];Wavecom|Q24/C@[$$cell.rate$$]</id>
<version>1.3</version>
<description>Digital UHF 2 modem with Wavecom Q24 CDMA module</description>
<compat-version>1</compat-version>

<profiles-list>
<profile name="internet">
	<description>Connect to Internet using CDMA modem</description>
	<block id="1" type="script" script="checkmod">
		<branch from="0" to="0" id="3"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="2">
			<try times="1" id="1"></try></branch>
	</block>
	<block id="2" type="script" script="tocdma">
		<branch from="0" to="0" id="3"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="2"></branch>
	</block>
	<block id="3" type="script" script="initcdma">
		<branch from="0" to="0" id="4"></branch>

		<branch from="1" to="1" id="7"></branch>

		<branch from="2" to="15" id="2">
			<try times="30" id="3"></try></branch>
	</block>
	<block id="4" type="script" script="setcdma">
		<branch from="0" to="0" id="5"></branch>

		<branch from="1" to="1" id="7"></branch>

		<branch from="2" to="15" id="3">
			<try times="10" id="4"></try></branch>
	</block>
	<block id="5" type="script" script="setppp">
		<branch from="0" to="0" id="6"></branch>

		<branch from="1" to="1" id="7"></branch>

		<branch from="2" to="15" id="4">
			<try times="30" id="5"></try></branch>
	</block>
	<block id="6" type="ppp" script="runppp">
		<branch from="0" to="0" id="5"></branch>

		<branch from="1" to="1" id="7"></branch>

		<branch from="2" to="15" id="5"></branch>
	</block>
	<block id="7" type="script" script="hangup">
		<branch from="0" to="1" id="8"></branch>

		<branch from="2" to="2" id="8">
			<try times="5" id="7"></try></branch>
		<branch from="3" to="15" id="8"></branch>
	</block>
	<block id="8" type="script" script="touhf">
		<branch from="0" to="0" id="0"></branch>
		<branch from="2" to="2" id="0">
			<try times="5" id="8"></try></branch>
		<branch from="3" to="3" id="0"></branch>
		<branch from="4" to="15" id="0">
			<try times="5" id="8"></try></branch>
	</block>
</profile>

</profiles-list>

<scripts-list>
<script name="checkmod">
<![CDATA[$ABORT||$ENDLINE|\r|$TIMEOUT|15|$REPORT|M105#Looking for modem|$DAISY|OFF||dm\r\n\p%%|RE002%%|%%dm,[$$dev.port$$]|RE|%%set,/par[$$dev.port$$]/rate,[$$cell.rate$$]|RE||$DAISY|[$$dev.port$$]|$TIMEOUT|10||AT|OK-AT-OK-AT-OK]]>
</script>

<script name="tocdma">
<![CDATA[$ABORT||$ENDLINE|\r|$TIMEOUT|15|$DAISY|OFF||dm\r\n\p%%|RE002%%|%%dm,[$$dev.port$$]|RE||$REPORT|M106#Configuring modem||%%set,/par[$$dev.port$$]/rate,[$$radio.rate$$]|RE|%%set,/par[$$dev.port$$]/rtscts,off|RE||$DAISY|[$$dev.port$$]|$TIMEOUT|15||++++\p|@00-++++-@01|ATI|Topcon||@00|LINK RFSW 1|@00|\p\pDATAMODE|$WAIT|10|$DAISY|OFF||dm\r\n\p%%|RE002%%|%%set,/par[$$dev.port$$]/rate,[$$cell.rate$$]|RE|%%set,/par[$$dev.port$$]/rtscts,on|RE||$DAISY|[$$dev.port$$]|]]>
</script>

<script name="initcdma">
<![CDATA[$ABORT|ERROR|$ENDLINE|\r|$TIMEOUT|10||AT|OK||$TIMEOUT|20|$REPORT|M106#Configuring modem||ATV1&D0|OK|ATE0S0=0|OK|AT+CMEE=0|OK]]>
</script>

<script name="setcdma">
<![CDATA[$ABORT||$TIMEOUT|10|$REPORT|M101#Registering||\p+++\p\pATH|OK:ERROR|AT+CREG=0|OK|]]>
</script>

<script name="setppp">
<![CDATA[$ABORT||$TIMEOUT|10||AT+CREG?|+CREG\:||[$$cell.roam$$]||OK|AT+CSQ|+CSQ\:||$9,||OK||$ABORT|NO CARRIER:BUSY:NO ANSWER:ERROR|$REPORT|M102#Dialing||ATD[$$cell.cdma.dial$$]|$TIMEOUT|400|CONNECT||]]>
</script>

<script name="hangup">
<![CDATA[$ABORT||$TIMEOUT|20||\p+++\p\p|OK-+++AT\p\p-OK-ATH-OK:ERROR|ATH|OK:ERROR|ATS0=0|OK|]]>
</script>

<script name="touhf">
<![CDATA[$ABORT||$TIMEOUT|20|$DAISY|OFF|$REPORT|M106#Configuring modem||dm\r\n\p%%|RE002%%|%%set,/par[$$dev.port$$]/rate,[$$radio.rate$$]|RE|%%set,/par[$$dev.port$$]/rtscts,off|RE||$ABORT|%1%||%[$$cell.offmode$$]%|RE||%0%:%%||$ABORT||$DAISY|[$$dev.port$$]|$TIMEOUT|15||++++\p|@00-++++-@01|ATI|Topcon||@00|LINK RFSW 0|@00|\p\pDATAMODE|$WAIT|10|$DAISY|OFF]]>
</script>

<script name="runppp">
<![CDATA[[$$dev.port$$]|[$$cell.rate$$]|[$$ppp.ip$$]|novj|novjccomp|lcp-echo-interval:0|lcp-echo-failure:0|default-asyncmap|lcp-restart:5|ipcp-accept-local|ipcp-accept-remote|ipcp-max-failure:3|ipcp-max-configure:10|usepeerdns|noipdefault|noproxyarp|idle:[$$ppp.idle$$]|name:[$$ppp.name$$]|password:[$$ppp.password$$]]]>
</script>

</scripts-list>

<vars-list>
<var name="dev.port" type="enum" default="3">
<ui>Port</ui>
<description>Name of hardware serial port that is connected to modem</description>
<enum_list>
	<enum index="1">
		<value>/dev/ser/a</value>
	</enum>
	<enum index="2">
		<value>/dev/ser/b</value>
	</enum>
	<enum index="3">
		<value>/dev/ser/c</value>
	</enum>
	<enum index="4">
		<value>/dev/ser/d</value>
	</enum>
</enum_list>
</var>

<var name="radio.rate" type="enum" default="6">
<ui>Baud Rate</ui>
<description>Baud rate of modem serial interface</description>
<enum_list>
	<enum index="1">
		<value>1200</value>
	</enum>
	<enum index="2">
		<value>2400</value>
	</enum>
	<enum index="3">
		<value>4800</value>
	</enum>
	<enum index="4">
		<value>9600</value>
	</enum>
	<enum index="5">
		<value>19200</value>
	</enum>
	<enum index="6">
		<value>38400</value>
	</enum>
	<enum index="7">
		<value>57600</value>
	</enum>
	<enum index="8">
		<value>115200</value>
	</enum>
</enum_list>
</var>

<var name="cell.rate" type="enum" default="6">
<ui>Baud Rate</ui>
<description>Baud rate of cellular module</description>
<enum_list>
	<enum index="1">
		<value>1200</value>
	</enum>
	<enum index="2">
		<value>2400</value>
	</enum>
	<enum index="3">
		<value>4800</value>
	</enum>
	<enum index="4">
		<value>9600</value>
	</enum>
	<enum index="5">
		<value>19200</value>
	</enum>
	<enum index="6">
		<value>38400</value>
	</enum>
	<enum index="7">
		<value>57600</value>
	</enum>
	<enum index="8">
		<value>115200</value>
	</enum>
</enum_list>
</var>

<var name="cell.cdma.dial" type="string" default="#777">
<ui>CDMA Dial</ui>
<description>CDMA Dial Number</description>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="ppp.name" type="string" default="">
<ui>User</ui>
<description>CDMA User Name</description>
<uvar>2</uvar>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="ppp.password" type="string" default="">
<ui>Password</ui>
<description>CDMA Password</description>
<uvar>3</uvar>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="ppp.ip" type="string" default="">
<ui>IP address</ui>
<description>Static PPP address</description>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="ppp.idle" type="numeric" default="0">
<ui>Timeout</ui>
<description>PPP Reconnection Timeout if datalink is lost</description>
<range min="0" max="9999">
<uifactor>0.1</uifactor>
</range>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="cell.roam" type="enum" default="1">
<ui>Roaming</ui>
<description>Allow network roaming</description>
<profiles>
	<name>internet</name>
</profiles>
<enum_list>
	<enum index="1">
		<value>,1:,5</value>
		<ui>Enabled</ui>
	</enum>
	<enum index="2">
		<value>,1</value>
		<ui>Disabled</ui>
	</enum>
</enum_list>
</var>

<var name="cell.offmode" type="string" default="0">
<ui>Keep Cellular Powered</ui>
<description>Flag to Keep cellular module powered when turning profile off</description>
<uvar>8</uvar>
</var>

<var name="cell.sq" type="string" default="">
<ui>Cellular Signal Quality</ui>
<description>Signal Quality (read only)</description>
<uvar>9</uvar>
</var>

</vars-list>
</template>

<template name="Satel|SATELLINE-3AS;Motorola|H24">
<id>[$$dev.port$$];Satel|SATELLINE-3AS@[$$radio.rate$$];Motorola|H24@[$$cell.rate$$]</id>
<version>1.3</version>
<description>Satel UHF modem with Motorola H24 3G module</description>
<compat-version>1</compat-version>

<profiles-list>
<profile name="internet">
	<description>Connect to Internet using GPRS by cellular modem</description>
	<block id="1" type="script" script="checkgsm">
		<branch from="0" to="0" id="3"></branch>

		<branch from="1" to="1" id="9"></branch>

		<branch from="2" to="15" id="2">
			<try times="1" id="1"></try></branch>
	</block>
	<block id="2" type="script" script="togsm">
		<branch from="0" to="0" id="3"></branch>

		<branch from="1" to="1" id="9"></branch>

		<branch from="2" to="15" id="2"></branch>
	</block>
	<block id="3" type="script" script="initgsm">
		<branch from="0" to="0" id="4"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="2" id="2">
			<try times="30" id="3"></try></branch>
		<branch from="3" to="15" id="4"></branch>
	</block>
	<block id="4" type="script" script="setpin">
		<branch from="0" to="0" id="10"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="2" id="1">
			<try times="2" id="4"></try></branch>
		<branch from="3" to="3" id="11">
			<try times="20" id="4"></try></branch>
		<branch from="4" to="15" id="5"></branch>
	</block>
	<block id="5" type="script" script="setgprs">
		<branch from="0" to="0" id="6"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="3">
			<try times="10" id="5"></try></branch>
	</block>
	<block id="6" type="script" script="setppp">
		<branch from="0" to="0" id="7"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="2" id="11">
			<try times="20" id="6"></try></branch>
		<branch from="3" to="15" id="5">
			<try times="30" id="6"></try></branch>
	</block>
	<block id="7" type="ppp" script="runppp">
		<branch from="0" to="0" id="6"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="6"></branch>
	</block>
	<block id="8" type="script" script="hangup">
		<branch from="0" to="1" id="9"></branch>

		<branch from="2" to="2" id="9">
			<try times="5" id="8"></try></branch>
		<branch from="3" to="15" id="9"></branch>
	</block>
	<block id="9" type="script" script="touhf">
		<branch from="0" to="0" id="0"></branch>
		<branch from="2" to="2" id="0">
			<try times="5" id="9"></try></branch>
		<branch from="3" to="3" id="0"></branch>
		<branch from="4" to="15" id="0">
			<try times="5" id="9"></try></branch>
	</block>
	<block id="10" type="script" script="error">
		<branch from="0" to="0" id="10"></branch>

		<branch from="1" to="15" id="8"></branch>
	</block>
	<block id="11" type="script" script="simreset">
		<branch from="0" to="0" id="3"></branch>
		<branch from="1" to="1" id="8"></branch>
		<branch from="2" to="2" id="3"></branch>
		<branch from="3" to="15" id="3"></branch>
	</block>
</profile>

<profile name="c-master">
	<description>Start outgoing cellular data connection</description>
	<block id="1" type="script" script="checkgsm">
		<branch from="0" to="0" id="3"></branch>

		<branch from="1" to="1" id="9"></branch>

		<branch from="2" to="15" id="2">
			<try times="1" id="1"></try></branch>
	</block>
	<block id="2" type="script" script="togsm">
		<branch from="0" to="0" id="3"></branch>

		<branch from="1" to="1" id="9"></branch>

		<branch from="2" to="15" id="2"></branch>
	</block>
	<block id="3" type="script" script="initgsm">
		<branch from="0" to="0" id="4"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="2" id="2">
			<try times="30" id="3"></try></branch>
		<branch from="3" to="15" id="4"></branch>
	</block>
	<block id="4" type="script" script="setpin">
		<branch from="0" to="0" id="10"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="2" id="1">
			<try times="2" id="4"></try></branch>
		<branch from="3" to="3" id="11">
			<try times="20" id="4"></try></branch>
		<branch from="4" to="15" id="5"></branch>
	</block>
	<block id="5" type="script" script="setgsm">
		<branch from="0" to="0" id="6"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="3">
			<try times="10" id="5"></try></branch>
	</block>
	<block id="6" type="script" script="setgsmm">
		<branch from="0" to="0" id="7"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="2" id="11">
			<try times="30" id="6"></try></branch>
		<branch from="3" to="15" id="5">
			<try times="30" id="6"></try></branch>
	</block>
	<block id="7" type="direct" script="rungsm">
		<branch from="0" to="0" id="6"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="5"></branch>
	</block>
	<block id="8" type="script" script="hangup">
		<branch from="0" to="1" id="9"></branch>

		<branch from="2" to="2" id="9">
			<try times="5" id="8"></try></branch>
		<branch from="3" to="15" id="9"></branch>
	</block>
	<block id="9" type="script" script="touhf">
		<branch from="0" to="0" id="0"></branch>

		<branch from="2" to="15" id="0">
			<try times="5" id="9"></try></branch>
	</block>
	<block id="10" type="script" script="error">
		<branch from="0" to="0" id="10"></branch>

		<branch from="1" to="15" id="8"></branch>
	</block>
	<block id="11" type="script" script="simreset">
		<branch from="0" to="0" id="3"></branch>
		<branch from="1" to="1" id="8"></branch>
		<branch from="2" to="2" id="3"></branch>
		<branch from="3" to="15" id="3"></branch>
	</block> 
</profile>

<profile name="c-slave">
	<description>Wait for incoming cellular data call</description>
	<block id="1" type="script" script="checkgsm">
		<branch from="0" to="0" id="3"></branch>

		<branch from="1" to="1" id="9"></branch>

		<branch from="2" to="15" id="2">
			<try times="1" id="1"></try></branch>
	</block>
	<block id="2" type="script" script="togsm">
		<branch from="0" to="0" id="3"></branch>

		<branch from="1" to="1" id="9"></branch>

		<branch from="2" to="15" id="2"></branch>
	</block>
	<block id="3" type="script" script="initgsm">
		<branch from="0" to="0" id="4"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="2" id="2">
			<try times="30" id="3"></try></branch>
		<branch from="3" to="15" id="4"></branch>
	</block>
	<block id="4" type="script" script="setpin">
		<branch from="0" to="0" id="10"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="2" id="1">
			<try times="2" id="4"></try></branch>
		<branch from="3" to="3" id="11">
			<try times="20" id="4"></try></branch>
		<branch from="4" to="15" id="5"></branch>
	</block>
	<block id="5" type="script" script="setgsm">
		<branch from="0" to="0" id="6"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="3">
			<try times="10" id="5"></try></branch>
	</block>
	<block id="6" type="script" script="setgsms">
		<branch from="0" to="0" id="7"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="2" id="5">
			<try times="30" id="6"></try></branch>
		<branch from="3" to="3" id="7"></branch>

		<branch from="4" to="15" id="5">
			<try times="3" id="6"></try></branch>
	</block>
	<block id="7" type="direct" script="rungsm">
		<branch from="0" to="0" id="6"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="5"></branch>
	</block>
	<block id="8" type="script" script="hangup">
		<branch from="0" to="1" id="9"></branch>

		<branch from="2" to="2" id="9">
			<try times="5" id="8"></try></branch>
		<branch from="3" to="15" id="9"></branch>
	</block>
	<block id="9" type="script" script="touhf">
		<branch from="0" to="0" id="0"></branch>

		<branch from="2" to="15" id="0">
			<try times="5" id="9"></try></branch>
	</block>
	<block id="10" type="script" script="error">
		<branch from="0" to="0" id="10"></branch>

		<branch from="1" to="15" id="8"></branch>
	</block>
	<block id="11" type="script" script="simreset">
		<branch from="0" to="0" id="3"></branch>
		<branch from="1" to="1" id="8"></branch>
		<branch from="2" to="2" id="3"></branch>
		<branch from="3" to="15" id="3"></branch>
	</block>
</profile>

</profiles-list>

<scripts-list>
<script name="checkgsm">
<![CDATA[$ABORT||$ENDLINE|\r|$TIMEOUT|15|$REPORT|M105#Looking for modem|$DAISY|OFF||dm\r\n\p%%|RE002%%|%%dm,[$$dev.port$$]|RE|%%set,/par[$$dev.port$$]/rate,[$$cell.rate$$]|RE||$DAISY|[$$dev.port$$]|$TIMEOUT|10||AT|OK-AT-OK-AT-OK]]>
</script>

<script name="togsm">
<![CDATA[$ABORT||$ENDLINE|\r|$TIMEOUT|15|$DAISY|OFF||dm\r\n\p%%|RE002%%|%%dm,[$$dev.port$$]|RE||$REPORT|M106#Configuring modem||%%set,/par[$$dev.port$$]/rtscts,off|RE|%%set,/par[$$dev.port$$]/rate,[$$radio.rate$$]|RE||$DAISY|[$$dev.port$$]|$TIMEOUT|15||SL+++|OK-SL+++-OK-SL+++-OK-SL+++-OK-SL!V?-3AS-+++\p\pSL@G=0-OK|\pSL@G=1\p||SL@G=1|$WAIT|10|$DAISY|OFF||dm\r\n\p%%|RE002%%|%%set,/par[$$dev.port$$]/rate,[$$cell.rate$$]|RE|%%set,/par[$$dev.port$$]/rtscts,on|RE||$DAISY|[$$dev.port$$]|]]>
</script> 

<script name="initgsm">
<![CDATA[$ABORT|ERROR|$ENDLINE|\r|$TIMEOUT|10||AT|OK||$TIMEOUT|20|$REPORT|M106#Configuring modem||ATV1&D0|OK|ATE0S0=0|OK|AT+CMEE=0|OK||$ABORT|+MCONN\: 3||AT+MCONN?|OK|AT+MCONN=3|OK|AT+MRST|OK|\pAT|OK]]>
</script>

<script name="setpin">
<![CDATA[$ABORT|ERROR|$ENDLINE|\r|$TIMEOUT|10||AT|OK|AT+CMEE=2|OK||$REPORT|M107#Checking SIM card|$ABORT|SIM busy:READY|$WAIT|5||AT+CPIN?|+CPIN\:||SIM PIN||OK-AT-OK||$TIMEOUT|30|$REPORT|M108#Entering PIN|$ABORT|||\pAT+CPIN="[$$cell.pin$$]"|OK:ERROR||$ABORT|#---#:READY||AT+CPIN?|+CPIN\:||SIM||$REPORT|E101#Wrong PIN|]]>
</script>

<script name="setgprs">
<![CDATA[$ABORT||$TIMEOUT|10|$REPORT|M101#Registering||\p+++\p\pATH|OK:ERROR|AT+CMEE=0|OK|AT+CREG=0|OK|AT+CGREG=0|OK||$ABORT|ERROR|$TIMEOUT|300||AT+COPS=[$$cell.3g.enable$$]|OK||$TIMEOUT|10||AT+WS46?|12:22:25||OK]]>
</script>

<script name="setppp">
<![CDATA[$ABORT|99,99|$TIMEOUT|10||AT+CREG?|+CREG\:||[$$cell.roam$$]||OK|AT+CSQ|+CSQ\:||OK|AT+CSQ|+CSQ\:||$9,||OK|AT+COPS?|+COPS\:||,"||[$$cell.op.name$$]"||OK|AT+CGDCONT=1,"IP","[$$cell.gprs.apn$$]"|OK||$ABORT|NO CARRIER:BUSY:NO ANSWER:ERROR|$REPORT|M102#Dialing||ATD[$$cell.gprs.dial$$]|$TIMEOUT|400|CONNECT||]]>
</script>

<script name="setgsm">
<![CDATA[$ABORT||$TIMEOUT|10|$REPORT|M101#Registering||\p+++\p\pATH|OK:ERROR|AT+CMEE=0|OK|AT+CREG=0|OK||$ABORT|ERROR|$TIMEOUT|300||AT+COPS=,0,,0|OK||$TIMEOUT|10||AT+WS46?|12||OK|AT+CSQ|+CSQ\:||$9,||OK|AT+COPS?|+COPS\:||,"||[$$cell.op.name$$]"||OK|]]>
</script>

<script name="setgsmm">
<![CDATA[$ABORT|99,99|$TIMEOUT|10||AT+CREG?|+CREG\:||[$$cell.roam$$]||OK|AT+CSQ|+CSQ\:||OK|AT+CSQ|+CSQ\:||$9,||OK|AT+COPS?|+COPS\:||,"||[$$cell.op.name$$]"||OK|AT+CBST=7|OK|AT+CBST=[$$cell.csd.cbst$$]|OK:ERROR||$ABORT|NO CARRIER:BUSY:NO ANSWER:ERROR|$REPORT|M102#Dialing||ATD[$$cell.csd.dial$$]|$TIMEOUT|400|CONNECT||]]>
</script>

<script name="setgsms">
<![CDATA[$ABORT|CONNECT:NO CARRIER:99,99|$TIMEOUT|10||AT+CREG?|+CREG\:||[$$cell.roam$$]||OK|AT+CSQ|+CSQ\:||OK|AT+CSQ|+CSQ\:||$9,||OK|AT+COPS?|+COPS\:||,"||[$$cell.op.name$$]"||OK|ATS0=2|OK||$TIMEOUT|3000|$REPORT|M103#Awaiting call|RING|ATA|$TIMEOUT|200|CONNECT||]]>
</script>

<script name="hangup">
<![CDATA[$ABORT||$TIMEOUT|20||\p+++\p\p|OK-AT-OK|ATI|OK:ERROR|ATH|OK:ERROR|ATS0=0|OK|]]>
</script>

<script name="touhf">
<![CDATA[$ABORT||$TIMEOUT|20|$DAISY|OFF|$REPORT|M106#Configuring modem||dm\r\n\p%%|RE002%%|%%set,/par[$$dev.port$$]/rate,[$$radio.rate$$]|RE|%%set,/par[$$dev.port$$]/rtscts,off|RE||$ABORT|%1%||%[$$cell.offmode$$]%|RE||%0%:%%||$ABORT||$DAISY|[$$dev.port$$]|$TIMEOUT|80||+++\p\pSL@G=0|OK||$TIMEOUT|10||AT+CGMI?|Satel-SL!V?-3AS|SL++O|OK-SL++O||$WAIT|10|$DAISY|OFF]]>
</script>

<script name="rungsm">
<![CDATA[$TIMEOUT|[$$cell.csd.idle$$]|$ABORT|NO CARRIER:ERROR:RING]]>
</script>

<script name="runppp">
<![CDATA[[$$dev.port$$]|[$$cell.rate$$]|[$$ppp.ip$$]:192.168.255.1|novj|novjccomp|lcp-echo-interval:15|lcp-echo-failure:2|lcp-restart:5|ipcp-accept-local|ipcp-accept-remote|ipcp-max-failure:3|ipcp-max-configure:10|usepeerdns|noipdefault|noproxyarp|idle:[$$ppp.idle$$]|name:[$$ppp.name$$]|password:[$$ppp.password$$]]]>
</script>

<script name="error">
<![CDATA[$ABORT||$WAIT|10|]]>
</script>

<script name="simreset">
<![CDATA[$ABORT|AT+MRST:SIM PIN|$TIMEOUT|20||AT+CPIN?|SIM busy-AT+MGSMSIM?-MGSMSIM\: 0|AT+CPIN?|SIM busy-AT+MGSMSIM=1-OK|ATE1|OK|AT+CPIN?|SIM busy-AT+MRST-OK|AT+MGSMSIM=0|OK|\pAT+MRST|OK]]>
</script>

</scripts-list>

<vars-list>
<var name="dev.port" type="enum" default="3">
<ui>Port</ui>
<description>Name of hardware serial port that is connected to modem</description>
<enum_list>
	<enum index="1">
		<value>/dev/ser/a</value>
	</enum>
	<enum index="2">
		<value>/dev/ser/b</value>
	</enum>
	<enum index="3">
		<value>/dev/ser/c</value>
	</enum>
	<enum index="4">
		<value>/dev/ser/d</value>
	</enum>
</enum_list>
</var>

<var name="radio.rate" type="enum" default="6">
<ui>Baud Rate</ui>
<description>Baud rate of modem serial interface</description>
<enum_list>
	<enum index="1">
		<value>1200</value>
	</enum>
	<enum index="2">
		<value>2400</value>
	</enum>
	<enum index="3">
		<value>4800</value>
	</enum>
	<enum index="4">
		<value>9600</value>
	</enum>
	<enum index="5">
		<value>19200</value>
	</enum>
	<enum index="6">
		<value>38400</value>
	</enum>
	<enum index="7">
		<value>57600</value>
	</enum>
	<enum index="8">
		<value>115200</value>
	</enum>
</enum_list>
</var>

<var name="cell.rate" type="enum" default="6">
<ui>Baud Rate</ui>
<description>Baud rate of cellular module</description>
<enum_list>
	<enum index="1">
		<value>1200</value>
	</enum>
	<enum index="2">
		<value>2400</value>
	</enum>
	<enum index="3">
		<value>4800</value>
	</enum>
	<enum index="4">
		<value>9600</value>
	</enum>
	<enum index="5">
		<value>19200</value>
	</enum>
	<enum index="6">
		<value>38400</value>
	</enum>
	<enum index="7">
		<value>57600</value>
	</enum>
	<enum index="8">
		<value>115200</value>
	</enum>
</enum_list>
</var>

<var name="cell.pin" type="string" default="0000">
<ui>PIN Code</ui>
<description>SIM PIN code</description>
<uvar>0</uvar>
</var>

<var name="cell.gprs.dial" type="string" default="*99***1#">
<ui>GPRS Dial</ui>
<description>GPRS Dial Number</description>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="cell.gprs.apn" type="string" default="">
<ui>APN</ui>
<description>GPRS APN</description>
<uvar>1</uvar>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="ppp.name" type="string" default="">
<ui>User</ui>
<description>GPRS User Name</description>
<uvar>2</uvar>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="ppp.password" type="string" default="">
<ui>Password</ui>
<description>GPRS Password</description>
<uvar>3</uvar>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="ppp.ip" type="string" default="">
<ui>IP address</ui>
<description>Static PPP address</description>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="ppp.idle" type="numeric" default="0">
<ui>Timeout</ui>
<description>GPRS Reconnection Timeout if datalink is lost</description>
<range min="0" max="9999">
<uifactor>0.1</uifactor>
</range>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="cell.roam" type="enum" default="1">
<ui>Roaming</ui>
<description>Allow network roaming</description>
<profiles>
	<name>internet</name>
	<name>c-master</name>
	<name>c-slave</name>
</profiles>
<enum_list>
	<enum index="1">
		<value>,1:,5</value>
		<ui>Enabled</ui>
	</enum>
	<enum index="2">
		<value>,1</value>
		<ui>Disabled</ui>
	</enum>
</enum_list>
</var>

<var name="cell.csd.cbst" type="enum" default="1">
<ui>Data Call Type</ui>
<description>Bearer type for outgoing and incoming data calls</description>
<uvar>6</uvar>
<profiles>
	<name>c-master</name>
	<name>c-slave</name>
</profiles>
<enum_list>
	<enum index="1">
		<value>0</value>
		<ui>Automatic</ui>
	</enum>
	<enum index="2">
		<value>7</value>
		<ui>Analog V.32</ui>
	</enum>
	<enum index="3">
		<value>71</value>
		<ui>Digital V.110</ui>
	</enum>
</enum_list>
</var>

<var name="cell.csd.dial" type="string" default="">
<ui>Dial Number</ui>
<description>CSD Base Phone Number</description>
<uvar>5</uvar>
<profiles>
	<name>c-master</name>
</profiles>
</var>

<var name="cell.csd.idle" type="numeric" default="300">
<ui>CSD Timeout</ui>
<description>Hangup CSD if no data is received within timeout threshold</description>
<range min="0" max="9999">
<uifactor>0.1</uifactor>
</range>
<profiles>
	<name>c-master</name>
	<name>c-slave</name>
</profiles>
</var>

<var name="cell.3g.enable" type="enum" default="1">
<ui>3G Mode</ui>
<description>Use 3G technology for Internet access</description>
<enum_list>
	<enum index="1">
		<value>0,0,,</value>
		<ui>Automatic</ui>
	</enum>
	<enum index="2">
		<value>,0,,0</value>
		<ui>2G only</ui>
	</enum>
	<enum index="3">
		<value>,0,,2</value>
		<ui>3G only</ui>
	</enum>
</enum_list>
</var>

<var name="cell.op.name" type="string" default="">
<ui>Cellular Operator Name</ui>
<description>Operator Name (read only)</description>
<uvar>7</uvar>
</var>

<var name="cell.offmode" type="string" default="0">
<ui>Keep Cellular Powered</ui>
<description>Flag to Keep cellular module powered when turning profile off</description>
<uvar>8</uvar>
</var>

<var name="cell.sq" type="string" default="">
<ui>Cellular Signal Quality</ui>
<description>Signal Quality (read only)</description>
<uvar>9</uvar>
</var>

</vars-list>
</template>

<template name=";Cinterion|PHS8">
<id>[$$dev.port$$];;Cinterion|PHS8@[$$cell.rate$$]</id>
<version>1.0</version>
<description>Cinterion PHS8 3G module</description>
<compat-version>1</compat-version>

<profiles-list>
<profile name="internet">
	<description>Connect to Internet using GPRS by cellular modem</description>
	<block id="1" type="script" script="checkgsm">
		<branch from="0" to="0" id="3"></branch>

		<branch from="1" to="1" id="9"></branch>

		<branch from="2" to="15" id="2">
			<try times="1" id="1"></try></branch>
	</block>
	<block id="2" type="script" script="togsm">
		<branch from="0" to="0" id="3"></branch>

		<branch from="1" to="1" id="9"></branch>

		<branch from="2" to="15" id="2"></branch>
	</block>
	<block id="3" type="script" script="initgsm">
		<branch from="0" to="0" id="4"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="2" id="2">
			<try times="30" id="3"></try></branch>
		<branch from="3" to="15" id="4"></branch>
	</block>
	<block id="4" type="script" script="setpin">
		<branch from="0" to="0" id="10"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="2" id="1">
			<try times="2" id="4"></try></branch>
		<branch from="3" to="3" id="11">
			<try times="20" id="4"></try></branch>
		<branch from="4" to="15" id="5"></branch>
	</block>
	<block id="5" type="script" script="setgprs">
		<branch from="0" to="0" id="6"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="3">
			<try times="10" id="5"></try></branch>
	</block>
	<block id="6" type="script" script="setppp">
		<branch from="0" to="0" id="7"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="5">
			<try times="30" id="6"></try></branch>
	</block>
	<block id="7" type="ppp" script="runppp">
		<branch from="0" to="0" id="6"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="6"></branch>
	</block>
	<block id="8" type="script" script="hangup">
		<branch from="0" to="1" id="9"></branch>

		<branch from="2" to="2" id="9">
			<try times="5" id="8"></try></branch>
		<branch from="3" to="15" id="9"></branch>
	</block>
	<block id="9" type="script" script="fromgsm">
		<branch from="0" to="0" id="0"></branch>
		<branch from="2" to="2" id="0">
			<try times="5" id="9"></try></branch>
		<branch from="3" to="3" id="0"></branch>
		<branch from="4" to="15" id="0">
			<try times="5" id="9"></try></branch>
	</block>
	<block id="10" type="script" script="error">
		<branch from="0" to="0" id="10"></branch>

		<branch from="1" to="15" id="8"></branch>
	</block>
	<block id="11" type="script" script="simreset">
		<branch from="0" to="0" id="3"></branch>
		<branch from="1" to="1" id="8"></branch>
		<branch from="2" to="2" id="3"></branch>
		<branch from="3" to="15" id="3"></branch>
	</block>
</profile>
<profile name="c-master">
	<description>Start outgoing cellular data connection</description>
	<block id="1" type="script" script="checkgsm">
		<branch from="0" to="0" id="3"></branch>

		<branch from="1" to="1" id="9"></branch>

		<branch from="2" to="15" id="2">
			<try times="1" id="1"></try></branch>
	</block>
	<block id="2" type="script" script="togsm">
		<branch from="0" to="0" id="3"></branch>

		<branch from="1" to="1" id="9"></branch>

		<branch from="2" to="15" id="2"></branch>
	</block>
	<block id="3" type="script" script="initgsm">
		<branch from="0" to="0" id="4"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="2" id="2">
			<try times="30" id="3"></try></branch>
		<branch from="3" to="15" id="4"></branch>
	</block>
	<block id="4" type="script" script="setpin">
		<branch from="0" to="0" id="10"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="2" id="1">
			<try times="2" id="4"></try></branch>
		<branch from="3" to="3" id="12">
			<try times="20" id="4"></try></branch>
		<branch from="4" to="15" id="5"></branch>
	</block>
	<block id="5" type="script" script="setgsm">
		<branch from="0" to="0" id="6"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="3">
			<try times="10" id="5"></try></branch>
	</block>
	<block id="6" type="script" script="setgsmm">
		<branch from="0" to="0" id="7"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="2" id="12">
			<try times="30" id="6"></try></branch>
		<branch from="3" to="15" id="5">
			<try times="30" id="6"></try></branch>

	</block>
	<block id="7" type="direct" script="rungsm">
		<branch from="0" to="0" id="6"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="11"></branch>
	</block>
	<block id="8" type="script" script="hangup">
		<branch from="0" to="1" id="9"></branch>

		<branch from="2" to="2" id="9">
			<try times="5" id="8"></try></branch>
		<branch from="3" to="15" id="9"></branch>
	</block>
	<block id="9" type="script" script="fromgsm">
		<branch from="0" to="0" id="0"></branch>

		<branch from="2" to="15" id="0">
			<try times="5" id="9"></try></branch>
	</block>
	<block id="10" type="script" script="error">
		<branch from="0" to="0" id="10"></branch>

		<branch from="1" to="15" id="8"></branch>
	</block>
	<block id="11" type="script" script="resetgsm">
		<branch from="0" to="0" id="5"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="2" id="2">
			<try times="5" id="11"></try></branch>
		<branch from="3" to="15" id="2"></branch>
	</block>
	<block id="12" type="script" script="simreset">
		<branch from="0" to="0" id="3"></branch>
		<branch from="1" to="1" id="8"></branch>
		<branch from="2" to="2" id="3"></branch>
		<branch from="3" to="15" id="3"></branch>
	</block> 
</profile>

<profile name="c-slave">
	<description>Wait for incoming cellular data call</description>
	<block id="1" type="script" script="checkgsm">
		<branch from="0" to="0" id="3"></branch>

		<branch from="1" to="1" id="9"></branch>

		<branch from="2" to="15" id="2">
			<try times="1" id="1"></try></branch>
	</block>
	<block id="2" type="script" script="togsm">
		<branch from="0" to="0" id="3"></branch>

		<branch from="1" to="1" id="9"></branch>

		<branch from="2" to="15" id="2"></branch>
	</block>
	<block id="3" type="script" script="initgsm">
		<branch from="0" to="0" id="4"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="2" id="2">
			<try times="30" id="3"></try></branch>
		<branch from="3" to="15" id="4"></branch>
	</block>
	<block id="4" type="script" script="setpin">
		<branch from="0" to="0" id="10"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="2" id="1">
			<try times="2" id="4"></try></branch>
		<branch from="3" to="3" id="12">
			<try times="20" id="4"></try></branch>
		<branch from="4" to="15" id="5"></branch>
	</block>
	<block id="5" type="script" script="setgsm">
		<branch from="0" to="0" id="6"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="3">
			<try times="10" id="5"></try></branch>
	</block>
	<block id="6" type="script" script="setgsms">
		<branch from="0" to="0" id="7"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="2" id="5">
			<try times="30" id="6"></try></branch>
		<branch from="3" to="3" id="7"></branch>

		<branch from="4" to="15" id="5">
			<try times="3" id="6"></try></branch>
	</block>
	<block id="7" type="direct" script="rungsm">
		<branch from="0" to="0" id="6"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="11"></branch>
	</block>
	<block id="8" type="script" script="hangup">
		<branch from="0" to="1" id="9"></branch>

		<branch from="2" to="2" id="9">
			<try times="5" id="8"></try></branch>
		<branch from="3" to="15" id="9"></branch>
	</block>
	<block id="9" type="script" script="fromgsm">
		<branch from="0" to="0" id="0"></branch>

		<branch from="2" to="15" id="0">
			<try times="5" id="9"></try></branch>
	</block>
	<block id="10" type="script" script="error">
		<branch from="0" to="0" id="10"></branch>

		<branch from="1" to="15" id="8"></branch>
	</block>
	<block id="11" type="script" script="resetgsm">
		<branch from="0" to="0" id="5"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="2" id="2">
			<try times="5" id="11"></try></branch>
		<branch from="3" to="15" id="2"></branch>
	</block> 
	<block id="12" type="script" script="simreset">
		<branch from="0" to="0" id="3"></branch>
		<branch from="1" to="1" id="8"></branch>
		<branch from="2" to="2" id="3"></branch>
		<branch from="3" to="15" id="3"></branch>
	</block>
</profile>

</profiles-list>

<scripts-list>
<script name="checkgsm">
<![CDATA[$ABORT||$ENDLINE|\r|$TIMEOUT|15|$REPORT|M105#Looking for modem|$DAISY|OFF||dm\r\n\p%%|RE002%%|%pc%set,pwr/cell,on|ER:RE|%%dm,[$$dev.port$$]|RE|%%set,/par[$$dev.port$$]/rate,[$$cell.rate$$]|RE|%%set,/par[$$dev.port$$]/rtscts,on|RE||$DAISY|[$$dev.port$$]|$TIMEOUT|20||AT|OK-AT-OK-AT-OK-AT-OK|AT\^SCFG="MEopMode/PwrSave"|\^SCFG\:||"enabled","52","50"||OK]]>
</script>

<script name="togsm">
<![CDATA[$ABORT||$ENDLINE|\r|$TIMEOUT|15|$DAISY|OFF||dm\r\n\p%%|RE002%%|%%dm,[$$dev.port$$]|RE||$REPORT|M106#Configuring modem||%%set,/par[$$dev.port$$]/rate,[$$cell.rate$$]|RE|%%set,/par[$$dev.port$$]/rtscts,off|RE||$DAISY|[$$dev.port$$]|$TIMEOUT|15||AT|OK-AT-OK|ATI|Cinterion||OK|AT\^SCFG="MEopMode/PwrSave","enabled","52","50"|OK||$WAIT|10|$DAISY|OFF||dm\r\n\p%%|RE002%%|%%set,/par[$$dev.port$$]/rate,[$$cell.rate$$]|RE|%%set,/par[$$dev.port$$]/rtscts,on|RE||$DAISY|[$$dev.port$$]|]]>
</script>

<script name="initgsm">
<![CDATA[$ABORT||$ENDLINE|\r|$TIMEOUT|10||AT|OK||$TIMEOUT|20|$REPORT|M106#Configuring modem||ATV1|OK|ATE0|OK|AT\\Q3|OK|AT+CMEE=0|OK|AT\^SAD=12|\^SAD\:||10-AT\^SAD=10-10||OK||$ABORT|SDPORT\: 2||AT\^SDPORT?|OK|AT\^SDPORT=2|OK|\pAT|OK]]>
</script>

<script name="setpin">
<![CDATA[$ABORT||$ENDLINE|\r|$TIMEOUT|10||AT|OK|AT+CMEE=2|OK||$REPORT|M107#Checking SIM card|$ABORT|SIM wrong:READY|$WAIT|5||AT+CPIN?|+CPIN\:||SIM PIN||OK-AT-OK||$TIMEOUT|30|$REPORT|M108#Entering PIN|$ABORT|||\pAT+CPIN="[$$cell.pin$$]"|OK:ERROR||$ABORT|#---#:READY||AT+CPIN?|+CPIN\:||SIM||$REPORT|E101#Wrong PIN|]]>
</script>

<script name="setgprs">
<![CDATA[$ABORT||$TIMEOUT|10|$REPORT|M101#Registering||\p+++\p\pATH|OK:ERROR|AT+CGMI|Cinterion||OK|AT&D0|OK|ATS0=0|OK|AT+CMEE=0|OK|AT+CREG=0|OK|AT+CGREG=0|OK||$ABORT|ERROR|$TIMEOUT|300||AT+COPS=[$$cell.3g.enable$$]|OK||$TIMEOUT|10||AT+WS46?|+WS46||12:22:25||OK]]>
</script>

<script name="setppp">
<![CDATA[$ABORT|99,99|$TIMEOUT|10||AT+CREG?|+CREG\:||[$$cell.roam$$]||OK|AT+CSQ|+CSQ\:||OK|AT+CSQ|+CSQ\:||$9,||OK|AT+COPS?|+COPS\:||,"||[$$cell.op.name$$]"||OK|AT+CGDCONT=1,"IP","[$$cell.gprs.apn$$]"|OK||$ABORT|NO CARRIER:BUSY:NO ANSWER:ERROR|$REPORT|M102#Dialing||ATD[$$cell.gprs.dial$$]|$TIMEOUT|400|CONNECT||]]>
</script>

<script name="setgsm">
<![CDATA[$ABORT||$TIMEOUT|10|$REPORT|M101#Registering||AT+CGMI|Cinterion||OK|AT&D0|OK|ATS0=0|OK|AT+CMEE=0|OK|ATH|OK:ERROR|AT+CREG=0|OK||$ABORT|ERROR|$TIMEOUT|300||AT+COPS=,0,,0|OK||$TIMEOUT|10||AT+WS46?|12||OK|AT+CSQ|+CSQ\:||$9,||OK|AT+COPS?|+COPS\:||,"||[$$cell.op.name$$]"||OK|]]>
</script>

<script name="setgsmm">
<![CDATA[$ABORT|99,99|$TIMEOUT|10||AT+CREG?|+CREG\:||[$$cell.roam$$]||OK|AT+CSQ|+CSQ\:||OK|AT+CSQ|+CSQ\:||$9,||OK|AT+COPS?|+COPS\:||,"||[$$cell.op.name$$]"||OK|AT+CBST=7|OK|AT+CBST=[$$cell.csd.cbst$$]|OK:ERROR||$ABORT|NO CARRIER:BUSY:NO ANSWER:ERROR|$REPORT|M102#Dialing||ATD[$$cell.csd.dial$$]|$TIMEOUT|400|CONNECT||]]>
</script>

<script name="setgsms">
<![CDATA[$ABORT|CONNECT:NO CARRIER:99,99|$TIMEOUT|10||AT+CREG?|+CREG\:||[$$cell.roam$$]||OK|AT+CSQ|+CSQ\:||OK|AT+CSQ|+CSQ\:||$9,||OK|AT+COPS?|+COPS\:||,"||[$$cell.op.name$$]"||OK|ATS0=2|OK||$TIMEOUT|3000|$REPORT|M103#Awaiting call|RING|ATA|$TIMEOUT|200|CONNECT||]]>
</script>

<script name="hangup">
<![CDATA[$ABORT||$TIMEOUT|20||\p+++\p\p|OK-AT-OK|ATI|OK:ERROR|ATH|OK:ERROR|ATS0=0|OK:ERROR|]]>
</script>

<script name="fromgsm">
<![CDATA[$ABORT||$TIMEOUT|20|$DAISY|OFF|$REPORT|M106#Configuring modem||dm\r\n\p%%|RE002%%|%%set,/par[$$dev.port$$]/rate,[$$cell.rate$$]|RE||$ABORT|%1%||%[$$cell.offmode$$]%|RE||%0%:%%||$ABORT||$DAISY|[$$dev.port$$]|$TIMEOUT|60||AT|OK|AT\^SMSO|OK||$WAIT|30|$DAISY|OFF|$TIMEOUT|20||%%|RE002%%|%%set,pwr/cell,off|RE:ER]]>
</script>

<script name="rungsm">
<![CDATA[$TIMEOUT|[$$cell.csd.idle$$]|$ABORT|NO CARRIER:ERROR:RING]]>
</script>

<script name="runppp">
<![CDATA[[$$dev.port$$]|[$$cell.rate$$]|[$$ppp.ip$$]:192.168.255.1|novj|novjccomp|lcp-echo-interval:15|lcp-echo-failure:2|lcp-restart:5|ipcp-accept-local|ipcp-accept-remote|ipcp-max-failure:3|ipcp-max-configure:10|usepeerdns|noipdefault|noproxyarp|idle:[$$ppp.idle$$]|name:[$$ppp.name$$]|password:[$$ppp.password$$]]]>
</script>

<script name="error">
<![CDATA[$ABORT||$WAIT|10|]]>
</script>

<script name="resetgsm">
<![CDATA[$ABORT||$TIMEOUT|60||\p+++\p\p|OK-AT-OK||$TIMEOUT|10||ATH|OK:ERROR|AT+CGMI|Cinterion||OK]]>
</script>

<script name="simreset">
<![CDATA[$ABORT|\^SYSSTART:SIM PIN|$TIMEOUT|20||AT+CPIN?|SIM wrong|ATE1|OK||$TIMEOUT|100||\pAT+CFUN=1,1|OK||$TIMEOUT|200|\^SYSSTART]]>
</script>

</scripts-list>

<vars-list>
<var name="dev.port" type="enum" default="3">
<ui>Port</ui>
<description>Name of hardware serial port that is connected to modem</description>
<enum_list>
	<enum index="1">
		<value>/dev/ser/a</value>
	</enum>
	<enum index="2">
		<value>/dev/ser/b</value>
	</enum>
	<enum index="3">
		<value>/dev/ser/c</value>
	</enum>
	<enum index="4">
		<value>/dev/ser/d</value>
	</enum>
</enum_list>
</var>

<var name="cell.rate" type="enum" default="5">
<ui>Baud Rate</ui>
<description>Baud rate of cellular module</description>
<enum_list>
	<enum index="1">
		<value>9600</value>
	</enum>
	<enum index="2">
		<value>19200</value>
	</enum>
	<enum index="3">
		<value>38400</value>
	</enum>
	<enum index="4">
		<value>57600</value>
	</enum>
	<enum index="5">
		<value>115200</value>
	</enum>
	<enum index="6">
		<value>230400</value>
	</enum>
	<enum index="7">
		<value>460800</value>
	</enum>
</enum_list>
</var>

<var name="cell.pin" type="string" default="0000">
<ui>PIN Code</ui>
<description>SIM PIN code</description>
<uvar>0</uvar>
</var>

<var name="cell.gprs.dial" type="string" default="*99***1#">
<ui>GPRS Dial</ui>
<description>GPRS Dial Number</description>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="cell.gprs.apn" type="string" default="">
<ui>APN</ui>
<description>GPRS APN</description>
<uvar>1</uvar>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="ppp.name" type="string" default="">
<ui>User</ui>
<description>GPRS User Name</description>
<uvar>2</uvar>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="ppp.password" type="string" default="">
<ui>Password</ui>
<description>GPRS Password</description>
<uvar>3</uvar>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="ppp.ip" type="string" default="">
<ui>IP address</ui>
<description>Static PPP address</description>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="ppp.idle" type="numeric" default="0">
<ui>Timeout</ui>
<description>GPRS Reconnection Timeout if datalink is lost</description>
<range min="0" max="9999">
<uifactor>0.1</uifactor>
</range>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="cell.roam" type="enum" default="1">
<ui>Roaming</ui>
<description>Allow network roaming</description>
<profiles>
	<name>internet</name>
	<name>c-master</name>
	<name>c-slave</name>
</profiles>
<enum_list>
	<enum index="1">
		<value>,1:,5</value>
		<ui>Enabled</ui>
	</enum>
	<enum index="2">
		<value>,1</value>
		<ui>Disabled</ui>
	</enum>
</enum_list>
</var>

<var name="cell.csd.cbst" type="enum" default="1">
<ui>Data Call Type</ui>
<description>Bearer type for outgoing and incoming data calls</description>
<uvar>6</uvar>
<profiles>
	<name>c-master</name>
	<name>c-slave</name>
</profiles>
<enum_list>
	<enum index="1">
		<value>0</value>
		<ui>Automatic</ui>
	</enum>
	<enum index="2">
		<value>7</value>
		<ui>Analog V.32</ui>
	</enum>
	<enum index="3">
		<value>71</value>
		<ui>Digital V.110</ui>
	</enum>
</enum_list>
</var>

<var name="cell.csd.dial" type="string" default="">
<ui>Dial Number</ui>
<description>CSD Base Phone Number</description>
<uvar>5</uvar>
<profiles>
	<name>c-master</name>
</profiles>
</var>

<var name="cell.csd.idle" type="numeric" default="300">
<ui>CSD Timeout</ui>
<description>Hangup CSD if no data is received within timeout threshold</description>
<range min="0" max="9999">
<uifactor>0.1</uifactor>
</range>
<profiles>
	<name>c-master</name>
	<name>c-slave</name>
</profiles>
</var>

<var name="cell.3g.enable" type="enum" default="1">
<ui>3G Mode</ui>
<description>Use 3G technology for Internet access</description>
<enum_list>
	<enum index="1">
		<value>0</value>
		<ui>Automatic</ui>
	</enum>
	<enum index="2">
		<value>,0,,0</value>
		<ui>2G only</ui>
	</enum>
	<enum index="3">
		<value>,0,,2</value>
		<ui>3G only</ui>
	</enum>
</enum_list>
</var>

<var name="cell.op.name" type="string" default="">
<ui>Cellular Operator Name</ui>
<description>Operator Name (read only)</description>
<uvar>7</uvar>
</var>

<var name="cell.offmode" type="string" default="0">
<ui>Keep Cellular Powered</ui>
<description>Flag to Keep cellular module powered when turning profile off</description>
<uvar>8</uvar>
</var>

<var name="cell.sq" type="string" default="">
<ui>Cellular Signal Quality</ui>
<description>Signal Quality (read only)</description>
<uvar>9</uvar>
</var>

</vars-list>
</template>

<template name="Topcon|DUHF2;Topcon|H24RC/UE866-EU">
<id>[$$dev.port$$];Topcon|DUHF2@[$$radio.rate$$];Topcon|H24RC/UE866-EU@[$$cell.rate$$]</id>
<version>1.0</version>
<description>Digital UHF II modem with H24 Replacement Card (EU)</description>
<compat-version>1</compat-version>

<profiles-list>
<profile name="internet">
	<description>Connect to Internet using GPRS by cellular modem</description>
	<block id="1" type="script" script="checkgsm">
		<branch from="0" to="0" id="3"></branch>

		<branch from="1" to="1" id="9"></branch>

		<branch from="2" to="15" id="2">
			<try times="1" id="1"></try></branch>
	</block>
	<block id="2" type="script" script="togsm">
		<branch from="0" to="0" id="3"></branch>

		<branch from="1" to="1" id="9"></branch>

		<branch from="2" to="15" id="2"></branch>
	</block>
	<block id="3" type="script" script="initgsm">
		<branch from="0" to="0" id="4"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="2" id="2">
			<try times="30" id="3"></try></branch>
		<branch from="3" to="15" id="4"></branch>
	</block>
	<block id="4" type="script" script="setpin">
		<branch from="0" to="0" id="11"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="3" id="1">
			<try times="2" id="4"></try></branch>
		<branch from="3" to="3" id="8">
			<try times="20" id="4"></try></branch>
		<branch from="4" to="15" id="5"></branch>
	</block>
	<block id="5" type="script" script="setgprs">
		<branch from="0" to="0" id="6"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="3">
			<try times="10" id="5"></try></branch>
	</block>
	<block id="6" type="script" script="setppp">
		<branch from="0" to="0" id="7"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="2" id="8">
			<try times="10" id="6"></try></branch>
		<branch from="3" to="15" id="5">
			<try times="30" id="6"></try></branch>
	</block>
	<block id="7" type="ppp" script="runppp">
		<branch from="0" to="0" id="6"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="6"></branch>
	</block>
	<block id="8" type="script" script="hangup">
		<branch from="0" to="1" id="9"></branch>

		<branch from="2" to="2" id="9">
			<try times="2" id="8"></try></branch>
		<branch from="3" to="15" id="9"></branch>
	</block>
	<block id="9" type="script" script="shutgsm">
		<branch from="0" to="1" id="10"></branch>
		<branch from="2" to="2" id="10">
			<try times="2" id="9"></try></branch>
		<branch from="3" to="3" id="0"></branch>
		<branch from="4" to="15" id="10">
			<try times="2" id="9"></try></branch>
	</block>
	<block id="10" type="script" script="touhf">
		<branch from="0" to="0" id="0"></branch>
		<branch from="2" to="15" id="0">
			<try times="5" id="10"></try></branch>
	</block>
	<block id="11" type="script" script="error">
		<branch from="0" to="0" id="11"></branch>
        
		<branch from="1" to="15" id="8"></branch>
	</block>
</profile>

<profile name="c-master">
	<description>Start outgoing cellular data connection</description>
	<block id="1" type="script" script="checkgsm">
		<branch from="0" to="0" id="3"></branch>

		<branch from="1" to="1" id="9"></branch>

		<branch from="2" to="15" id="2">
			<try times="1" id="1"></try></branch>
	</block>
	<block id="2" type="script" script="togsm">
		<branch from="0" to="0" id="3"></branch>

		<branch from="1" to="1" id="9"></branch>

		<branch from="2" to="15" id="2"></branch>
	</block>
	<block id="3" type="script" script="initgsm">
		<branch from="0" to="0" id="4"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="2" id="2">
			<try times="30" id="3"></try></branch>
		<branch from="3" to="15" id="4"></branch>
	</block>
	<block id="4" type="script" script="setpin">
		<branch from="0" to="0" id="11"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="2" id="1">
			<try times="2" id="4"></try></branch>
		<branch from="3" to="3" id="8">
			<try times="20" id="4"></try></branch>
		<branch from="4" to="15" id="5"></branch>
	</block>
	<block id="5" type="script" script="setgsm">
		<branch from="0" to="0" id="6"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="3">
			<try times="10" id="5"></try></branch>
	</block>
	<block id="6" type="script" script="setgsmm">
		<branch from="0" to="0" id="7"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="2" id="8">
			<try times="30" id="6"></try></branch>
		<branch from="3" to="15" id="5">
			<try times="30" id="6"></try></branch>
	</block>
	<block id="7" type="direct" script="rungsm">
		<branch from="0" to="0" id="6"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="5"></branch>
	</block>
	<block id="8" type="script" script="hangup">
		<branch from="0" to="1" id="9"></branch>

		<branch from="2" to="2" id="9">
			<try times="5" id="8"></try></branch>
		<branch from="3" to="15" id="9"></branch>
	</block>
	<block id="9" type="script" script="shutgsm">
		<branch from="0" to="1" id="10"></branch>
		<branch from="2" to="2" id="10">
			<try times="2" id="9"></try></branch>
		<branch from="3" to="3" id="0"></branch>
		<branch from="4" to="15" id="10">
			<try times="2" id="9"></try></branch>
	</block>
	<block id="10" type="script" script="touhf">
		<branch from="0" to="0" id="0"></branch>
		<branch from="2" to="15" id="0">
			<try times="5" id="10"></try></branch>
	</block>
	<block id="11" type="script" script="error">
		<branch from="0" to="0" id="11"></branch>

		<branch from="1" to="15" id="8"></branch>
	</block>
</profile>

<profile name="c-slave">
	<description>Wait for incoming cellular data call</description>
	<block id="1" type="script" script="checkgsm">
		<branch from="0" to="0" id="3"></branch>

		<branch from="1" to="1" id="9"></branch>

		<branch from="2" to="15" id="2">
			<try times="1" id="1"></try></branch>
	</block>
	<block id="2" type="script" script="togsm">
		<branch from="0" to="0" id="3"></branch>

		<branch from="1" to="1" id="9"></branch>

		<branch from="2" to="15" id="2"></branch>
	</block>
	<block id="3" type="script" script="initgsm">
		<branch from="0" to="0" id="4"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="2" id="2">
			<try times="30" id="3"></try></branch>
		<branch from="3" to="15" id="4"></branch>
	</block>
	<block id="4" type="script" script="setpin">
		<branch from="0" to="0" id="11"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="2" id="1">
			<try times="2" id="4"></try></branch>
		<branch from="3" to="3" id="8">
			<try times="20" id="4"></try></branch>
		<branch from="4" to="15" id="5"></branch>
	</block>
	<block id="5" type="script" script="setgsm">
		<branch from="0" to="0" id="6"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="3">
			<try times="10" id="5"></try></branch>
	</block>
	<block id="6" type="script" script="setgsms">
		<branch from="0" to="0" id="7"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="2" id="5">
			<try times="30" id="6"></try></branch>
		<branch from="3" to="3" id="7"></branch>

		<branch from="4" to="15" id="5">
			<try times="3" id="6"></try></branch>
	</block>
	<block id="7" type="direct" script="rungsm">
		<branch from="0" to="0" id="6"></branch>

		<branch from="1" to="1" id="8"></branch>

		<branch from="2" to="15" id="5"></branch>
	</block>
	<block id="8" type="script" script="hangup">
		<branch from="0" to="1" id="9"></branch>

		<branch from="2" to="2" id="9">
			<try times="5" id="8"></try></branch>
		<branch from="3" to="15" id="9"></branch>
	</block>
	<block id="9" type="script" script="shutgsm">
		<branch from="0" to="1" id="10"></branch>
		<branch from="2" to="2" id="10">
			<try times="2" id="9"></try></branch>
		<branch from="3" to="3" id="0"></branch>
		<branch from="4" to="15" id="10">
			<try times="2" id="9"></try></branch>
	</block>
	<block id="10" type="script" script="touhf">
		<branch from="0" to="0" id="0"></branch>
		<branch from="2" to="15" id="0">
			<try times="5" id="10"></try></branch>
	</block>
	<block id="11" type="script" script="error">
		<branch from="0" to="0" id="11"></branch>

		<branch from="1" to="15" id="8"></branch>
	</block>
</profile>

</profiles-list>

<scripts-list>
<script name="checkgsm">
<![CDATA[$ABORT||$ENDLINE|\r|$TIMEOUT|15|$REPORT|M105#Looking for modem|$DAISY|OFF||dm\r\n\p%%|RE002%%|%%dm,[$$dev.port$$]|RE|%%set,/par[$$dev.port$$]/rate,[$$cell.rate$$]|RE|%%set,/par[$$dev.port$$]/rts,on|RE|%%set,/par[$$dev.port$$]/rtscts,on|RE||$DAISY|[$$dev.port$$]|$TIMEOUT|10||AT|OK-AT-OK-AT-OK|]]>
</script>

<script name="togsm">
<![CDATA[$ABORT||$ENDLINE|\r|$TIMEOUT|15|$DAISY|OFF||dm\r\n\p%%|RE002%%|%%dm,[$$dev.port$$]|RE||$REPORT|M106#Configuring modem||%%set,/par[$$dev.port$$]/rate,[$$radio.rate$$]|RE|%%set,/par[$$dev.port$$]/rtscts,off|RE||$DAISY|[$$dev.port$$]|$TIMEOUT|15||++++\p|@00-++++-@01|ATI|Topcon||@00|LINK RFSW|0-LINK RFSW 0\n\p\pDATAMODE\n\p\p\p\p\p-@00|LINK RFSW 1|@00|\p\pDATAMODE|$WAIT|10|$DAISY|OFF||dm\r\n\p%%|RE002%%|%%set,/par[$$dev.port$$]/rate,[$$cell.rate$$]|RE|%%set,/par[$$dev.port$$]/rts,on|RE|%%set,/par[$$dev.port$$]/rtscts,on|RE||$DAISY|[$$dev.port$$]|]]>
</script>

<script name="initgsm">
<![CDATA[$ABORT|ERROR|$ENDLINE|\r|$TIMEOUT|10||AT|OK||$TIMEOUT|20|$REPORT|M106#Configuring modem||ATV1&D0|OK|ATE0S0=0|OK|AT#CFLO=1|OK|AT+CMEE=0|OK]]>
</script>

<script name="setpin">
<![CDATA[$ABORT|ERROR|$ENDLINE|\r|$TIMEOUT|10||AT|OK|AT+CMEE=2|OK||$REPORT|M107#Checking SIM card|$ABORT|SIM busy:READY|$WAIT|5||AT+CPIN?|+CPIN\:||SIM PIN||OK-AT-OK||$TIMEOUT|30|$REPORT|M108#Entering PIN|$ABORT|||\pAT+CPIN="[$$cell.pin$$]"|OK:ERROR||$ABORT|#---#:READY||AT+CPIN?|+CPIN\:||SIM||$REPORT|E101#Wrong PIN|]]>
</script>

<script name="setgprs">
<![CDATA[$ABORT||$TIMEOUT|10|$REPORT|M101#Registering||\p+++\p\pATH|OK:ERROR|AT+CMEE=0|OK|AT+CREG=0|OK|AT+CGREG=0|OK||$ABORT|ERROR|$TIMEOUT|300||AT+WS46=[$$cell.3g.enable$$]|OK||$TIMEOUT|10||AT+WS46?|12:22:25||OK]]>
</script>

<script name="setppp">
<![CDATA[$ABORT|0,2|$TIMEOUT|10||\pAT+CREG?|+CREG\:||[$$cell.roam$$]||OK||$ABORT|99,99||AT+CSQ|+CSQ\:||OK|AT+CSQ|+CSQ\:||$9,||OK|AT+COPS?|+COPS\:||,"||[$$cell.op.name$$]"||OK|AT+CGDCONT=1,"IP","[$$cell.gprs.apn$$]"|OK||$ABORT|NO CARRIER:BUSY:NO ANSWER:ERROR|$REPORT|M102#Dialing||ATD[$$cell.gprs.dial$$]|$TIMEOUT|400|CONNECT||]]>
</script>

<script name="setgsm">
<![CDATA[$ABORT||$TIMEOUT|10|$REPORT|M101#Registering||\p+++\p\pATH|OK:ERROR|AT+CMEE=0|OK|AT+CREG=0|OK||$ABORT|ERROR|$TIMEOUT|300||AT+WS46=12|OK||$TIMEOUT|10||AT+WS46?|12||OK|AT+CSQ|+CSQ\:||$9,||OK|AT+COPS?|+COPS\:||,"||[$$cell.op.name$$]"||OK|]]>
</script>

<script name="setgsmm">
<![CDATA[$ABORT|99,99|$TIMEOUT|10||AT+CREG?|+CREG\:||[$$cell.roam$$]||OK|AT+CSQ|+CSQ\:||OK|AT+CSQ|+CSQ\:||$9,||OK|AT+COPS?|+COPS\:||,"||[$$cell.op.name$$]"||OK|AT+CBST=7|OK|AT+CBST=[$$cell.csd.cbst$$]|OK:ERROR||$ABORT|NO CARRIER:BUSY:NO ANSWER:ERROR|$REPORT|M102#Dialing||ATD[$$cell.csd.dial$$]|$TIMEOUT|400|CONNECT||]]>
</script>

<script name="setgsms">
<![CDATA[$ABORT|CONNECT:NO CARRIER:99,99|$TIMEOUT|10||AT+CREG?|+CREG\:||[$$cell.roam$$]||OK|AT+CSQ|+CSQ\:||OK|AT+CSQ|+CSQ\:||$9,||OK|AT+COPS?|+COPS\:||,"||[$$cell.op.name$$]"||OK|ATS0=2|OK||$TIMEOUT|3000|$REPORT|M103#Awaiting call|RING|ATA|$TIMEOUT|200|CONNECT||]]>
</script>

<script name="hangup">
<![CDATA[$ABORT|Topcon:Error|$TIMEOUT|20||\p+++\p\p|OK-AT-OK|ATI|OK:ERROR|ATH|OK:ERROR|ATS0=0|OK|]]>
</script>

<script name="shutgsm">
<![CDATA[$ABORT||$TIMEOUT|15|$DAISY|OFF|$REPORT|M106#Configuring modem||dm\r\n\p%%|RE002%%|%%set,/par[$$dev.port$$]/rate,[$$radio.rate$$]|RE|%%set,/par[$$dev.port$$]/rtscts,off|RE||$ABORT|%1%||%[$$cell.offmode$$]%|RE||%0%:%%||$ABORT|||%%set,/par[$$dev.port$$]/rate,[$$cell.rate$$]|RE||$TIMEOUT|10|$DAISY|[$$dev.port$$]||AT|OK||$TIMEOUT|30||AT#SYSHALT|OK||$WAIT|90|$DAISY|OFF]]>
</script>

<script name="touhf">
<![CDATA[$ABORT||$TIMEOUT|15|$DAISY|OFF||dm\r\n\p%%|RE002%%|%%dm,[$$dev.port$$]|RE|%%set,/par[$$dev.port$$]/rate,[$$radio.rate$$]|RE|%%set,/par[$$dev.port$$]/rtscts,off|RE||$DAISY|[$$dev.port$$]|$TIMEOUT|15||++++\p|@00-++++-@01|ATI|Topcon||@00|LINK RFSW 0|@00|\p\pDATAMODE|$WAIT|10|$DAISY|OFF]]>
</script>

<script name="rungsm">
<![CDATA[$TIMEOUT|[$$cell.csd.idle$$]|$ABORT|NO CARRIER:ERROR:RING]]>
</script>

<script name="runppp">
<![CDATA[[$$dev.port$$]|[$$cell.rate$$]|[$$ppp.ip$$]:192.168.255.1|novj|novjccomp|lcp-echo-interval:10|lcp-echo-failure:2|default-asyncmap|lcp-restart:5|ipcp-accept-local|ipcp-accept-remote|ipcp-max-failure:3|ipcp-max-configure:10|usepeerdns|noipdefault|noproxyarp|idle:[$$ppp.idle$$]|name:[$$ppp.name$$]|password:[$$ppp.password$$]]]>
</script>

<script name="error">
<![CDATA[$ABORT||$WAIT|10|]]>
</script>

</scripts-list>

<vars-list>
<var name="dev.port" type="enum" default="3">
<ui>Port</ui>
<description>Name of hardware serial port that is connected to modem</description>
<enum_list>
	<enum index="1">
		<value>/dev/ser/a</value>
	</enum>
	<enum index="2">
		<value>/dev/ser/b</value>
	</enum>
	<enum index="3">
		<value>/dev/ser/c</value>
	</enum>
	<enum index="4">
		<value>/dev/ser/d</value>
	</enum>
</enum_list>
</var>

<var name="radio.rate" type="enum" default="6">
<ui>Baud Rate</ui>
<description>Baud rate of modem serial interface</description>
<enum_list>
	<enum index="1">
		<value>1200</value>
	</enum>
	<enum index="2">
		<value>2400</value>
	</enum>
	<enum index="3">
		<value>4800</value>
	</enum>
	<enum index="4">
		<value>9600</value>
	</enum>
	<enum index="5">
		<value>19200</value>
	</enum>
	<enum index="6">
		<value>38400</value>
	</enum>
	<enum index="7">
		<value>57600</value>
	</enum>
	<enum index="8">
		<value>115200</value>
	</enum>
</enum_list>
</var>

<var name="cell.rate" type="enum" default="8">
<ui>Baud Rate</ui>
<description>Baud rate of cellular module</description>
<enum_list>
	<enum index="1">
		<value>1200</value>
	</enum>
	<enum index="2">
		<value>2400</value>
	</enum>
	<enum index="3">
		<value>4800</value>
	</enum>
	<enum index="4">
		<value>9600</value>
	</enum>
	<enum index="5">
		<value>19200</value>
	</enum>
	<enum index="6">
		<value>38400</value>
	</enum>
	<enum index="7">
		<value>57600</value>
	</enum>
	<enum index="8">
		<value>115200</value>
	</enum>
</enum_list>
</var>

<var name="cell.pin" type="string" default="0000">
<ui>PIN Code</ui>
<description>SIM PIN code</description>
<uvar>0</uvar>
</var>

<var name="cell.gprs.dial" type="string" default="*99***1#">
<ui>GPRS Dial</ui>
<description>GPRS Dial Number</description>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="cell.gprs.apn" type="string" default="">
<ui>APN</ui>
<description>GPRS APN</description>
<uvar>1</uvar>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="ppp.name" type="string" default="">
<ui>User</ui>
<description>GPRS User Name</description>
<uvar>2</uvar>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="ppp.password" type="string" default="">
<ui>Password</ui>
<description>GPRS Password</description>
<uvar>3</uvar>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="ppp.ip" type="string" default="">
<ui>IP address</ui>
<description>Static PPP address</description>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="ppp.idle" type="numeric" default="0">
<ui>Timeout</ui>
<description>GPRS Reconnection Timeout if datalink is lost</description>
<range min="0" max="9999">
<uifactor>0.1</uifactor>
</range>
<profiles>
	<name>internet</name>
</profiles>
</var>

<var name="cell.roam" type="enum" default="1">
<ui>Roaming</ui>
<description>Allow network roaming</description>
<profiles>
	<name>internet</name>
	<name>c-master</name>
	<name>c-slave</name>
</profiles>
<enum_list>
	<enum index="1">
		<value>,1:,5</value>
		<ui>Enabled</ui>
	</enum>
	<enum index="2">
		<value>,1</value>
		<ui>Disabled</ui>
	</enum>
</enum_list>
</var>

<var name="cell.csd.cbst" type="enum" default="1">
<ui>Data Call Type</ui>
<description>Bearer type for outgoing and incoming data calls</description>
<uvar>6</uvar>
<profiles>
	<name>c-master</name>
	<name>c-slave</name>
</profiles>
<enum_list>
	<enum index="1">
		<value>0</value>
		<ui>Automatic</ui>
	</enum>
	<enum index="2">
		<value>7</value>
		<ui>Analog V.32</ui>
	</enum>
	<enum index="3">
		<value>71</value>
		<ui>Digital V.110</ui>
	</enum>
</enum_list>
</var>

<var name="cell.csd.dial" type="string" default="">
<ui>Dial Number</ui>
<description>CSD Base Phone Number</description>
<uvar>5</uvar>
<profiles>
	<name>c-master</name>
</profiles>
</var>

<var name="cell.csd.idle" type="numeric" default="300">
<ui>CSD Timeout</ui>
<description>Hangup CSD if no data is received within timeout threshold</description>
<range min="0" max="9999">
<uifactor>0.1</uifactor>
</range>
<profiles>
	<name>c-master</name>
	<name>c-slave</name>
</profiles>
</var>

<var name="cell.3g.enable" type="enum" default="1">
<ui>3G Mode</ui>
<description>Use 3G technology for Internet access</description>
<enum_list>
	<enum index="1">
		<value>25</value>
		<ui>Automatic</ui>
	</enum>
	<enum index="2">
		<value>12</value>
		<ui>2G only</ui>
	</enum>
	<enum index="3">
		<value>22</value>
		<ui>3G only</ui>
	</enum>
</enum_list>
</var>

<var name="cell.op.name" type="string" default="">
<ui>Cellular Operator Name</ui>
<description>Operator Name (read only)</description>
<uvar>7</uvar>
</var>

<var name="cell.offmode" type="string" default="0">
<ui>Keep Cellular Powered</ui>
<description>Flag to Keep cellular module powered when turning profile off</description>
<uvar>8</uvar>
</var>

<var name="cell.sq" type="string" default="">
<ui>Cellular Signal Quality</ui>
<description>Signal Quality (read only)</description>
<uvar>9</uvar>
</var>

</vars-list>
</template>

</templates-list> 
