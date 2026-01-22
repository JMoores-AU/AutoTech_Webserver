WinWait "PuTTY Security Alert" 
If WinActive 
{ 
; WinActivate "PuTTY Security Alert" 
ControlClick "Yes" 
SendInput "{Enter}" 
} 
ExitApp 
