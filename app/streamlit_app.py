# streamlit_app.py
import os
import streamlit as st

# local packages
from config.config import *
from ..database.db_models import *
from ..initial_setup.db_setup import setup_database
from ..utils.utils_uuid import *


# Setup database on app start if it doesn't exist
try:
    if os.path.exists(FULL_DATABASE_FILE_PATH):
        pass
    else:
        setup_database()
except Exception as e:
    print(f"An unexpected error occurred: {e}")
setup_database()


st.title("AI Document Management App")

# Sidebar for login
with st.sidebar:
    st.header("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        conn = create_connection()
        c = conn.cursor()
        c.execute("PRAGMA foreign_keys = ON")
        c.execute("""
        SELECT user_uuid, organization_uuid, user_role_uuid, pwd 
        FROM user 
        WHERE username = ? AND is_active = 1
        """, (username,))
        user_data = c.fetchone()
        conn.close()

        pwd_converted = derive_uuid(password)
        print(pwd_converted)
        if user_data and user_data[3] == pwd_converted:
            st.session_state['logged_in'] = True
            st.session_state['user_uuid'] = user_data[0]
            st.session_state['org_uuid'] = user_data[1]
            st.session_state['role_uuid'] = user_data[2]
            st.success("Logged in successfully!")
        else:
            st.error("Invalid username or password")

# Main content if logged in
if 'logged_in' in st.session_state and st.session_state['logged_in']:
    # Determine if admin
    conn = create_connection()
    c = conn.cursor()
    c.execute("SELECT name FROM user_role WHERE user_role_uuid = ?", (st.session_state['role_uuid'],))
    role_name = c.fetchone()[0]
    conn.close()
    is_admin = role_name == 'admin'

    st.write(f"Welcome, {username}! You are logged in as {role_name}.")

    # Example tabs
    tab1, tab2, tab3 = st.tabs(["Dashboard", "Documents", "Settings"])

    with tab1:
        st.subheader("Dashboard")
        st.write("Overview of your organization's data.")
        # Add more content here later

    with tab2:
        st.subheader("Documents")
        st.write("Manage documents here.")
        # Add more content here later

    with tab3:
        st.subheader("Settings")
        if is_admin:
            st.write("Admin settings: Access to all organizations.")
        else:
            st.write("User settings.")
        # Add more content here later

else:
    st.info("Please log in to access the app.")