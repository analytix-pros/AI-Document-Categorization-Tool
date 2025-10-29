"""LLM Models management component with data_editor."""
import streamlit as st
import pandas as pd
from database.db_models import LLMModel, create_connection
from utils.utils_logging import (
    get_logger_from_session, log_page_view, log_button_click,
    log_form_submit, log_database_operation
)


def get_all_llm_models():
    """Retrieve all LLM models from database including inactive ones."""
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
    """Render LLM models management interface with data editor."""
    log_page_view(st.session_state, '/admin/llm_models')
    # print("=== LLM MODELS MANAGEMENT PAGE ===")
    
    # st.markdown("### LLM Models Management")
    
    df = get_all_llm_models()
    
    if df.empty:
        st.info("No LLM models found.")
        if st.button("➕ Add New Model", key="llm_add_first_model"):
            st.session_state['adding_llm_model'] = True
        
        if st.session_state.get('adding_llm_model', False):
            render_add_form()
        return
    
    # Create two columns: table on left, details on right
    col_table, col_details = st.columns([4, 2])
    
    with col_table:
        # Prepare display dataframe
        display_df = df.copy()
        display_df['is_active'] = display_df['is_active'].astype(bool)
        display_df['gpu_required'] = display_df['gpu_required'].astype(bool)
        display_df['gpu_optional'] = display_df['gpu_optional'].astype(bool)
        
        # Select columns for display
        edit_columns = ['system', 'name', 'min_ram_gb', 'default_timeout', 
                       'gpu_required', 'gpu_optional', 'min_vram_gb', 'is_active']
        
        # Data editor
        edited_df = st.data_editor(
            display_df[['llm_model_uuid'] + edit_columns],
            hide_index=True,
            width='stretch',
            disabled=['llm_model_uuid'],
            column_config={
                'llm_model_uuid': st.column_config.TextColumn('UUID', width='small'),
                'system': st.column_config.TextColumn('System', width='small'),
                'name': st.column_config.TextColumn('Name', width='medium'),
                'min_ram_gb': st.column_config.NumberColumn('Min RAM (GB)', min_value=0, max_value=512),
                'default_timeout': st.column_config.NumberColumn('Timeout (s)', min_value=1, max_value=3600),
                'gpu_required': st.column_config.CheckboxColumn('GPU Req'),
                'gpu_optional': st.column_config.CheckboxColumn('GPU Opt'),
                'min_vram_gb': st.column_config.NumberColumn('Min VRAM (GB)', min_value=0, max_value=512),
                'is_active': st.column_config.CheckboxColumn('Active')
            },
            key='llm_models_editor'
        )
        
        # Detect changes
        if not edited_df.equals(display_df[['llm_model_uuid'] + edit_columns]):
            st.info("⚠️ Changes detected - Click 'Save Changes' to apply")
            
            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                if st.button("💾 Save Changes", key="llm_save_changes", type="primary", width='stretch'):
                    save_changes(df, edited_df)
                    st.rerun()
            with col2:
                if st.button("↩️ Discard", key="llm_discard_changes", width='stretch'):
                    st.rerun()
        
        # Add new button
        if st.button("➕ Add New Model", key="llm_add_new_button", width='stretch'):
            st.session_state['adding_llm_model'] = True
            st.rerun()
        
        if st.session_state.get('adding_llm_model', False):
            render_add_form()
    
    with col_details:
        # st.markdown("#### Full Details")
        
        # Selection mechanism
        model_options = ['(View More Details)'] + df['name'].tolist()
        selected_model = st.selectbox(
            "Select model to view details",
            model_options,
            key='llm_detail_select',
            label_visibility='collapsed'
        )
        
        if selected_model != '(View More Details)':
            model_data = df[df['name'] == selected_model].iloc[0]
            
            st.markdown(f"**System:** {model_data['system']}")
            st.markdown(f"**Name:** {model_data['name']}")
            st.markdown(f"**Min RAM:** {model_data['min_ram_gb']} GB")
            st.markdown(f"**Min VRAM:** {model_data['min_vram_gb']} GB")
            st.markdown(f"**Timeout:** {model_data['default_timeout']} seconds")
            st.markdown(f"**GPU Required:** {'Yes' if model_data['gpu_required'] else 'No'}")
            st.markdown(f"**GPU Optional:** {'Yes' if model_data['gpu_optional'] else 'No'}")
            st.markdown(f"**Active:** {'Yes' if model_data['is_active'] else 'No'}")
            
            st.markdown("---")
            st.markdown("**Description:**")
            st.write(model_data['description'] if pd.notna(model_data['description']) else 'N/A')
            
            st.markdown("---")
            st.caption(f"Created: {model_data['created_datetime']}")
            st.caption(f"Updated: {model_data['updated_datetime']}")
            
            # Edit description button
            if st.button("✏️ Edit Description", key="llm_edit_desc_button", width='stretch'):
                st.session_state['editing_description'] = model_data['llm_model_uuid']
                st.rerun()
            
            if st.session_state.get('editing_description') == model_data['llm_model_uuid']:
                render_description_editor(model_data)


