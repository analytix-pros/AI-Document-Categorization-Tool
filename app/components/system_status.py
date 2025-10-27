"""System status sidebar component."""
import streamlit as st
import sys
from initial_setup.system_checker import check_all_dependencies
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


def render_hardware_info(system_specs):
    """Render hardware information summary."""
    if not system_specs:
        st.info("Hardware info unavailable")
        return
    
    st.write(f"**CPU:** {system_specs['cpu']['cores_physical']} cores")
    st.write(f"**RAM:** {system_specs['memory']['total_gb']:.1f} GB")
    st.write(f"**GPU:** {'✓ Available' if system_specs.get('gpu_available') else '✗ Not detected'}")
    st.write(f"**OS:** {system_specs['os']['name']} {system_specs['os']['version']}")


def render_system_status_sidebar():
    """Render system status in sidebar."""
    
    if 'system_status' not in st.session_state:
        st.session_state['system_status'] = check_all_dependencies()
    
    status = st.session_state['system_status']
    
    with st.sidebar:
        st.markdown("---")
        
        # LLM (Ollama) with Internet Status
        with st.expander("🤖 LLM (Ollama)", expanded=True):
            render_ollama_status(status['ollama'], status.get('internet', {}))
        
        # OCR Status
        with st.expander("📝 OCR Models", expanded=True):
            render_ocr_status(status['ocr'])
        
        # Hardware Info
        with st.expander("💻 Hardware Info", expanded=False):
            render_hardware_info(status.get('system_specs', {}))
        
        # Refresh button at bottom
        if st.button("🔄 Refresh Status", use_container_width=True):
            st.session_state['system_status'] = check_all_dependencies()
            st.rerun()


def render_ollama_status(ollama_status, internet_status):
    """Render Ollama installation status and controls."""
    
    # Internet connectivity status
    if internet_status.get('connected'):
        st.success("🌐 Internet: Connected")
    else:
        st.error("🌐 Internet: Disconnected")
        st.caption("Required for model downloads")
    
    st.markdown("---")
    
    if not ollama_status['installed']:
        st.error("❌ Ollama not installed")
        
        if st.button("📖 Installation Guide", key="ollama_instructions", use_container_width=True):
            st.session_state['show_ollama_install'] = True
        
        if st.session_state.get('show_ollama_install', False):
            instructions = get_ollama_install_instructions()
            
            st.markdown(f"**Method:** {instructions['method']}")
            
            for instruction in instructions['instructions']:
                st.markdown(f"- {instruction}")
            
            if 'cli_command' in instructions:
                st.code(instructions['cli_command'], language='bash')
            
            if 'url' in instructions:
                if st.button("🌐 Open Download Page", key="open_ollama_dl"):
                    open_ollama_download_page()
            
            if st.button("Close", key="close_ollama_inst", use_container_width=True):
                st.session_state['show_ollama_install'] = False
                st.rerun()
    
    else:
        st.success(f"✅ Ollama installed")
        st.caption(f"Version: {ollama_status.get('version', 'Unknown')}")
        
        # Show online/offline status
        online_status = ollama_status.get('online_status')
        if online_status:
            if online_status['success']:
                st.success("✓ Service: Running")
            else:
                st.warning("⚠ Service: Not running")
                st.caption("Please start Ollama")
        
        # Show model status summary (without individual model details)
        if ollama_status['models']:
            models_status = ollama_status['models']
            
            total_required = len(models_status.get('required', []))
            total_installed = sum(1 for installed in models_status['status'].values() if installed)
            
            if total_required == 0:
                st.info("No models required for your hardware")
            elif total_installed == total_required:
                st.success(f"✅ All models ready ({total_installed}/{total_required})")
            else:
                st.warning(f"⚠️ Models: {total_installed}/{total_required} installed")
                st.info("Configure models in Admin panel")


