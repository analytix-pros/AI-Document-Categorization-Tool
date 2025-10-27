"""System checker to verify LLM and OCR dependencies."""
import subprocess
import sys
import platform
import os
import socket
from database.db_models import create_connection
from utils.utils_system_specs import get_system_specs


def get_os_info():
    """Get current operating system information."""
    return {
        'system': platform.system(),  # Windows, Linux, Darwin (macOS)
        'version': platform.version(),
        'machine': platform.machine(),
        'python_version': sys.version
    }


def check_internet_connection():
    """
    Check if internet connection is available.
    
    Returns:
        dict: Internet connectivity status
    """
    try:
        # Try to connect to Google's DNS server
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return {
            'connected': True,
            'error': None
        }
    except OSError:
        return {
            'connected': False,
            'error': 'No internet connection detected'
        }


def disable_ollama_airplane_mode():
    """
    Attempt to disable Ollama's offline mode if it exists.
    
    Returns:
        dict: Result of the operation
    """
    system = platform.system()
    
    try:
        # Ollama doesn't have a traditional "airplane mode" but we can check connectivity
        # and attempt to restart the service if needed
        
        result = subprocess.run(
            ['ollama', 'list'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            return {
                'success': True,
                'message': 'Ollama service is online and accessible'
            }
        else:
            # Try to start/restart Ollama service
            if system in ['Darwin', 'Linux']:
                subprocess.Popen(
                    ['ollama', 'serve'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                return {
                    'success': True,
                    'message': 'Attempted to start Ollama service'
                }
            else:
                return {
                    'success': False,
                    'message': 'Please start Ollama from Start Menu'
                }
    except Exception as e:
        return {
            'success': False,
            'message': f'Could not connect to Ollama: {str(e)}'
        }


def check_machine_meets_requirements(required_specs):
    """
    Check if machine meets hardware requirements.
    
    Args:
        required_specs: Dict with min_ram_gb, gpu_required, gpu_optional, min_vram_gb
        
    Returns:
        tuple: (meets_requirements, reason)
    """
    system_specs = get_system_specs()
    
    # Check RAM
    available_ram_gb = system_specs['memory']['total_gb']
    if required_specs.get('min_ram_gb', 0) > available_ram_gb:
        return False, f"Insufficient RAM: {available_ram_gb:.1f}GB available, {required_specs['min_ram_gb']}GB required"
    
    # Check GPU requirement
    gpu_available = system_specs.get('gpu_available', False)
    gpu_required = bool(required_specs.get('gpu_required', 0))
    
    if gpu_required and not gpu_available:
        return False, f"GPU required but not available"
    
    # If GPU is available and VRAM requirements exist, check VRAM
    if gpu_available and required_specs.get('min_vram_gb', 0) > 0:
        # We'd need additional logic to check actual VRAM, for now assume it's met if GPU exists
        pass
    
    return True, "Requirements met"


def get_compatible_llm_models():
    """
    Get LLM models from database that are compatible with current hardware.
    
    Returns:
        list: List of compatible model info dicts
    """
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
            'uuid': row[0],
            'system': row[1],
            'name': row[2],
            'min_ram_gb': row[3],
            'gpu_required': row[4],
            'gpu_optional': row[5],
            'min_vram_gb': row[6],
            'is_active': row[7]
        }
        
        meets_req, reason = check_machine_meets_requirements(model_info)
        
        if meets_req:
            compatible_models.append({
                'name': model_info['name'],
                'requirements': {
                    'min_ram_gb': model_info['min_ram_gb'],
                    'gpu_required': bool(model_info['gpu_required']),
                    'min_vram_gb': model_info['min_vram_gb']
                }
            })
        else:
            # Store incompatible models separately for reporting
            pass
    
    return compatible_models


def get_compatible_ocr_models():
    """
    Get OCR models from database that are compatible with current hardware.
    
    Returns:
        list: List of compatible OCR model names
    """
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
        
        meets_req, reason = check_machine_meets_requirements(model_info)
        
        if meets_req:
            compatible_models.append(model_info['name'])
    
    return compatible_models


def check_ollama_installed():
    """
    Check if Ollama is installed on the system.
    
    Returns:
        dict: Status information about Ollama installation
    """
    try:
        result = subprocess.run(
            ['ollama', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            version = result.stdout.strip()
            return {
                'installed': True,
                'version': version,
                'error': None
            }
        else:
            return {
                'installed': False,
                'version': None,
                'error': 'Ollama command failed'
            }
    except FileNotFoundError:
        return {
            'installed': False,
            'version': None,
            'error': 'Ollama not found in PATH'
        }
    except subprocess.TimeoutExpired:
        return {
            'installed': False,
            'version': None,
            'error': 'Ollama command timeout'
        }
    except Exception as e:
        return {
            'installed': False,
            'version': None,
            'error': str(e)
        }


def check_ollama_models():
    """
    Check which Ollama models are installed.
    
    Returns:
        dict: Information about installed Ollama models
    """
    try:
        result = subprocess.run(
            ['ollama', 'list'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            # Skip header line
            models = []
            for line in lines[1:]:
                if line.strip():
                    parts = line.split()
                    if parts:
                        models.append(parts[0])
            
            return {
                'success': True,
                'models': models,
                'error': None
            }
        else:
            return {
                'success': False,
                'models': [],
                'error': 'Failed to list models'
            }
    except Exception as e:
        return {
            'success': False,
            'models': [],
            'error': str(e)
        }


def check_required_ollama_models():
    """
    Check if required Ollama models (compatible with hardware) are installed.
    
    Returns:
        dict: Comparison of required vs installed models
    """
    compatible_models = get_compatible_llm_models()
    required_models = [m['name'] for m in compatible_models]
    
    installed_info = check_ollama_models()
    installed_models = installed_info.get('models', [])
    
    model_status = {}
    for model in required_models:
        model_status[model] = model in installed_models
    
    return {
        'required': required_models,
        'installed': installed_models,
        'status': model_status,
        'all_installed': all(model_status.values()) if model_status else True,
        'compatible_models_info': compatible_models
    }


def check_tesseract_installed():
    """Check if Tesseract OCR is installed."""
    try:
        result = subprocess.run(
            ['tesseract', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            return {
                'installed': True,
                'version': version_line,
                'error': None
            }
        else:
            return {
                'installed': False,
                'version': None,
                'error': 'Tesseract command failed'
            }
    except FileNotFoundError:
        return {
            'installed': False,
            'version': None,
            'error': 'Tesseract not found in PATH'
        }
    except Exception as e:
        return {
            'installed': False,
            'version': None,
            'error': str(e)
        }


def check_python_package(package_name):
    """
    Check if a Python package is installed.
    
    Args:
        package_name: Name of the package to check
        
    Returns:
        dict: Installation status and version
    """
    try:
        import importlib
        module = importlib.import_module(package_name)
        version = getattr(module, '__version__', 'Unknown')
        
        return {
            'installed': True,
            'version': version,
            'error': None
        }
    except ImportError:
        return {
            'installed': False,
            'version': None,
            'error': f'{package_name} not installed'
        }
    except SyntaxError as e:
        # Package is installed but has syntax errors (likely Python version incompatibility)
        return {
            'installed': False,
            'version': None,
            'error': f'{package_name} installed but incompatible with Python {sys.version_info.major}.{sys.version_info.minor}'
        }
    except TypeError as e:
        # Handle union type errors from Python 3.9 with packages requiring 3.10+
        if "unsupported operand type(s) for |" in str(e):
            return {
                'installed': False,
                'version': None,
                'error': f'{package_name} requires Python 3.10+ (current: {sys.version_info.major}.{sys.version_info.minor})'
            }
        return {
            'installed': False,
            'version': None,
            'error': f'{package_name} error: {str(e)}'
        }
    except Exception as e:
        return {
            'installed': False,
            'version': None,
            'error': f'{package_name} check failed: {str(e)}'
        }


def check_ocr_dependencies():
    """
    Check OCR dependencies that are compatible with current hardware.
    
    Returns:
        dict: Status of compatible OCR dependencies
    """
    compatible_ocr_names = get_compatible_ocr_models()
    
    ocr_status = {}
    
    for model_name in compatible_ocr_names:
        model_lower = model_name.lower()
        
        if model_lower == 'tesseract':
            ocr_status['Tesseract'] = check_tesseract_installed()
        
        elif model_lower == 'easyocr':
            ocr_status['EasyOCR'] = check_python_package('easyocr')
        
        elif model_lower == 'paddleocr':
            paddle_status = check_python_package('paddleocr')
            paddlepaddle_status = check_python_package('paddlepaddle')
            
            ocr_status['PaddleOCR'] = {
                'installed': paddle_status['installed'] and paddlepaddle_status['installed'],
                'version': paddle_status.get('version'),
                'error': paddle_status.get('error') or paddlepaddle_status.get('error')
            }
    
    all_installed = all(status['installed'] for status in ocr_status.values()) if ocr_status else True
    
    return {
        'ocr_models': ocr_status,
        'all_installed': all_installed
    }


def check_all_dependencies():
    """
    Perform comprehensive system check.
    
    Returns:
        dict: Complete status of all dependencies
    """
    os_info = get_os_info()
    system_specs = get_system_specs()
    internet_status = check_internet_connection()
    ollama_status = check_ollama_installed()
    ollama_models = check_required_ollama_models() if ollama_status['installed'] else None
    ocr_status = check_ocr_dependencies()
    
    # Attempt to ensure Ollama is online if installed
    ollama_online = None
    if ollama_status['installed']:
        ollama_online = disable_ollama_airplane_mode()
    
    return {
        'os': os_info,
        'system_specs': system_specs,
        'internet': internet_status,
        'ollama': {
            'installed': ollama_status['installed'],
            'version': ollama_status.get('version'),
            'error': ollama_status.get('error'),
            'models': ollama_models,
            'online_status': ollama_online
        },
        'ocr': ocr_status,
        'all_ready': (
            internet_status['connected'] and
            ollama_status['installed'] and 
            (ollama_models['all_installed'] if ollama_models else False) and
            ocr_status['all_installed']
        )
    }


if __name__ == "__main__":
    import json
    status = check_all_dependencies()
    print(json.dumps(status, indent=2))


def get_os_info():
    """Get current operating system information."""
    return {
        'system': platform.system(),  # Windows, Linux, Darwin (macOS)
        'version': platform.version(),
        'machine': platform.machine(),
        'python_version': sys.version
    }


def check_ollama_installed():
    """
    Check if Ollama is installed on the system.
    
    Returns:
        dict: Status information about Ollama installation
    """
    try:
        result = subprocess.run(
            ['ollama', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            version = result.stdout.strip()
            return {
                'installed': True,
                'version': version,
                'error': None
            }
        else:
            return {
                'installed': False,
                'version': None,
                'error': 'Ollama command failed'
            }
    except FileNotFoundError:
        return {
            'installed': False,
            'version': None,
            'error': 'Ollama not found in PATH'
        }
    except subprocess.TimeoutExpired:
        return {
            'installed': False,
            'version': None,
            'error': 'Ollama command timeout'
        }
    except Exception as e:
        return {
            'installed': False,
            'version': None,
            'error': str(e)
        }


def check_ollama_models():
    """
    Check which Ollama models are installed.
    
    Returns:
        dict: Information about installed Ollama models
    """
    try:
        result = subprocess.run(
            ['ollama', 'list'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            # Skip header line
            models = []
            for line in lines[1:]:
                if line.strip():
                    parts = line.split()
                    if parts:
                        models.append(parts[0])
            
            return {
                'success': True,
                'models': models,
                'error': None
            }
        else:
            return {
                'success': False,
                'models': [],
                'error': 'Failed to list models'
            }
    except Exception as e:
        return {
            'success': False,
            'models': [],
            'error': str(e)
        }


def check_required_ollama_models():
    """
    Check if required Ollama models from database are installed.
    
    Returns:
        dict: Comparison of required vs installed models
    """
    conn = create_connection()
    query = "SELECT name FROM llm_models WHERE system = 'Ollama' AND is_active = 1"
    cursor = conn.cursor()
    cursor.execute(query)
    required_models = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    installed_info = check_ollama_models()
    installed_models = installed_info.get('models', [])
    
    model_status = {}
    for model in required_models:
        model_status[model] = model in installed_models
    
    return {
        'required': required_models,
        'installed': installed_models,
        'status': model_status,
        'all_installed': all(model_status.values())
    }


def check_tesseract_installed():
    """Check if Tesseract OCR is installed."""
    try:
        result = subprocess.run(
            ['tesseract', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            return {
                'installed': True,
                'version': version_line,
                'error': None
            }
        else:
            return {
                'installed': False,
                'version': None,
                'error': 'Tesseract command failed'
            }
    except FileNotFoundError:
        return {
            'installed': False,
            'version': None,
            'error': 'Tesseract not found in PATH'
        }
    except Exception as e:
        return {
            'installed': False,
            'version': None,
            'error': str(e)
        }


def check_python_package(package_name):
    """
    Check if a Python package is installed.
    
    Args:
        package_name: Name of the package to check
        
    Returns:
        dict: Installation status and version
    """
    try:
        import importlib
        module = importlib.import_module(package_name)
        version = getattr(module, '__version__', 'Unknown')
        
        return {
            'installed': True,
            'version': version,
            'error': None
        }
    except ImportError:
        return {
            'installed': False,
            'version': None,
            'error': f'{package_name} not installed'
        }
    except SyntaxError as e:
        # Package is installed but has syntax errors (likely Python version incompatibility)
        return {
            'installed': False,
            'version': None,
            'error': f'{package_name} installed but incompatible with Python {sys.version_info.major}.{sys.version_info.minor}'
        }
    except TypeError as e:
        # Handle union type errors from Python 3.9 with packages requiring 3.10+
        if "unsupported operand type(s) for |" in str(e):
            return {
                'installed': False,
                'version': None,
                'error': f'{package_name} requires Python 3.10+ (current: {sys.version_info.major}.{sys.version_info.minor})'
            }
        return {
            'installed': False,
            'version': None,
            'error': f'{package_name} error: {str(e)}'
        }
    except Exception as e:
        return {
            'installed': False,
            'version': None,
            'error': f'{package_name} check failed: {str(e)}'
        }


def check_ocr_dependencies():
    """
    Check all OCR dependencies from database.
    
    Returns:
        dict: Status of all OCR dependencies
    """
    conn = create_connection()
    query = "SELECT name FROM ocr_models WHERE is_active = 1"
    cursor = conn.cursor()
    cursor.execute(query)
    ocr_models = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    ocr_status = {}
    
    for model in ocr_models:
        model_lower = model.lower()
        
        if model_lower == 'tesseract':
            ocr_status['Tesseract'] = check_tesseract_installed()
        
        elif model_lower == 'easyocr':
            ocr_status['EasyOCR'] = check_python_package('easyocr')
        
        elif model_lower == 'paddleocr':
            paddle_status = check_python_package('paddleocr')
            paddlepaddle_status = check_python_package('paddlepaddle')
            
            ocr_status['PaddleOCR'] = {
                'installed': paddle_status['installed'] and paddlepaddle_status['installed'],
                'version': paddle_status.get('version'),
                'error': None if (paddle_status['installed'] and paddlepaddle_status['installed']) 
                         else 'PaddleOCR or PaddlePaddle not installed'
            }
    
    all_installed = all(status['installed'] for status in ocr_status.values())
    
    return {
        'ocr_models': ocr_status,
        'all_installed': all_installed
    }


def check_all_dependencies():
    """
    Perform comprehensive system check.
    
    Returns:
        dict: Complete status of all dependencies
    """
    os_info = get_os_info()
    ollama_status = check_ollama_installed()
    ollama_models = check_required_ollama_models() if ollama_status['installed'] else None
    ocr_status = check_ocr_dependencies()
    
    return {
        'os': os_info,
        'ollama': {
            'installed': ollama_status['installed'],
            'version': ollama_status.get('version'),
            'error': ollama_status.get('error'),
            'models': ollama_models
        },
        'ocr': ocr_status,
        'all_ready': (
            ollama_status['installed'] and 
            (ollama_models['all_installed'] if ollama_models else False) and
            ocr_status['all_installed']
        )
    }


if __name__ == "__main__":
    import json
    status = check_all_dependencies()
    print(json.dumps(status, indent=2))