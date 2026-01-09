$windowWidth = 40
$windowHeight = 20

$Host.UI.RawUI.WindowSize = New-Object System.Management.Automation.Host.Size($windowWidth, $windowHeight)


Add-Type -AssemblyName System.Windows.Forms

$Form = New-Object System.Windows.Forms.Form
$Form.Text = "Internal Tool"
$Form.Width = 270
$Form.Height = 460
$Form.TopMost = $true
$Form.FormBorderStyle = [System.Windows.Forms.FormBorderStyle]::FixedDialog

$HeaderLabel = New-Object System.Windows.Forms.Label
$HeaderLabel.Text = "Komatsu GRM T1 Scripts"
$HeaderLabel.Location = New-Object System.Drawing.Point(0, 0)
$HeaderLabel.Size = New-Object System.Drawing.Size($Form.Width, 30)
$FontConverter = New-Object System.Drawing.FontConverter
$HeaderLabel.Font = $FontConverter.ConvertFrom("Arial,12")
$HeaderLabel.BackColor = "Blue"
$HeaderLabel.ForeColor = "White"
$HeaderLabel.TextAlign = "MiddleCenter"


$Button1 = New-Object System.Windows.Forms.Button
$Button1.Text = "IP Finder"
$Button1.Location = New-Object System.Drawing.Point(50, 50)
$Button1.Width = 150 
$Button1.Add_Click({ Start-Process -FilePath "C:\Komatsu_Tier1\Boxy_Adam\IP_Finder.bat" })

$Button2 = New-Object System.Windows.Forms.Button
$Button2.Text = "PTX Uptime Report"
$Button2.Location = New-Object System.Drawing.Point(50, 80)
$Button2.Width = 150 
$Button2.Add_Click({ Start-Process -FilePath "C:\Komatsu_Tier1\Boxy_Adam\PTX_Uptime.bat" })

$Button3 = New-Object System.Windows.Forms.Button
$Button3.Text = "Mineview Sessions"
$Button3.Location = New-Object System.Drawing.Point(50, 110)
$Button3.Width = 150 
$Button3.Add_Click({ Start-Process -FilePath "C:\Komatsu_Tier1\Boxy_Adam\MineView_Session.bat" })

$Button4 = New-Object System.Windows.Forms.Button
$Button4.Text = "Start PTX VNC"
$Button4.Location = New-Object System.Drawing.Point(50, 140)
$Button4.Width = 150 
$Button4.Add_Click({ Start-Process -FilePath "C:\Komatsu_Tier1\Boxy_Adam\Adam_PTXC_VNC\Start_VNC.bat" })

$Button5 = New-Object System.Windows.Forms.Button
$Button5.Text = "PTX Health Check"
$Button5.Location = New-Object System.Drawing.Point(50, 170)
$Button5.Width = 150 
$Button5.Add_Click({ Start-Process -FilePath "C:\Komatsu_Tier1\Boxy_Adam\PTXC_Health_Check.bat" })

$Button6 = New-Object System.Windows.Forms.Button
$Button6.Text = "MM2 AVI Reboot"
$Button6.Location = New-Object System.Drawing.Point(50, 200)
$Button6.Width = 150 
$Button6.Add_Click({ Start-Process -FilePath "C:\Komatsu_Tier1\Boxy_Adam\AVI_MM2_Reboot.bat" })

$Button7 = New-Object System.Windows.Forms.Button
$Button7.Text = "PTX-AVI Watchdog Deploy"
$Button7.Location = New-Object System.Drawing.Point(50, 230)
$Button7.Width = 150 
$Button7.Add_Click({ Start-Process -FilePath "C:\Komatsu_Tier1\Boxy_Adam\PTX-AVI_Watchdog_SingleDeploy\PTX-AVI_Watchdog_SingleDeploy.bat" })

$Button8 = New-Object System.Windows.Forms.Button
$Button8.Text = "Live KOA Data"
$Button8.Location = New-Object System.Drawing.Point(50, 260)
$Button8.Width = 150 
$Button8.Add_Click({ Start-Process -FilePath "C:\Komatsu_Tier1\Boxy_Adam\LIVE_KOA_DataCheck.bat" })

$Button9 = New-Object System.Windows.Forms.Button
$Button9.Text = "Live Speed Limit Data"
$Button9.Location = New-Object System.Drawing.Point(50, 290)
$Button9.Width = 150 
$Button9.Add_Click({ Start-Process -FilePath "C:\Komatsu_Tier1\Boxy_Adam\Latest_SpeedLimit_DataCheck.bat" })

$Button10 = New-Object System.Windows.Forms.Button
$Button10.Text = "Linux Perf/Usage Check"
$Button10.Location = New-Object System.Drawing.Point(50, 320)
$Button10.Width = 150 
$Button10.Add_Click({ Start-Process -FilePath "C:\Komatsu_Tier1\Boxy_Adam\Linux_Health_Check.bat" })

$Button11 = New-Object System.Windows.Forms.Button
$Button11.Text = "Field Component Tracking"
$Button11.Location = New-Object System.Drawing.Point(50, 350)
$Button11.Width = 150 
$Button11.Add_Click({ Start-Process -FilePath "C:\Komatsu_Tier1\Boxy_Adam\ComponentTracking.bat" })

$Button12 = New-Object System.Windows.Forms.Button
$Button12.Text = "Linux Logs Downloader"
$Button12.Location = New-Object System.Drawing.Point(50, 380)
$Button12.Width = 150 
$Button12.Add_Click({ Start-Process -FilePath "C:\Komatsu_Tier1\Boxy_Adam\Log_Downloader.bat" })

$Form.Controls.Add($HeaderLabel)
$Form.Controls.Add($Button1)
$Form.Controls.Add($Button2)
$Form.Controls.Add($Button3)
$Form.Controls.Add($Button4)
$Form.Controls.Add($Button5)
$Form.Controls.Add($Button6)
$Form.Controls.Add($Button7)
$Form.Controls.Add($Button8)
$Form.Controls.Add($Button9)
$Form.Controls.Add($Button10)
$Form.Controls.Add($Button11)
$Form.Controls.Add($Button12)

$Form.ShowDialog() | Out-Null