def render_ocr_status(ocr_status):
    """Render OCR installation status and controls."""
    
    if not ocr_status['ocr_models']:
        st.info("No OCR models configured")
        return
    
    all_installed = ocr_status['all_installed']
    
    total_models = len(ocr_status['ocr_models'])
    installed_count = sum(1 for status in ocr_status['ocr_models'].values() if status['installed'])
    
    if all_installed:
        st.success(f"✅ All models ready ({installed_count}/{total_models})")
    else:
        st.warning(f"⚠️ Models: {installed_count}/{total_models} installed")
    
    st.markdown("---")
    
    for ocr_name, status in ocr_status['ocr_models'].items():
        col1, col2 = st.columns([3, 1])
        
        with col1:
            if status['installed']:
                st.write(f"✅ {ocr_name}")
                if status.get('version') and status['version'] != 'Unknown':
                    st.caption(f"v{status['version']}")
            else:
                st.write(f"❌ {ocr_name}")
                # Show error message if it's a compatibility issue
                if status.get('error') and 'Python' in status.get('error', ''):
                    st.caption(f"⚠️ {status['error']}")
        
        with col2:
            if not status['installed']:
                # Don't show install button if it's a Python version issue
                if status.get('error') and 'requires Python 3.10+' in status.get('error', ''):
                    st.caption("⚠️")
                else:
                    if st.button("📥", key=f"install_ocr_{ocr_name}", help=f"Install {ocr_name}"):
                        st.session_state[f'show_ocr_install_{ocr_name}'] = True
                        st.rerun()
        
        # Show installation instructions
        if st.session_state.get(f'show_ocr_install_{ocr_name}', False):
            # Check for Python version compatibility first
            if status.get('error') and 'requires Python 3.10+' in status.get('error', ''):
                st.error(f"⚠️ {ocr_name} requires Python 3.10+")
                st.info(f"Current: Python {sys.version_info.major}.{sys.version_info.minor}")
                st.warning("Please upgrade Python")
                
                if st.button("Close", key=f"close_{ocr_name}_inst", use_container_width=True):
                    st.session_state[f'show_ocr_install_{ocr_name}'] = False
                    st.rerun()
                continue
            
            instructions = get_ocr_install_instructions(ocr_name)
            
            st.markdown(f"**Install {ocr_name}:**")
            st.markdown(f"*{instructions['method']}*")
            
            for instruction in instructions['instructions']:
                st.markdown(f"- {instruction}")
            
            if 'cli_command' in instructions:
                st.code(instructions['cli_command'], language='bash')
            
            # Special handling for Python packages
            if ocr_name.lower() in ['easyocr', 'paddleocr']:
                if st.button(f"🚀 Install Now", key=f"do_install_{ocr_name}", use_container_width=True):
                    with st.spinner(f'Installing {ocr_name}...'):
                        result = install_python_ocr_package(ocr_name.lower())
                        
                        if result['success']:
                            stdout, stderr = result['process'].communicate()
                            
                            if result['process'].returncode == 0:
                                st.success(f"✅ {ocr_name} installed!")
                                st.session_state[f'show_ocr_install_{ocr_name}'] = False
                                st.session_state['system_status'] = check_all_dependencies()
                                st.rerun()
                            else:
                                st.error(f"Failed to install {ocr_name}")
                                st.code(stderr)
                        else:
                            st.error(result['message'])
            
            # Tesseract needs manual installation
            elif ocr_name.lower() == 'tesseract':
                if 'url' in instructions:
                    if st.button("🌐 Download Page", key=f"open_{ocr_name}_dl", use_container_width=True):
                        open_tesseract_download_page()
            
            if st.button("Close", key=f"close_{ocr_name}_inst", use_container_width=True):
                st.session_state[f'show_ocr_install_{ocr_name}'] = False
                st.rerun()


def check_system_ready():
    """
    Check if system is ready for AI categorization.
    
    Returns:
        tuple: (is_ready, missing_items)
    """
    status = st.session_state.get('system_status')
    
    if not status:
        status = check_all_dependencies()
        st.session_state['system_status'] = status
    
    missing = []
    
    if not status['ollama']['installed']:
        missing.append("Ollama not installed")
    elif status['ollama']['models'] and not status['ollama']['models']['all_installed']:
        missing_models = [m for m, installed in status['ollama']['models']['status'].items() if not installed]
        missing.append(f"Missing Ollama models: {', '.join(missing_models)}")
    
    if not status['ocr']['all_installed']:
        missing_ocr = [name for name, s in status['ocr']['ocr_models'].items() if not s['installed']]
        missing.append(f"Missing OCR: {', '.join(missing_ocr)}")
    
    return len(missing) == 0, missing