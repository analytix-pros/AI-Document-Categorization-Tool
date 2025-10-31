"""System checker with automatic model downloads - NEVER disables Ollama airplane mode."""
import subprocess
import sys
import platform
import socket
from database.db_models import create_connection
from utils.utils_system_specs import get_system_specs


def get_os_info():
    """Get current operating system information."""
    return {
        'system': platform.system(),
        'version': platform.version(),
        'machine': platform.machine(),
        'python_version': sys.version
    }


def check_internet_connection():
    """
    Check Ollama's own internet/airplane-mode status.
    
    Returns:
        dict with the following keys:
            ollama_connected_to_internet    - bool - True only when Ollama can reach the internet
            airplane_mode                   - bool - True when Ollama is deliberately offline
            status                          - str  - 'online' | 'offline' | 'unavailable'
            message                         - str  - human-readable explanation
    """
    import subprocess
    import requests

    # 1. Verify the Ollama CLI can talk to the local server
    try:
        cli_result = subprocess.run(
            ['ollama', 'list'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if cli_result.returncode != 0:
            return {
                'ollama_connected_to_internet': False,
                'airplane_mode': False,
                'status': 'unavailable',
                'message': 'Ollama service not reachable - cannot determine internet/airplane status'
            }
    except FileNotFoundError:
        return {
            'ollama_connected_to_internet': False,
            'airplane_mode': False,
            'status': 'unavailable',
            'message': 'Ollama CLI not found - cannot check internet/airplane mode'
        }

    # 2. Query Ollama’s local HTTP API
    try:
        resp = requests.get(
            "http://localhost:11434/api/tags",
            timeout=3
        )
        # 200 → server is up and NOT in airplane mode
        if resp.status_code == 200:
            return {
                'ollama_connected_to_internet': True,
                'airplane_mode': False,
                'status': 'online',
                'message': 'Ollama is online and can reach the internet'
            }

        # Non-200 – look for the airplane/offline hint
        try:
            data = resp.json()
            err = data.get("error", "").lower()
            if "airplane" in err or "offline" in err:
                return {
                    'ollama_connected_to_internet': False,
                    'airplane_mode': True,
                    'status': 'offline',
                    'message': 'Ollama is in airplane/offline mode (desired state)'
                }
        except Exception:
            pass

        return {
            'ollama_connected_to_internet': False,
            'airplane_mode': False,
            'status': 'unavailable',
            'message': f'Ollama API returned {resp.status_code} - unknown state'
        }

    except requests.exceptions.ConnectionError:
        # The local API is unreachable → most likely airplane mode
        return {
            'ollama_connected_to_internet': False,
            'airplane_mode': True,
            'status': 'offline',
            'message': 'Cannot reach Ollama API (localhost:11434) - airplane/offline mode active'
        }
    except requests.exceptions.Timeout:
        return {
            'ollama_connected_to_internet': False,
            'airplane_mode': True,
            'status': 'offline',
            'message': 'Ollama API timeout - treated as airplane/offline mode'
        }
    except Exception as e:
        return {
            'ollama_connected_to_internet': False,
            'airplane_mode': False,
            'status': 'unavailable',
            'message': f'Unexpected error while checking Ollama internet: {str(e)}'
        }


def check_machine_meets_requirements(required_specs):
    """Check if machine meets hardware requirements."""
    system_specs = get_system_specs()
    available_ram_gb = system_specs['memory']['total_gb']
    
    if required_specs.get('min_ram_gb', 0) > available_ram_gb:
        return False, f"Insufficient RAM: {available_ram_gb:.1f}GB available, {required_specs['min_ram_gb']}GB required"
    
    gpu_available = system_specs.get('gpu_available', False)
    gpu_required = bool(required_specs.get('gpu_required', 0))
    
    if gpu_required and not gpu_available:
        return False, "GPU required but not available"
    
    return True, "Requirements met"


def get_compatible_llm_models():
    """Get LLM models compatible with current hardware."""
    conn = create_connection()
    query = """
        SELECT llm_model_uuid, system, name, min_ram_gb, gpu_required, 
               gpu_optional, min_vram_gb, is_active
        FROM llm_models 
        WHERE system = 'Ollama' AND is_active = 1
    """
    cursor = conn.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()
    
    compatible_models = []
    
    for row in rows:
        model_info = {
            'uuid': row[0], 'system': row[1], 'name': row[2],
            'min_ram_gb': row[3], 'gpu_required': row[4],
            'gpu_optional': row[5], 'min_vram_gb': row[6], 'is_active': row[7]
        }
        
        meets_req, _ = check_machine_meets_requirements(model_info)
        
        if meets_req:
            compatible_models.append({
                'name': model_info['name'],
                'requirements': {
                    'min_ram_gb': model_info['min_ram_gb'],
                    'gpu_required': bool(model_info['gpu_required']),
                    'min_vram_gb': model_info['min_vram_gb']
                }
            })
    
    return compatible_models


def get_compatible_ocr_models():
    """Get OCR models compatible with current hardware."""
    conn = create_connection()
    query = """
        SELECT name, min_ram_gb, gpu_required, gpu_optional, min_vram_gb, is_active
        FROM ocr_models 
        WHERE is_active = 1
    """
    cursor = conn.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()
    
    compatible_models = []
    
    for row in rows:
        model_info = {
            'name': row[0],
            'min_ram_gb': row[1] if row[1] else 0,
            'gpu_required': row[2] if row[2] else 0,
            'gpu_optional': row[3] if row[3] else 0,
            'min_vram_gb': row[4] if row[4] else 0
        }
        
        meets_req, _ = check_machine_meets_requirements(model_info)
        
        if meets_req:
            compatible_models.append(model_info['name'])
    
    return compatible_models


def check_ollama_installed():
    """Check if Ollama is installed."""
    try:
        result = subprocess.run(['ollama', '--version'], capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0:
            return {'installed': True, 'version': result.stdout.strip(), 'error': None}
        else:
            return {'installed': False, 'version': None, 'error': 'Ollama command failed'}
    except FileNotFoundError:
        return {'installed': False, 'version': None, 'error': 'Ollama not found in PATH'}
    except subprocess.TimeoutExpired:
        return {'installed': False, 'version': None, 'error': 'Ollama command timeout'}
    except Exception as e:
        return {'installed': False, 'version': None, 'error': str(e)}


def check_ollama_models():
    """Check installed Ollama models."""
    try:
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            models = [line.split()[0] for line in lines[1:] if line.strip()]
            return {'success': True, 'models': models, 'error': None}
        else:
            return {'success': False, 'models': [], 'error': 'Failed to list models'}
    except Exception as e:
        return {'success': False, 'models': [], 'error': str(e)}


def download_ollama_model(model_name):
    """
    Download an Ollama model if not already installed.
    
    Args:
        model_name (str): Name of the model to download (e.g., 'llama2:7b')
    
    Returns:
        dict: Download status with success, message, and optional process
    """
    try:
        # Check if already installed
        installed_models = check_ollama_models()
        if model_name in installed_models.get('models', []):
            return {
                'success': True,
                'already_installed': True,
                'message': f'Model {model_name} already installed',
                'process': None
            }
        
        # Start download process
        process = subprocess.Popen(
            ['ollama', 'pull', model_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        return {
            'success': True,
            'already_installed': False,
            'message': f'Downloading {model_name}...',
            'process': process
        }
    except FileNotFoundError:
        return {
            'success': False,
            'already_installed': False,
            'message': 'Ollama not found. Please install Ollama first.',
            'process': None
        }
    except Exception as e:
        return {
            'success': False,
            'already_installed': False,
            'message': f'Error: {str(e)}',
            'process': None
        }


def download_all_required_models(progress_callback=None):
    """
    Download all required Ollama models that are compatible with the system.
    
    Args:
        progress_callback: Optional function to call with progress updates
                          Signature: callback(model_name, status, message)
    
    Returns:
        dict: Overall download status
    """
    compatible_models = get_compatible_llm_models()
    required_models = [m['name'] for m in compatible_models]
    
    if not required_models:
        return {
            'success': True,
            'message': 'No models required for this hardware',
            'models_processed': [],
            'models_downloaded': [],
            'models_failed': []
        }
    
    models_downloaded = []
    models_already_installed = []
    models_failed = []
    
    for model_name in required_models:
        if progress_callback:
            progress_callback(model_name, 'starting', f'Checking {model_name}...')
        
        result = download_ollama_model(model_name)
        
        if result['success']:
            if result['already_installed']:
                models_already_installed.append(model_name)
                if progress_callback:
                    progress_callback(model_name, 'already_installed', result['message'])
            else:
                # Wait for download to complete
                process = result['process']
                if process:
                    if progress_callback:
                        progress_callback(model_name, 'downloading', result['message'])
                    
                    stdout, stderr = process.communicate()
                    
                    if process.returncode == 0:
                        models_downloaded.append(model_name)
                        if progress_callback:
                            progress_callback(model_name, 'completed', f'Successfully downloaded {model_name}')
                    else:
                        models_failed.append({'model': model_name, 'error': stderr})
                        if progress_callback:
                            progress_callback(model_name, 'failed', f'Failed to download {model_name}: {stderr}')
        else:
            models_failed.append({'model': model_name, 'error': result['message']})
            if progress_callback:
                progress_callback(model_name, 'failed', result['message'])
    
    all_success = len(models_failed) == 0
    
    return {
        'success': all_success,
        'message': f"Downloaded {len(models_downloaded)}, Already installed {len(models_already_installed)}, Failed {len(models_failed)}",
        'models_processed': required_models,
        'models_downloaded': models_downloaded,
        'models_already_installed': models_already_installed,
        'models_failed': models_failed
    }


def check_required_ollama_models():
    """Check if required compatible Ollama models are installed."""
    compatible_models = get_compatible_llm_models()
    required_models = [m['name'] for m in compatible_models]
    
    installed_info = check_ollama_models()
    installed_models = installed_info.get('models', [])
    
    model_status = {model: model in installed_models for model in required_models}
    
    return {
        'required': required_models,
        'installed': installed_models,
        'status': model_status,
        'all_installed': all(model_status.values()) if model_status else True,
        'compatible_models_info': compatible_models,
        'missing_models': [m for m, installed in model_status.items() if not installed]
    }


def check_tesseract_installed():
    """Check if Tesseract is installed."""
    try:
        result = subprocess.run(['tesseract', '--version'], capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0:
            return {'installed': True, 'version': result.stdout.split('\n')[0], 'error': None}
        else:
            return {'installed': False, 'version': None, 'error': 'Tesseract command failed'}
    except FileNotFoundError:
        return {'installed': False, 'version': None, 'error': 'Tesseract not found in PATH'}
    except Exception as e:
        return {'installed': False, 'version': None, 'error': str(e)}


def check_python_package(package_name):
    """Check if Python package is installed."""
    try:
        import importlib
        module = importlib.import_module(package_name)
        version = getattr(module, '__version__', 'Unknown')
        return {'installed': True, 'version': version, 'error': None}
    except ImportError:
        return {'installed': False, 'version': None, 'error': f'{package_name} not installed'}
    except SyntaxError:
        return {'installed': False, 'version': None, 
                'error': f'{package_name} incompatible with Python {sys.version_info.major}.{sys.version_info.minor}'}
    except TypeError as e:
        if "unsupported operand type(s) for |" in str(e):
            return {'installed': False, 'version': None,
                    'error': f'{package_name} requires Python 3.10+ (current: {sys.version_info.major}.{sys.version_info.minor})'}
        return {'installed': False, 'version': None, 'error': f'{package_name} error: {str(e)}'}
    except Exception as e:
        return {'installed': False, 'version': None, 'error': f'{package_name} check failed: {str(e)}'}


def check_ocr_dependencies():
    """
    Check OCR dependencies compatible with hardware.
    Returns status with available_models list for use in processing.
    """
    compatible_ocr_names = get_compatible_ocr_models()
    
    ocr_status = {}
    available_models = []
    
    for model_name in compatible_ocr_names:
        model_lower = model_name.lower()
        
        if model_lower == 'tesseract':
            status = check_tesseract_installed()
            ocr_status['Tesseract'] = status
            if status['installed']:
                available_models.append('Tesseract')
        
        elif model_lower == 'easyocr':
            status = check_python_package('easyocr')
            ocr_status['EasyOCR'] = status
            if status['installed']:
                available_models.append('EasyOCR')
        
        elif model_lower == 'paddleocr':
            paddle_status = check_python_package('paddleocr')
            paddlepaddle_status = check_python_package('paddlepaddle')
            
            installed = paddle_status['installed'] and paddlepaddle_status['installed']
            ocr_status['PaddleOCR'] = {
                'installed': installed,
                'version': paddle_status.get('version'),
                'error': paddle_status.get('error') or paddlepaddle_status.get('error')
            }
            if installed:
                available_models.append('PaddleOCR')
    
    all_installed = all(status['installed'] for status in ocr_status.values()) if ocr_status else True
    at_least_one_installed = len(available_models) > 0
    
    return {
        'ocr_models': ocr_status,
        'all_installed': all_installed,
        'available_models': available_models,
        'at_least_one_available': at_least_one_installed
    }


def check_ollama_service_status():
    """
    Check if Ollama service is accessible.
    CRITICAL: NEVER attempts to disable airplane mode or modify Ollama settings.
    
    Returns:
        dict: Service status information only
    """
    try:
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            return {
                'success': True,
                'accessible': True,
                'message': 'Ollama service is online and accessible',
                'airplane_mode': 'Airplane mode status: PRESERVED (not checked or modified)'
            }
        else:
            return {
                'success': False,
                'accessible': False,
                'message': 'Ollama service returned error. Please check Ollama application.',
                'airplane_mode': 'Airplane mode status: PRESERVED (not checked or modified)'
            }
    except Exception as e:
        return {
            'success': False,
            'accessible': False,
            'message': f'Could not connect to Ollama: {str(e)}',
            'airplane_mode': 'Airplane mode status: PRESERVED (not checked or modified)'
        }


def check_all_dependencies():
    """
    Comprehensive system check.
    Returns available OCR models and Ollama status without modifying airplane mode.
    """
    os_info = get_os_info()
    system_specs = get_system_specs()
    internet_status = check_internet_connection()
    ollama_status = check_ollama_installed()
    ollama_models = check_required_ollama_models() if ollama_status['installed'] else None
    ocr_status = check_ocr_dependencies()
    
    ollama_service = None
    if ollama_status['installed']:
        ollama_service = check_ollama_service_status()
    
    # System is "ready" if at least one OCR is available
    system_ready = (
        internet_status['connected'] and
        ollama_status['installed'] and 
        (ollama_models['all_installed'] if ollama_models else False) and
        ocr_status['at_least_one_available']
    )
    
    return {
        'os': os_info,
        'system_specs': system_specs,
        'internet': internet_status,
        'ollama': {
            'installed': ollama_status['installed'],
            'version': ollama_status.get('version'),
            'error': ollama_status.get('error'),
            'models': ollama_models,
            'service_status': ollama_service
        },
        'ocr': ocr_status,
        'all_ready': system_ready
    }


if __name__ == "__main__":
    import json
    status = check_all_dependencies()
    print(json.dumps(status, indent=2))