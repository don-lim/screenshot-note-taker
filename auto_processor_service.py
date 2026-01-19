"""
Background service that watches for new screenshots and processes them automatically
Using Ollama for processing
"""
import time
import os
from pathlib import Path
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from ocr_processor import process_image_to_db, are_models_loaded

class ScreenshotHandler(FileSystemEventHandler):
    """Handle new screenshot files"""
    
    def __init__(self):
        self.processed_count = 0
    
    def on_created(self, event):
        """Process new PNG files"""
        if event.is_directory:
            return
        
        if event.src_path.lower().endswith('.png'):
            # Wait a moment for file to be fully written
            time.sleep(0.5)
            
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] New screenshot detected: {Path(event.src_path).name}")
            
            success, reason = process_image_to_db(event.src_path)
            if success:
                self.processed_count += 1
                if reason == "duplicate":
                    print(f"  ⏭️  Skipped (duplicate) - Total: {self.processed_count}")
                else:
                    print(f"  ✅ Processed successfully - Total: {self.processed_count}")
            else:
                reason_display = reason.replace('_', ' ').title()
                print(f"  ❌ Processing failed: {reason_display}")

def start_service():
    """Start the background service"""
    screenshot_dir = r'C:\Users\user\Pictures\Screenshots'
    
    print("=" * 60)
    print("Screenshot Auto-Processor Service (Ollama)")
    print("=" * 60)
    
    # Check Ollama
    if are_models_loaded():
        print("✅ Ollama is connected and ready!")
    else:
        print("⚠️ Warning: Ollama not detected. Please start Ollama for processing.")
        
    print(f"👀 Watching: {screenshot_dir}")
    print("\nService is running. Press Ctrl+C to stop.")
    print("=" * 60)
    
    event_handler = ScreenshotHandler()
    observer = Observer()
    observer.schedule(event_handler, screenshot_dir, recursive=False)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nStopping service...")
        observer.stop()
        observer.join()
        print(f"✅ Service stopped. Processed {event_handler.processed_count} screenshots.")

if __name__ == "__main__":
    start_service()
