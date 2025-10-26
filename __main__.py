"""Main entry point for the AI Document Categorization Tool."""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    from app.streamlit_app import main
    main()