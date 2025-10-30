"""Main Streamlit application entry point with AI Analysis tab."""
import os
import time
import streamlit as st
import sqlite3

from config.config import FULL_DATABASE_FILE_PATH
from database.db_models import create_connection
from initial_setup.db_setup import setup_database
from utils.utils_uuid import derive_uuid
from utils.utils_logging import get_logger_from_session, log_page_view, log_authentication
from app.pages import login, admin_panel
from app.components.ai_analysis import render_ai_analysis_page
from app.components.system_status import render_system_status_sidebar, check_system_ready_for_upload


def initialize_database():
    """Initialize database if it doesn't exist."""
    print("=== INITIALIZING DATABASE ===")
    if not os.path.exists(FULL_DATABASE_FILE_PATH):
        print(f"Database not found at {FULL_DATABASE_FILE_PATH}, setting up new database")
        setup_database()
        time.sleep(10) # give the database time to initialize
        print("Database setup completed")
    else:
        print(f"Database already exists at {FULL_DATABASE_FILE_PATH}")


def initialize_session_state():
    """Initialize session state variables."""
    print("=== INITIALIZING SESSION STATE ===")
    
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
        print("Initialized 'logged_in' to False")
    
    if 'user_uuid' not in st.session_state:
        st.session_state['user_uuid'] = None
        print("Initialized 'user_uuid' to None")
    
    if 'org_uuid' not in st.session_state:
        st.session_state['org_uuid'] = None
        print("Initialized 'org_uuid' to None")
    
    if 'username' not in st.session_state:
        st.session_state['username'] = None
        print("Initialized 'username' to None")
    
    if 'role_name' not in st.session_state:
        st.session_state['role_name'] = None
        print("Initialized 'role_name' to None")
    
    if 'active_tab' not in st.session_state:
        st.session_state['active_tab'] = 0
        print("Initialized 'active_tab' to 0")
    
    print("Session state initialization complete")


def authenticate_user(username, password):
    """
    Authenticate user credentials and populate session state.
    
    Returns:
        tuple: (success: bool, message: str)
    """
    print(f"=== AUTHENTICATING USER: {username} ===")
    
    try:
        conn = create_connection()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("PRAGMA foreign_keys = ON")
        
        print(f"Querying database for user: {username}")
        c.execute("""
            SELECT u.user_uuid, u.organization_uuid, u.user_role_uuid, u.pwd, r.name
            FROM user u
            JOIN user_role r ON u.user_role_uuid = r.user_role_uuid
            WHERE u.username = ? AND u.is_active = 1
        """, (username,))
        
        user_data = c.fetchone()
        conn.close()

        print(f"User data retrieved: {dict(user_data) if user_data else None}")
        
        if not user_data:
            print(f"!!! Authentication failed: User '{username}' not found or inactive")
            log_authentication(username, success=False, failure_reason="User not found or inactive")
            return False, "Invalid username or password"
        
        pwd_hash = derive_uuid(password)
        print(f"Password hash generated for comparison")
        
        if user_data['pwd'] == pwd_hash:
            print(f"✓ Password match successful for user: {username}")
            
            st.session_state['logged_in'] = True
            st.session_state['user_uuid'] = user_data['user_uuid']
            st.session_state['org_uuid'] = user_data['organization_uuid']
            st.session_state['role_uuid'] = user_data['user_role_uuid']
            st.session_state['username'] = username
            st.session_state['role_name'] = user_data['name']
            
            print(f"✓ Session state populated for user: {username}")
            print(f"  - User UUID: {user_data['user_uuid']}")
            print(f"  - Org UUID: {user_data['organization_uuid']}")
            print(f"  - Role: {user_data['name']}")
            
            # Log successful authentication
            logger = get_logger_from_session(st.session_state)
            logger.info('/login', f'Successful login for user: {username}')
            log_authentication(username, success=True)
            
            return True, "Login successful"
        else:
            print(f"!!! Password mismatch for user: {username}")
            log_authentication(username, success=False, failure_reason="Invalid password")
            return False, "Invalid username or password"
            
    except Exception as e:
        print(f"!!! ERROR during authentication: {str(e)}")
        log_authentication(username, success=False, failure_reason=f"Error: {str(e)}")
        return False, f"Authentication error: {str(e)}"


def logout():
    """Clear session state and log out user."""
    username = st.session_state.get('username', 'unknown')
    print(f"=== LOGGING OUT USER: {username} ===")
    
    # Log logout before clearing session
    logger = get_logger_from_session(st.session_state)
    logger.info('/logout', f'User logged out: {username}')
    
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    
    print("✓ Session state cleared")
    st.rerun()


