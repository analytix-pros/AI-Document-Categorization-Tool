"""System status sidebar component - updated to work with new system_checker."""
import streamlit as st
import sys
import pandas as pd

from utils.utils_logging import log_system_status
from initial_setup.system_checker import (
    check_all_dependencies,
    download_all_required_models,
    check_required_ollama_models,
    check_ocr_dependencies,
    enable_ollama_airplane_mode,
    start_ollama_service
)
from initial_setup.llm_installer import (
    get_ollama_install_instructions,
    install_ollama_model,
    open_ollama_download_page
)
from initial_setup.ocr_installer import (
    get_ocr_install_instructions,
    install_python_ocr_package,
    open_tesseract_download_page
)


def render_system_status_sidebar():
    """Render full system status inside a collapsible expander, minimized by default."""
    with st.sidebar:
        with st.expander("System Status", expanded=False):
            if 'system_status' not in st.session_state:
                with st.spinner("Checking system dependencies..."):
                    st.session_state['system_status'] = check_all_dependencies()

            status = st.session_state['system_status']

            # Overall System Ready Status
            st.markdown("---")
            if status.get('all_ready'):
                st.success("✅ System Ready")
            else:
                st.error("❌ System Not Ready")
                
                # Show what's missing
                issues = []
                if not status.get('ollama', {}).get('installed'):
                    issues.append("Ollama not installed")
                elif not status.get('ollama', {}).get('running'):
                    issues.append("Ollama not running")
                else:
                    models = status.get('ollama', {}).get('models', {})
                    if not models.get('all_working'):
                        missing = models.get('missing_models', [])
                        broken = models.get('broken_models', [])
                        if missing:
                            issues.append(f"{len(missing)} model(s) missing")
                        if broken:
                            issues.append(f"{len(broken)} model(s) broken")
                
                if not status.get('ocr', {}).get('at_least_one_available'):
                    issues.append("No OCR models")
                
                if not status.get('poppler', {}).get('installed'):
                    issues.append("Poppler not installed")
                
                if issues:
                    with st.expander("Issues"):
                        for issue in issues:
                            st.markdown(f"- {issue}")
                        
            if st.button("🔄 Refresh Status", key="refresh_system_status", width='stretch'):
                with st.spinner("Refreshing system status..."):
                    st.session_state['system_status'] = check_all_dependencies()
                    st.rerun()

            st.markdown("---")

            
            # OCR Status
            st.markdown("## OCR Models")
            ocr_status = status.get('ocr', {})
            ocr_models = ocr_status.get('ocr_models', {})
            
            for model_name, model_info in ocr_models.items():
                if model_info.get('installed') and model_info.get('running'):
                    st.caption(f"✅ **{model_name}:** {model_info.get('version', 'Installed')}")
                else:
                    st.caption(f"❌ **{model_name}:** {model_info.get('error', 'Not installed')}")
                    if st.button(f"Install {model_name}", key=f"install_ocr_{model_name}"):
                        st.session_state[f'show_{model_name}_install_guide'] = True
            
            if not ocr_status.get('at_least_one_available', False):
                st.error("⚠️ No OCR models available. Please install at least one OCR model.")
            
            # Ollama Status
            st.markdown("## Ollama (LLM)")
            ollama_info = status.get('ollama', {})
            
            if not ollama_info.get('installed'):
                st.error("❌ Ollama not installed")
                st.caption(ollama_info.get('message', 'Please install Ollama'))
                if st.button("📥 Install Ollama", key="show_ollama_install"):
                    st.session_state['show_ollama_install_guide'] = True
            else:
                st.caption(f"✅ **Version:** {ollama_info.get('version', 'Unknown')}")
                
                if not ollama_info.get('running'):
                    st.warning("⚠️ Ollama service not running")
                    if st.button("▶️ Start Ollama", key="start_ollama_service"):
                        with st.spinner("Starting Ollama service..."):
                            start_result = start_ollama_service()
                            if start_result['success']:
                                st.success("Ollama service started!")
                                st.session_state['system_status'] = check_all_dependencies()
                                st.rerun()
                            else:
                                st.error(f"Failed to start: {start_result['message']}")
                else:
                    st.caption("✅ **Service:** Running")
                    
                    # Models Status
                    models_info = ollama_info.get('models', {})
                    required_models = models_info.get('required', [])
                    installed_models = models_info.get('installed', [])
                    missing_models = models_info.get('missing_models', [])
                    broken_models = models_info.get('broken_models', [])
                    all_working = models_info.get('all_working', False)
                    
                    if required_models:
                        working_count = len([m for m in required_models if m not in missing_models and m not in broken_models])
                        st.caption(f"**Models:** {working_count}/{len(required_models)} working")
                        
                        # Show missing models
                        if missing_models:
                            st.warning(f"⚠️ Missing {len(missing_models)} model(s)")
                            with st.expander("Missing Models"):
                                for model in missing_models:
                                    st.caption(f"- {model}")
                        
                        # Show broken models
                        if broken_models:
                            st.error(f"🔴 {len(broken_models)} broken model(s)")
                            with st.expander("Broken Models"):
                                verification = models_info.get('verification', {})
                                for model in broken_models:
                                    error_msg = verification.get(model, {}).get('error', 'Unknown error')
                                    st.caption(f"- **{model}**: {error_msg}")
                        
                        # Button to pull all models (missing or broken)
                        if missing_models or broken_models:
                            if st.button("📥 Pull All Required Models", key="pull_all_models"):
                                with st.spinner("Pulling models..."):
                                    download_result = download_all_required_models()
                                    if download_result['success']:
                                        st.success("All models pulled successfully!")
                                        st.session_state['system_status'] = check_all_dependencies()
                                        st.rerun()
                                    else:
                                        failed = download_result.get('models_failed', [])
                                        st.error(f"Some models failed: {download_result['message']}")
                                        if failed:
                                            with st.expander("Failed Models"):
                                                for fail in failed:
                                                    st.markdown(f"- **{fail['model']}**: {fail['error']}")
                    
                    # # Airplane Mode Status
                    # airplane_info = ollama_info.get('airplane_mode', {})
                    # if airplane_info.get('in_airplane_mode'):
                    #     st.markdown("✅ **Airplane Mode:** ON (Secure)")
                    # else:
                    #     st.warning("⚠️ **Airplane Mode:** OFF")
                    #     st.markdown(airplane_info.get('message', ''))
                        
                    #     if airplane_info.get('can_verify'):
                    #         if st.button("🛡️ Enable Airplane Mode", key="enable_airplane_mode"):
                    #             with st.spinner("Enabling airplane mode..."):
                    #                 enable_result = enable_ollama_airplane_mode()
                    #                 if enable_result['success']:
                    #                     st.success("Airplane mode enabled!")
                    #                     st.session_state['system_status'] = check_all_dependencies()
                    #                     st.rerun()
                    #                 else:
                    #                     st.error(f"Failed: {enable_result['message']}")
                    #     else:
                    #         st.info("Cannot verify airplane mode - service may not be responding")
            
            st.markdown("---")

            # OS Info
            st.markdown("## System Details")
            os_info = status.get('os', {})
            st.caption(f"{os_info.get('system', 'Unknown')} - {os_info.get('machine', 'Unknown')}")
            
            # System Specs
            specs = status.get('system_specs', {})
            if 'memory' in specs:
                st.markdown("#### RAM")
                st.caption(f"{specs['memory'].get('total_gb', 0):.1f} GB")
            if 'gpu_available' in specs:
                st.markdown("#### GPU Available")
                gpu_status = "✅ Available" if specs['gpu_available'] else "❌ Not Available"
                st.caption(f"{gpu_status}")
            if 'python' in specs:
                st.markdown("#### Python")
                st.caption(f"Version: {specs['python']['version']}")
            
            # Poppler Status
            st.markdown("#### Poppler")
            poppler_status = status.get('poppler', {})
            if poppler_status.get('installed'):
                st.caption("✅ **Poppler:** Installed")
            else:
                st.caption(f"❌ **Poppler:** {poppler_status.get('error', 'Not installed')}")


