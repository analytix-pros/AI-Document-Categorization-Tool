"""Document Categories management component with level-based tables."""
import streamlit as st
import pandas as pd
from database.db_models import Category, Stamps, create_connection
from utils.utils_uuid import derive_uuid
from utils.utils import get_utc_datetime


def get_all_categories(organization_uuid=None):
    """Retrieve all categories with parent and stamp information."""
    conn = create_connection()
    query = """
        SELECT 
            c.category_uuid, c.parent_category_uuid, c.organization_uuid,
            c.name, c.hierarchy_level, c.use_stamps, c.stamps_uuid,
            c.description, c.keywords, c.min_threshold, c.exclusion_rules,
            c.file_rename_rules, c.is_active,
            p.name as parent_name,
            s.name as stamp_name,
            o.name as org_name,
            c.created_datetime, c.updated_datetime
        FROM category c
        LEFT JOIN category p ON c.parent_category_uuid = p.category_uuid
        LEFT JOIN stamps s ON c.stamps_uuid = s.stamps_uuid
        LEFT JOIN organization o ON c.organization_uuid = o.organization_uuid
        WHERE c.is_active = 1
    """
    params = []
    
    if organization_uuid:
        query += " AND c.organization_uuid = ?"
        params.append(organization_uuid)
    
    query += " ORDER BY c.hierarchy_level, c.name"
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


def get_organizations():
    """Retrieve all active organizations."""
    conn = create_connection()
    query = "SELECT organization_uuid, name FROM organization WHERE is_active = 1 ORDER BY name"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def get_stamps_for_org(organization_uuid):
    """Retrieve all active stamps for an organization."""
    conn = create_connection()
    query = """
        SELECT stamps_uuid, name 
        FROM stamps 
        WHERE organization_uuid = ? AND is_active = 1 
        ORDER BY name
    """
    df = pd.read_sql_query(query, conn, params=[organization_uuid])
    conn.close()
    return df


def get_parent_categories(organization_uuid, current_level, exclude_uuid=None):
    """Get available parent categories (one level up)."""
    conn = create_connection()
    query = """
        SELECT category_uuid, name, hierarchy_level
        FROM category
        WHERE organization_uuid = ? AND hierarchy_level = ? AND is_active = 1
    """
    params = [organization_uuid, current_level - 1]
    
    if exclude_uuid:
        query += " AND category_uuid != ?"
        params.append(exclude_uuid)
    
    query += " ORDER BY name"
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


def get_category_children(category_uuid):
    """Get direct children of a category."""
    conn = create_connection()
    query = """
        SELECT category_uuid, name, hierarchy_level
        FROM category
        WHERE parent_category_uuid = ? AND is_active = 1
        ORDER BY name
    """
    df = pd.read_sql_query(query, conn, params=[category_uuid])
    conn.close()
    return df


def get_max_hierarchy_level(organization_uuid):
    """Get the maximum hierarchy level for an organization."""
    conn = create_connection()
    query = """
        SELECT MAX(hierarchy_level) as max_level
        FROM category
        WHERE organization_uuid = ? AND is_active = 1
    """
    result = conn.execute(query, [organization_uuid]).fetchone()
    conn.close()
    return result[0] if result[0] else 0


def prepare_display_dataframe(df, level):
    """Prepare dataframe for display with selected columns in logical order."""
    display_df = df.copy()
    
    columns_order = ['name', 'description', 'keywords', 'min_threshold']
    
    if level > 1:
        columns_order.insert(1, 'parent_name')
    
    if 'stamp_name' in display_df.columns and display_df['stamp_name'].notna().any():
        columns_order.append('stamp_name')
    
    display_columns = {
        'name': 'Category Name',
        'parent_name': 'Parent Category',
        'description': 'Description',
        'keywords': 'Keywords',
        'min_threshold': 'Min Threshold',
        'stamp_name': 'Stamp'
    }
    
    display_df = display_df[[col for col in columns_order if col in display_df.columns]]
    display_df = display_df.rename(columns={col: display_columns[col] for col in display_df.columns if col in display_columns})
    
    return display_df


