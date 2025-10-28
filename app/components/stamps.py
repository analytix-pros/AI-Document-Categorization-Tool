"""Stamps management component with data_editor."""
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
    """Render stamps management interface with data editor."""
    # st.markdown("### Stamps Management")
    
    df = get_all_stamps()
    
    if df.empty:
        st.info("No stamps found.")
        if st.button("➕ Add New Stamp", key="stamps_add_first"):
            st.session_state['adding_stamp'] = True
        
        if st.session_state.get('adding_stamp', False):
            render_add_form()
        return
    
    col_table, col_details = st.columns([4, 2])
    
    with col_table:
        display_df = df.copy()
        display_df['is_active'] = display_df['is_active'].astype(bool)
        
        edit_columns = ['name', 'keywords', 'is_active']
        
        edited_df = st.data_editor(
            display_df[['stamps_uuid', 'org_name'] + edit_columns],
            hide_index=True,
            width='stretch',
            disabled=['stamps_uuid', 'org_name'],
            column_config={
                'stamps_uuid': st.column_config.TextColumn('UUID', width='small'),
                'org_name': st.column_config.TextColumn('Organization', width='medium'),
                'name': st.column_config.TextColumn('Stamp Name', width='medium'),
                'keywords': st.column_config.TextColumn('Keywords', width='large'),
                'is_active': st.column_config.CheckboxColumn('Active')
            },
            key='stamps_editor'
        )
        
        if not edited_df.equals(display_df[['stamps_uuid', 'org_name'] + edit_columns]):
            st.info("⚠️ Changes detected - Click 'Save Changes' to apply")
            
            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                if st.button("💾 Save Changes", key="stamps_save_changes", type="primary", width='stretch'):
                    save_changes(df, edited_df)
                    st.rerun()
            with col2:
                if st.button("↩️ Discard", key="stamps_discard_changes", width='stretch'):
                    st.rerun()
        
        if st.button("➕ Add New Stamp", key="stamps_add_new_button", width='stretch'):
            st.session_state['adding_stamp'] = True
            st.rerun()
        
        if st.session_state.get('adding_stamp', False):
            render_add_form()
    
    with col_details:
        # st.markdown("#### Full Details")
        
        stamp_options = ['(View More Details)'] + [f"{row['name']} ({row['org_name']})" for _, row in df.iterrows()]
        selected_stamp = st.selectbox(
            "Select stamp",
            stamp_options,
            key='stamp_detail_select',
            label_visibility='collapsed'
        )
        
        if selected_stamp != '(View More Details)':
            stamp_name = selected_stamp.split(' (')[0]
            org_name = selected_stamp.split(' (')[1].rstrip(')')
            stamp_data = df[(df['name'] == stamp_name) & (df['org_name'] == org_name)].iloc[0]
            
            st.markdown(f"**Name:** {stamp_data['name']}")
            st.markdown(f"**Organization:** {stamp_data['org_name']}")
            st.markdown(f"**Keywords:** {stamp_data['keywords']}")
            st.markdown(f"**Active:** {'Yes' if stamp_data['is_active'] else 'No'}")
            
            st.markdown("---")
            st.markdown("**Description:**")
            st.write(stamp_data['description'] if pd.notna(stamp_data['description']) else 'N/A')
            
            st.markdown("---")
            st.caption(f"Created: {stamp_data['created_datetime']}")
            st.caption(f"Updated: {stamp_data['updated_datetime']}")
            
            if st.button("✏️ Edit Description", key="stamps_edit_desc_button", width='stretch'):
                st.session_state['editing_stamp_desc'] = stamp_data['stamps_uuid']
                st.rerun()
            
            if st.session_state.get('editing_stamp_desc') == stamp_data['stamps_uuid']:
                render_description_editor(stamp_data)


def save_changes(original_df, edited_df):
    """Save changes to database."""
    merged = edited_df.merge(
        original_df[['stamps_uuid', 'name', 'keywords', 'is_active']],
        on='stamps_uuid',
        suffixes=('_new', '_old')
    )
    
    changes_made = 0
    for idx, row in merged.iterrows():
        changed = False
        update_params = {'stamps_uuid': row['stamps_uuid']}
        
        if row['name_new'] != row['name_old']:
            update_params['name'] = row['name_new']
            changed = True
        if row['keywords_new'] != row['keywords_old']:
            update_params['keywords'] = row['keywords_new']
            changed = True
        if row['is_active_new'] != row['is_active_old']:
            update_params['is_active'] = 1 if row['is_active_new'] else 0
            changed = True
        
        if changed:
            try:
                stamp = Stamps()
                stamp.update(**update_params)
                changes_made += 1
            except Exception as e:
                st.error(f"Error updating {row['name_new']}: {str(e)}")
    
    if changes_made > 0:
        st.success(f"✅ Updated {changes_made} stamp(s)")


def render_add_form():
    """Render add stamp form."""
    st.markdown("---")
    st.markdown("#### Add New Stamp")
    
    orgs_df = get_organizations()
    
    if orgs_df.empty:
        st.warning("No active organizations. Please create an organization first.")
        if st.button("Cancel", key="stamps_cancel_no_orgs", width='stretch'):
            st.session_state['adding_stamp'] = False
            st.rerun()
        return
    
    with st.form("add_stamp_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Stamp Name*", placeholder="e.g., FILED")
            organization = st.selectbox("Organization*", orgs_df['name'].tolist())
            keywords = st.text_input("Keywords*", placeholder="['filed', 'file stamped']")
        
        with col2:
            description = st.text_area("Description")
            is_active = st.checkbox("Active", value=True)
        
        col_submit, col_cancel = st.columns(2)
        
        with col_submit:
            submit = st.form_submit_button("Add Stamp", width='stretch')
        
        with col_cancel:
            cancel = st.form_submit_button("Cancel", width='stretch')
        
        if cancel:
            st.session_state['adding_stamp'] = False
            st.rerun()
        
        if submit:
            if not name or not keywords:
                st.error("Name and Keywords are required")
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
                    st.success(f"Stamp '{name}' added!")
                    st.session_state['adding_stamp'] = False
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {str(e)}")


def render_description_editor(stamp_data):
    """Render description editor."""
    with st.form(f"edit_desc_{stamp_data['stamps_uuid']}"):
        new_description = st.text_area(
            "Edit Description",
            value=stamp_data['description'] if pd.notna(stamp_data['description']) else '',
            height=150
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("💾 Save", width='stretch'):
                try:
                    stamp = Stamps()
                    stamp.update(
                        stamps_uuid=stamp_data['stamps_uuid'],
                        description=new_description,
                        updated_by=st.session_state.get('user_uuid')
                    )
                    st.success("Description updated!")
                    st.session_state['editing_stamp_desc'] = None
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        
        with col2:
            if st.form_submit_button("Cancel", width='stretch'):
                st.session_state['editing_stamp_desc'] = None
                st.rerun()