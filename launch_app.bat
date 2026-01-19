@echo off
REM Screenshot Note Taker Launcher
REM This batch file activates the virtual environment and launches the Flet app

echo ========================================
echo   Screenshot Note Taker
echo ========================================
echo.

REM Change to the script's directory
cd /d "%~dp0"

REM Check if virtual environment exists
if not exist ".venv\Scripts\Activate.ps1" (
    echo ERROR: Virtual environment not found!
    echo Please ensure .venv folder exists in: %CD%
    echo.
    pause
    exit /b 1
)

REM Activate virtual environment and run the app
echo Starting application...
echo.
powershell -ExecutionPolicy Bypass -Command ".\.venv\Scripts\Activate.ps1; python app.py"

REM If the app closes with an error, keep the window open
if errorlevel 1 (
    echo.
    echo Application exited with an error.
    pause
)
