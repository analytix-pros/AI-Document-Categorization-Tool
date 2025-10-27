"""Login page for the application."""
import streamlit as st
import sqlite3
from config.config import FULL_DATABASE_FILE_PATH
from utils.utils_logging import log_authentication, log_page_view
from utils.utils_uuid import derive_uuid


def authenticate_callback(username, password):
    """
    Authenticate a user by validating the entered password against the database.
    
    Args:
        username (str): The username entered in the login form.
        password (str): The password entered in the login form.
    
    Returns:
        tuple: (success, message) where success is a boolean and message is a string.
    """
    try:
        # Transform the entered password using derive_uuid
        transformed_password = derive_uuid(password)

        print(f"Should be:\nda3ba40c-1af9-5704-8dfb-9b1571aa6ae4\nActually is:\n{transformed_password}")
        
        # Connect to the database (replace 'your_database.db' with your actual database)
        conn = sqlite3.connect(FULL_DATABASE_FILE_PATH)
        cursor = conn.cursor()
        
        # Query the user table for the username
        cursor.execute("SELECT pwd FROM user WHERE username = ?", (username,))
        result = cursor.fetchone()
        
        # Close the database connection
        conn.close()
        
        # Check if the user exists
        if result is None:
            return False, "Username not found"
        
        # Compare the transformed entered password with the stored password
        stored_password = result[0]
        if transformed_password == stored_password:
            return True, "Authentication successful"
        else:
            return False, "Invalid password"
            
    except Exception as e:
        # Handle any database or processing errors
        return False, f"Authentication error: {str(e)}"



def render_login_page(authenticate_callback):
    """
    Render the login page.
    
    Args:
        authenticate_callback: Function to call for authentication (username, password) -> (success, message)
    """
    
    st.title("AI Document Management System")
    
    col1, col2, col3 = st.columns([1, 2, 1])

    # Log page view
    log_page_view(st.session_state, '/login')
    print("=== LOGIN PAGE VIEWED ===")
    
    with col2:
        # st.subheader("Login")
        
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submit = st.form_submit_button("Login", use_container_width=True)
            
            if submit:
                print(f"=== LOGIN ATTEMPT: User '{username}' ===")

                print(f"Should be:\nda3ba40c-1af9-5704-8dfb-9b1571aa6ae4\nActually is:\n{derive_uuid(password)}")
                
                if not username or not password:
                    st.error("Please enter both username and password")
                    log_authentication(username or "unknown", success=False, 
                                     failure_reason="Missing username or password")
                    print(f"!!! LOGIN FAILED: Missing credentials for user '{username or 'unknown'}' !!!")
                else:
                    success, message = authenticate_callback(username, password)
                    if success:
                        st.success(message)
                        log_authentication(username, success=True)
                        print(f"✓ LOGIN SUCCESS: User '{username}' authenticated successfully")
                        st.rerun()
                    else:
                        st.error(message)
                        log_authentication(username, success=False, 
                                         failure_reason="Invalid credentials")
                        print(f"!!! LOGIN FAILED: Invalid credentials for user '{username}' !!!")
        
        # with st.expander("Test Credentials"):
        #     st.write("**Admin User:**")
        #     st.code("Username: cameron\nPassword: password")
        #     st.write("**Editor User:**")
        #     st.code("Username: bryan\nPassword: password")