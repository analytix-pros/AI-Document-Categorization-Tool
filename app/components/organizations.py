"""Organizations management component with data_editor."""
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
    """Render organizations management interface with data editor."""
    # st.markdown("### Organizations Management")
    
    df = get_all_organizations()
    
    if df.empty:
        st.info("No organizations found.")
        if st.button("➕ Add New Organization", key="org_add_first"):
            st.session_state['adding_organization'] = True
        
        if st.session_state.get('adding_organization', False):
            render_add_form()
        return
    
    col_table, col_details = st.columns([4, 2])
    
    with col_table:
        display_df = df.copy()
        display_df['is_active'] = display_df['is_active'].astype(bool)
        display_df['is_automation_on'] = display_df['is_automation_on'].astype(bool)
        
        edit_columns = ['name', 'vm_name', 'is_active', 'is_automation_on']
        
        edited_df = st.data_editor(
            display_df[['organization_uuid'] + edit_columns],
            hide_index=True,
            use_container_width=True,
            disabled=['organization_uuid'],
            column_config={
                'organization_uuid': st.column_config.TextColumn('UUID', width='small'),
                'name': st.column_config.TextColumn('Name', width='medium'),
                'vm_name': st.column_config.TextColumn('VM Name', width='medium'),
                'is_active': st.column_config.CheckboxColumn('Active'),
                'is_automation_on': st.column_config.CheckboxColumn('Automation')
            },
            key='organizations_editor'
        )
        
        if not edited_df.equals(display_df[['organization_uuid'] + edit_columns]):
            st.info("⚠️ Changes detected - Click 'Save Changes' to apply")
            
            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                if st.button("💾 Save Changes", key="org_save_changes", type="primary", use_container_width=True):
                    save_changes(df, edited_df)
                    st.rerun()
            with col2:
                if st.button("↩️ Discard", key="org_discard_changes", use_container_width=True):
                    st.rerun()
        
        if st.button("➕ Add New Organization", key="org_add_new_button", use_container_width=True):
            st.session_state['adding_organization'] = True
            st.rerun()
        
        if st.session_state.get('adding_organization', False):
            render_add_form()
    
    with col_details:
        # st.markdown("#### Full Details")
        
        org_options = ['(View More Details)'] + df['name'].tolist()
        selected_org = st.selectbox(
            "Select organization",
            org_options,
            key='org_detail_select',
            label_visibility='collapsed'
        )
        
        if selected_org != '(View More Details)':
            org_data = df[df['name'] == selected_org].iloc[0]
            
            st.markdown(f"**Name:** {org_data['name']}")
            st.markdown(f"**VM Name:** {org_data['vm_name']}")
            st.markdown(f"**Active:** {'Yes' if org_data['is_active'] else 'No'}")
            st.markdown(f"**Automation:** {'On' if org_data['is_automation_on'] else 'Off'}")
            
            st.markdown("---")
            st.caption(f"Created: {org_data['created_datetime']}")
            st.caption(f"Updated: {org_data['updated_datetime']}")


def save_changes(original_df, edited_df):
    """Save changes to database."""
    merged = edited_df.merge(
        original_df[['organization_uuid', 'name', 'vm_name', 'is_active', 'is_automation_on']],
        on='organization_uuid',
        suffixes=('_new', '_old')
    )
    
    changes_made = 0
    for idx, row in merged.iterrows():
        changed = False
        update_params = {'organization_uuid': row['organization_uuid']}
        
        if row['name_new'] != row['name_old']:
            update_params['name'] = row['name_new']
            changed = True
        if row['vm_name_new'] != row['vm_name_old']:
            update_params['vm_name'] = row['vm_name_new']
            changed = True
        if row['is_active_new'] != row['is_active_old']:
            update_params['is_active'] = 1 if row['is_active_new'] else 0
            changed = True
        if row['is_automation_on_new'] != row['is_automation_on_old']:
            update_params['is_automation_on'] = 1 if row['is_automation_on_new'] else 0
            changed = True
        
        if changed:
            try:
                org = Organization()
                org.update(**update_params)
                changes_made += 1
            except Exception as e:
                st.error(f"Error updating {row['name_new']}: {str(e)}")
    
    if changes_made > 0:
        st.success(f"✅ Updated {changes_made} organization(s)")


def render_add_form():
    """Render add form."""
    st.markdown("---")
    st.markdown("#### Add New Organization")
    
    with st.form("add_org_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Name*", placeholder="e.g., Acme Corp")
            vm_name = st.text_input("VM Name*", placeholder="e.g., ACME-SERVER-01")
        
        with col2:
            is_active = st.checkbox("Active", value=True)
            is_automation_on = st.checkbox("Automation On", value=False)
        
        col_submit, col_cancel = st.columns(2)
        
        with col_submit:
            submit = st.form_submit_button("Add Organization", use_container_width=True)
        
        with col_cancel:
            cancel = st.form_submit_button("Cancel", use_container_width=True)
        
        if cancel:
            st.session_state['adding_organization'] = False
            st.rerun()
        
        if submit:
            if not name or not vm_name:
                st.error("Name and VM Name are required")
            else:
                try:
                    org = Organization()
                    org.insert(
                        name=name,
                        vm_name=vm_name,
                        is_active=1 if is_active else 0,
                        is_automation_on=1 if is_automation_on else 0
                    )
                    st.success(f"Organization '{name}' added!")
                    st.session_state['adding_organization'] = False
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {str(e)}")