"""LLM Models management component."""
import streamlit as st
import pandas as pd
from database.db_models import LLMModel, create_connection
from utils.utils_logging import (
    get_logger_from_session, log_page_view, log_button_click,
    log_form_submit, log_database_operation
)


def get_all_llm_models():
    """Retrieve all LLM models from database."""
    conn = create_connection()
    query = """
        SELECT llm_model_uuid, system, name, description, min_ram_gb, 
               default_timeout, gpu_required, gpu_optional, min_vram_gb, 
               is_active, created_datetime, updated_datetime
        FROM llm_models
        ORDER BY system, name
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def render_llm_models_management():
    """Render LLM models management interface."""
    log_page_view(st.session_state, '/admin/llm_models')
    print("=== LLM MODELS MANAGEMENT PAGE ===")
    
    # st.markdown("### LLM Models Management")
    
    action = st.radio("Action", ["View All", "Add New", "Update", "Delete"], horizontal=True)
    
    logger = get_logger_from_session(st.session_state, console_output=True)
    logger.debug('/admin/llm_models', f"Selected action: {action}")
    print(f"--- Action Selected: {action} ---")
    
    if action == "View All":
        render_view_llm_models()
    elif action == "Add New":
        render_add_llm_model()
    elif action == "Update":
        render_update_llm_model()
    elif action == "Delete":
        render_delete_llm_model()


def render_view_llm_models():
    """Display all LLM models."""
    print("Fetching LLM models from database...")
    
    try:
        df = get_all_llm_models()
        log_database_operation(st.session_state, '/admin/llm_models', 
                              'SELECT', 'llm_models', success=True)
        print(f"✓ Successfully loaded {len(df)} LLM models")
    except Exception as e:
        log_database_operation(st.session_state, '/admin/llm_models', 
                              'SELECT', 'llm_models', success=False, error_msg=str(e))
        print(f"!!! Error loading LLM models: {str(e)} !!!")
        st.error(f"Error loading LLM models: {str(e)}")
        return
    
    if df.empty:
        st.info("No LLM models found.")
        print("No LLM models in database")
        return
    
    df['is_active'] = df['is_active'].map({1: '✓', 0: '✗'})
    df['gpu_required'] = df['gpu_required'].map({1: '✓', 0: '✗'})
    df['gpu_optional'] = df['gpu_optional'].map({1: '✓', 0: '✗'})
    
    st.dataframe(
        df[['system', 'name', 'min_ram_gb', 'gpu_required', 'gpu_optional', 
            'min_vram_gb', 'default_timeout', 'is_active']],
        use_container_width=True,
        hide_index=True
    )
    
    with st.expander("View Full Details"):
        selected_model = st.selectbox("Select Model", df['name'].tolist())
        if selected_model:
            logger = get_logger_from_session(st.session_state, console_output=True)
            logger.debug('/admin/llm_models', f"Viewing details for model: {selected_model}")
            print(f"Viewing details for: {selected_model}")
            
            model_data = df[df['name'] == selected_model].iloc[0]
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**System:** {model_data['system']}")
                st.write(f"**Name:** {model_data['name']}")
                st.write(f"**Min RAM (GB):** {model_data['min_ram_gb']}")
                st.write(f"**Min VRAM (GB):** {model_data['min_vram_gb']}")
                st.write(f"**Default Timeout:** {model_data['default_timeout']}")
            
            with col2:
                st.write(f"**GPU Required:** {model_data['gpu_required']}")
                st.write(f"**GPU Optional:** {model_data['gpu_optional']}")
                st.write(f"**Active:** {model_data['is_active']}")
                st.write(f"**Created:** {model_data['created_datetime']}")
                st.write(f"**Updated:** {model_data['updated_datetime']}")
            
            st.write(f"**Description:** {model_data['description']}")


def render_add_llm_model():
    """Render form to add new LLM model."""
    print("Rendering Add LLM Model form")
    
    with st.form("add_llm_model_form"):
        st.markdown("#### Add New LLM Model")
        
        col1, col2 = st.columns(2)
        
        with col1:
            system = st.text_input("System*", placeholder="e.g., Ollama")
            name = st.text_input("Name*", placeholder="e.g., llama2:7b")
            min_ram_gb = st.number_input("Min RAM (GB)*", min_value=0, value=8)
            min_vram_gb = st.number_input("Min VRAM (GB)", min_value=0, value=0)
        
        with col2:
            default_timeout = st.number_input("Default Timeout (seconds)*", min_value=1, value=60)
            gpu_required = st.checkbox("GPU Required")
            gpu_optional = st.checkbox("GPU Optional")
            is_active = st.checkbox("Active", value=True)
        
        description = st.text_area("Description", placeholder="Describe the model's capabilities and use cases")
        
        submit = st.form_submit_button("Add LLM Model", use_container_width=True)
        
        if submit:
            log_button_click(st.session_state, '/admin/llm_models', 
                           'Add LLM Model', f"Attempting to add model: {name}")
            print(f"=== FORM SUBMITTED: Adding LLM Model '{name}' ===")
            
            if not system or not name:
                st.error("System and Name are required fields")
                log_form_submit(st.session_state, '/admin/llm_models', 
                              'add_llm_model_form', success=False, 
                              details="Missing required fields")
                print("!!! Form validation failed: Missing required fields !!!")
            else:
                try:
                    llm_model = LLMModel()
                    model_uuid = llm_model.insert(
                        system=system,
                        name=name,
                        description=description,
                        min_ram_gb=min_ram_gb,
                        default_timeout=default_timeout,
                        gpu_required=1 if gpu_required else 0,
                        gpu_optional=1 if gpu_optional else 0,
                        min_vram_gb=min_vram_gb,
                        is_active=1 if is_active else 0
                    )
                    log_database_operation(st.session_state, '/admin/llm_models', 
                                          'INSERT', 'llm_models', success=True)
                    log_form_submit(st.session_state, '/admin/llm_models', 
                                  'add_llm_model_form', success=True, 
                                  details=f"Added LLM model: {name}")
                    print(f"✓ SUCCESS: LLM Model '{name}' added (UUID: {model_uuid})")
                    st.success(f"LLM Model '{name}' added successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error adding LLM model: {str(e)}")
                    log_database_operation(st.session_state, '/admin/llm_models', 
                                          'INSERT', 'llm_models', success=False, 
                                          error_msg=str(e))
                    log_form_submit(st.session_state, '/admin/llm_models', 
                                  'add_llm_model_form', success=False, 
                                  details=f"Error: {str(e)}")
                    print(f"!!! ERROR: Failed to add LLM model - {str(e)} !!!")


def render_update_llm_model():
    """Render form to update existing LLM model."""
    print("Rendering Update LLM Model interface")
    
    df = get_all_llm_models()
    
    if df.empty:
        st.info("No LLM models available to update.")
        print("No LLM models available for update")
        return
    
    model_name = st.selectbox("Select Model to Update", df['name'].tolist())
    
    if model_name:
        logger = get_logger_from_session(st.session_state, console_output=True)
        logger.debug('/admin/llm_models', f"Selected model for update: {model_name}")
        print(f"Selected for update: {model_name}")
        
        model_data = df[df['name'] == model_name].iloc[0]
        
        with st.form("update_llm_model_form"):
            st.markdown(f"#### Update: {model_name}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                system = st.text_input("System", value=model_data['system'])
                name = st.text_input("Name", value=model_data['name'])
                min_ram_gb = st.number_input("Min RAM (GB)", min_value=0, value=int(model_data['min_ram_gb']))
                min_vram_gb = st.number_input("Min VRAM (GB)", min_value=0, value=int(model_data['min_vram_gb']))
            
            with col2:
                default_timeout = st.number_input("Default Timeout (seconds)", min_value=1, value=int(model_data['default_timeout']))
                gpu_required = st.checkbox("GPU Required", value=bool(model_data['gpu_required']))
                gpu_optional = st.checkbox("GPU Optional", value=bool(model_data['gpu_optional']))
                is_active = st.checkbox("Active", value=bool(model_data['is_active']))
            
            description = st.text_area("Description", value=model_data['description'])
            
            submit = st.form_submit_button("Update LLM Model", use_container_width=True)
            
            if submit:
                log_button_click(st.session_state, '/admin/llm_models', 
                               'Update LLM Model', f"Updating model: {model_name}")
                print(f"=== FORM SUBMITTED: Updating LLM Model '{model_name}' ===")
                
                try:
                    llm_model = LLMModel()
                    llm_model.update(
                        llm_model_uuid=model_data['llm_model_uuid'],
                        system=system,
                        name=name,
                        description=description,
                        min_ram_gb=min_ram_gb,
                        default_timeout=default_timeout,
                        gpu_required=1 if gpu_required else 0,
                        gpu_optional=1 if gpu_optional else 0,
                        min_vram_gb=min_vram_gb,
                        is_active=1 if is_active else 0
                    )
                    log_database_operation(st.session_state, '/admin/llm_models', 
                                          'UPDATE', 'llm_models', success=True)
                    log_form_submit(st.session_state, '/admin/llm_models', 
                                  'update_llm_model_form', success=True, 
                                  details=f"Updated LLM model: {model_name} to {name}")
                    print(f"✓ SUCCESS: LLM Model updated '{model_name}' -> '{name}'")
                    st.success(f"LLM Model '{name}' updated successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error updating LLM model: {str(e)}")
                    log_database_operation(st.session_state, '/admin/llm_models', 
                                          'UPDATE', 'llm_models', success=False, 
                                          error_msg=str(e))
                    log_form_submit(st.session_state, '/admin/llm_models', 
                                  'update_llm_model_form', success=False, 
                                  details=f"Error: {str(e)}")
                    print(f"!!! ERROR: Failed to update LLM model - {str(e)} !!!")


def render_delete_llm_model():
    """Render interface to soft delete LLM model."""
    print("Rendering Delete LLM Model interface")
    
    df = get_all_llm_models()
    active_models = df[df['is_active'] == 1]
    
    if active_models.empty:
        st.info("No active LLM models available to delete.")
        print("No active LLM models available for deletion")
        return
    
    model_name = st.selectbox("Select Model to Delete", active_models['name'].tolist())
    
    if model_name:
        logger = get_logger_from_session(st.session_state, console_output=True)
        logger.debug('/admin/llm_models', f"Selected model for deletion: {model_name}")
        print(f"Selected for deletion: {model_name}")
        
        model_data = active_models[active_models['name'] == model_name].iloc[0]
        
        st.warning(f"Are you sure you want to delete '{model_name}'? This will soft delete (set is_active=0).")
        
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.button("Confirm Delete", type="primary", use_container_width=True):
                log_button_click(st.session_state, '/admin/llm_models', 
                               'Confirm Delete', f"Deleting model: {model_name}")
                print(f"=== DELETING LLM Model: {model_name} ===")
                
                try:
                    llm_model = LLMModel()
                    llm_model.delete(model_data['llm_model_uuid'])
                    log_database_operation(st.session_state, '/admin/llm_models', 
                                          'DELETE', 'llm_models', success=True)
                    print(f"✓ SUCCESS: LLM Model '{model_name}' soft deleted")
                    st.success(f"LLM Model '{model_name}' deleted successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error deleting LLM model: {str(e)}")
                    log_database_operation(st.session_state, '/admin/llm_models', 
                                          'DELETE', 'llm_models', success=False, 
                                          error_msg=str(e))
                    print(f"!!! ERROR: Failed to delete LLM model - {str(e)} !!!")
        
        with col2:
            if st.button("Cancel", use_container_width=True):
                log_button_click(st.session_state, '/admin/llm_models', 
                               'Cancel Delete', "Cancelled LLM model deletion")
                print("--- Cancelled deletion ---")
                st.rerun()
    """Retrieve all LLM models from database."""
    conn = create_connection()
    query = """
        SELECT llm_model_uuid, system, name, description, min_ram_gb, 
               default_timeout, gpu_required, gpu_optional, min_vram_gb, 
               is_active, created_datetime, updated_datetime
        FROM llm_models
        ORDER BY system, name
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def render_llm_models_management():
    """Render LLM models management interface."""
    # st.markdown("### LLM Models Management")
    
    action = st.radio("Action", ["View All", "Add New", "Update", "Delete"], horizontal=True)
    
    if action == "View All":
        render_view_llm_models()
    elif action == "Add New":
        render_add_llm_model()
    elif action == "Update":
        render_update_llm_model()
    elif action == "Delete":
        render_delete_llm_model()


