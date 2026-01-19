# Screenshot Note Taker - PowerShell Launcher
# This script provides a robust way to launch the Flet application

param(
    [switch]$NoWait  # Don't wait for user input on error
)

# Set console colors
$Host.UI.RawUI.BackgroundColor = "Black"
$Host.UI.RawUI.ForegroundColor = "White"
Clear-Host

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Screenshot Note Taker" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get the script's directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# Check if virtual environment exists
$VenvPath = Join-Path $ScriptDir ".venv\Scripts\Activate.ps1"
if (-not (Test-Path $VenvPath)) {
    Write-Host "ERROR: Virtual environment not found!" -ForegroundColor Red
    Write-Host "Expected location: $VenvPath" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Please run the following command to create it:" -ForegroundColor Yellow
    Write-Host "  python -m venv .venv" -ForegroundColor Green
    Write-Host ""
    if (-not $NoWait) {
        Read-Host "Press Enter to exit"
    }
    exit 1
}

# Check if app.py exists
$AppPath = Join-Path $ScriptDir "app.py"
if (-not (Test-Path $AppPath)) {
    Write-Host "ERROR: app.py not found!" -ForegroundColor Red
    Write-Host "Expected location: $AppPath" -ForegroundColor Yellow
    Write-Host ""
    if (-not $NoWait) {
        Read-Host "Press Enter to exit"
    }
    exit 1
}

# Check if PostgreSQL is running (optional check)
Write-Host "Checking PostgreSQL connection..." -ForegroundColor Yellow
try {
    $env:POSTGRES_HOST = "localhost"
    $env:POSTGRES_PORT = "5432"
    $testConnection = Test-NetConnection -ComputerName localhost -Port 5432 -WarningAction SilentlyContinue -ErrorAction SilentlyContinue
    if ($testConnection.TcpTestSucceeded) {
        Write-Host "✓ PostgreSQL is running" -ForegroundColor Green
    } else {
        Write-Host "⚠ PostgreSQL might not be running on port 5432" -ForegroundColor Yellow
        Write-Host "  The app may not work correctly without the database" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠ Could not check PostgreSQL status" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Starting application..." -ForegroundColor Green
Write-Host ""

# Activate virtual environment and run the app
try {
    & $VenvPath
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to activate virtual environment"
    }
    
    python $AppPath
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "Application exited with error code: $LASTEXITCODE" -ForegroundColor Red
        if (-not $NoWait) {
            Read-Host "Press Enter to exit"
        }
        exit $LASTEXITCODE
    }
} catch {
    Write-Host ""
    Write-Host "ERROR: $_" -ForegroundColor Red
    Write-Host ""
    if (-not $NoWait) {
        Read-Host "Press Enter to exit"
    }
    exit 1
}

Write-Host ""
Write-Host "Application closed successfully." -ForegroundColor Green
