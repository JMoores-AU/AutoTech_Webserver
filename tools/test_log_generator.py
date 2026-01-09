"""
Test Data Generator for Log Cleanup
Creates a fake PTX log directory structure for offline testing
"""

import os
import random
from datetime import datetime, timedelta

# Use project root directory (where main.py is located)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
TEST_DATA_PATH = os.path.join(PROJECT_ROOT, "test_logs")


def generate_test_logs():
    """
    Generate a realistic test log directory structure:
    - Monthly folders (202512, 202511, 202510, 202509, 202508, etc.)
    - Various log files with different ages
    - 0-byte broken files
    - Loose files in root
    """
    
    # Create base directory
    os.makedirs(TEST_DATA_PATH, exist_ok=True)
    print(f"Creating test logs in: {TEST_DATA_PATH}")
    
    current_date = datetime.now()
    
    # Generate monthly folders (last 10 months)
    for months_back in range(10):
        folder_date = current_date - timedelta(days=months_back * 30)
        folder_name = folder_date.strftime("%Y%m")
        folder_path = os.path.join(TEST_DATA_PATH, folder_name)

        os.makedirs(folder_path, exist_ok=True)
        print(f"  Created folder: {folder_name}")

        # Generate log files in this folder (20-40 files per month)
        num_files = random.randint(20, 40)
        for i in range(num_files):
            # Random date within that month
            days_back = random.randint(0, 30)
            file_date = folder_date - timedelta(days=days_back)
            
            # Random file type
            file_types = [
                f"frontrunner_minemobile-mde_{file_date.strftime('%Y-%m-%d_%H-%M-%S')}_AEST_{random.randint(500,999)}.dbg",
                f"management_minemobile-mde_{file_date.strftime('%Y-%m-%d_%H-%M-%S')}_AEST_{random.randint(500,999)}.dbg",
                f"input-events_minemobile-mde_{file_date.strftime('%Y-%m-%d')}_AEST_{random.randint(500,999)}.log",
                f"stats_minemobile-mde_{file_date.strftime('%Y-%m-%d_%H-%M-%S')}_AEST_{random.randint(500,999)}.csv",
            ]
            
            filename = random.choice(file_types)
            filepath = os.path.join(folder_path, filename)
            
            # Create file with random size (or 0-byte for some)
            if random.random() < 0.1:  # 10% chance of 0-byte file
                # Create empty file
                open(filepath, 'w').close()
            else:
                # Create file with random content
                with open(filepath, 'w') as f:
                    f.write(f"Test log data for {filename}\n" * random.randint(1, 100))
            
            # Set file modification time to match the date
            mod_time = file_date.timestamp()
            os.utime(filepath, (mod_time, mod_time))
    
    # Generate loose files in root (not in monthly folders)
    print("\n  Creating loose files in root...")
    for i in range(5):
        days_back = random.randint(5, 30)
        file_date = current_date - timedelta(days=days_back)
        
        filenames = [
            f"error_log_{file_date.strftime('%Y%m%d')}.txt",
            f"debug_{file_date.strftime('%Y%m%d')}.log",
            f"temp_stats_{file_date.strftime('%Y%m%d')}.csv",
        ]
        
        filename = random.choice(filenames)
        filepath = os.path.join(TEST_DATA_PATH, filename)
        
        # 20% chance of 0-byte
        if random.random() < 0.2:
            open(filepath, 'w').close()
            print(f"    Created 0-byte: {filename}")
        else:
            with open(filepath, 'w') as f:
                f.write(f"Loose log data\n" * random.randint(1, 50))
            print(f"    Created loose file: {filename}")
        
        mod_time = file_date.timestamp()
        os.utime(filepath, (mod_time, mod_time))
    
    # Generate 300 0-byte broken files in root
    print("\n  Creating 300 0-byte broken files in root...")
    for i in range(300):
        days_back = random.randint(8, 60)
        file_date = current_date - timedelta(days=days_back)

        filename = f"broken_log_{file_date.strftime('%Y%m%d')}_{i:03d}.csv"
        filepath = os.path.join(TEST_DATA_PATH, filename)
        open(filepath, 'w').close()

        mod_time = file_date.timestamp()
        os.utime(filepath, (mod_time, mod_time))

        if i % 50 == 0:  # Progress indicator every 50 files
            print(f"    Created {i+1}/300 broken files...")
    
    print(f"\n[SUCCESS] Test data generated successfully!")
    print(f"   Location: {TEST_DATA_PATH}")
    print(f"   Folders: 10 monthly folders")
    print(f"   Files: ~350 log files total")
    print(f"   0-byte broken files: ~330 (300 in root + ~30 in folders)")
    print(f"   Loose files: 5-8 in root directory")


def show_test_structure():
    """Display the test directory structure"""
    if not os.path.exists(TEST_DATA_PATH):
        print("Test data not found. Run generate_test_logs() first.")
        return
    
    print(f"\n{'='*60}")
    print(f"TEST LOG STRUCTURE: {TEST_DATA_PATH}")
    print(f"{'='*60}")
    
    # Count items
    folders = 0
    loose_files = 0
    total_files = 0
    zero_byte_files = 0
    
    for item in os.listdir(TEST_DATA_PATH):
        item_path = os.path.join(TEST_DATA_PATH, item)
        if os.path.isdir(item_path):
            folders += 1
            files_in_folder = len([f for f in os.listdir(item_path) if os.path.isfile(os.path.join(item_path, f))])
            zero_in_folder = len([f for f in os.listdir(item_path) if os.path.isfile(os.path.join(item_path, f)) and os.path.getsize(os.path.join(item_path, f)) == 0])
            
            print(f"\n[FOLDER] {item}/ - {files_in_folder} files ({zero_in_folder} zero-byte)")
            total_files += files_in_folder
            zero_byte_files += zero_in_folder
        else:
            loose_files += 1
            size = os.path.getsize(item_path)
            mod_time = datetime.fromtimestamp(os.path.getmtime(item_path))
            days_old = (datetime.now() - mod_time).days

            if size == 0:
                zero_byte_files += 1
                print(f"  [FILE] {item} - 0 bytes ({days_old} days old)")
            else:
                print(f"  [FILE] {item} - {size} bytes ({days_old} days old)")
            
            total_files += 1
    
    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  Folders: {folders}")
    print(f"  Total files: {total_files}")
    print(f"  Loose files (in root): {loose_files}")
    print(f"  0-byte files: {zero_byte_files}")
    print(f"{'='*60}\n")


def cleanup_test_data():
    """Remove all test data"""
    import shutil
    if os.path.exists(TEST_DATA_PATH):
        shutil.rmtree(TEST_DATA_PATH)
        print(f"[SUCCESS] Test data removed: {TEST_DATA_PATH}")
    else:
        print("No test data to remove")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "clean":
            cleanup_test_data()
        elif sys.argv[1] == "show":
            show_test_structure()
        else:
            print("Usage: python test_log_generator.py [generate|show|clean]")
    else:
        # Default: generate test data
        generate_test_logs()
        show_test_structure()
