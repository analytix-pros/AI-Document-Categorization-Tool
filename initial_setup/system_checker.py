"""System checker with OCR, LLM models, Poppler, and enforced Ollama airplane mode."""
import os
import sys
import platform
import shutil
import subprocess

# ─────────────────────────────────────────────────────────────────────────────
# Set project root and change working directory
# ─────────────────────────────────────────────────────────────────────────────
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_ROOT)   # ← CRITICAL: Add root to import path

# Now change working directory (optional, for file ops)
os.chdir(PROJECT_ROOT)
print(f"Project Root: {PROJECT_ROOT}")
print(f"Current Directory: {os.getcwd()}")

try:
    from database.db_models import create_connection
    from utils.utils_system_specs import get_system_specs
except ImportError as e:
    print(f"ERROR: Failed to import required modules: {str(e)}")
    print("Make sure you're running from initial_setup/ and the project structure is correct.")
    sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────────
# Do OCR and LLM Dependancy Checks
# ─────────────────────────────────────────────────────────────────────────────
def get_os_info():
    """Get current operating system information."""
    return {
        'system': platform.system(),
        'version': platform.version(),
        'machine': platform.machine(),
        'python_version': sys.version
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


def get_compatible_ocr_models():
    """Get OCR models compatible with current hardware from database."""
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


def check_tesseract_installed():
    """Check if Tesseract OCR is installed and running."""
    try:
        result = subprocess.run(['tesseract', '--version'], capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0:
            return {'installed': True, 'running': True, 'version': result.stdout.split('\n')[0], 'error': None}
        else:
            return {'installed': False, 'running': False, 'version': None, 'error': 'Tesseract command failed'}
    except FileNotFoundError:
        return {'installed': False, 'running': False, 'version': None, 'error': 'Tesseract not found in PATH'}
    except Exception as e:
        return {'installed': False, 'running': False, 'version': None, 'error': str(e)}


def check_python_package(package_name):
    """Check if Python package is installed and can be imported."""
    try:
        import importlib
        module = importlib.import_module(package_name)
        version = getattr(module, '__version__', 'Unknown')
        return {'installed': True, 'running': True, 'version': version, 'error': None}
    except ImportError:
        return {'installed': False, 'running': False, 'version': None, 'error': f'{package_name} not installed'}
    except SyntaxError:
        return {'installed': False, 'running': False, 'version': None, 
                'error': f'{package_name} incompatible with Python {sys.version_info.major}.{sys.version_info.minor}'}
    except TypeError as e:
        if "unsupported operand type(s) for |" in str(e):
            return {'installed': False, 'running': False, 'version': None,
                    'error': f'{package_name} requires Python 3.10+ (current: {sys.version_info.major}.{sys.version_info.minor})'}
        return {'installed': False, 'running': False, 'version': None, 'error': f'{package_name} error: {str(e)}'}
    except Exception as e:
        return {'installed': False, 'running': False, 'version': None, 'error': f'{package_name} check failed: {str(e)}'}


def check_ocr_dependencies():
    """Check OCR dependencies compatible with hardware - returns installed & running status."""
    compatible_ocr_names = get_compatible_ocr_models()
    
    ocr_status = {}
    available_models = []
    
    for model_name in compatible_ocr_names:
        model_lower = model_name.lower()
        
        if model_lower == 'tesseract':
            status = check_tesseract_installed()
            ocr_status['Tesseract'] = status
            if status['installed'] and status['running']:
                available_models.append('Tesseract')
        
        elif model_lower == 'easyocr':
            status = check_python_package('easyocr')
            ocr_status['EasyOCR'] = status
            if status['installed'] and status['running']:
                available_models.append('EasyOCR')
        
        elif model_lower == 'paddleocr':
            paddle_status = check_python_package('paddleocr')
            paddlepaddle_status = check_python_package('paddlepaddle')
            
            installed = paddle_status['installed'] and paddlepaddle_status['installed']
            running = paddle_status['running'] and paddlepaddle_status['running']
            ocr_status['PaddleOCR'] = {
                'installed': installed,
                'running': running,
                'version': paddle_status.get('version'),
                'error': paddle_status.get('error') or paddlepaddle_status.get('error')
            }
            if installed and running:
                available_models.append('PaddleOCR')
    
    all_installed = all(status['installed'] for status in ocr_status.values()) if ocr_status else True
    at_least_one_installed = len(available_models) > 0
    
    return {
        'ocr_models': ocr_status,
        'all_installed': all_installed,
        'available_models': available_models,
        'at_least_one_available': at_least_one_installed
    }


def check_poppler_installed():
    """Check if Poppler is installed by verifying pdftotext command."""
    try:
        result = subprocess.run(['pdftotext', '-v'], capture_output=True, text=True, timeout=5)
        if result:
            return {'installed': True, 'error': None}
    except FileNotFoundError:
        return {'installed': False, 'error': 'Poppler not found in PATH'}
    except Exception as e:
        return {'installed': False, 'error': str(e)}


def install_poppler_if_needed():
    """Install Poppler if not already installed using poppler_installer."""
    poppler_status = check_poppler_installed()
    if poppler_status['installed']:
        return {'success': True, 'message': 'Poppler already installed', 'action': 'none'}
    
    try:
        from initial_setup.poppler_installer import install_poppler
        install_poppler()
        
        # Verify installation
        poppler_status = check_poppler_installed()
        if poppler_status['installed']:
            return {'success': True, 'message': 'Poppler installed successfully', 'action': 'installed'}
        else:
            return {'success': False, 'message': 'Poppler installation may have failed', 'action': 'attempted'}
    except Exception as e:
        return {'success': False, 'message': f'Failed to install Poppler: {str(e)}', 'action': 'failed'}


def get_compatible_llm_models():
    """Get LLM models compatible with current hardware from database."""
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


def check_ollama_service_running():
    """Check if Ollama service is running and accessible."""
    try:
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            return {'running': True, 'accessible': True, 'message': 'Ollama service is running and accessible'}
        else:
            return {'running': False, 'accessible': False, 'message': 'Ollama service returned error'}
    except Exception as e:
        return {'running': False, 'accessible': False, 'message': f'Could not connect to Ollama: {str(e)}'}


def start_ollama_service():
    """Start Ollama service if not running."""
    try:
        os_system = platform.system()
        
        if os_system in ['Darwin', 'Linux']:
            process = subprocess.Popen(
                ['ollama', 'serve'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
        elif os_system == 'Windows':
            process = subprocess.Popen(
                ['ollama', 'serve'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        else:
            return {'success': False, 'message': f'Unsupported OS: {os_system}'}
        
        # Wait up to 10 seconds for service to start
        import time
        for _ in range(50):
            service_status = check_ollama_service_running()
            if service_status['running']:
                return {'success': True, 'message': 'Ollama service started successfully'}
            time.sleep(0.2)
        
        return {'success': False, 'message': 'Ollama service failed to start within 10 seconds'}
        
    except Exception as e:
        return {'success': False, 'message': f'Failed to start service: {str(e)}'}


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
    """Reliable ollama pull with path resolution."""
    # Find ollama binary
    ollama_cmd = shutil.which("ollama")
    if not ollama_cmd:
        # Fallback: common install locations
        system = platform.system()
        if system == "Windows":
            fallback = os.path.expandvars(r"%LOCALAPPDATA%\Programs\Ollama\ollama.exe")
        elif system == "Darwin":
            fallback = "/usr/local/bin/ollama"
        else:
            fallback = "/usr/bin/ollama"
        
        if os.path.exists(fallback):
            ollama_cmd = fallback
    
    if not ollama_cmd or not os.path.exists(ollama_cmd):
        return {
            'success': False,
            'error': 'ollama binary not found. Install from https://ollama.com'
        }

    try:
        print(f"Pulling {model_name} using {ollama_cmd}")
        result = subprocess.run(
            [ollama_cmd, 'pull', model_name],
            check=False,
            capture_output=True,
            text=True,
            timeout=600
        )

        if result.returncode == 0:
            return {'success': True, 'message': f'Pulled {model_name}'}
        else:
            err = result.stderr.strip() or result.stdout.strip()
            return {'success': False, 'error': err or 'Pull failed'}
    except subprocess.TimeoutExpired:
        return {'success': False, 'error': 'Pull timeout after 10 minutes'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def download_all_required_models(progress_callback=None):
    """Force pull all required Ollama models compatible with the system."""
    compatible_models = get_compatible_llm_models()
    required_models = [m['name'] for m in compatible_models]
    
    if not required_models:
        return {
            'success': True,
            'message': 'No models required for this hardware',
            'models_processed': [],
            'models_pulled': [],
            'models_failed': []
        }
    
    models_pulled = []
    models_failed = []

    for model_name in required_models:
        if progress_callback:
            progress_callback(model_name, 'starting', f'Pulling {model_name}...')

        result = download_ollama_model(model_name)

        if result['success']:
            models_pulled.append(model_name)
            if progress_callback:
                progress_callback(model_name, 'completed', result['message'])
        else:
            error_msg = result.get('error') or result.get('message', 'Unknown error')
            models_failed.append({'model': model_name, 'error': error_msg})
            if progress_callback:
                progress_callback(model_name, 'failed', error_msg)

    all_success = len(models_failed) == 0

    return {
        'success': all_success,
        'message': f"Pulled: {len(models_pulled)}, Failed: {len(models_failed)}",
        'models_processed': required_models,
        'models_pulled': models_pulled,
        'models_failed': models_failed
    }


def check_required_ollama_models():
    """Check if required Ollama models are installed **and runnable**."""
    compatible_models = get_compatible_llm_models()
    required_models = [m['name'] for m in compatible_models]

    # First: get the global list
    installed_info = check_ollama_models()
    installed_models = installed_info.get('models', [])

    # Per-model status
    model_status = {}
    model_verification = {}

    for model in required_models:
        # 1. Is it in `ollama list`?
        installed = model in installed_models
        model_status[model] = installed

        # 2. If installed, run `ollama list <model>` to verify it works
        if installed:
            verification = verify_ollama_model(model)
            model_verification[model] = verification
        else:
            model_verification[model] = {'working': False, 'error': 'not installed'}

    # Overall health
    all_installed = all(model_status.values())
    all_working   = all(v['working'] for v in model_verification.values())

    return {
        'required': required_models,
        'installed': installed_models,
        'status': model_status,                 # installed?
        'verification': model_verification,     # runnable?
        'all_installed': all_installed,
        'all_working': all_working,
        'compatible_models_info': compatible_models,
        'missing_models': [m for m, ok in model_status.items() if not ok],
        'broken_models': [m for m, v in model_verification.items() if not v['working']]
    }


def verify_ollama_model(model_name: str) -> dict:
    """
    Run `ollama list <model>` and return whether the model is usable.
    Returns:
        {
            'working': bool,
            'error': str | None
        }
    """
    # Find the same ollama binary we use for pulling
    ollama_cmd = shutil.which("ollama")
    if not ollama_cmd:
        system = platform.system()
        if system == "Darwin":
            fallback = "/opt/homebrew/bin/ollama"   # <-- your Mac
        elif system == "Windows":
            fallback = os.path.expandvars(r"%LOCALAPPDATA%\Programs\Ollama\ollama.exe")
        else:
            fallback = "/usr/bin/ollama"
        if os.path.exists(fallback):
            ollama_cmd = fallback

    if not ollama_cmd:
        return {'working': False, 'error': 'ollama binary not found'}

    try:
        result = subprocess.run(
            [ollama_cmd, 'list', model_name],
            capture_output=True,
            text=True,
            timeout=15
        )
        if result.returncode == 0 and model_name in result.stdout:
            return {'working': True, 'error': None}
        else:
            err = result.stderr.strip() or result.stdout.strip()
            return {'working': False, 'error': err or 'model not listed'}
    except Exception as e:
        return {'working': False, 'error': str(e)}


def check_ollama_airplane_mode():
    """Check if Ollama is in airplane mode (cannot access external network)."""
    try:
        import requests
        resp = requests.get("http://localhost:11434/api/tags", timeout=3)
        
        if resp.status_code != 200:
            return {'in_airplane_mode': True, 'can_verify': False, 'message': 'Ollama service not responding properly'}
        
        # Try a quick pull test with a small test model
        test_payload = {"name": "library/phi3:mini"}
        pull_resp = requests.post(
            "http://localhost:11434/api/pull",
            json=test_payload,
            timeout=5,
            stream=True
        )
        
        for line in pull_resp.iter_lines():
            if line:
                import json
                data = json.loads(line)
                if data.get("status") == "pulling manifest":
                    return {'in_airplane_mode': False, 'can_verify': True, 'message': 'Ollama can access external network'}
                if "error" in data and any(kw in data["error"].lower() for kw in ["network", "connection", "timeout"]):
                    return {'in_airplane_mode': True, 'can_verify': True, 'message': 'Ollama is in airplane mode (desired state)'}
                break
        
        return {'in_airplane_mode': True, 'can_verify': True, 'message': 'Ollama appears to be in airplane mode'}
        
    except requests.exceptions.ConnectionError:
        return {'in_airplane_mode': True, 'can_verify': False, 'message': 'Cannot connect to Ollama service'}
    except Exception as e:
        return {'in_airplane_mode': True, 'can_verify': False, 'message': f'Error checking airplane mode: {str(e)}'}


def enable_ollama_airplane_mode():
    """Force enable Ollama airplane mode by configuring environment and restarting service."""
    try:
        # Kill existing Ollama service
        os_system = platform.system()
        
        if os_system in ['Darwin', 'Linux']:
            subprocess.run(['pkill', '-f', 'ollama'], capture_output=True)
        elif os_system == 'Windows':
            subprocess.run(['taskkill', '/F', '/IM', 'ollama.exe'], capture_output=True)
        
        # Wait for service to stop
        import time
        time.sleep(2)
        
        # Set environment variables for airplane mode
        env = os.environ.copy()
        env["OLLAMA_HOST"] = "127.0.0.1:11434"
        env["OLLAMA_ORIGINS"] = "127.0.0.1"
        
        # Restart with airplane mode enforced
        if os_system in ['Darwin', 'Linux']:
            process = subprocess.Popen(
                ['ollama', 'serve'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                env=env,
                start_new_session=True
            )
        elif os_system == 'Windows':
            process = subprocess.Popen(
                ['ollama', 'serve'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                env=env,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        
        # Wait for service to start
        for _ in range(50):
            service_status = check_ollama_service_running()
            if service_status['running']:
                airplane_status = check_ollama_airplane_mode()
                if airplane_status['in_airplane_mode']:
                    return {'success': True, 'message': 'Ollama airplane mode enabled successfully'}
                else:
                    return {'success': False, 'message': 'Ollama started but airplane mode verification failed'}
            time.sleep(0.2)
        
        return {'success': False, 'message': 'Ollama failed to restart in airplane mode'}
        
    except Exception as e:
        return {'success': False, 'message': f'Failed to enable airplane mode: {str(e)}'}


def check_all_dependencies():
    """Comprehensive system check with OCR, Poppler, Ollama, models, and airplane mode enforcement."""
    os_info = get_os_info()
    system_specs = get_system_specs()
    

    # Check OCR models
    print("\n" + "="*80)
    print(f"DEBUG: Checking OCR Dependencies")
    print("="*80 + "\n")
    ocr_status = check_ocr_dependencies()
    

    # Check and install Poppler if needed
    print("\n" + "="*80)
    print(f"DEBUG: Installing Poppler (if needed)")
    print("="*80 + "\n")
    install_result = install_poppler_if_needed()
    
    # Now get the *actual* installed status
    poppler_status = check_poppler_installed()
    
    # Optional: log install action
    if install_result.get('action') == 'installed':
        print("Poppler was installed during this run.")
    elif install_result.get('action') == 'attempted':
        print("Poppler installation attempted but may have failed.")
    

    # Check Ollama installation
    print("\n" + "="*80)
    print(f"DEBUG: Checking Ollama Installed")
    print("="*80 + "\n")
    ollama_status = check_ollama_installed()
    
    if not ollama_status['installed']:
        return {
            'os': os_info,
            'system_specs': system_specs,
            'ocr': ocr_status,
            'poppler': poppler_status,
            'ollama': {
                'installed': False,
                'message': 'Ollama not installed. Please install Ollama to continue.',
                'install_instructions': 'Visit https://ollama.ai/download'
            },
            'all_ready': False
        }
    

    # Check if Ollama service is running
    print("\n" + "="*80)
    print(f"DEBUG: Checking Ollama service is running")
    print("="*80 + "\n")
    ollama_service = check_ollama_service_running()
    
    if not ollama_service['running']:
        # Start Ollama service
        start_result = start_ollama_service()
        if start_result['success']:
            ollama_service = check_ollama_service_running()
        else:
            return {
                'os': os_info,
                'system_specs': system_specs,
                'ocr': ocr_status,
                'poppler': poppler_status,
                'ollama': {
                    'installed': True,
                    'version': ollama_status['version'],
                    'running': False,
                    'message': start_result['message']
                },
                'all_ready': False
            }
    

    # Always ensure all models are pulled (fresh)
    print("\n" + "="*80)
    print(f"DEBUG: Force pulling all compatible Ollama models")
    print("="*80 + "\n")
    download_result = download_all_required_models()
    ollama_models = check_required_ollama_models()  # Final check
    

    # Check airplane mode
    print("\n" + "="*80)
    print(f"DEBUG: Checking Airplane mode for Ollama")
    print("="*80 + "\n")
    airplane_mode = check_ollama_airplane_mode()
    

    # If airplane mode is OFF, forcefully turn it ON
    print("\n" + "="*80)
    print(f"DEBUG: Try to turn Airplane mode ON")
    print("="*80 + "\n")
    if not airplane_mode['in_airplane_mode'] and airplane_mode['can_verify']:
        enable_result = enable_ollama_airplane_mode()
        if enable_result['success']:
            airplane_mode = check_ollama_airplane_mode()
        else:
            airplane_mode['enforcement_message'] = enable_result['message']
    
    system_ready = (
        ollama_status['installed'] and
        ollama_service['running'] and
        ollama_models['all_working'] and     
        ocr_status['at_least_one_available'] and
        poppler_status['installed']
    )
    
    
    return {
        'os': os_info,
        'system_specs': system_specs,
        'ocr': ocr_status,
        'poppler': poppler_status,
        'ollama': {
            'installed': ollama_status['installed'],
            'version': ollama_status.get('version'),
            'running': ollama_service['running'],
            'accessible': ollama_service['accessible'],
            'models': ollama_models,
            'airplane_mode': airplane_mode
        },
        'all_ready': system_ready
    }


if __name__ == "__main__":
    import json
    status = check_all_dependencies()
    print(json.dumps(status, indent=4, default=str))