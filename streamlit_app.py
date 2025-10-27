"""Main Streamlit application entry point."""
import os
import streamlit as st
import sqlite3

from config.config import FULL_DATABASE_FILE_PATH
from database.db_models import create_connection
from initial_setup.db_setup import setup_database
from utils.utils_uuid import derive_uuid
from app.pages import login, admin_panel
from app.components.document_categories import render_document_categories
from app.components.documents import render_documents_page
from app.components.system_status import render_system_status_sidebar, check_system_ready
from app.components.documents import render_documents_page


def initialize_database():
    """Initialize database if it doesn't exist."""
    if not os.path.exists(FULL_DATABASE_FILE_PATH):
        setup_database()


def initialize_session_state():
    """Initialize session state variables."""
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
    if 'user_uuid' not in st.session_state:
        st.session_state['user_uuid'] = None
    if 'org_uuid' not in st.session_state:
        st.session_state['org_uuid'] = None
    if 'username' not in st.session_state:
        st.session_state['username'] = None
    if 'role_name' not in st.session_state:
        st.session_state['role_name'] = None


def authenticate_user(username, password):
    """
    Authenticate user credentials and populate session state.
    
    Returns:
        tuple: (success: bool, message: str)
    """
    conn = create_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("PRAGMA foreign_keys = ON")
    
    c.execute("""
        SELECT u.user_uuid, u.organization_uuid, u.user_role_uuid, u.pwd, r.name
        FROM user u
        JOIN user_role r ON u.user_role_uuid = r.user_role_uuid
        WHERE u.username = ? AND u.is_active = 1
    """, (username,))
    
    user_data = c.fetchone()
    conn.close()

    print(user_data)
    
    if not user_data:
        return False, "Invalid username or password"
    
    pwd_hash = derive_uuid(password)
    
    if user_data['pwd'] == pwd_hash:
        st.session_state['logged_in'] = True
        st.session_state['user_uuid'] = user_data['user_uuid']
        st.session_state['org_uuid'] = user_data['organization_uuid']
        st.session_state['role_uuid'] = user_data['user_role_uuid']
        st.session_state['username'] = username
        st.session_state['role_name'] = user_data['name']
        return True, "Login successful"
    
    return False, "Invalid username or password"


def logout():
    """Clear session state and log out user."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()


def main():
    """Main application flow."""
    st.set_page_config(
        page_title="AI Document Management",
        page_icon="📄",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    initialize_database()
    initialize_session_state()
    
    if not st.session_state['logged_in']:
        login.render_login_page(authenticate_user)
    else:
        render_main_app()


def render_main_app():
    """Render main application after login."""
    st.title("AI Document Management System")
    
    with st.sidebar:
        st.header(f"Welcome, {st.session_state['username'].upper()}")
        st.write(f"**Role:** {st.session_state['role_name'].upper()}")
        
        if st.button("Logout", use_container_width=True):
            logout()
        
        # Render system status checker
        render_system_status_sidebar()
    
    is_admin = st.session_state['role_name'] == 'admin'
    
    if is_admin:
        tabs = st.tabs(["Dashboard", "Documents", "Document Categories", "Admin", "Settings"])
        
        with tabs[0]:
            st.subheader("Dashboard")
            st.info("Dashboard coming soon...")
        
        with tabs[1]:
            render_documents_page()
        
        with tabs[2]:
            render_document_categories()
        
        with tabs[3]:
            admin_panel.render_admin_panel()
        
        with tabs[4]:
            st.subheader("Settings")
            st.info("Settings coming soon...")
    else:
        tabs = st.tabs(["Dashboard", "Documents", "Document Categories", "Settings"])
        
        with tabs[0]:
            st.subheader("Dashboard")
            st.info("Dashboard coming soon...")
        
        with tabs[1]:
            render_documents_page()
        
        with tabs[2]:
            render_document_categories()
        
        with tabs[3]:
            st.subheader("Settings")
            st.info("Settings coming soon...")


if __name__ == "__main__":
    main()