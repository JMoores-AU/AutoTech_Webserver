WinWait "127.0.0.1:5901 - Remote Desktop Connection" 
If WinActive 
{ 
; WinActivate "Log On to Windows" 
SendInput "administrator" 
Send "{Tab}" 
SendInput "komatsu" 
SendInput "{Enter}" 
} 
ExitApp 