def render_ollama_install_guide():
    """Render Ollama installation guide modal."""
    if not st.session_state.get('show_ollama_install_guide'):
        return
    
    instructions = get_ollama_install_instructions()
    st.markdown("#### Ollama Installation")
    st.markdown(f"**Method:** {instructions['method']}")
    for instruction in instructions['instructions']:
        st.markdown(f"- {instruction}")
    if 'cli_command' in instructions:
        st.code(instructions['cli_command'], language='bash')
    if 'url' in instructions:
        if st.button("Open Download Page", key="open_ollama_dl"):
            open_ollama_download_page()
    if st.button("Close", key="close_ollama_guide"):
        st.session_state['show_ollama_install_guide'] = False
        st.rerun()


def check_system_ready_for_upload():
    """Check if system is ready for file upload operations."""
    status = st.session_state.get('system_status') or check_all_dependencies()
    st.session_state['system_status'] = status
    missing = []

    # Check Ollama
    if not status['ollama']['installed']:
        missing.append("Ollama not installed")
    elif not status['ollama'].get('running'):
        missing.append("Ollama service not running")
    else:
        models_info = status['ollama'].get('models', {})
        
        # Check for missing models
        missing_models = models_info.get('missing_models', [])
        if missing_models:
            missing.append(f"{len(missing_models)} Ollama model(s) not installed")
        
        # Check for broken models
        broken_models = models_info.get('broken_models', [])
        if broken_models:
            missing.append(f"{len(broken_models)} Ollama model(s) broken/not working")
        
        # Overall working status
        if not models_info.get('all_working'):
            if not missing_models and not broken_models:
                missing.append("Some Ollama models are not working properly")
        
        # # Check airplane mode
        # airplane_info = status['ollama'].get('airplane_mode', {})
        # if not airplane_info.get('in_airplane_mode') and airplane_info.get('can_verify'):
        #     missing.append("Airplane mode not enabled (security requirement)")

    # Check OCR
    ocr_status = status.get('ocr', {})
    if not ocr_status.get('at_least_one_available'):
        missing_ocr = [n for n, s in ocr_status.get('ocr_models', {}).items() if not s.get('installed')]
        missing.append(f"No OCR models installed. Need: {', '.join(missing_ocr)}")

    # Check Poppler
    if not status.get('poppler', {}).get('installed'):
        missing.append("Poppler not installed")

    return len(missing) == 0, missing


