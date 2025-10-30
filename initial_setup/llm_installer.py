"""LLM installation utilities for Ollama – with forced airplane mode."""
import subprocess
import platform
import webbrowser
import time
import urllib.request
import os


def _ollama_http_check():
    """Fast check if Ollama server is responding via HTTP."""
    try:
        urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=1)
        return True
    except Exception:
        return False


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
    # Check if model already exists
    try:
        result = subprocess.run(
            ['ollama', 'list'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0 and model_name.split(':')[0] in result.stdout:
            return {
                'success': True,
                'process': None,
                'message': f'Model {model_name} already installed'
            }
    except:
        pass  # Continue to pull

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
    return _ollama_http_check()


def start_ollama_service():
    """
    Attempt to start Ollama service in airplane mode.
    
    Returns:
        dict: Start result
    """
    system = platform.system()
    
    # === FORCE AIRPLANE MODE ===
    env = os.environ.copy()
    env["OLLAMA_HOST"] = "127.0.0.1:11434"
    env["OLLAMA_TURBO_DISABLED"] = "1"
    env["OLLAMA_SEARCH_DISABLED"] = "1"
    env["OLLAMA_NOPROMPT"] = "1"

    try:
        if system in ['Darwin', 'Linux']:
            subprocess.Popen(
                ['ollama', 'serve'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                env=env,
                start_new_session=True
            )
        elif system == 'Windows':
            subprocess.Popen(
                ['ollama', 'serve'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                env=env,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        else:
            return {
                'success': False,
                'message': f'Unsupported OS: {system}'
            }

        # Wait up to 10 seconds for server to start
        for _ in range(50):
            if check_ollama_service_running():
                return {
                    'success': True,
                    'message': 'Ollama service started (airplane mode)'
                }
            time.sleep(0.2)

        return {
            'success': False,
            'message': 'Ollama service failed to start within 10 seconds'
        }

    except Exception as e:
        return {
            'success': False,
            'message': f'Failed to start service: {str(e)}'
        }


def open_ollama_download_page():
    """Open Ollama download page in browser."""
    webbrowser.open('https://ollama.ai/download')