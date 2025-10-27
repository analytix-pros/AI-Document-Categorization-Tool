"""OCR Models management component."""
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
    """Render OCR models management interface."""
    # st.markdown("### OCR Models Management")
    
    action = st.radio("Action", ["View All", "Add New", "Update", "Delete"], horizontal=True, key="ocr_action")
    
    if action == "View All":
        render_view_ocr_models()
    elif action == "Add New":
        render_add_ocr_model()
    elif action == "Update":
        render_update_ocr_model()
    elif action == "Delete":
        render_delete_ocr_model()


def render_view_ocr_models():
    """Display all OCR models."""
    df = get_all_ocr_models()
    
    if df.empty:
        st.info("No OCR models found.")
        return
    
    df['is_active'] = df['is_active'].map({1: '✓', 0: '✗'})
    
    st.dataframe(
        df[['name', 'default_language', 'default_dpi', 'max_pages', 'is_active']],
        use_container_width=True,
        hide_index=True
    )
    
    with st.expander("View Full Details"):
        selected_model = st.selectbox("Select Model", df['name'].tolist(), key="ocr_view_select")
        if selected_model:
            model_data = df[df['name'] == selected_model].iloc[0]
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Name:** {model_data['name']}")
                st.write(f"**Default Language:** {model_data['default_language']}")
                st.write(f"**Default DPI:** {model_data['default_dpi']}")
            
            with col2:
                st.write(f"**Max Pages:** {model_data['max_pages']}")
                st.write(f"**Active:** {model_data['is_active']}")
                st.write(f"**Created:** {model_data['created_datetime']}")
                st.write(f"**Updated:** {model_data['updated_datetime']}")


def render_add_ocr_model():
    """Render form to add new OCR model."""
    with st.form("add_ocr_model_form"):
        st.markdown("#### Add New OCR Model")
        
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Name*", placeholder="e.g., Tesseract")
            default_language = st.text_input("Default Language*", value="English")
            default_dpi = st.number_input("Default DPI*", min_value=72, max_value=1200, value=400)
        
        with col2:
            max_pages = st.number_input("Max Pages*", min_value=1, value=10)
            is_active = st.checkbox("Active", value=True)
        
        submit = st.form_submit_button("Add OCR Model", use_container_width=True)
        
        if submit:
            if not name or not default_language:
                st.error("Name and Default Language are required fields")
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
                    st.success(f"OCR Model '{name}' added successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error adding OCR model: {str(e)}")


def render_update_ocr_model():
    """Render form to update existing OCR model."""
    df = get_all_ocr_models()
    
    if df.empty:
        st.info("No OCR models available to update.")
        return
    
    model_name = st.selectbox("Select Model to Update", df['name'].tolist(), key="ocr_update_select")
    
    if model_name:
        model_data = df[df['name'] == model_name].iloc[0]
        
        with st.form("update_ocr_model_form"):
            st.markdown(f"#### Update: {model_name}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Name", value=model_data['name'])
                default_language = st.text_input("Default Language", value=model_data['default_language'])
                default_dpi = st.number_input("Default DPI", min_value=72, max_value=1200, value=int(model_data['default_dpi']))
            
            with col2:
                max_pages = st.number_input("Max Pages", min_value=1, value=int(model_data['max_pages']))
                is_active = st.checkbox("Active", value=bool(model_data['is_active']))
            
            submit = st.form_submit_button("Update OCR Model", use_container_width=True)
            
            if submit:
                try:
                    ocr_model = OCRModel()
                    ocr_model.update(
                        ocr_models_uuid=model_data['ocr_models_uuid'],
                        name=name,
                        default_language=default_language,
                        default_dpi=default_dpi,
                        max_pages=max_pages,
                        is_active=1 if is_active else 0
                    )
                    st.success(f"OCR Model '{name}' updated successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error updating OCR model: {str(e)}")


def render_delete_ocr_model():
    """Render interface to soft delete OCR model."""
    df = get_all_ocr_models()
    active_models = df[df['is_active'] == 1]
    
    if active_models.empty:
        st.info("No active OCR models available to delete.")
        return
    
    model_name = st.selectbox("Select Model to Delete", active_models['name'].tolist(), key="ocr_delete_select")
    
    if model_name:
        model_data = active_models[active_models['name'] == model_name].iloc[0]
        
        st.warning(f"Are you sure you want to delete '{model_name}'? This will soft delete (set is_active=0).")
        
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.button("Confirm Delete", type="primary", use_container_width=True, key="ocr_delete_confirm"):
                try:
                    ocr_model = OCRModel()
                    ocr_model.delete(model_data['ocr_models_uuid'])
                    st.success(f"OCR Model '{model_name}' deleted successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error deleting OCR model: {str(e)}")
        
        with col2:
            if st.button("Cancel", use_container_width=True, key="ocr_delete_cancel"):
                st.rerun()