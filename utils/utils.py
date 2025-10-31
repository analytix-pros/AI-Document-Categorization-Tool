# utils/utils.py
import os
import sys
import datetime
from datetime import timezone

# Ensure project root is in path
if __name__ == "__main__":
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.config import *



def get_utc_datetime():
    """
    Get the current UTC datetime as an ISO 8601 string with microsecond precision.
    """
    return datetime.datetime.now(timezone.utc).isoformat()


# print(get_utc_datetime())


def create_root_directories():
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


# print_directory_tree(APP_DIRECTORY)


def custom_badge(label, color="gray", icon=""):
    colors = {
        # Core
        "green":   "#10B981",  # emerald-500
        "red":     "#EF4444",  # red-500
        "orange":  "#F59E0B",  # amber-500
        "gray":    "#6B7280",  # slate-500
        
        # New colors
        "blue":    "#3B82F6",  # blue-500
        "indigo":  "#6366F1",  # indigo-500
        "purple":  "#8B5CF6",  # violet-500
        "pink":    "#EC4899",  # pink-500
        "yellow":  "#FBBF24",  # yellow-400
        "teal":    "#14B8A6",  # teal-500
        "cyan":    "#06B6D4",  # cyan-500
        "lime":    "#84CC16",  # lime-500
        
        # Light variants
        "lightgreen": "#86EFAC",
        "lightred":   "#FCA5A5",
        "lightblue":  "#93C5FD",
        
        # Dark / status
        "success": "#10B981",
        "warning": "#F59E0B",
        "danger":  "#EF4444",
        "info":    "#3B82F6",
        "neutral": "#6B7280",
    }
    bg = colors.get(color, "#6B7280")
    html = f"""
    <div style="
        display: inline-flex;
        justify-content: top;
        align-items: top;
        background-color: {bg}10;
        color: {bg};
        padding: 6px 10px;
        border-radius: 6px;
        font-weight: bold;
        font-size: 14px;
        border: 2px solid {bg};
    ">
        {icon} {label}
    </div>
    """
    return html