def render_view_llm_models():
    """Display all LLM models."""
    df = get_all_llm_models()
    
    if df.empty:
        st.info("No LLM models found.")
        return
    
    df['is_active'] = df['is_active'].map({1: '✓', 0: '✗'})
    df['gpu_required'] = df['gpu_required'].map({1: '✓', 0: '✗'})
    df['gpu_optional'] = df['gpu_optional'].map({1: '✓', 0: '✗'})
    
    st.dataframe(
        df[['system', 'name', 'min_ram_gb', 'gpu_required', 'gpu_optional', 
            'min_vram_gb', 'default_timeout', 'is_active']],
        use_container_width=True,
        hide_index=True
    )
    
    with st.expander("View Full Details"):
        selected_model = st.selectbox("Select Model", df['name'].tolist())
        if selected_model:
            model_data = df[df['name'] == selected_model].iloc[0]
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**System:** {model_data['system']}")
                st.write(f"**Name:** {model_data['name']}")
                st.write(f"**Min RAM (GB):** {model_data['min_ram_gb']}")
                st.write(f"**Min VRAM (GB):** {model_data['min_vram_gb']}")
                st.write(f"**Default Timeout:** {model_data['default_timeout']}")
            
            with col2:
                st.write(f"**GPU Required:** {model_data['gpu_required']}")
                st.write(f"**GPU Optional:** {model_data['gpu_optional']}")
                st.write(f"**Active:** {model_data['is_active']}")
                st.write(f"**Created:** {model_data['created_datetime']}")
                st.write(f"**Updated:** {model_data['updated_datetime']}")
            
            st.write(f"**Description:** {model_data['description']}")


