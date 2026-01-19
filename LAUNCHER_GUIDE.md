# Screenshot Note Taker - Launcher Guide

This guide explains how to launch your Screenshot Note Taker application on Windows.

## Quick Start Options

### Option 1: Batch File (Simplest) ⚡
**Best for:** Quick double-click launching

1. Double-click `launch_app.bat` in the project folder
2. The app will start automatically

**Pros:**
- Simplest method
- No configuration needed
- Works on all Windows systems

**Cons:**
- Less error handling
- Console window stays open

---

### Option 2: PowerShell Script (Recommended) ⭐
**Best for:** Better error handling and status checks

1. Right-click `launch_app.ps1`
2. Select "Run with PowerShell"

**Pros:**
- Checks PostgreSQL connection
- Better error messages
- Colored console output
- Validates environment before launching

**Cons:**
- May require execution policy change (see Troubleshooting)

---

### Option 3: Desktop Shortcut (Most Convenient) 🖥️
**Best for:** Daily use with easy access

1. Right-click `create_shortcut.ps1`
2. Select "Run with PowerShell"
3. A shortcut will appear on your desktop
4. Double-click the desktop shortcut to launch the app

**Pros:**
- Easy desktop access
- Professional appearance
- Runs silently in background

---

### Option 4: Package as Executable (Advanced) 📦
**Best for:** Distribution or running without Python visible

See the "Creating a Standalone Executable" section below.

---

## Creating a Standalone Executable

If you want to create a single `.exe` file that doesn't require Python to be installed:

### Step 1: Install PyInstaller

```powershell
.\.venv\Scripts\Activate.ps1
pip install pyinstaller
```

### Step 2: Create the executable

```powershell
pyinstaller --name "Screenshot Note Taker" `
            --onefile `
            --windowed `
            --add-data "assets;assets" `
            --icon=assets/icon.ico `
            app.py
```

**Note:** You'll need to create an icon file first. If you don't have one, remove the `--icon` line.

### Step 3: Find your executable

The executable will be in the `dist` folder: `dist\Screenshot Note Taker.exe`

**Important Considerations:**
- The executable will be large (50-100MB) because it includes Python and all dependencies
- First launch may be slow as it extracts files
- You'll still need PostgreSQL and Ollama running separately
- The `.env` file must be in the same directory as the executable

---

## Troubleshooting

### "Execution Policy" Error (PowerShell)

If you get an error about execution policy when running `.ps1` files:

**Solution 1: Temporary bypass (for current session)**
```powershell
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
.\launch_app.ps1
```

**Solution 2: Permanent fix (recommended)**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### "Virtual environment not found"

Make sure you've created the virtual environment:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### "PostgreSQL connection failed"

1. Make sure PostgreSQL is running:
   ```powershell
   # Check if PostgreSQL service is running
   Get-Service -Name postgresql*
   ```

2. If not running, start it:
   ```powershell
   # Start PostgreSQL service (adjust name if needed)
   Start-Service postgresql-x64-14
   ```

3. Verify your `.env` file has correct database credentials

### "Ollama Offline" in the app

1. Make sure Ollama is running:
   ```powershell
   ollama serve
   ```

2. Verify your models are pulled:
   ```powershell
   ollama list
   ```

3. Pull required models if missing:
   ```powershell
   ollama pull qwen3-vl-4b-gpu-only
   ollama pull bge-m3:latest
   ```

---

## Auto-Start on Windows Boot (Optional)

To make the app start automatically when Windows boots:

### Method 1: Startup Folder
1. Press `Win + R`
2. Type `shell:startup` and press Enter
3. Copy the desktop shortcut to this folder

### Method 2: Task Scheduler (More Control)
1. Open Task Scheduler
2. Create Basic Task
3. Name: "Screenshot Note Taker"
4. Trigger: "When I log on"
5. Action: "Start a program"
6. Program: `powershell.exe`
7. Arguments: `-ExecutionPolicy Bypass -WindowStyle Hidden -File "d:\screenshot-note-taker\launch_app.ps1"`
8. Start in: `d:\screenshot-note-taker`

---

## Running in Background

To run the app minimized or in the system tray, you can modify the launcher:

Create `launch_app_hidden.ps1`:
```powershell
Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass -WindowStyle Hidden -File `"$PSScriptRoot\launch_app.ps1`" -NoWait" -WindowStyle Hidden
```

This will launch the app without showing the PowerShell window.

---

## Performance Tips

1. **Keep Ollama running:** Start Ollama before launching the app for faster response times
2. **PostgreSQL optimization:** Ensure PostgreSQL is configured for your system's RAM
3. **GPU acceleration:** Verify CUDA is properly configured for faster AI processing

---

## File Descriptions

| File | Purpose |
|------|---------|
| `launch_app.bat` | Simple batch launcher |
| `launch_app.ps1` | Advanced PowerShell launcher with checks |
| `create_shortcut.ps1` | Creates desktop shortcut |
| `app.py` | Main Flet application |
| `.env` | Configuration file (database, models) |
| `requirements.txt` | Python dependencies |

---

## Need Help?

If you encounter issues:
1. Check the console output for error messages
2. Verify all prerequisites are installed (Python, PostgreSQL, Ollama)
3. Ensure your `.env` file is configured correctly
4. Check that your virtual environment has all dependencies installed

---

**Enjoy your Screenshot Note Taker! 🚀**
