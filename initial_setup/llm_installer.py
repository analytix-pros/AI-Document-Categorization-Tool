"""LLM installation utilities for Ollama."""
import subprocess
import platform
import webbrowser


def get_ollama_install_instructions():
    """
    Get installation instructions for Ollama based on OS.
    
    Returns:
        dict: Installation instructions and commands
    """
    system = platform.system()
    
    if system == 'Darwin':  # macOS
        return {
            'method': 'Download and Install',
            'url': 'https://ollama.ai/download',
            'instructions': [
                '1. Download Ollama from https://ollama.ai/download',
                '2. Open the downloaded .dmg file',
                '3. Drag Ollama to Applications folder',
                '4. Open Ollama from Applications',
                '5. Restart this application after installation'
            ],
            'cli_method': 'Homebrew (Alternative)',
            'cli_command': 'brew install ollama',
            'cli_instructions': [
                '1. Open Terminal',
                '2. Run: brew install ollama',
                '3. Run: ollama serve (to start the service)',
                '4. Restart this application'
            ]
        }
    
    elif system == 'Linux':
        return {
            'method': 'Install Script',
            'url': 'https://ollama.ai/download',
            'instructions': [
                '1. Open Terminal',
                '2. Run the installation command below',
                '3. Wait for installation to complete',
                '4. Restart this application'
            ],
            'cli_command': 'curl -fsSL https://ollama.ai/install.sh | sh',
            'verify_command': 'ollama --version'
        }
    
    elif system == 'Windows':
        return {
            'method': 'Download and Install',
            'url': 'https://ollama.ai/download',
            'instructions': [
                '1. Download Ollama installer from https://ollama.ai/download',
                '2. Run the OllamaSetup.exe installer',
                '3. Follow the installation wizard',
                '4. Ollama will start automatically',
                '5. Restart this application after installation'
            ],
            'note': 'Windows may require administrator privileges'
        }
    
    else:
        return {
            'method': 'Manual Installation Required',
            'url': 'https://ollama.ai/download',
            'instructions': [
                f'Automatic installation not supported for {system}',
                'Please visit https://ollama.ai/download for instructions'
            ]
        }


def install_ollama_model(model_name):
    """
    Install an Ollama model.
    
    Args:
        model_name: Name of the model to install (e.g., 'llama2:7b')
        
    Returns:
        dict: Installation result
    """
    try:
        process = subprocess.Popen(
            ['ollama', 'pull', model_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        return {
            'success': True,
            'process': process,
            'message': f'Installing {model_name}...'
        }
    except FileNotFoundError:
        return {
            'success': False,
            'process': None,
            'message': 'Ollama not found. Please install Ollama first.'
        }
    except Exception as e:
        return {
            'success': False,
            'process': None,
            'message': f'Error: {str(e)}'
        }


def check_ollama_service_running():
    """
    Check if Ollama service is running.
    
    Returns:
        bool: True if service is running
    """
    try:
        result = subprocess.run(
            ['ollama', 'list'],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except:
        return False


def start_ollama_service():
    """
    Attempt to start Ollama service.
    
    Returns:
        dict: Start result
    """
    system = platform.system()
    
    try:
        if system == 'Darwin' or system == 'Linux':
            subprocess.Popen(
                ['ollama', 'serve'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            return {
                'success': True,
                'message': 'Ollama service started'
            }
        elif system == 'Windows':
            return {
                'success': False,
                'message': 'Please start Ollama from Start Menu'
            }
    except Exception as e:
        return {
            'success': False,
            'message': f'Failed to start service: {str(e)}'
        }


def open_ollama_download_page():
    """Open Ollama download page in browser."""
    webbrowser.open('https://ollama.ai/download')