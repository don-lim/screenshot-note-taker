# Create Desktop Shortcut for Screenshot Note Taker
# Run this script once to create a desktop shortcut

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$DesktopPath = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $DesktopPath "Screenshot Note Taker.lnk"

Write-Host "Creating desktop shortcut..." -ForegroundColor Cyan

# Create WScript Shell object
$WScriptShell = New-Object -ComObject WScript.Shell

# Create shortcut
$Shortcut = $WScriptShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = "powershell.exe"
$Shortcut.Arguments = "-ExecutionPolicy Bypass -WindowStyle Hidden -File `"$ScriptDir\launch_app.ps1`""
$Shortcut.WorkingDirectory = $ScriptDir
$Shortcut.Description = "Screenshot Note Taker - AI-powered screenshot search"
$Shortcut.WindowStyle = 1  # Normal window

# Try to set an icon (using Python icon if available)
$PythonPath = (Get-Command python -ErrorAction SilentlyContinue).Source
if ($PythonPath) {
    $Shortcut.IconLocation = "$PythonPath,0"
}

$Shortcut.Save()

Write-Host "✓ Desktop shortcut created successfully!" -ForegroundColor Green
Write-Host "Location: $ShortcutPath" -ForegroundColor Yellow
Write-Host ""
Write-Host "You can now double-click the shortcut to launch the app." -ForegroundColor Green
Read-Host "Press Enter to exit"