def main():
    """Main application flow."""
    print("=== STARTING MAIN APPLICATION ===")
    
    st.set_page_config(
        page_title="AI Document Labeling",
        page_icon=os.path.join("assets", "icons", "network_intel_node.svg"),
        layout="wide",
        initial_sidebar_state="expanded"
    )
    print("✓ Page config set")
    
    initialize_database()
    initialize_session_state()
    
    if not st.session_state['logged_in']:
        print("User not logged in, rendering login page")
        login.render_login_page(authenticate_user)
    else:
        print(f"User logged in: {st.session_state.get('username')}, rendering main app")
        render_main_app()


def render_main_app():
    """Render main application after login."""
    username = st.session_state.get("username", "unknown")
    role     = st.session_state.get("role_name", "unknown")

    # --------------------------------------------------------------
    # 1. First-load splash – runs only once
    # --------------------------------------------------------------
    if st.session_state.get("first_load", True):
        with st.sidebar:
            # Show a compact status inside the sidebar
            with st.status(
                "Validating system & loading status…",
                expanded=False,
                state="running"
            ) as status:
                # -----------------------------------------------------------------
                # Render the *real* sidebar content **inside** the status block.
                # This is what the user will see while the heavy work runs.
                # -----------------------------------------------------------------
                st.header(f"Welcome, {username.upper()}")
                st.write(f"**Role:** {role.upper()}")

                if st.button("Logout", use_container_width=True):
                    print(f"Logout button clicked by user: {username}")
                    logout()

                # ---- THE HEAVY PART ------------------------------------------------
                render_system_status_sidebar()      # <-- this is the slow call
                # -----------------------------------------------------------------

                # Small visual pause so the user sees the "complete" state
                time.sleep(0.3)

                # Mark as finished
                status.update(label="Ready!", state="complete", expanded=False)

        # One-time flag – next render will skip the whole block
        st.session_state.first_load = False
        st.rerun()
        return          # stop here; the normal UI is rendered on the next run

    # --------------------------------------------------------------
    # 2. Normal UI – runs on every subsequent render
    # --------------------------------------------------------------
    print(f"=== RENDERING MAIN APP FOR USER: {username} (Role: {role}) ===")

    # ---- Sidebar (lightweight, no heavy work) -------------------------
    with st.sidebar:
        st.header(f"Welcome, {username.upper()}")
        st.write(f"**Role:** {role.upper()}")

        if st.button("Logout", use_container_width=True):
            print(f"Logout button clicked by user: {username}")
            logout()

        render_system_status_sidebar()   # now fast because the data is cached

    # ---- Tabs ---------------------------------------------------------
    is_admin = role == "admin"
    print(f"User is admin: {is_admin}")

    if is_admin:
        tabs = st.tabs(["Dashboard", "AI Analyze", "Admin", "Settings"])

        with tabs[0]:
            if st.session_state.get("active_tab") != 0:
                st.session_state.active_tab = 0
            log_page_view(st.session_state, "/dashboard")
            st.info("Dashboard coming soon...")

        with tabs[1]:
            if st.session_state.get("active_tab") != 1:
                st.session_state.active_tab = 1
            log_page_view(st.session_state, "/ai-analyze")
            render_ai_analysis_page()

        with tabs[2]:
            if st.session_state.get("active_tab") != 2:
                st.session_state.active_tab = 2
            log_page_view(st.session_state, "/admin")
            admin_panel.render_admin_panel()

        with tabs[3]:
            if st.session_state.get("active_tab") != 3:
                st.session_state.active_tab = 3
            log_page_view(st.session_state, "/settings")
            st.info("Settings coming soon...")
    else:
        tabs = st.tabs(["Dashboard", "AI Analyze", "Settings"])

        with tabs[0]:
            if st.session_state.get("active_tab") != 0:
                st.session_state.active_tab = 0
            log_page_view(st.session_state, "/dashboard")
            st.info("Dashboard coming soon...")

        with tabs[1]:
            if st.session_state.get("active_tab") != 1:
                st.session_state.active_tab = 1
            log_page_view(st.session_state, "/ai-analyze")
            render_ai_analysis_page()

        with tabs[2]:
            if st.session_state.get("active_tab") != 2:
                st.session_state.active_tab = 2
            log_page_view(st.session_state, "/settings")
            st.info("Settings coming soon...")

            

if __name__ == "__main__":
    print("="*60)
    print("APPLICATION STARTED")
    print("="*60)
    main()