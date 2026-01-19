"""
Check which screenshot files failed to process or were skipped
"""
import os
import glob
import psycopg2
from dotenv import load_dotenv

load_dotenv()

screenshot_dir = r'C:\Users\user\Pictures\Screenshots'

# Get all PNG files
all_files = set(glob.glob(os.path.join(screenshot_dir, '*.png')))
print(f"Total PNG files in directory: {len(all_files)}")

# Get files in database
conn = psycopg2.connect(
    host=os.getenv("POSTGRES_HOST"),
    port=os.getenv("POSTGRES_PORT"),
    dbname=os.getenv("POSTGRES_DB"),
    user=os.getenv("POSTGRES_USER"),
    password=os.getenv("POSTGRES_PASSWORD")
)
cursor = conn.cursor()
cursor.execute("SELECT filepath FROM images")
processed_files = {row[0] for row in cursor.fetchall()}
cursor.close()
conn.close()

print(f"Files in database: {len(processed_files)}")

# Find files not in database
missing_files = all_files - processed_files

print(f"\n{'='*60}")
print(f"Files NOT in database: {len(missing_files)}")
print(f"{'='*60}")

if missing_files:
    print("\nList of unprocessed files:")
    for i, filepath in enumerate(sorted(missing_files), 1):
        filename = os.path.basename(filepath)
        print(f"{i:3d}. {filename}")
else:
    print("\n✅ All files have been processed!")

# Also check for files in DB that no longer exist
orphaned_files = processed_files - all_files
if orphaned_files:
    print(f"\n{'='*60}")
    print(f"Files in database but NOT on disk: {len(orphaned_files)}")
    print(f"{'='*60}")
    for i, filepath in enumerate(sorted(orphaned_files), 1):
        filename = os.path.basename(filepath)
        print(f"{i:3d}. {filename}")
