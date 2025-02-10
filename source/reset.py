import os
import glob

def clean_session_files():
    # Get the current directory
    current_dir = os.getcwd()
    
    # Create patterns for both types of files
    session_patterns = [
        "*.session",
        "*.session-journal"
    ]
    
    # Keep track of removed files
    removed_files = []
    
    # Iterate through each pattern and remove matching files
    for pattern in session_patterns:
        # Find all files matching the pattern
        files = glob.glob(os.path.join(current_dir, pattern))
        
        for file_path in files:
            try:
                os.remove(file_path)
                removed_files.append(os.path.basename(file_path))
            except OSError as e:
                print(f"Error removing {file_path}: {e}")
    
    # Print summary
    if removed_files:
        print("Successfully removed the following files:")
        for file in removed_files:
            print(f"- {file}")
    else:
        print("No session files found to remove.")

if __name__ == "__main__":
    # Ask for confirmation before proceeding
    response = input("This will remove all .session and .session-journal files. Continue? (y/n): ")
    
    if response.lower() == 'y':
        clean_session_files()
    else:
        print("Operation cancelled.")