"""Organizations management component."""
import streamlit as st
import pandas as pd
from database.db_models import Organization, create_connection


def get_all_organizations():
    """Retrieve all organizations from database."""
    conn = create_connection()
    query = """
        SELECT organization_uuid, name, vm_name, is_active, is_automation_on,
               created_datetime, updated_datetime
        FROM organization
        ORDER BY name
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def render_organizations_management():
    """Render organizations management interface."""
    # st.markdown("### Organizations Management")
    
    action = st.radio("Action", ["View All", "Add New", "Update", "Delete"], horizontal=True, key="org_action")
    
    if action == "View All":
        render_view_organizations()
    elif action == "Add New":
        render_add_organization()
    elif action == "Update":
        render_update_organization()
    elif action == "Delete":
        render_delete_organization()


def render_view_organizations():
    """Display all organizations."""
    df = get_all_organizations()
    
    if df.empty:
        st.info("No organizations found.")
        return
    
    df['is_active'] = df['is_active'].map({1: '✓', 0: '✗'})
    df['is_automation_on'] = df['is_automation_on'].map({1: '✓', 0: '✗'})
    
    st.dataframe(
        df[['name', 'vm_name', 'is_active', 'is_automation_on']],
        use_container_width=True,
        hide_index=True
    )
    
    with st.expander("View Full Details"):
        selected_org = st.selectbox("Select Organization", df['name'].tolist(), key="org_view_select")
        if selected_org:
            org_data = df[df['name'] == selected_org].iloc[0]
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Name:** {org_data['name']}")
                st.write(f"**VM Name:** {org_data['vm_name']}")
                st.write(f"**Active:** {org_data['is_active']}")
            
            with col2:
                st.write(f"**Automation On:** {org_data['is_automation_on']}")
                st.write(f"**Created:** {org_data['created_datetime']}")
                st.write(f"**Updated:** {org_data['updated_datetime']}")


def render_add_organization():
    """Render form to add new organization."""
    with st.form("add_org_form"):
        st.markdown("#### Add New Organization")
        
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Organization Name*", placeholder="e.g., Acme Corp")
            vm_name = st.text_input("VM Name*", placeholder="e.g., ACME-SERVER-01")
        
        with col2:
            is_active = st.checkbox("Active", value=True)
            is_automation_on = st.checkbox("Automation On", value=False)
        
        submit = st.form_submit_button("Add Organization", use_container_width=True)
        
        if submit:
            if not name or not vm_name:
                st.error("Organization Name and VM Name are required fields")
            else:
                try:
                    org = Organization()
                    org.insert(
                        name=name,
                        vm_name=vm_name,
                        is_active=1 if is_active else 0,
                        is_automation_on=1 if is_automation_on else 0
                    )
                    st.success(f"Organization '{name}' added successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error adding organization: {str(e)}")


def render_update_organization():
    """Render form to update existing organization."""
    df = get_all_organizations()
    
    if df.empty:
        st.info("No organizations available to update.")
        return
    
    org_name = st.selectbox("Select Organization to Update", df['name'].tolist(), key="org_update_select")
    
    if org_name:
        org_data = df[df['name'] == org_name].iloc[0]
        
        with st.form("update_org_form"):
            st.markdown(f"#### Update: {org_name}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Organization Name", value=org_data['name'])
                vm_name = st.text_input("VM Name", value=org_data['vm_name'])
            
            with col2:
                is_active = st.checkbox("Active", value=bool(org_data['is_active']))
                is_automation_on = st.checkbox("Automation On", value=bool(org_data['is_automation_on']))
            
            submit = st.form_submit_button("Update Organization", use_container_width=True)
            
            if submit:
                try:
                    org = Organization()
                    org.update(
                        organization_uuid=org_data['organization_uuid'],
                        name=name,
                        vm_name=vm_name,
                        is_active=1 if is_active else 0,
                        is_automation_on=1 if is_automation_on else 0
                    )
                    st.success(f"Organization '{name}' updated successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error updating organization: {str(e)}")


def render_delete_organization():
    """Render interface to soft delete organization."""
    df = get_all_organizations()
    active_orgs = df[df['is_active'] == 1]
    
    if active_orgs.empty:
        st.info("No active organizations available to delete.")
        return
    
    org_name = st.selectbox("Select Organization to Delete", active_orgs['name'].tolist(), key="org_delete_select")
    
    if org_name:
        org_data = active_orgs[active_orgs['name'] == org_name].iloc[0]
        
        st.warning(f"Are you sure you want to delete '{org_name}'? This will soft delete (set is_active=0).")
        
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.button("Confirm Delete", type="primary", use_container_width=True, key="org_delete_confirm"):
                try:
                    org = Organization()
                    org.delete(org_data['organization_uuid'])
                    st.success(f"Organization '{org_name}' deleted successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error deleting organization: {str(e)}")
        
        with col2:
            if st.button("Cancel", use_container_width=True, key="org_delete_cancel"):
                st.rerun()