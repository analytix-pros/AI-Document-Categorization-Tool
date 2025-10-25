import os

APP_DIRECTORY = os.path.dirname(os.path.abspath(__file__))

# Define directories
DIRECTORIES = {
    "INITIAL_SETUP": os.path.join(APP_DIRECTORY, 'initial_setup'),
    "DATABASE": os.path.join(APP_DIRECTORY, 'database'),
    "UTILS": os.path.join(APP_DIRECTORY, 'utils'),
    'APP': os.path.join(APP_DIRECTORY, 'app')
}

DATABASE_NAME = 'ai_mail_app.db'
FULL_DATABASE_FILE_PATH = os.path.join(DIRECTORIES['DATABASE'], DATABASE_NAME)

# Loop through the directories and create them if they don't exist
for name, path in DIRECTORIES.items():
    os.makedirs(path, exist_ok=True)
    print(f"Checked/created directory: {path}")



def print_directory_tree(startpath, indent="", prefix="", exclude_dot_folders=True):
    """
    Print the directory structure starting from startpath, including all subfolders and files.
    Optionally exclude folders with a '.' prefix (e.g., .git, .venv).
    
    Args:
        startpath (str): The root directory to start traversing.
        indent (str): Current indentation level for formatting.
        prefix (str): Prefix for the current line (e.g., '├──' or '└──').
        exclude_dot_folders (bool): If True, exclude folders starting with '.'.
    """
    # Ensure the path exists
    if not os.path.exists(startpath):
        print(f"Directory '{startpath}' does not exist.")
        return

    # Get the base name of the start path
    base_name = os.path.basename(os.path.abspath(startpath))
    print(f"{indent}{prefix}{base_name}/")

    # Get all entries in the directory, excluding folders starting with '.' if specified
    entries = sorted(os.listdir(startpath))  # Sort for consistent output
    if exclude_dot_folders:
        entries = [e for e in entries if not (os.path.isdir(os.path.join(startpath, e)) and e.startswith('.'))]
    
    entries_count = len(entries)
    
    for i, entry in enumerate(entries):
        entry_path = os.path.join(startpath, entry)
        is_last = i == entries_count - 1  # Check if this is the last entry
        new_prefix = "└── " if is_last else "├── "
        new_indent = indent + ("    " if is_last else "│   ")

        if os.path.isdir(entry_path):
            # Recursively print subdirectory
            print_directory_tree(entry_path, new_indent, new_prefix, exclude_dot_folders)
        else:
            # Print file
            print(f"{indent}{new_prefix}{entry}")


print_directory_tree(APP_DIRECTORY)