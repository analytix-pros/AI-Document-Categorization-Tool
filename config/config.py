import os

# Set project root and change working directory
APP_DIRECTORY = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# os.chdir(PROJECT_ROOT)
# APP_DIRECTORY = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Define directories
DIRECTORIES = {
    "INITIAL_SETUP": os.path.join(APP_DIRECTORY, 'initial_setup'),
    "DATABASE": os.path.join(APP_DIRECTORY, 'database'),
    "UTILS": os.path.join(APP_DIRECTORY, 'utils'),
    'APP': os.path.join(APP_DIRECTORY, 'app')
}

DATABASE_NAME = 'ai_mail_app.db'
FULL_DATABASE_FILE_PATH = os.path.join('.', DATABASE_NAME)


# Streamlit Configurations

# Admin panel tabs configuration - dynamically configurable
ADMIN_TABS = {
    "CAT": {
        "tab_name": "Document Categories",
        "ordinal": 0,
        "render": "document_categories.render_document_categories()"
    },
    "LLM": {
        "tab_name": "LLM Models",
        "ordinal": 1,
        "render": "llm_models.render_llm_models_management()"
    },
    "OCR": {
        "tab_name": "OCR Models",
        "ordinal": 2,
        "render": "ocr_models.render_ocr_models_management()"
    },
    "STMP": {
        "tab_name": "Stamps",
        "ordinal": 3,
        "render": "stamps.render_stamps_management()"
    },
    "ORG": {
        "tab_name": "Organizations",
        "ordinal": 4,
        "render": "organizations.render_organizations_management()"
    },
    "USR": {
        "tab_name": "Users",
        "ordinal": 5,
        "render": "users.render_users_management()"
    },
    
    
}