def render_add_category_form(organization_uuid, level, parent_category_uuid=None):
    """Render compact add form for specific level."""
    form_key = f"add_form_level_{level}_{parent_category_uuid or 'root'}"
    
    with st.form(form_key, clear_on_submit=True):
        st.markdown(f"**Add Level {level} Category**")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            name = st.text_input("Name*", key=f"name_{form_key}")
        
        with col2:
            min_threshold = st.number_input("Threshold", min_value=0.0, max_value=1.0, value=0.75, step=0.05, key=f"threshold_{form_key}")
        
        with col3:
            use_stamps = st.checkbox("Use Stamps", key=f"stamps_{form_key}")
        
        col4, col5 = st.columns(2)
        
        with col4:
            description = st.text_area("Description", key=f"desc_{form_key}", height=80)
        
        with col5:
            keywords = st.text_area("Keywords", placeholder="['keyword1', 'keyword2']", key=f"keywords_{form_key}", height=80)
        
        stamps_uuid = None
        if use_stamps:
            stamps_df = get_stamps_for_org(organization_uuid)
            if not stamps_df.empty:
                stamp_options = stamps_df['name'].tolist()
                stamp_name = st.selectbox("Select Stamp*", stamp_options, key=f"stamp_select_{form_key}")
                stamps_uuid = stamps_df[stamps_df['name'] == stamp_name]['stamps_uuid'].iloc[0]
        
        col_submit, col_cancel = st.columns([1, 1])
        
        with col_submit:
            submit = st.form_submit_button("Add Category", use_container_width=True)
        
        with col_cancel:
            cancel = st.form_submit_button("Cancel", use_container_width=True)
        
        if cancel:
            st.session_state[f'adding_level_{level}'] = False
            st.rerun()
        
        if submit:
            if not name:
                st.error("Category name is required")
            else:
                try:
                    category = Category()
                    category.insert(
                        organization_uuid=organization_uuid,
                        name=name,
                        hierarchy_level=level,
                        parent_category_uuid=parent_category_uuid,
                        use_stamps=1 if use_stamps else 0,
                        stamps_uuid=stamps_uuid,
                        description=description,
                        keywords=keywords,
                        min_threshold=min_threshold,
                        is_active=1,
                        created_by=st.session_state.get('user_uuid'),
                        updated_by=st.session_state.get('user_uuid')
                    )
                    st.success(f"Category '{name}' added successfully!")
                    st.session_state[f'adding_level_{level}'] = False
                    st.rerun()
                except Exception as e:
                    st.error(f"Error adding category: {str(e)}")


