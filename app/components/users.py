"""Users management component with data_editor."""
import streamlit as st
import pandas as pd
from database.db_models import User, create_connection
from utils.utils_uuid import derive_uuid


def get_all_users():
    """Retrieve all users with role and organization info."""
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
    """Render users management interface with data editor."""
    # st.markdown("### Users Management")
    
    df = get_all_users()
    
    if df.empty:
        st.info("No users found.")
        if st.button("➕ Add New User", key="users_add_first"):
            st.session_state['adding_user'] = True
        
        if st.session_state.get('adding_user', False):
            render_add_form()
        return
    
    col_table, col_details = st.columns([4, 2])
    
    with col_table:
        display_df = df.copy()
        display_df['is_active'] = display_df['is_active'].astype(bool)
        
        edit_columns = ['username', 'first_name', 'last_name', 'email', 'is_active']
        
        edited_df = st.data_editor(
            display_df[['user_uuid'] + edit_columns],
            hide_index=True,
            width='stretch',
            disabled=['user_uuid'],
            column_config={
                'user_uuid': st.column_config.TextColumn('UUID', width='small'),
                'username': st.column_config.TextColumn('Username', width='medium'),
                'first_name': st.column_config.TextColumn('First Name', width='medium'),
                'last_name': st.column_config.TextColumn('Last Name', width='medium'),
                'email': st.column_config.TextColumn('Email', width='large'),
                'is_active': st.column_config.CheckboxColumn('Active')
            },
            key='users_editor'
        )
        
        if not edited_df.equals(display_df[['user_uuid'] + edit_columns]):
            st.info("⚠️ Changes detected - Click 'Save Changes' to apply")
            
            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                if st.button("💾 Save Changes", key="users_save_changes", type="primary", width='stretch'):
                    save_changes(df, edited_df)
                    st.rerun()
            with col2:
                if st.button("↩️ Discard", key="users_discard_changes", width='stretch'):
                    st.rerun()
        
        if st.button("➕ Add New User", key="users_add_new_button", width='stretch'):
            st.session_state['adding_user'] = True
            st.rerun()
        
        if st.session_state.get('adding_user', False):
            render_add_form()
    
    with col_details:
        # st.markdown("#### Full Details")
        
        user_options = ['(View More Details)'] + df['username'].tolist()
        selected_user = st.selectbox(
            "Select user",
            user_options,
            key='user_detail_select',
            label_visibility='collapsed'
        )
        
        if selected_user != '(View More Details)':
            user_data = df[df['username'] == selected_user].iloc[0]
            
            st.markdown(f"**Username:** {user_data['username']}")
            st.markdown(f"**Name:** {user_data['first_name']} {user_data['last_name']}")
            st.markdown(f"**Email:** {user_data['email']}")
            st.markdown(f"**Role:** {user_data['role_name']}")
            st.markdown(f"**Organization:** {user_data['org_name'] if pd.notna(user_data['org_name']) else 'None'}")
            st.markdown(f"**Active:** {'Yes' if user_data['is_active'] else 'No'}")
            
            st.markdown("---")
            st.caption(f"Created: {user_data['created_datetime']}")
            st.caption(f"Updated: {user_data['updated_datetime']}")
            
            st.markdown("---")
            
            if st.button("🔑 Reset Password", key="users_reset_pwd_button", width='stretch'):
                st.session_state['resetting_password'] = user_data['user_uuid']
                st.rerun()
            
            if st.button("✏️ Edit Role/Org", key="users_edit_details_button", width='stretch'):
                st.session_state['editing_user_details'] = user_data['user_uuid']
                st.rerun()
            
            if st.session_state.get('resetting_password') == user_data['user_uuid']:
                render_password_reset(user_data)
            
            if st.session_state.get('editing_user_details') == user_data['user_uuid']:
                render_details_editor(user_data)


