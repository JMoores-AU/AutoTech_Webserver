WinWait "Remote Desktop Connection" 
If WinActive 
{ 
; WinActivate "Remote Desktop Connection" 
ControlClick "Yes" 
SendInput "{Enter}" 
} 
ExitApp 
