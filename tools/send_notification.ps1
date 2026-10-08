param(
    [string]$Title = "J.A.R.V.I.S. Task Completed",
    [string]$Message = "Task finished and PDF document compiled."
)

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$notify = New-Object System.Windows.Forms.NotifyIcon
$notify.Icon = [System.Drawing.SystemIcons]::Information
$notify.BalloonTipTitle = $Title
$notify.BalloonTipText = $Message
$notify.BalloonTipIcon = [System.Windows.Forms.ToolTipIcon]::Info
$notify.Visible = $true

$notify.ShowBalloonTip(5000)
Start-Sleep -Milliseconds 1200
$notify.Dispose()
Write-Output "Notification Delivered"