def prepare_ollama_models_background(progress_container=None):
    """Prepare Ollama models in background - force pull all required models."""
    models_status = check_required_ollama_models()
    required_models = models_status.get('required', [])
    
    if not required_models:
        return {
            'success': True,
            'message': 'No models required for this hardware',
            'models_prepared': [],
            'already_available': []
        }

    # Check airplane mode before attempting downloads
    status = st.session_state.get('system_status', {})
    airplane = status.get('ollama', {}).get('airplane_mode', {})
    
    if airplane.get('in_airplane_mode') and airplane.get('can_verify'):
        # In airplane mode - can't download
        missing = models_status.get('missing_models', [])
        broken = models_status.get('broken_models', [])
        
        return {
            'success': False,
            'message': 'Cannot download models - airplane mode is enabled (security requirement)',
            'models_prepared': [],
            'already_available': [m for m in required_models if m not in missing and m not in broken],
            'failed': missing + broken
        }

    # Not in airplane mode or can't verify - attempt to pull all models
    if progress_container:
        with progress_container:
            st.info(f"Pulling {len(required_models)} model(s)...")
            progress_bar = st.progress(0)
            status_text = st.empty()
            completed = 0
            total = len(required_models)

            def progress_callback(model_name, status_type, message):
                nonlocal completed
                if status_type in ['completed', 'failed']:
                    completed += 1
                progress_bar.progress(completed / total)
                status_text.text(f"{completed}/{total} models processed")

            result = download_all_required_models(progress_callback=progress_callback)
    else:
        result = download_all_required_models()

    return {
        'success': result['success'],
        'message': result['message'],
        'models_prepared': result.get('models_pulled', []),
        'already_available': [],
        'failed': result.get('models_failed', [])
    }



# Backward compatibility
def check_system_ready():
    return_val = check_system_ready_for_upload()
    log_system_status(session_state=st.session_state, system_status_payload=return_val, page_name='/system_status') 
    return return_val