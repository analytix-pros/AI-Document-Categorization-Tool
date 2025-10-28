"""System status sidebar component - with OCR, Hardware, and Ollama Airplane Mode."""
import streamlit as st
import sys
import requests
import json
import pandas as pd
from urllib.parse import urljoin

# === Your existing imports ===
from initial_setup.system_checker import (
    check_all_dependencies,
    download_all_required_models,
    check_required_ollama_models,
    check_ocr_dependencies
)
from initial_setup.llm_installer import (
    get_ollama_install_instructions,
    install_ollama_model,
    open_ollama_download_page,
    check_ollama_service_running
)
from initial_setup.ocr_installer import (
    get_ocr_install_instructions,
    install_python_ocr_package,
    open_tesseract_download_page
)


# === NEW: Ollama Airplane Mode Detection ===
def check_ollama_airplane_mode():
    """Detect if Ollama can pull models (i.e. not in airplane/offline mode)."""
    OLLAMA_API = "http://localhost:11434"

    try:
        resp = requests.get(urljoin(OLLAMA_API, "/api/tags"), timeout=3)
        if resp.status_code != 200:
            return {'in_airplane_mode': False, 'reason': 'Ollama service not responding'}
    except requests.RequestException:
        return {'in_airplane_mode': False, 'reason': 'Ollama service not accessible'}

    try:
        payload = {"name": "library/phi3:mini"}
        pull_resp = requests.post(
            urljoin(OLLAMA_API, "/api/pull"),
            json=payload,
            timeout=8,
            stream=True
        )
        for line in pull_resp.iter_lines():
            if line:
                data = json.loads(line)
                if data.get("status") == "pulling manifest":
                    return {'in_airplane_mode': False, 'reason': 'Can pull models'}
                if "error" in data and any(kw in data["error"].lower() for kw in ["network", "connection", "timeout"]):
                    return {'in_airplane_mode': True, 'reason': 'Network error during pull'}
                break
        return {'in_airplane_mode': True, 'reason': 'Pull failed silently'}
    except requests.Timeout:
        return {'in_airplane_mode': True, 'reason': 'Pull timeout'}
    except requests.ConnectionError:
        return {'in_airplane_mode': True, 'reason': 'Connection refused'}
    except Exception as e:
        if "network" in str(e).lower():
            return {'in_airplane_mode': True, 'reason': f'Network issue: {e}'}
        return {'in_airplane_mode': False, 'reason': 'Unknown'}

    return {'in_airplane_mode': True, 'reason': 'No internet access'}


# === ENHANCED: check_all_dependencies with airplane mode & OCR ===
def check_all_dependencies():
    """Wrap original + inject airplane mode and OCR status."""
    try:
        from initial_setup.system_checker import check_all_dependencies as orig
        status = orig()
    except Exception:
        status = {
            'ollama': {'installed': False},
            'internet': {'connected': False},
            'system_specs': {}
        }

    # Add airplane mode
    if status['ollama'].get('installed'):
        service_status = status['ollama'].get('service_status', {})
        if service_status.get('accessible'):
            status['ollama']['airplane_mode'] = check_ollama_airplane_mode()
        else:
            status['ollama']['airplane_mode'] = {'in_airplane_mode': False, 'reason': 'Service not running'}
    else:
        status['ollama']['airplane_mode'] = {'in_airplane_mode': False, 'reason': 'Ollama not installed'}

    # Add OCR status
    status['ocr_status'] = check_ocr_dependencies()

    return status


