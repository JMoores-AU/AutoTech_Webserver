WinWait "Warning" 
If WinActive 
{ 
; WinActivate "Warning" 
ControlClick "Yes" 
SendInput "{Enter}" 
} 
ExitApp 
