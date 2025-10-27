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

# For the admin_panel.py instead of having the admin tabs in the file, can you add a dictionary variable in the confg/config.py file structured like the following - I want to dynamically be able to adjust it through the config vs through code:

ADMIN_TABS = {
    "LLM": {
        "tab_name": "LLM Models",
        "ordinal": 0,
        "render": "llm_models.render_llm_models_management()"
    },
    "OCR": {
        "tab_name": "OCR Models",
        "ordinal": 1,
        "render": "ocr_models.render_ocr_models_management()"
    }
}