# === UPDATED: System Status Sidebar with Expander (Minimized by Default) ===
def render_system_status_sidebar():
    """Render full system status inside a collapsible expander, minimized by default."""
    if 'system_status' not in st.session_state:
        st.session_state['system_status'] = check_all_dependencies()
    
    status = st.session_state['system_status']
    
    with st.sidebar:
        st.markdown("---")

        # === MAIN EXPANDER: All status inside, collapsed by default ===
        with st.expander("System Status", expanded=False):
            st.markdown("### LLM Status")
            
            # === Ollama Status ===
            ollama_status = status['ollama']
            
            st.caption(f"{ollama_status.get('version', 'Unknown').upper()}")

            if ollama_status['installed']:
                st.success("Ollama Installed")
            else:
                st.error("Ollama Not Installed")
                if st.button("Install Guide", key="show_ollama_install", use_container_width=True):
                    st.session_state['show_ollama_install_guide'] = True
            
            # Service + Airplane Mode
            service_status = ollama_status.get('service_status', {})
            if service_status.get('accessible'):
                st.success("Service Running")
                
                airplane = ollama_status.get('airplane_mode', {})
                if airplane.get('in_airplane_mode'):
                    st.warning("Internet Disconnected")
                else:
                    st.caption("Internet Online")
            else:
                st.error("Service Not Running")
                st.caption("Please start Ollama")

            st.markdown("---")

            # === OCR Status ===
            st.markdown("### OCR Models")
            render_ocr_status(status['ocr_status'])

            st.markdown("---")

            # === Hardware Info ===
            st.markdown("### Hardware")
            render_hardware_info(status.get('system_specs', {}))


        # Refresh button at the top
        if st.button("Refresh All", use_container_width=True):
            st.session_state['system_status'] = check_all_dependencies()
            st.rerun()

        # === INSTALL GUIDES (outside expander, but only show when triggered) ===
        if st.session_state.get('show_ollama_install_guide', False):
            render_ollama_install_guide()


# === OCR Status Renderer (from your input) ===
def render_ocr_status(ocr_status):
    """Render OCR installation status and controls."""
    if not ocr_status.get('ocr_models'):
        st.info("No OCR models configured")
        return

    total_models = len(ocr_status['ocr_models'])
    installed_count = sum(1 for s in ocr_status['ocr_models'].values() if s['installed'])

    if ocr_status['all_installed']:
        st.success(f"All models ready ({installed_count}/{total_models})")
    else:
        st.warning(f"⚠️ Models: {installed_count}/{total_models} installed")

    ## st.markdown("---")

    for ocr_name, status in ocr_status['ocr_models'].items():
        col1, col2 = st.columns([3, 1])
        
        with col1:
            if status['installed']:
                # st.write(f"{ocr_name}")
                if status.get('version') and status['version'] != 'Unknown':
                    st.caption(f"{ocr_name} - v{status['version']}")
            else:
                st.write(f"{ocr_name}")
                if status.get('error'):
                    st.caption(f"{ocr_name} - {status['error']}")

        with col2:
            if not status['installed']:
                if status.get('error') and 'requires Python 3.10+' in status.get('error', ''):
                    st.caption("")
                else:
                    if st.button("Install", key=f"install_ocr_{ocr_name}", help=f"Install {ocr_name}"):
                        st.session_state[f'show_ocr_install_{ocr_name}'] = True
                        st.rerun()

        # Installation Guide
        if st.session_state.get(f'show_ocr_install_{ocr_name}', False):
            if status.get('error') and 'requires Python 3.10+' in status.get('error', ''):
                st.error(f"{ocr_name} requires Python 3.10+")
                st.info(f"Current: Python {sys.version_info.major}.{sys.version_info.minor}")
                st.warning("Please upgrade Python")
                if st.button("Close", key=f"close_{ocr_name}_inst", use_container_width=True):
                    st.session_state[f'show_ocr_install_{ocr_name}'] = False
                    st.rerun()
                continue

            instructions = get_ocr_install_instructions(ocr_name)
            st.markdown(f"**Install {ocr_name}:**")
            st.markdown(f"*{instructions['method']}*")
            for inst in instructions['instructions']:
                st.markdown(f"- {inst}")
            if 'cli_command' in instructions:
                st.code(instructions['cli_command'], language='bash')

            if ocr_name.lower() in ['easyocr', 'paddleocr']:
                if st.button(f"Install Now", key=f"do_install_{ocr_name}", use_container_width=True):
                    with st.spinner(f'Installing {ocr_name}...'):
                        result = install_python_ocr_package(ocr_name.lower())
                        if result['success'] and result['process'].returncode == 0:
                            st.success(f"{ocr_name} installed!")
                            st.session_state[f'show_ocr_install_{ocr_name}'] = False
                            st.session_state['system_status'] = check_all_dependencies()
                            st.rerun()
                        else:
                            st.error(f"Failed to install {ocr_name}")
                            if 'process' in result:
                                _, stderr = result['process'].communicate()
                                if stderr:
                                    st.code(stderr)
            elif ocr_name.lower() == 'tesseract':
                if 'url' in instructions:
                    if st.button("Download Page", key=f"open_{ocr_name}_dl", use_container_width=True):
                        open_tesseract_download_page()

            if st.button("Close", key=f"close_{ocr_name}_inst", use_container_width=True):
                st.session_state[f'show_ocr_install_{ocr_name}'] = False
                st.rerun()


