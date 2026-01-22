WinWait "Device Select" 
If WinActive 
{ 
; WinActivate "Device Select" 
ControlClick "Ethernet" 
Sleep 1000 
SendInput "{Enter}" 
} 
ExitApp 
