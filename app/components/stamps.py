"""Stamps management component."""
import streamlit as st
import pandas as pd
from database.db_models import Stamps, create_connection


def get_all_stamps():
    """Retrieve all stamps with organization information."""
    conn = create_connection()
    query = """
        SELECT s.stamps_uuid, s.name, s.description, s.keywords, s.is_active,
               o.name as org_name, s.organization_uuid, s.created_datetime, s.updated_datetime
        FROM stamps s
        LEFT JOIN organization o ON s.organization_uuid = o.organization_uuid
        ORDER BY o.name, s.name
    """
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


def render_stamps_management():
    """Render stamps management interface."""
    # st.markdown("### Stamps Management")
    
    action = st.radio("Action", ["View All", "Add New", "Update", "Delete"], horizontal=True, key="stamp_action")
    
    if action == "View All":
        render_view_stamps()
    elif action == "Add New":
        render_add_stamp()
    elif action == "Update":
        render_update_stamp()
    elif action == "Delete":
        render_delete_stamp()


def render_view_stamps():
    """Display all stamps."""
    df = get_all_stamps()
    
    if df.empty:
        st.info("No stamps found.")
        return
    
    df['is_active'] = df['is_active'].map({1: '✓', 0: '✗'})
    
    st.dataframe(
        df[['org_name', 'name', 'keywords', 'is_active']],
        use_container_width=True,
        hide_index=True
    )
    
    with st.expander("View Full Details"):
        stamp_options = [f"{row['name']} ({row['org_name']})" for _, row in df.iterrows()]
        selected_stamp = st.selectbox("", stamp_options, key="stamp_view_select")
        
        if selected_stamp:
            stamp_name = selected_stamp.split(' (')[0]
            org_name = selected_stamp.split(' (')[1].rstrip(')')
            stamp_data = df[(df['name'] == stamp_name) & (df['org_name'] == org_name)].iloc[0]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Name:** {stamp_data['name']}")
                st.write(f"**Organization:** {stamp_data['org_name']}")
                st.write(f"**Keywords:** {stamp_data['keywords']}")
            
            with col2:
                st.write(f"**Active:** {stamp_data['is_active']}")
                st.write(f"**Created:** {stamp_data['created_datetime']}")
                st.write(f"**Updated:** {stamp_data['updated_datetime']}")
            
            st.write(f"**Description:** {stamp_data['description']}")


def render_add_stamp():
    """Render form to add new stamp."""
    orgs_df = get_organizations()
    
    if orgs_df.empty:
        st.warning("No active organizations available. Please create an organization first.")
        return
    
    with st.form("add_stamp_form"):
        st.markdown("#### Add New Stamp")
        
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Stamp Name*", placeholder="e.g., FILED")
            organization = st.selectbox("Organization*", orgs_df['name'].tolist())
            keywords = st.text_input("Keywords*", placeholder="['filed', 'file stamped']", 
                                    help="Enter as a Python list format")
        
        with col2:
            description = st.text_area("Description", placeholder="Describe the stamp's purpose")
            is_active = st.checkbox("Active", value=True)
        
        submit = st.form_submit_button("Add Stamp", use_container_width=True)
        
        if submit:
            if not name or not keywords:
                st.error("Stamp Name and Keywords are required fields")
            else:
                try:
                    stamp = Stamps()
                    org_uuid = orgs_df[orgs_df['name'] == organization]['organization_uuid'].iloc[0]
                    
                    stamp.insert(
                        organization_uuid=org_uuid,
                        name=name,
                        description=description,
                        keywords=keywords,
                        is_active=1 if is_active else 0,
                        created_by=st.session_state.get('user_uuid'),
                        updated_by=st.session_state.get('user_uuid')
                    )
                    st.success(f"Stamp '{name}' added successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error adding stamp: {str(e)}")


def render_update_stamp():
    """Render form to update existing stamp."""
    df = get_all_stamps()
    orgs_df = get_organizations()
    
    if df.empty:
        st.info("No stamps available to update.")
        return
    
    stamp_options = [f"{row['name']} ({row['org_name']})" for _, row in df.iterrows()]
    selected_stamp = st.selectbox("Select Stamp to Update", stamp_options, key="stamp_update_select")
    
    if selected_stamp:
        stamp_name = selected_stamp.split(' (')[0]
        org_name = selected_stamp.split(' (')[1].rstrip(')')
        stamp_data = df[(df['name'] == stamp_name) & (df['org_name'] == org_name)].iloc[0]
        
        with st.form("update_stamp_form"):
            st.markdown(f"#### Update: {stamp_name}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Stamp Name", value=stamp_data['name'])
                org_index = orgs_df['name'].tolist().index(stamp_data['org_name']) if stamp_data['org_name'] in orgs_df['name'].tolist() else 0
                organization = st.selectbox("Organization", orgs_df['name'].tolist(), index=org_index)
                keywords = st.text_input("Keywords", value=stamp_data['keywords'])
            
            with col2:
                description = st.text_area("Description", value=stamp_data['description'] or "")
                is_active = st.checkbox("Active", value=bool(stamp_data['is_active']))
            
            submit = st.form_submit_button("Update Stamp", use_container_width=True)
            
            if submit:
                try:
                    stamp = Stamps()
                    org_uuid = orgs_df[orgs_df['name'] == organization]['organization_uuid'].iloc[0]
                    
                    stamp.update(
                        stamps_uuid=stamp_data['stamps_uuid'],
                        organization_uuid=org_uuid,
                        name=name,
                        description=description,
                        keywords=keywords,
                        is_active=1 if is_active else 0,
                        updated_by=st.session_state.get('user_uuid')
                    )
                    st.success(f"Stamp '{name}' updated successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error updating stamp: {str(e)}")


def render_delete_stamp():
    """Render interface to soft delete stamp."""
    df = get_all_stamps()
    active_stamps = df[df['is_active'] == 1]
    
    if active_stamps.empty:
        st.info("No active stamps available to delete.")
        return
    
    stamp_options = [f"{row['name']} ({row['org_name']})" for _, row in active_stamps.iterrows()]
    selected_stamp = st.selectbox("Select Stamp to Delete", stamp_options, key="stamp_delete_select")
    
    if selected_stamp:
        stamp_name = selected_stamp.split(' (')[0]
        org_name = selected_stamp.split(' (')[1].rstrip(')')
        stamp_data = active_stamps[(active_stamps['name'] == stamp_name) & (active_stamps['org_name'] == org_name)].iloc[0]
        
        st.warning(f"Are you sure you want to delete stamp '{stamp_name}'? This will soft delete (set is_active=0).")
        
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.button("Confirm Delete", type="primary", use_container_width=True, key="stamp_delete_confirm"):
                try:
                    stamp = Stamps()
                    stamp.delete(stamp_data['stamps_uuid'])
                    st.success(f"Stamp '{stamp_name}' deleted successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error deleting stamp: {str(e)}")
        
        with col2:
            if st.button("Cancel", use_container_width=True, key="stamp_delete_cancel"):
                st.rerun()