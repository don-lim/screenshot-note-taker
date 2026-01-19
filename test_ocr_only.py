import os
import sys

# --- CUDA/cuDNN DLL Path Fix ---
if sys.platform == 'win32':
    fix_path = r"D:\paddle_gpu_fix"
    cudnn_path = r"C:\Program Files\NVIDIA\CUDNN\v9.17\bin\13.1"
    cuda_bin = r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.1\bin"
    cuda_bin_x64 = r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.1\bin\x64"
    
    for path in [fix_path, cudnn_path, cuda_bin, cuda_bin_x64]:
        if os.path.exists(path):
            os.environ["PATH"] = path + os.pathsep + os.environ["PATH"]
            if hasattr(os, 'add_dll_directory'):
                try:
                    os.add_dll_directory(path)
                except Exception:
                    pass
# -------------------------------

from paddleocr import PaddleOCR
import cv2
import numpy as np

test_image = r'C:\Users\user\Pictures\Screenshots\스크린샷 2025-11-13 220802.png'

print("=" * 60)
print("Testing PaddleOCR - CPU Mode")
print("=" * 60)
ocr_cpu = PaddleOCR(use_angle_cls=True, lang='korean', use_gpu=False, show_log=False)
img = cv2.imdecode(np.fromfile(test_image, dtype=np.uint8), cv2.IMREAD_COLOR)
result_cpu = ocr_cpu.ocr(img, cls=True)

if result_cpu and result_cpu[0]:
    print(f"\nExtracted {len(result_cpu[0])} lines:\n")
    for idx, line in enumerate(result_cpu[0], 1):
        text = line[1][0]
        confidence = line[1][1]
        print(f"{idx:2d}. [{confidence:.2f}] {text}")
else:
    print("No text found (CPU)")

print("\n" + "=" * 60)
print("Testing PaddleOCR - GPU Mode")
print("=" * 60)
ocr_gpu = PaddleOCR(use_angle_cls=True, lang='korean', use_gpu=True, show_log=False)
result_gpu = ocr_gpu.ocr(img, cls=True)

if result_gpu and result_gpu[0]:
    print(f"\nExtracted {len(result_gpu[0])} lines:\n")
    for idx, line in enumerate(result_gpu[0], 1):
        text = line[1][0]
        confidence = line[1][1]
        print(f"{idx:2d}. [{confidence:.2f}] {text}")
else:
    print("No text found (GPU)")

print("\n" + "=" * 60)