def render_add_llm_model():
    """Render form to add new LLM model."""
    with st.form("add_llm_model_form"):
        st.markdown("#### Add New LLM Model")
        
        col1, col2 = st.columns(2)
        
        with col1:
            system = st.text_input("System*", placeholder="e.g., Ollama")
            name = st.text_input("Name*", placeholder="e.g., llama2:7b")
            min_ram_gb = st.number_input("Min RAM (GB)*", min_value=0, value=8)
            min_vram_gb = st.number_input("Min VRAM (GB)", min_value=0, value=0)
        
        with col2:
            default_timeout = st.number_input("Default Timeout (seconds)*", min_value=1, value=60)
            gpu_required = st.checkbox("GPU Required")
            gpu_optional = st.checkbox("GPU Optional")
            is_active = st.checkbox("Active", value=True)
        
        description = st.text_area("Description", placeholder="Describe the model's capabilities and use cases")
        
        submit = st.form_submit_button("Add LLM Model", use_container_width=True)
        
        if submit:
            if not system or not name:
                st.error("System and Name are required fields")
            else:
                try:
                    llm_model = LLMModel()
                    llm_model.insert(
                        system=system,
                        name=name,
                        description=description,
                        min_ram_gb=min_ram_gb,
                        default_timeout=default_timeout,
                        gpu_required=1 if gpu_required else 0,
                        gpu_optional=1 if gpu_optional else 0,
                        min_vram_gb=min_vram_gb,
                        is_active=1 if is_active else 0
                    )
                    st.success(f"LLM Model '{name}' added successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error adding LLM model: {str(e)}")