# === Hardware Info Renderer as Markdown-like Table ===
def render_hardware_info(system_specs):
    """Render hardware information in a clean Markdown-style table."""
    if not system_specs:
        st.info("⚠️ Hardware info unavailable")
        return

    # Create 2-column grid
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**CPU**")
        st.markdown("**RAM**")
        st.markdown("**GPU**")
        st.markdown("**OS**")

    with col2:
        st.markdown(f"{system_specs['cpu']['cores_physical']} cores")
        st.markdown(f"{system_specs['memory']['total_gb']:.1f} GB")
        st.markdown("Available" if system_specs.get('gpu_available') else "Not detected")
        st.markdown(f"{system_specs['os']['name']} {system_specs['os']['version']}")


# === Ollama Install Guide ===
def render_ollama_install_guide():
    """Render Ollama installation guide."""
    instructions = get_ollama_install_instructions()
    st.markdown("#### Ollama Installation")
    st.markdown(f"**Method:** {instructions['method']}")
    for instruction in instructions['instructions']:
        st.markdown(f"- {instruction}")
    if 'cli_command' in instructions:
        st.code(instructions['cli_command'], language='bash')
    if 'url' in instructions:
        if st.button("Open Download Page", key="open_ollama_dl", use_container_width=True):
            open_ollama_download_page()
    if st.button("Close", key="close_ollama_guide", use_container_width=True):
        st.session_state['show_ollama_install_guide'] = False
        st.rerun()


# === check_system_ready_for_upload (updated) ===
def check_system_ready_for_upload():
    status = st.session_state.get('system_status') or check_all_dependencies()
    st.session_state['system_status'] = status
    missing = []

    # Ollama
    if not status['ollama']['installed']:
        missing.append("Ollama not installed")
    elif not status['ollama'].get('service_status', {}).get('accessible'):
        missing.append("Ollama service not running")

    # Airplane mode + missing models
    airplane = status['ollama'].get('airplane_mode', {})
    if airplane.get('in_airplane_mode'):
        missing_models = check_required_ollama_models().get('missing_models', [])
        if missing_models:
            missing.append(f"Airplane mode: cannot download {len(missing_models)} model(s)")

    # OCR
    ocr_status = status['ocr_status']
    if not ocr_status['at_least_one_available']:
        missing_ocr = [n for n, s in ocr_status['ocr_models'].items() if not s['installed']]
        missing.append(f"No OCR models. Install: {', '.join(missing_ocr)}")

    return len(missing) == 0, missing


# === prepare_ollama_models_background (respects airplane mode) ===
def prepare_ollama_models_background(progress_container=None):
    models_status = check_required_ollama_models()
    missing_models = models_status.get('missing_models', [])
    
    if not missing_models:
        return {'success': True, 'message': 'All models ready', 'models_prepared': [], 'already_available': models_status.get('installed', [])}

    status = st.session_state.get('system_status', {})
    airplane = status.get('ollama', {}).get('airplane_mode', {})
    if airplane.get('in_airplane_mode'):
        return {
            'success': False,
            'message': 'Cannot download models in airplane mode',
            'models_prepared': [],
            'already_available': models_status.get('installed', []),
            'failed': missing_models
        }

    if progress_container:
        with progress_container:
            st.info(f"Preparing {len(missing_models)} model(s)...")
            progress_bar = st.progress(0)
            status_text = st.empty()
            completed = 0
            total = len(missing_models)

            def progress_callback(model_name, status_type, message):
                nonlocal completed
                if status_type in ['completed', 'already_installed', 'failed']:
                    completed += 1
                progress_bar.progress(completed / total)
                status_text.text(f"{completed}/{total} models prepared")

            result = download_all_required_models(progress_callback=progress_callback)
    else:
        result = download_all_required_models()

    return {
        'success': result['success'],
        'message': result['message'],
        'models_prepared': result.get('models_downloaded', []),
        'already_available': result.get('models_already_installed', []),
        'failed': result.get('models_failed', [])
    }


# === Backward compatibility ===
def check_system_ready():
    return check_system_ready_for_upload()