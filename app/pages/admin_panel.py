"""Admin panel for managing system entities."""
import streamlit as st
from app.components import llm_models, ocr_models, organizations, users, stamps, document_categories


def render_admin_panel():
    """Render the admin panel with sub-tabs for different management areas."""
    
    admin_tabs = st.tabs([
        "LLM Models",
        "OCR Models", 
        "Organizations",
        "Users",
        "Stamps",
        "Document Categories"
    ])
    
    with admin_tabs[0]:
        llm_models.render_llm_models_management()
    
    with admin_tabs[1]:
        ocr_models.render_ocr_models_management()
    
    with admin_tabs[2]:
        organizations.render_organizations_management()
    
    with admin_tabs[3]:
        users.render_users_management()
    
    with admin_tabs[4]:
        stamps.render_stamps_management()
    
    with admin_tabs[5]:
        document_categories.render_document_categories()