def render_update_llm_model():
    """Render form to update existing LLM model."""
    df = get_all_llm_models()
    
    if df.empty:
        st.info("No LLM models available to update.")
        return
    
    model_name = st.selectbox("Select Model to Update", df['name'].tolist())
    
    if model_name:
        model_data = df[df['name'] == model_name].iloc[0]
        
        with st.form("update_llm_model_form"):
            st.markdown(f"#### Update: {model_name}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                system = st.text_input("System", value=model_data['system'])
                name = st.text_input("Name", value=model_data['name'])
                min_ram_gb = st.number_input("Min RAM (GB)", min_value=0, value=int(model_data['min_ram_gb']))
                min_vram_gb = st.number_input("Min VRAM (GB)", min_value=0, value=int(model_data['min_vram_gb']))
            
            with col2:
                default_timeout = st.number_input("Default Timeout (seconds)", min_value=1, value=int(model_data['default_timeout']))
                gpu_required = st.checkbox("GPU Required", value=bool(model_data['gpu_required']))
                gpu_optional = st.checkbox("GPU Optional", value=bool(model_data['gpu_optional']))
                is_active = st.checkbox("Active", value=bool(model_data['is_active']))
            
            description = st.text_area("Description", value=model_data['description'])
            
            submit = st.form_submit_button("Update LLM Model", use_container_width=True)
            
            if submit:
                try:
                    llm_model = LLMModel()
                    llm_model.update(
                        llm_model_uuid=model_data['llm_model_uuid'],
                        system=system,
                        name=name,
                        description=description,
                        min_ram_gb=min_ram_gb,
                        default_timeout=default_timeout,
                        gpu_required=1 if gpu_required else 0,
                        gpu_optional=1 if gpu_optional else 0,
                        min_vram_gb=min_vram_gb,
                        is_active=1 if is_active else 0
                    )
                    st.success(f"LLM Model '{name}' updated successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error updating LLM model: {str(e)}")


def render_delete_llm_model():
    """Render interface to soft delete LLM model."""
    df = get_all_llm_models()
    active_models = df[df['is_active'] == 1]
    
    if active_models.empty:
        st.info("No active LLM models available to delete.")
        return
    
    model_name = st.selectbox("Select Model to Delete", active_models['name'].tolist())
    
    if model_name:
        model_data = active_models[active_models['name'] == model_name].iloc[0]
        
        st.warning(f"Are you sure you want to delete '{model_name}'? This will soft delete (set is_active=0).")
        
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.button("Confirm Delete", type="primary", use_container_width=True):
                try:
                    llm_model = LLMModel()
                    llm_model.delete(model_data['llm_model_uuid'])
                    st.success(f"LLM Model '{model_name}' deleted successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error deleting LLM model: {str(e)}")
        
        with col2:
            if st.button("Cancel", use_container_width=True):
                st.rerun()