$windowWidth = 40
$windowHeight = 20

$Host.UI.RawUI.WindowSize = New-Object System.Management.Automation.Host.Size($windowWidth, $windowHeight)

Add-Type -AssemblyName System.Windows.Forms

$trebuchetFont = New-Object System.Drawing.Font("Trebuchet MS", 10)

# CamStudio & Playback button logic
$tools = @(
    @{
        Name = "Playback Tool"
        PlaybackPath = "frontrunnerV3-3.7.0-076-full"
        BatchFileName = "V3.7.0 Playback Tool.bat"
    },
    @{
        Name = "CamStudio Tool"
        PlaybackPath = "CamStudio_USB"
        BatchFileName = "CamStudioPortable.exe"
    }
)

# CamStudio/Playback USB logic
function FindAndRunTool {
    param (
        [string]$PlaybackPath,
        [string]$BatchFileName
    )
    $drives = Get-PSDrive -PSProvider 'FileSystem'
    foreach ($drive in $drives) {
        $driveInfo = New-Object System.IO.DriveInfo($drive.Name)
        if ($driveInfo.DriveType -eq 'Removable') {
            $targetFolderPath = Join-Path $drive.Root $PlaybackPath
            $filePath = Join-Path $targetFolderPath $BatchFileName
            Write-Host "Checking path: $filePath"

            if (Test-Path $filePath) {
                try {
                    if ($BatchFileName -like "*.bat") {
                        # Execute .bat files via cmd.exe
                        Start-Process cmd.exe -ArgumentList "/c `"$filePath`"" -WorkingDirectory $targetFolderPath -WindowStyle Minimized
                        Write-Host "$BatchFileName (batch file) started."
                    } elseif ($BatchFileName -like "*.exe") {
                        # Execute .exe files directly
                        Start-Process -FilePath $filePath -WorkingDirectory $targetFolderPath -WindowStyle Minimized
                        Write-Host "$BatchFileName (executable) started."
                    } else {
                        Write-Host "Unsupported file type for $BatchFileName"
                    }
                    return $true
                } catch {
                    Write-Host "Error: Failed to start $BatchFileName. $_"
                    return $false
                }
            } else {
                Write-Host "$BatchFileName not found at $filePath"
            }
        }
    }
    return $false
}

#T1 Tools Prompt
$buttonScriptV13 = {
    Add-Type -AssemblyName System.Windows.Forms
    $form = New-Object System.Windows.Forms.Form
    $form.Text = "Password Required"
    $form.Width = 300
    $form.Height = 150
    $form.StartPosition = [System.Windows.Forms.FormStartPosition]::CenterScreen
    $label = New-Object System.Windows.Forms.Label
    $label.Text = "Enter Password:"
    $label.AutoSize = $true
    $label.Location = New-Object System.Drawing.Point(10, 20)
    $form.Controls.Add($label)
    $textBox = New-Object System.Windows.Forms.TextBox
    $textBox.UseSystemPasswordChar = $true
    $textBox.Location = New-Object System.Drawing.Point(10, 50)
    $textBox.Width = 260
    $form.Controls.Add($textBox)
    $textBox.Add_KeyDown({
        if ($_.KeyCode -eq [System.Windows.Forms.Keys]::Enter) {
            if ($textBox.Text -eq "komatsu") {
                Start-Process -FilePath "C:\Komatsu_Tier1\T1_Tools\bin\T1_Tools.bat"
                Write-Host "Password accepted. Batch file started."
                $form.Close()
            } else {
                [System.Windows.Forms.MessageBox]::Show("Incorrect password. Please try again.", "Error", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Error)
                $textBox.Clear()
            }
        }
    })
    $form.ShowDialog()
}

# Build Form
$Form = New-Object System.Windows.Forms.Form
$Form.Text = "T1 PCN Dashboard"
$Form.Width = 280
$Form.Height = 700
$Form.TopMost = $false
$Form.FormBorderStyle = [System.Windows.Forms.FormBorderStyle]::FixedDialog
$Form.BackColor = [System.Drawing.Color]::FromArgb(45, 45, 48) # Dark background color
$Form.Font = $trebuchetFont
$imagePath = "C:\Komatsu_Tier1\T1_Tools\bin\icon.png"
$iconImage = [System.Drawing.Image]::FromFile($imagePath)

# Create PictureBox and set properties
$PictureBox = New-Object System.Windows.Forms.PictureBox
$PictureBox.SizeMode = [System.Windows.Forms.PictureBoxSizeMode]::StretchImage # Set to StretchImage to fit the image within the PictureBox
$PictureBox.Image = $iconImage
$pictureBoxWidth = 80  
$pictureBoxHeight = 80 
$PictureBox.Size = New-Object System.Drawing.Size($pictureBoxWidth, $pictureBoxHeight)
$iconX = ($Form.Width - $PictureBox.Width) / 2
$iconY = 5 
$PictureBox.Location = New-Object System.Drawing.Point($iconX, $iconY)
$Form.Controls.Add($PictureBox)

# Button Creation. 
function Create-DarkButton {
    param (
        [string]$Text,
        [int]$PosX,
        [int]$PosY,
        [scriptblock]$OnClick
    )

    $Button = New-Object System.Windows.Forms.Button
    $Button.Text = $Text
    $Button.Location = New-Object System.Drawing.Point($PosX, $PosY)
    $Button.Size = New-Object System.Drawing.Size(175, 30)
    $Button.BackColor = [System.Drawing.Color]::FromArgb(63, 63, 70)
    $Button.ForeColor = [System.Drawing.Color]::White
    $Button.Font = $trebuchetFont
    $Button.Add_Click($OnClick)
    return $Button
}

# Define all buttons
$buttons = @(
    @{Text = "IP Finder"; Script = { Start-Process -FilePath "C:\Komatsu_Tier1\T1_Tools\mms_scripts\IP_Finder.bat" }; PosY = 90},
    @{Text = "PTX Uptime Report"; Script = { Start-Process -FilePath "C:\Komatsu_Tier1\T1_Tools\mms_scripts\PTX_Uptime.bat" }; PosY = 125},
    @{Text = "Mineview Sessions"; Script = { Start-Process -FilePath "C:\Komatsu_Tier1\T1_Tools\mms_scripts\MineView_Session.bat" }; PosY = 160},
    @{Text = "Start PTX VNC"; Script = { Start-Process -FilePath "C:\Komatsu_Tier1\T1_Tools\mms_scripts\Start_VNC.bat" }; PosY = 195},
    @{Text = "PTX Health Check"; Script = { Start-Process -FilePath "C:\Komatsu_Tier1\T1_Tools\mms_scripts\PTXC_Health_Check.bat" }; PosY = 230},
    @{Text = "MM2/AVI Reboot"; Script = { Start-Process -FilePath "C:\Komatsu_Tier1\T1_Tools\mms_scripts\AVI_MM2_Reboot.bat" }; PosY = 265},
    @{Text = "PTX-AVI Watchdog Deploy"; Script = { Start-Process -FilePath "C:\Komatsu_Tier1\T1_Tools\mms_scripts\PTX-AVI_Watchdog_SingleDeploy.bat" }; PosY = 300},
    @{Text = "Live KOA Data"; Script = { Start-Process -FilePath "C:\Komatsu_Tier1\T1_Tools\mms_scripts\LIVE_KOA_DataCheck.bat" }; PosY = 335},
    @{Text = "Live Speed Limit Data"; Script = { Start-Process -FilePath "C:\Komatsu_Tier1\T1_Tools\mms_scripts\Latest_SpeedLimit_DataCheck.bat" }; PosY = 370},
    @{Text = "Linux Perf/Usage Check"; Script = { Start-Process -FilePath "C:\Komatsu_Tier1\T1_Tools\mms_scripts\Linux_Health_Check.bat" }; PosY = 405},
    @{Text = "Field Component Tracking"; Script = { Start-Process -FilePath "C:\Komatsu_Tier1\T1_Tools\mms_scripts\ComponentTracking.bat" }; PosY = 440},
    @{Text = "Linux Logs Downloader"; Script = { Start-Process -FilePath "C:\Komatsu_Tier1\T1_Tools\mms_scripts\Log_Downloader.bat" }; PosY = 475},
    @{Text = "T1 Tools - V1.3"; Script = $buttonScriptV13; PosY = 520},
    @{Text = "Playback USB"; Script = {
        if (!(FindAndRunTool -PlaybackPath "frontrunnerV3-3.7.0-076-full" -BatchFileName "V3.7.0 Playback Tool.bat")) {
            [System.Windows.Forms.MessageBox]::Show("Playback USB tool not found. Please insert the correct USB drive.")
        }
    }; PosY = 555},
    @{Text = "CamStudio USB"; Script = {
        if (!(FindAndRunTool -PlaybackPath "CamStudio_USB" -BatchFileName "CamStudioPortable.exe")) {
            [System.Windows.Forms.MessageBox]::Show("CamStudio USB tool not found. Please insert the correct USB drive.")
        }
    }; PosY = 590}
)

# Add buttons to the form
foreach ($button in $buttons) {
    $darkButton = Create-DarkButton -Text $button.Text -PosX 50 -PosY $button.PosY -OnClick $button.Script
    $Form.Controls.Add($darkButton)
}

$Form.ShowDialog()
