"""OCR installation utilities."""
import subprocess
import platform
import sys
import webbrowser


def get_tesseract_install_instructions():
    """
    Get installation instructions for Tesseract based on OS.
    
    Returns:
        dict: Installation instructions
    """
    system = platform.system()
    
    if system == 'Darwin':  # macOS
        return {
            'method': 'Homebrew',
            'instructions': [
                '1. Open Terminal',
                '2. Run: brew install tesseract',
                '3. Wait for installation to complete',
                '4. Restart this application'
            ],
            'cli_command': 'brew install tesseract',
            'verify_command': 'tesseract --version'
        }
    
    elif system == 'Linux':
        return {
            'method': 'Package Manager',
            'instructions': [
                '1. Open Terminal',
                '2. Run the appropriate command for your distribution:',
                '   Ubuntu/Debian: sudo apt-get install tesseract-ocr',
                '   Fedora: sudo dnf install tesseract',
                '   Arch: sudo pacman -S tesseract',
                '3. Wait for installation to complete',
                '4. Restart this application'
            ],
            'cli_command': 'sudo apt-get install tesseract-ocr',
            'verify_command': 'tesseract --version'
        }
    
    elif system == 'Windows':
        return {
            'method': 'Download Installer',
            'url': 'https://github.com/UB-Mannheim/tesseract/wiki',
            'instructions': [
                '1. Download installer from GitHub (link above)',
                '2. Run the installer as Administrator',
                '3. Follow installation wizard',
                '4. Add Tesseract to PATH if not done automatically',
                '5. Restart this application'
            ],
            'note': 'You may need to add C:\\Program Files\\Tesseract-OCR to PATH'
        }
    
    else:
        return {
            'method': 'Manual Installation Required',
            'url': 'https://github.com/tesseract-ocr/tesseract',
            'instructions': [
                f'Automatic installation not supported for {system}',
                'Please visit the GitHub repository for instructions'
            ]
        }


def install_python_ocr_package(package_name):
    """
    Install a Python OCR package using pip.
    
    Args:
        package_name: Name of package ('easyocr' or 'paddleocr')
        
    Returns:
        dict: Installation result with process
    """
    packages_map = {
        'easyocr': ['easyocr'],
        'paddleocr': ['paddleocr', 'paddlepaddle']
    }
    
    packages = packages_map.get(package_name.lower(), [package_name])
    
    try:
        # Start pip install process
        process = subprocess.Popen(
            [sys.executable, '-m', 'pip', 'install'] + packages,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        return {
            'success': True,
            'process': process,
            'message': f'Installing {package_name}...',
            'packages': packages
        }
    except Exception as e:
        return {
            'success': False,
            'process': None,
            'message': f'Error: {str(e)}',
            'packages': packages
        }


def get_easyocr_install_instructions():
    """Get EasyOCR installation instructions."""
    return {
        'method': 'Python pip',
        'instructions': [
            '1. Click "Install EasyOCR" button below',
            '2. Wait for installation to complete',
            '3. Installation may take several minutes',
            '4. Restart application after completion'
        ],
        'cli_command': f'{sys.executable} -m pip install easyocr',
        'requirements': [
            'Python 3.6+',
            '~500MB download size',
            'PyTorch will be installed as dependency'
        ]
    }


def get_paddleocr_install_instructions():
    """Get PaddleOCR installation instructions."""
    return {
        'method': 'Python pip',
        'instructions': [
            '1. Click "Install PaddleOCR" button below',
            '2. Wait for installation to complete',
            '3. Installation may take several minutes',
            '4. Restart application after completion'
        ],
        'cli_command': f'{sys.executable} -m pip install paddleocr paddlepaddle',
        'requirements': [
            'Python 3.6+',
            '~300MB download size',
            'Both paddleocr and paddlepaddle will be installed'
        ]
    }


def get_ocr_install_instructions(ocr_name):
    """
    Get installation instructions for a specific OCR.
    
    Args:
        ocr_name: Name of OCR (Tesseract, EasyOCR, PaddleOCR)
        
    Returns:
        dict: Installation instructions
    """
    ocr_lower = ocr_name.lower()
    
    if ocr_lower == 'tesseract':
        return get_tesseract_install_instructions()
    elif ocr_lower == 'easyocr':
        return get_easyocr_install_instructions()
    elif ocr_lower == 'paddleocr':
        return get_paddleocr_install_instructions()
    else:
        return {
            'method': 'Unknown',
            'instructions': [f'Installation instructions not available for {ocr_name}']
        }


def open_tesseract_download_page():
    """Open Tesseract download page in browser."""
    system = platform.system()
    
    if system == 'Windows':
        webbrowser.open('https://github.com/UB-Mannheim/tesseract/wiki')
    else:
        webbrowser.open('https://github.com/tesseract-ocr/tesseract')