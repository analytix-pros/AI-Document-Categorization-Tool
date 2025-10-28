"""OCR Models management component with data_editor."""
import streamlit as st
import pandas as pd
from database.db_models import OCRModel, create_connection


def get_all_ocr_models():
    """Retrieve all OCR models from database."""
    conn = create_connection()
    query = """
        SELECT ocr_models_uuid, name, default_language, default_dpi, 
               max_pages, is_active, created_datetime, updated_datetime
        FROM ocr_models
        ORDER BY name
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def render_ocr_models_management():
    """Render OCR models management interface with data editor."""
    # st.markdown("### OCR Models Management")
    
    df = get_all_ocr_models()
    
    if df.empty:
        st.info("No OCR models found.")
        if st.button("➕ Add New Model", key="ocr_add_first_model"):
            st.session_state['adding_ocr_model'] = True
        
        if st.session_state.get('adding_ocr_model', False):
            render_add_form()
        return
    
    col_table, col_details = st.columns([4, 2])
    
    with col_table:
        display_df = df.copy()
        display_df['is_active'] = display_df['is_active'].astype(bool)
        
        edit_columns = ['name', 'default_language', 'default_dpi', 'max_pages', 'is_active']
        
        edited_df = st.data_editor(
            display_df[['ocr_models_uuid'] + edit_columns],
            hide_index=True,
            width='stretch',
            disabled=['ocr_models_uuid'],
            column_config={
                'ocr_models_uuid': st.column_config.TextColumn('UUID', width='small'),
                'name': st.column_config.TextColumn('Name', width='medium'),
                'default_language': st.column_config.TextColumn('Language', width='small'),
                'default_dpi': st.column_config.NumberColumn('DPI', min_value=72, max_value=1200),
                'max_pages': st.column_config.NumberColumn('Max Pages', min_value=1, max_value=1000),
                'is_active': st.column_config.CheckboxColumn('Active')
            },
            key='ocr_models_editor'
        )
        
        if not edited_df.equals(display_df[['ocr_models_uuid'] + edit_columns]):
            st.info("⚠️ Changes detected - Click 'Save Changes' to apply")
            
            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                if st.button("💾 Save Changes", key="ocr_save_changes", type="primary", width='stretch'):
                    save_changes(df, edited_df)
                    st.rerun()
            with col2:
                if st.button("↩️ Discard", key="ocr_discard_changes", width='stretch'):
                    st.rerun()
        
        if st.button("➕ Add New Model", key="ocr_add_new_button", width='stretch'):
            st.session_state['adding_ocr_model'] = True
            st.rerun()
        
        if st.session_state.get('adding_ocr_model', False):
            render_add_form()
    
    with col_details:
        # st.markdown("#### Full Details")
        
        model_options = ['(View More Details)'] + df['name'].tolist()
        selected_model = st.selectbox(
            "Select model",
            model_options,
            key='ocr_detail_select',
            label_visibility='collapsed'
        )
        
        if selected_model != '(View More Details)':
            model_data = df[df['name'] == selected_model].iloc[0]
            
            st.markdown(f"**Name:** {model_data['name']}")
            st.markdown(f"**Language:** {model_data['default_language']}")
            st.markdown(f"**DPI:** {model_data['default_dpi']}")
            st.markdown(f"**Max Pages:** {model_data['max_pages']}")
            st.markdown(f"**Active:** {'Yes' if model_data['is_active'] else 'No'}")
            
            st.markdown("---")
            st.caption(f"Created: {model_data['created_datetime']}")
            st.caption(f"Updated: {model_data['updated_datetime']}")


def save_changes(original_df, edited_df):
    """Save changes to database."""
    merged = edited_df.merge(
        original_df[['ocr_models_uuid', 'name', 'default_language', 'default_dpi', 'max_pages', 'is_active']],
        on='ocr_models_uuid',
        suffixes=('_new', '_old')
    )
    
    changes_made = 0
    for idx, row in merged.iterrows():
        changed = False
        update_params = {'ocr_models_uuid': row['ocr_models_uuid']}
        
        if row['name_new'] != row['name_old']:
            update_params['name'] = row['name_new']
            changed = True
        if row['default_language_new'] != row['default_language_old']:
            update_params['default_language'] = row['default_language_new']
            changed = True
        if row['default_dpi_new'] != row['default_dpi_old']:
            update_params['default_dpi'] = int(row['default_dpi_new'])
            changed = True
        if row['max_pages_new'] != row['max_pages_old']:
            update_params['max_pages'] = int(row['max_pages_new'])
            changed = True
        if row['is_active_new'] != row['is_active_old']:
            update_params['is_active'] = 1 if row['is_active_new'] else 0
            changed = True
        
        if changed:
            try:
                ocr_model = OCRModel()
                ocr_model.update(**update_params)
                changes_made += 1
            except Exception as e:
                st.error(f"Error updating {row['name_new']}: {str(e)}")
    
    if changes_made > 0:
        st.success(f"✅ Updated {changes_made} model(s)")


def render_add_form():
    """Render add form."""
    st.markdown("---")
    st.markdown("#### Add New OCR Model")
    
    with st.form("add_ocr_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Name*", placeholder="e.g., Tesseract")
            default_language = st.text_input("Default Language*", value="English")
            default_dpi = st.number_input("Default DPI*", min_value=72, max_value=1200, value=400)
        
        with col2:
            max_pages = st.number_input("Max Pages*", min_value=1, value=10)
            is_active = st.checkbox("Active", value=True)
        
        col_submit, col_cancel = st.columns(2)
        
        with col_submit:
            submit = st.form_submit_button("Add Model", width='stretch')
        
        with col_cancel:
            cancel = st.form_submit_button("Cancel", width='stretch')
        
        if cancel:
            st.session_state['adding_ocr_model'] = False
            st.rerun()
        
        if submit:
            if not name or not default_language:
                st.error("Name and Language are required")
            else:
                try:
                    ocr_model = OCRModel()
                    ocr_model.insert(
                        name=name,
                        default_language=default_language,
                        default_dpi=default_dpi,
                        max_pages=max_pages,
                        is_active=1 if is_active else 0
                    )
                    st.success(f"Model '{name}' added!")
                    st.session_state['adding_ocr_model'] = False
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {str(e)}")