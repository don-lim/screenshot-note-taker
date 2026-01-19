"""
Interactive batch processor - Using Ollama for processing
"""
import os
import glob
from ocr_processor import process_image_to_db, are_models_loaded

print("=" * 60)
print("Screenshot Batch Processor (Ollama Edition)")
print("=" * 60)

# Check if Ollama is available
if are_models_loaded():
    print("✅ Ollama is connected and ready!")
else:
    print("❌ Ollama not detected. Please ensure Ollama is running.")

screenshot_dir = r'C:\Users\user\Pictures\Screenshots'

def process_all():
    """Process all screenshots"""
    files = glob.glob(os.path.join(screenshot_dir, '*.png'))
    print(f"\nFound {len(files)} PNG files")
    
    processed = 0
    skipped = 0
    failed = 0
    failed_files = []  # List of (filename, reason) tuples
    
    for i, file_path in enumerate(files, 1):
        print(f"[{i}/{len(files)}] Processing {os.path.basename(file_path)}")
        success, reason = process_image_to_db(file_path)
        if success:
            if reason == "duplicate":
                skipped += 1
            else:
                processed += 1
        else:
            failed += 1
            failed_files.append((os.path.basename(file_path), reason))
    
    print(f"\n✅ Complete: {processed} processed, {skipped} skipped (duplicates), {failed} failed")
    
    if failed_files:
        print(f"\n{'='*60}")
        print(f"FAILED FILES ({len(failed_files)}):")
        print(f"{'='*60}")
        for idx, (filename, reason) in enumerate(failed_files, 1):
            reason_display = reason.replace('_', ' ').title()
            print(f"{idx:3d}. {filename}")
            print(f"      Reason: {reason_display}")
    
    return processed, failed

def process_new():
    """Process only images not in database"""
    import psycopg2
    from dotenv import load_dotenv
    load_dotenv()
    
    # Get existing filepaths from database
    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT"),
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD")
    )
    cursor = conn.cursor()
    cursor.execute("SELECT filepath FROM images")
    existing = {row[0] for row in cursor.fetchall()}
    cursor.close()
    conn.close()
    
    # Get all PNG files
    files = glob.glob(os.path.join(screenshot_dir, '*.png'))
    new_files = [f for f in files if f not in existing]
    
    print(f"\nFound {len(files)} total files, {len(new_files)} new files")
    
    if not new_files:
        print("No new files to process!")
        return 0, 0
    
    processed = 0
    skipped = 0
    failed = 0
    failed_files = []  # List of (filename, reason) tuples
    
    for i, file_path in enumerate(new_files, 1):
        print(f"[{i}/{len(new_files)}] Processing {os.path.basename(file_path)}")
        success, reason = process_image_to_db(file_path)
        if success:
            if reason == "duplicate":
                skipped += 1
            else:
                processed += 1
        else:
            failed += 1
            failed_files.append((os.path.basename(file_path), reason))
    
    print(f"\n✅ Complete: {processed} processed, {skipped} skipped (duplicates), {failed} failed")
    
    if failed_files:
        print(f"\n{'='*60}")
        print(f"FAILED FILES ({len(failed_files)}):")
        print(f"{'='*60}")
        for idx, (filename, reason) in enumerate(failed_files, 1):
            reason_display = reason.replace('_', ' ').title()
            print(f"{idx:3d}. {filename}")
            print(f"      Reason: {reason_display}")
    
    return processed, failed

# Interactive menu
while True:
    print("\n" + "=" * 60)
    print("Options:")
    print("  1. Process all screenshots")
    print("  2. Process only new screenshots")
    print("  3. Show database stats")
    print("  4. Exit")
    print("=" * 60)
    
    choice = input("Choose option (1-4): ").strip()
    
    if choice == "1":
        process_all()
    
    elif choice == "2":
        process_new()
    
    elif choice == "3":
        import psycopg2
        from dotenv import load_dotenv
        load_dotenv()
        
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST"),
            port=os.getenv("POSTGRES_PORT"),
            dbname=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD")
        )
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM images")
        img_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM ocr_results")
        ocr_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM text_embedding")
        emb_count = cursor.fetchone()[0]
        
        print(f"\nDatabase Statistics:")
        print(f"  Images: {img_count}")
        print(f"  OCR Results: {ocr_count}")
        print(f"  Embeddings: {emb_count}")
        
        cursor.close()
        conn.close()
    
    elif choice == "4":
        print("Goodbye!")
        break
    
    else:
        print("Invalid option!")