def render_edit_category_form(category_data, organization_uuid):
    """Render edit form for a category."""
    form_key = f"edit_form_{category_data['category_uuid']}"
    
    with st.form(form_key):
        st.markdown(f"**Edit: {category_data['name']}**")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            name = st.text_input("Name*", value=category_data['name'])
        
        with col2:
            min_threshold = st.number_input("Threshold", min_value=0.0, max_value=1.0, value=float(category_data['min_threshold']), step=0.05)
        
        with col3:
            use_stamps = st.checkbox("Use Stamps", value=bool(category_data['use_stamps']))
        
        col4, col5 = st.columns(2)
        
        with col4:
            description = st.text_area("Description", value=category_data['description'] if pd.notna(category_data['description']) else "")
        
        with col5:
            keywords = st.text_area("Keywords", value=category_data['keywords'] if pd.notna(category_data['keywords']) else "")
        
        stamps_uuid = category_data['stamps_uuid']
        if use_stamps:
            stamps_df = get_stamps_for_org(organization_uuid)
            if not stamps_df.empty:
                stamp_options = stamps_df['name'].tolist()
                current_idx = stamp_options.index(category_data['stamp_name']) if category_data['stamp_name'] in stamp_options else 0
                stamp_name = st.selectbox("Select Stamp*", stamp_options, index=current_idx)
                stamps_uuid = stamps_df[stamps_df['name'] == stamp_name]['stamps_uuid'].iloc[0]
        
        col_save, col_cancel = st.columns([1, 1])
        
        with col_save:
            submit = st.form_submit_button("Save Changes", use_container_width=True)
        
        with col_cancel:
            cancel = st.form_submit_button("Cancel", use_container_width=True)
        
        if cancel:
            st.session_state['editing_category'] = None
            st.rerun()
        
        if submit:
            if not name:
                st.error("Category name is required")
            else:
                try:
                    category = Category()
                    category.update(
                        category_uuid=category_data['category_uuid'],
                        name=name,
                        use_stamps=1 if use_stamps else 0,
                        stamps_uuid=stamps_uuid,
                        description=description,
                        keywords=keywords,
                        min_threshold=min_threshold,
                        updated_by=st.session_state.get('user_uuid')
                    )
                    st.success(f"Category '{name}' updated successfully!")
                    st.session_state['editing_category'] = None
                    st.rerun()
                except Exception as e:
                    st.error(f"Error updating category: {str(e)}")


def render_delete_confirmation(category_data):
    """Render delete confirmation dialog."""
    st.warning(f"⚠️ Delete Category: **{category_data['name']}**?")
    
    children_df = get_category_children(category_data['category_uuid'])
    
    if not children_df.empty:
        st.error(f"Cannot delete: This category has {len(children_df)} child categories.")
        st.write("Child categories:")
        for _, child in children_df.iterrows():
            st.write(f"  • {child['name']}")
        
        if st.button("Cancel", key="cancel_delete_with_children"):
            st.session_state['deleting_category'] = None
            st.rerun()
    else:
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("⚠️ Confirm Delete", type="primary", use_container_width=True):
                try:
                    category = Category()
                    category.delete(category_data['category_uuid'])
                    st.success(f"Category '{category_data['name']}' deleted!")
                    st.session_state['deleting_category'] = None
                    if f'selected_level_{category_data["hierarchy_level"]}' in st.session_state:
                        del st.session_state[f'selected_level_{category_data["hierarchy_level"]}']
                    st.rerun()
                except Exception as e:
                    st.error(f"Error deleting: {str(e)}")
        
        with col2:
            if st.button("Cancel", use_container_width=True):
                st.session_state['deleting_category'] = None
                st.rerun()


