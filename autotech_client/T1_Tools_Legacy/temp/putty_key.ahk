WinWait "PuTTY Security Alert" 
IF WinActive 
{ 
; WinActivate ("PuTTY Security Alert") 
ControlClick "Accept" 
SendInput "{Enter}" 
} 
ExitApp 
