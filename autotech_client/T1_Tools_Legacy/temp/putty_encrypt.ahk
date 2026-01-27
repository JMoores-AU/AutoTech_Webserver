WinWait "PuTTY Security Alert" 
IF WinActive 
{ 
; WinActivate ("PuTTY Security Alert") 
ControlClick "Yes" 
SendInput "{Enter}" 
} 
ExitApp 