def render_level_table(df_all, level, organization_uuid, parent_filter_uuid=None):
    """Render a table for a specific hierarchy level with filtering."""
    df_level = df_all[df_all['hierarchy_level'] == level].copy()
    
    if parent_filter_uuid and level > 1:
        df_level = df_level[df_level['parent_category_uuid'] == parent_filter_uuid]
    
    st.markdown(f"### Level {level} Categories")
    
    if df_level.empty:
        st.info(f"No Level {level} categories found." + (f" (Filtered by parent)" if parent_filter_uuid else ""))
        
        if st.button(f"➕ Add Level {level} Category", key=f"btn_add_level_{level}_{parent_filter_uuid or 'root'}"):
            st.session_state[f'adding_level_{level}'] = True
            st.session_state[f'adding_parent_{level}'] = parent_filter_uuid
            st.rerun()
        
        if st.session_state.get(f'adding_level_{level}', False):
            render_add_category_form(organization_uuid, level, parent_filter_uuid)
        
        return None
    
    display_df = prepare_display_dataframe(df_level, level)
    
    # Display the dataframe
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    # Create selectbox for row selection
    category_options = ["(None)"] + df_level['name'].tolist()
    current_selection = st.session_state.get(f'selected_level_{level}_name')
    default_idx = category_options.index(current_selection) if current_selection in category_options else 0
    
    selected_name = st.selectbox(
        f"Select Level {level} Category",
        category_options,
        index=default_idx,
        key=f"select_level_{level}_{parent_filter_uuid or 'root'}"
    )
    
    selected_uuid = None
    
    if selected_name != "(None)":
        selected_row = df_level[df_level['name'] == selected_name].iloc[0]
        selected_uuid = selected_row['category_uuid']
        st.session_state[f'selected_level_{level}'] = selected_uuid
        st.session_state[f'selected_level_{level}_name'] = selected_name
        
        st.markdown(f"**Selected:** {selected_row['name']}")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if level < 3:  # Only show Add Child if not at max level
                if st.button("➕ Add Child", key=f"add_child_{selected_uuid}", use_container_width=True):
                    st.session_state[f'adding_level_{level + 1}'] = True
                    st.session_state[f'adding_parent_{level + 1}'] = selected_uuid
                    st.rerun()
        
        with col2:
            if st.button("✏️ Edit", key=f"edit_{selected_uuid}", use_container_width=True):
                st.session_state['editing_category'] = selected_uuid
                st.rerun()
        
        with col3:
            if st.button("🗑️ Delete", key=f"delete_{selected_uuid}", use_container_width=True):
                st.session_state['deleting_category'] = selected_uuid
                st.rerun()
        
        with col4:
            if st.button("Clear Selection", key=f"clear_{level}", use_container_width=True):
                if f'selected_level_{level}' in st.session_state:
                    del st.session_state[f'selected_level_{level}']
                if f'selected_level_{level}_name' in st.session_state:
                    del st.session_state[f'selected_level_{level}_name']
                st.rerun()
    else:
        if f'selected_level_{level}' in st.session_state:
            del st.session_state[f'selected_level_{level}']
        if f'selected_level_{level}_name' in st.session_state:
            del st.session_state[f'selected_level_{level}_name']
        
        if st.button(f"➕ Add Level {level} Category", key=f"btn_add_level_{level}_{parent_filter_uuid or 'root'}"):
            st.session_state[f'adding_level_{level}'] = True
            st.session_state[f'adding_parent_{level}'] = parent_filter_uuid
            st.rerun()
    
    if st.session_state.get('editing_category') in df_level['category_uuid'].values:
        category_data = df_level[df_level['category_uuid'] == st.session_state['editing_category']].iloc[0]
        render_edit_category_form(category_data, organization_uuid)
    
    if st.session_state.get('deleting_category') in df_level['category_uuid'].values:
        category_data = df_level[df_level['category_uuid'] == st.session_state['deleting_category']].iloc[0]
        render_delete_confirmation(category_data)
    
    if st.session_state.get(f'adding_level_{level}', False):
        parent_uuid = st.session_state.get(f'adding_parent_{level}')
        render_add_category_form(organization_uuid, level, parent_uuid)
    
    return selected_uuid


def render_document_categories():
    """Main render function for document categories management."""
    st.markdown("### Document Categories")
    
    orgs_df = get_organizations()
    
    if orgs_df.empty:
        st.warning("No organizations available. Please create an organization first.")
        return
    
    org_options = orgs_df['name'].tolist()
    selected_org = st.selectbox("Organization", org_options, key="doc_cat_org_select")
    selected_org_uuid = orgs_df[orgs_df['name'] == selected_org]['organization_uuid'].iloc[0]
    
    df_all = get_all_categories(selected_org_uuid)
    
    if df_all.empty:
        st.info("No categories found for this organization. Start by adding a Level 1 category.")
        if st.button("➕ Add Level 1 Category"):
            st.session_state['adding_level_1'] = True
            st.rerun()
        
        if st.session_state.get('adding_level_1', False):
            render_add_category_form(selected_org_uuid, 1, None)
        return
    
    max_level = get_max_hierarchy_level(selected_org_uuid)
    
    selected_parent = None
    
    for level in range(1, max_level + 1):
        st.markdown("---")
        selected_parent = render_level_table(df_all, level, selected_org_uuid, selected_parent)