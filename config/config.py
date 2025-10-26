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