"""
Test processing a single screenshot file
"""
import os
import glob
from ocr_processor import process_image_to_db, check_for_duplicate_image
from dotenv import load_dotenv
import psycopg2

load_dotenv()

# Find one test image
screenshots_dir = r'C:\Users\user\Pictures\Screenshots'
special_test_file = os.path.join(screenshots_dir, '스크린샷 2025-11-13 220802.png')

if os.path.exists(special_test_file):
    test_file = special_test_file
else:
    test_images = glob.glob(os.path.join(screenshots_dir, '*.png'))
    test_file = test_images[0] if test_images else None

if test_file:
    print(f"Testing with file: {os.path.basename(test_file)}")
    print("=" * 60)
    
    # Check if duplicate and delete if so for a fresh test
    image_id = check_for_duplicate_image(test_file)
    if image_id:
        print(f"Duplicate found (ID: {image_id}). Deleting for fresh test...")
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST"),
            port=os.getenv("POSTGRES_PORT"),
            dbname=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD")
        )
        cursor = conn.cursor()
        # Delete in correct order to respect foreign key constraints
        cursor.execute("DELETE FROM text_embedding WHERE image_id = %s", (image_id,))
        cursor.execute("DELETE FROM ocr_results WHERE image_id = %s", (image_id,))
        cursor.execute("DELETE FROM images WHERE id = %s", (image_id,))
        conn.commit()
        cursor.close()
        conn.close()
        print("Deleted.")

    # Process the image
    success, reason = process_image_to_db(test_file)
    
    if success:
        print(f"\n✅ Processing successful! Reason: {reason}")
        print("✅ SUCCESS! Image processed successfully")
        print("=" * 60)
        
        # Verify data in database
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST"),
            port=os.getenv("POSTGRES_PORT"),
            dbname=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD")
        )
        cursor = conn.cursor()
        
        # Check image record
        cursor.execute("SELECT id, ai_description, model_name FROM images ORDER BY id DESC LIMIT 1")
        img_id, ai_desc, model = cursor.fetchone()
        
        print(f"\nImage Record (ID: {img_id}):")
        print(f"  - Model: {model}")
        print(f"  - AI Description: {ai_desc[:200]}...")
        
        # Check embeddings
        cursor.execute("SELECT chunk_index FROM text_embedding WHERE image_id = %s", (img_id,))
        indices = [row[0] for row in cursor.fetchall()]
        print(f"  - Embedding indices found: {indices}")
        
        if -1 in indices:
            print("  - ✅ AI Description embedding (index -1) verified.")
        else:
            print("  - ❌ AI Description embedding (index -1) MISSING.")
            
        cursor.close()
        conn.close()
    else:
        print("\n" + "=" * 60)
        print("❌ FAILED - Check errors above")
        print("=" * 60)
else:
    print("No PNG files found in screenshots directory")
