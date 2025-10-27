"""Users management component."""
import streamlit as st
import pandas as pd
from database.db_models import User, create_connection
from utils.utils_uuid import derive_uuid


def get_all_users():
    """Retrieve all users with their role and organization information."""
    conn = create_connection()
    query = """
        SELECT u.user_uuid, u.username, u.first_name, u.last_name, u.email,
               r.name as role_name, o.name as org_name, u.is_active,
               u.organization_uuid, u.user_role_uuid, u.created_datetime, u.updated_datetime
        FROM user u
        LEFT JOIN user_role r ON u.user_role_uuid = r.user_role_uuid
        LEFT JOIN organization o ON u.organization_uuid = o.organization_uuid
        ORDER BY u.username
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def get_user_roles():
    """Retrieve all active user roles."""
    conn = create_connection()
    query = "SELECT user_role_uuid, name FROM user_role WHERE is_active = 1 ORDER BY name"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def get_organizations():
    """Retrieve all active organizations."""
    conn = create_connection()
    query = "SELECT organization_uuid, name FROM organization WHERE is_active = 1 ORDER BY name"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def render_users_management():
    """Render users management interface."""
    # st.markdown("### Users Management")
    
    action = st.radio("Action", ["View All", "Add New", "Update", "Delete"], horizontal=True, key="user_action")
    
    if action == "View All":
        render_view_users()
    elif action == "Add New":
        render_add_user()
    elif action == "Update":
        render_update_user()
    elif action == "Delete":
        render_delete_user()


def render_view_users():
    """Display all users."""
    df = get_all_users()
    
    if df.empty:
        st.info("No users found.")
        return
    
    df['is_active'] = df['is_active'].map({1: '✓', 0: '✗'})
    
    st.dataframe(
        df[['username', 'first_name', 'last_name', 'email', 'role_name', 'org_name', 'is_active']],
        use_container_width=True,
        hide_index=True
    )
    
    with st.expander("View Full Details"):
        selected_user = st.selectbox("Select User", df['username'].tolist(), key="user_view_select")
        if selected_user:
            user_data = df[df['username'] == selected_user].iloc[0]
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Username:** {user_data['username']}")
                st.write(f"**First Name:** {user_data['first_name']}")
                st.write(f"**Last Name:** {user_data['last_name']}")
                st.write(f"**Email:** {user_data['email']}")
            
            with col2:
                st.write(f"**Role:** {user_data['role_name']}")
                st.write(f"**Organization:** {user_data['org_name']}")
                st.write(f"**Active:** {user_data['is_active']}")
                st.write(f"**Created:** {user_data['created_datetime']}")


def render_add_user():
    """Render form to add new user."""
    roles_df = get_user_roles()
    orgs_df = get_organizations()
    
    with st.form("add_user_form"):
        st.markdown("#### Add New User")
        
        col1, col2 = st.columns(2)
        
        with col1:
            username = st.text_input("Username*", placeholder="e.g., jdoe")
            password = st.text_input("Password*", type="password", placeholder="Enter password")
            confirm_password = st.text_input("Confirm Password*", type="password", placeholder="Re-enter password")
            first_name = st.text_input("First Name", placeholder="John")
            last_name = st.text_input("Last Name", placeholder="Doe")
        
        with col2:
            email = st.text_input("Email", placeholder="john.doe@example.com")
            role = st.selectbox("Role*", roles_df['name'].tolist())
            organization = st.selectbox("Organization", ["None"] + orgs_df['name'].tolist())
            is_active = st.checkbox("Active", value=True)
        
        submit = st.form_submit_button("Add User", use_container_width=True)
        
        if submit:
            if not username or not password or not role:
                st.error("Username, Password, and Role are required fields")
            elif password != confirm_password:
                st.error("Passwords do not match")
            else:
                try:
                    user = User()
                    role_uuid = roles_df[roles_df['name'] == role]['user_role_uuid'].iloc[0]
                    org_uuid = None if organization == "None" else orgs_df[orgs_df['name'] == organization]['organization_uuid'].iloc[0]
                    pwd_hash = derive_uuid(password)
                    
                    user.insert(
                        user_role_uuid=role_uuid,
                        username=username,
                        pwd=pwd_hash,
                        first_name=first_name,
                        last_name=last_name,
                        email=email,
                        is_active=1 if is_active else 0,
                        organization_uuid=org_uuid
                    )
                    st.success(f"User '{username}' added successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error adding user: {str(e)}")


def render_update_user():
    """Render form to update existing user."""
    df = get_all_users()
    roles_df = get_user_roles()
    orgs_df = get_organizations()
    
    if df.empty:
        st.info("No users available to update.")
        return
    
    username = st.selectbox("Select User to Update", df['username'].tolist(), key="user_update_select")
    
    if username:
        user_data = df[df['username'] == username].iloc[0]
        
        with st.form("update_user_form"):
            st.markdown(f"#### Update: {username}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                new_username = st.text_input("Username", value=user_data['username'])
                change_pwd = st.checkbox("Change Password")
                if change_pwd:
                    new_password = st.text_input("New Password", type="password")
                    confirm_password = st.text_input("Confirm Password", type="password")
                first_name = st.text_input("First Name", value=user_data['first_name'] or "")
                last_name = st.text_input("Last Name", value=user_data['last_name'] or "")
            
            with col2:
                email = st.text_input("Email", value=user_data['email'] or "")
                role = st.selectbox("Role", roles_df['name'].tolist(), 
                                   index=roles_df['name'].tolist().index(user_data['role_name']) if user_data['role_name'] else 0)
                org_options = ["None"] + orgs_df['name'].tolist()
                org_index = org_options.index(user_data['org_name']) if user_data['org_name'] in org_options else 0
                organization = st.selectbox("Organization", org_options, index=org_index)
                is_active = st.checkbox("Active", value=bool(user_data['is_active']))
            
            submit = st.form_submit_button("Update User", use_container_width=True)
            
            if submit:
                if change_pwd and new_password != confirm_password:
                    st.error("Passwords do not match")
                else:
                    try:
                        user = User()
                        role_uuid = roles_df[roles_df['name'] == role]['user_role_uuid'].iloc[0]
                        org_uuid = None if organization == "None" else orgs_df[orgs_df['name'] == organization]['organization_uuid'].iloc[0]
                        
                        update_params = {
                            'user_uuid': user_data['user_uuid'],
                            'user_role_uuid': role_uuid,
                            'username': new_username,
                            'first_name': first_name,
                            'last_name': last_name,
                            'email': email,
                            'is_active': 1 if is_active else 0,
                            'organization_uuid': org_uuid
                        }
                        
                        if change_pwd and new_password:
                            update_params['pwd'] = derive_uuid(new_password)
                        
                        user.update(**update_params)
                        st.success(f"User '{new_username}' updated successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error updating user: {str(e)}")


def render_delete_user():
    """Render interface to soft delete user."""
    df = get_all_users()
    active_users = df[df['is_active'] == 1]
    
    if active_users.empty:
        st.info("No active users available to delete.")
        return
    
    username = st.selectbox("Select User to Delete", active_users['username'].tolist(), key="user_delete_select")
    
    if username:
        user_data = active_users[active_users['username'] == username].iloc[0]
        
        st.warning(f"Are you sure you want to delete user '{username}'? This will soft delete (set is_active=0).")
        
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.button("Confirm Delete", type="primary", use_container_width=True, key="user_delete_confirm"):
                try:
                    user = User()
                    user.delete(user_data['user_uuid'])
                    st.success(f"User '{username}' deleted successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error deleting user: {str(e)}")
        
        with col2:
            if st.button("Cancel", use_container_width=True, key="user_delete_cancel"):
                st.rerun()