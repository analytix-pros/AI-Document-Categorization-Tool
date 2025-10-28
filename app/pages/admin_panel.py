"""Admin panel for managing system entities."""
import streamlit as st
from config.config import ADMIN_TABS
from app.components import llm_models, ocr_models, organizations, users, stamps, document_categories


def render_admin_panel():
    """Render the admin panel with dynamically configured tabs."""
    
    # Sort tabs by ordinal
    sorted_tabs = sorted(ADMIN_TABS.items(), key=lambda x: x[1]['ordinal'])
    
    # Extract tab names in sorted order
    tab_names = [tab_config['tab_name'] for _, tab_config in sorted_tabs]
    
    # Create tabs
    admin_tabs = st.tabs(tab_names)
    
    # Map of component names to actual functions
    component_map = {
        'llm_models.render_llm_models_management()': llm_models.render_llm_models_management,
        'ocr_models.render_ocr_models_management()': ocr_models.render_ocr_models_management,
        'organizations.render_organizations_management()': organizations.render_organizations_management,
        'users.render_users_management()': users.render_users_management,
        'stamps.render_stamps_management()': stamps.render_stamps_management,
        'document_categories.render_document_categories()': document_categories.render_document_categories
    }
    
    # Render each tab dynamically
    for idx, (tab_key, tab_config) in enumerate(sorted_tabs):
        with admin_tabs[idx]:
            render_function_str = tab_config['render']
            render_function = component_map.get(render_function_str)
            
            if render_function:
                render_function()
            else:
                st.error(f"Render function not found for: {render_function_str}")
                st.info(f"Available functions: {list(component_map.keys())}")