def save_changes(original_df, edited_df):
    """Save changes to database."""
    merged = edited_df.merge(
        original_df[['user_uuid', 'username', 'first_name', 'last_name', 'email', 'is_active']],
        on='user_uuid',
        suffixes=('_new', '_old')
    )
    
    changes_made = 0
    for idx, row in merged.iterrows():
        changed = False
        update_params = {'user_uuid': row['user_uuid']}
        
        if row['username_new'] != row['username_old']:
            update_params['username'] = row['username_new']
            changed = True
        if row['first_name_new'] != row['first_name_old']:
            update_params['first_name'] = row['first_name_new']
            changed = True
        if row['last_name_new'] != row['last_name_old']:
            update_params['last_name'] = row['last_name_new']
            changed = True
        if row['email_new'] != row['email_old']:
            update_params['email'] = row['email_new']
            changed = True
        if row['is_active_new'] != row['is_active_old']:
            update_params['is_active'] = 1 if row['is_active_new'] else 0
            changed = True
        
        if changed:
            try:
                user = User()
                user.update(**update_params)
                changes_made += 1
            except Exception as e:
                st.error(f"Error updating {row['username_new']}: {str(e)}")
    
    if changes_made > 0:
        st.success(f"✅ Updated {changes_made} user(s)")


def render_add_form():
    """Render add user form."""
    st.markdown("---")
    st.markdown("#### Add New User")
    
    roles_df = get_user_roles()
    orgs_df = get_organizations()
    
    with st.form("add_user_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            username = st.text_input("Username*", placeholder="e.g., jdoe")
            password = st.text_input("Password*", type="password")
            confirm_password = st.text_input("Confirm Password*", type="password")
            first_name = st.text_input("First Name")
            last_name = st.text_input("Last Name")
        
        with col2:
            email = st.text_input("Email")
            role = st.selectbox("Role*", roles_df['name'].tolist())
            org_options = ["None"] + orgs_df['name'].tolist()
            organization = st.selectbox("Organization", org_options)
            is_active = st.checkbox("Active", value=True)
        
        col_submit, col_cancel = st.columns(2)
        
        with col_submit:
            submit = st.form_submit_button("Add User", width='stretch')
        
        with col_cancel:
            cancel = st.form_submit_button("Cancel", width='stretch')
        
        if cancel:
            st.session_state['adding_user'] = False
            st.rerun()
        
        if submit:
            if not username or not password or not role:
                st.error("Username, Password, and Role are required")
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
                    st.success(f"User '{username}' added!")
                    st.session_state['adding_user'] = False
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {str(e)}")


def render_password_reset(user_data):
    """Render password reset form."""
    with st.form(f"reset_pwd_{user_data['user_uuid']}"):
        st.markdown("**Reset Password**")
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("🔑 Reset", width='stretch'):
                if not new_password:
                    st.error("Password required")
                elif new_password != confirm_password:
                    st.error("Passwords do not match")
                else:
                    try:
                        user = User()
                        user.update(
                            user_uuid=user_data['user_uuid'],
                            pwd=derive_uuid(new_password)
                        )
                        st.success("Password reset!")
                        st.session_state['resetting_password'] = None
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
        
        with col2:
            if st.form_submit_button("Cancel", width='stretch'):
                st.session_state['resetting_password'] = None
                st.rerun()


def render_details_editor(user_data):
    """Render role/org editor."""
    roles_df = get_user_roles()
    orgs_df = get_organizations()
    
    with st.form(f"edit_details_{user_data['user_uuid']}"):
        st.markdown("**Edit Role & Organization**")
        
        role_idx = roles_df['name'].tolist().index(user_data['role_name']) if user_data['role_name'] else 0
        role = st.selectbox("Role", roles_df['name'].tolist(), index=role_idx)
        
        org_options = ["None"] + orgs_df['name'].tolist()
        org_idx = org_options.index(user_data['org_name']) if user_data['org_name'] in org_options else 0
        organization = st.selectbox("Organization", org_options, index=org_idx)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("💾 Save", width='stretch'):
                try:
                    user = User()
                    role_uuid = roles_df[roles_df['name'] == role]['user_role_uuid'].iloc[0]
                    org_uuid = None if organization == "None" else orgs_df[orgs_df['name'] == organization]['organization_uuid'].iloc[0]
                    
                    user.update(
                        user_uuid=user_data['user_uuid'],
                        user_role_uuid=role_uuid,
                        organization_uuid=org_uuid
                    )
                    st.success("Updated!")
                    st.session_state['editing_user_details'] = None
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        
        with col2:
            if st.form_submit_button("Cancel", width='stretch'):
                st.session_state['editing_user_details'] = None
                st.rerun()