def save_changes(original_df, edited_df):
    """Save changes from data editor to database."""
    logger = get_logger_from_session(st.session_state, console_output=True)
    
    # Merge to find changes
    merged = edited_df.merge(
        original_df[['llm_model_uuid', 'system', 'name', 'min_ram_gb', 'default_timeout',
                     'gpu_required', 'gpu_optional', 'min_vram_gb', 'is_active']],
        on='llm_model_uuid',
        suffixes=('_new', '_old')
    )
    
    changes_made = 0
    errors = []
    
    for idx, row in merged.iterrows():
        changed = False
        update_params = {'llm_model_uuid': row['llm_model_uuid']}
        
        # Check each field for changes
        if row['system_new'] != row['system_old']:
            update_params['system'] = row['system_new']
            changed = True
        
        if row['name_new'] != row['name_old']:
            update_params['name'] = row['name_new']
            changed = True
        
        if row['min_ram_gb_new'] != row['min_ram_gb_old']:
            update_params['min_ram_gb'] = int(row['min_ram_gb_new'])
            changed = True
        
        if row['default_timeout_new'] != row['default_timeout_old']:
            update_params['default_timeout'] = int(row['default_timeout_new'])
            changed = True
        
        if row['gpu_required_new'] != row['gpu_required_old']:
            update_params['gpu_required'] = 1 if row['gpu_required_new'] else 0
            changed = True
        
        if row['gpu_optional_new'] != row['gpu_optional_old']:
            update_params['gpu_optional'] = 1 if row['gpu_optional_new'] else 0
            changed = True
        
        if row['min_vram_gb_new'] != row['min_vram_gb_old']:
            update_params['min_vram_gb'] = int(row['min_vram_gb_new'])
            changed = True
        
        if row['is_active_new'] != row['is_active_old']:
            update_params['is_active'] = 1 if row['is_active_new'] else 0
            changed = True
        
        if changed:
            try:
                llm_model = LLMModel()
                llm_model.update(**update_params)
                changes_made += 1
                log_database_operation(st.session_state, '/admin/llm_models', 
                                      'UPDATE', 'llm_models', success=True)
                logger.info('/admin/llm_models', f"Updated model: {row['name_new']}")
            except Exception as e:
                errors.append(f"Error updating {row['name_new']}: {str(e)}")
                log_database_operation(st.session_state, '/admin/llm_models', 
                                      'UPDATE', 'llm_models', success=False, error_msg=str(e))
    
    if errors:
        for error in errors:
            st.error(error)
    
    if changes_made > 0:
        st.success(f"✅ Successfully updated {changes_made} model(s)")
        logger.info('/admin/llm_models', f"Saved {changes_made} changes")


def render_add_form():
    """Render form to add new LLM model."""
    st.markdown("---")
    st.markdown("#### Add New LLM Model")
    
    with st.form("add_llm_form", width='stretch'):
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
        
        description = st.text_area("Description", placeholder="Describe the model's capabilities")
        
        col_submit, col_cancel = st.columns(2)
        
        with col_submit:
            submit = st.form_submit_button("Add Model", width='stretch')
        
        with col_cancel:
            cancel = st.form_submit_button("Cancel", width='stretch')
        
        if cancel:
            st.session_state['adding_llm_model'] = False
            st.rerun()
        
        if submit:
            if not system or not name:
                st.error("System and Name are required")
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
                    st.success(f"Model '{name}' added successfully!")
                    st.session_state['adding_llm_model'] = False
                    st.rerun()
                except Exception as e:
                    st.error(f"Error adding model: {str(e)}")
                    log_database_operation(st.session_state, '/admin/llm_models', 
                                          'INSERT', 'llm_models', success=False, error_msg=str(e))


def render_description_editor(model_data):
    """Render inline description editor."""
    with st.form(f"edit_desc_{model_data['llm_model_uuid']}"):
        new_description = st.text_area(
            "Edit Description",
            value=model_data['description'] if pd.notna(model_data['description']) else '',
            height=200
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("💾 Save", width='stretch'):
                try:
                    llm_model = LLMModel()
                    llm_model.update(
                        llm_model_uuid=model_data['llm_model_uuid'],
                        description=new_description
                    )
                    st.success("Description updated!")
                    st.session_state['editing_description'] = None
                    log_database_operation(st.session_state, '/admin/llm_models', 
                                          'UPDATE', 'llm_models', success=True)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        
        with col2:
            if st.form_submit_button("Cancel", width='stretch'):
                st.session_state['editing_description'] = None
                st.rerun()