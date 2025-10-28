"""Main entry point for the AI Document Categorization Tool."""
import sys
import os
import subprocess

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    # Get the path to streamlit_app.py
    streamlit_app_path = os.path.join(os.path.dirname(__file__), 'streamlit_app.py')
    
    # Run with streamlit
    try:
        # Start Ollama in background — works on Windows, macOS, Linux
        subprocess.Popen(['ollama', 'serve'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)

        # Start Streamlit
        subprocess.run(['streamlit', 'run', streamlit_app_path], check=True)
        
    except FileNotFoundError:
        print("Error: Streamlit is not installed or not in PATH")
        print("Please install it with: pip install streamlit")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Error running Streamlit: {e}")
        sys.exit(1)