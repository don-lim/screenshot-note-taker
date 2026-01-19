# CUDA 11.8 + cuDNN 8.6 Installation Guide

This is needed to let PaddleOCR use GPU for OCR. However, I decided to use CPU until PaddleOCR supports CUDA 13.1.

## Step 1: Download CUDA 11.8 Toolkit

1. Visit: https://developer.nvidia.com/cuda-11-8-0-download-archive
2. Select the following options:
   - Operating System: **Windows**
   - Architecture: **x86_64**
   - Version: **11**
   - Installer Type: **exe (local)** (recommended, ~3GB)
3. Click **Download** button
4. Save the file (e.g., `cuda_11.8.0_522.06_windows.exe`)

**Direct Link:** The page will provide a direct download link after selection.

## Step 2: Install CUDA 11.8

1. Run the downloaded `.exe` file as Administrator
2. Choose **Custom (Advanced)** installation
3. **IMPORTANT:** Deselect the following components (to avoid conflicts with CUDA 13.1):
   - Visual Studio Integration
   - Nsight for Visual Studio
   - GeForce Experience components (if present)
4. Keep selected:
   - CUDA Toolkit
   - CUDA Runtime
   - CUDA Development
5. Installation path will be: `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8`
6. Complete the installation (takes ~5-10 minutes)

## Step 3: Download cuDNN 8.6.0

1. Visit: https://developer.nvidia.com/rdp/cudnn-archive
2. Find and click: **Download cuDNN v8.6.0 (October 3rd, 2022), for CUDA 11.x**
3. You may need to log in with an NVIDIA Developer account (free)
4. Download: **cuDNN Library for Windows (x86)**
5. Save the ZIP file (e.g., `cudnn-windows-x86_64-8.6.0.163_cuda11-archive.zip`)

## Step 4: Extract and Configure cuDNN

1. Extract the downloaded ZIP file
2. You'll see a folder structure like:
   ```
   cudnn-windows-x86_64-8.6.0.163_cuda11-archive/
   ├── bin/
   ├── include/
   └── lib/
   ```
3. Copy the contents to CUDA 11.8 directory:
   - Copy all files from `bin/` to `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8\bin\`
   - Copy all files from `include/` to `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8\include\`
   - Copy all files from `lib/` to `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8\lib\x64\`

## Step 5: Set Environment Variables

### Option A: Using PowerShell (Temporary - for testing)
```powershell
$env:CUDA_PATH = "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8"
$env:PATH = "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8\bin;" + $env:PATH
```

### Option B: System Environment Variables (Permanent)
1. Press `Win + X` and select **System**
2. Click **Advanced system settings**
3. Click **Environment Variables**
4. Under **System variables**:
   - Find `CUDA_PATH` and change it to: `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8`
   - Find `Path`, click **Edit**, and ensure `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8\bin` is at the top
5. Click **OK** to save

## Step 6: Verify Installation

Open a **new** PowerShell terminal and run:
```powershell
cd d:\screenshot-note-taker
.\.venv\Scripts\Activate.ps1
python test_ocr_only.py
```

**Expected Result:** GPU mode should now produce clean Korean text (not garbled characters).

---

## Troubleshooting

### If you still see garbled output:
1. Restart your computer (to ensure environment variables are loaded)
2. Verify CUDA 11.8 is active:
   ```powershell
   nvcc --version
   ```
   Should show: `Cuda compilation tools, release 11.8`

### If you see "CUDA not found" errors:
1. Check that `CUDA_PATH` points to v11.8 (not v13.1)
2. Ensure the `bin` directory is in your PATH

### To switch back to CUDA 13.1 later:
Simply change `CUDA_PATH` back to `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.1`

---

**After successful installation, I'll help you verify GPU OCR is working correctly!**
