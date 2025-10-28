"""Documents upload and management component - simplified."""
import streamlit as st
import os
from pathlib import Path
from app.components.system_status import check_system_ready_for_upload


def render_documents_page():
    """Main render function for documents upload and management."""
    # st.markdown("### Document Upload & Management")
    
    # Initialize session state for uploads
    if 'uploaded_files' not in st.session_state:
        st.session_state['uploaded_files'] = []
    
    # st.markdown("---")
    
    # Create two columns: upload section and ready to process section
    col_upload, _, col_process = st.columns([5, 1, 4])
    
    with col_upload:
        st.markdown("#### Upload Files")
        
        uploaded_files = st.file_uploader(
            "Choose files",
            accept_multiple_files=True,
            key="files_upload",
            type=['pdf'], # 'png', 'jpg', 'jpeg', 'tiff', 'tif'],
            label_visibility="collapsed"
        )
        
        if uploaded_files:
            # st.success(f"✓ {len(uploaded_files)} file(s) selected")
            st.session_state['uploaded_files'] = uploaded_files
            
            # with st.expander("View uploaded files"):
            #     for file in uploaded_files:
            #         file_size = len(file.getvalue()) / 1024  # KB
            #         st.write(f"📄 {file.name} ({file_size:.1f} KB)")
    
    with col_process:
        # Show Ready to Process section if files are uploaded
        if st.session_state['uploaded_files']:
            file_count = len(st.session_state['uploaded_files'])
            
            st.markdown("#### Ready to Process")
            st.info(f"{file_count} document(s) uploaded")
            
            # Check if system is ready (only Ollama service + OCR)
            is_ready, missing_items = check_system_ready_for_upload()
            
            if not is_ready:
                st.warning("⚠️ System not ready")
                st.error("Missing requirements:")
                for item in missing_items:
                    st.write(f"• {item}")
                st.info("Check sidebar for system status")
                
                # Disabled button
                st.button("Start AI Analysis", type="primary", use_container_width=True, disabled=True)
            else:
                if st.button("Start AI Analysis", type="primary", use_container_width=True):
                    # Set flag to switch to AI Analysis tab
                    st.session_state['switch_to_ai_analysis'] = True
                    st.session_state['start_categorization'] = True
                    st.rerun()
            
            if st.button("Clear Upload", use_container_width=True):
                st.session_state['uploaded_files'] = []
                if 'start_categorization' in st.session_state:
                    del st.session_state['start_categorization']
                if 'models_prepared' in st.session_state:
                    del st.session_state['models_prepared']
                st.rerun()
        else:
            st.markdown("#### Ready to Process")
            st.info("Upload files to begin processing")
    
    # # Show upload history/results
    # st.markdown("---")
    # render_upload_history()


def render_upload_history():
    """Render upload history and previous results."""
    st.markdown("#### 📚 Recent Uploads")
    
    # Placeholder for actual database queries
    st.info("Upload history will be displayed here once documents are processed and saved to the database.")
    
    # Example of what the history table might look like
    with st.expander("Preview: Upload History Format"):
        import pandas as pd
        
        example_data = {
            'Upload Date': ['2025-10-26 10:30', '2025-10-25 14:15', '2025-10-24 09:45'],
            'Files': [5, 1, 12],
            'Status': ['✅ Completed', '✅ Completed', '⚠️ Needs Review'],
            'Categories': ['Mixed', 'Service > Served', 'Mixed']
        }
        
        df = pd.DataFrame(example_data)
        st.dataframe(df, use_container_width=True, hide_index=True)