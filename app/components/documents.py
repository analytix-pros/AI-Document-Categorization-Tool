"""Documents upload and management component."""
import streamlit as st
import os
from pathlib import Path
from app.components.system_status import check_system_ready


def render_documents_page():
    """Main render function for documents upload and management."""
    st.markdown("### Document Upload & Management")
    
    # Initialize session state for uploads
    if 'uploaded_files' not in st.session_state:
        st.session_state['uploaded_files'] = []
    
    st.markdown("---")
    
    # Create two columns: upload section and ready to process section
    col_upload, col_process = st.columns([5, 5])
    
    with col_upload:
        st.markdown("#### 📁 Upload Files")
        st.markdown("*Upload one or multiple files*")
        
        uploaded_files = st.file_uploader(
            "Choose files",
            accept_multiple_files=True,
            key="files_upload",
            type=['pdf', 'png', 'jpg', 'jpeg', 'tiff', 'tif'],
            label_visibility="collapsed"
        )
        
        if uploaded_files:
            st.success(f"✓ {len(uploaded_files)} file(s) selected")
            st.session_state['uploaded_files'] = uploaded_files
            
            with st.expander("View uploaded files"):
                for file in uploaded_files:
                    file_size = len(file.getvalue()) / 1024  # KB
                    st.write(f"📄 {file.name} ({file_size:.1f} KB)")
    
    with col_process:
        # Show Ready to Process section if files are uploaded
        if st.session_state['uploaded_files']:
            file_count = len(st.session_state['uploaded_files'])
            
            st.markdown("#### Ready to Process")
            st.info(f"📊 {file_count} document(s) uploaded")
            
            # Check if system is ready
            is_ready, missing_items = check_system_ready()
            
            if not is_ready:
                st.warning("⚠️ System not ready")
                st.error("Missing requirements:")
                for item in missing_items:
                    st.write(f"• {item}")
                st.info("👈 Check sidebar for installation instructions")
                
                # Disabled button
                st.button("🤖 AI Categorize", type="primary", use_container_width=True, disabled=True)
            else:
                if st.button("🤖 AI Categorize", type="primary", use_container_width=True):
                    st.session_state['start_categorization'] = True
                    st.rerun()
            
            if st.button("🗑️ Clear Upload", use_container_width=True):
                st.session_state['uploaded_files'] = []
                if 'start_categorization' in st.session_state:
                    del st.session_state['start_categorization']
                st.rerun()
        else:
            st.markdown("#### Ready to Process")
            st.info("👆 Upload files to begin processing")
    
    # Show categorization process if started
    if st.session_state.get('start_categorization', False):
        st.markdown("---")
        render_categorization_process()
    
    # Show upload history/results
    st.markdown("---")
    render_upload_history()


def render_categorization_process():
    """Render the AI categorization process."""
    st.markdown("---")
    st.markdown("#### 🤖 AI Categorization in Progress")
    
    with st.container():
        st.info("⏳ Processing documents... (This is a placeholder for the actual AI categorization logic)")
        
        # Placeholder for progress
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        files = st.session_state['uploaded_files']
        
        for idx, file in enumerate(files):
            progress = (idx + 1) / len(files)
            progress_bar.progress(progress)
            status_text.text(f"Processing: {file.name} ({idx + 1}/{len(files)})")
        
        st.success(f"✅ Successfully processed {len(files)} document(s)!")
        
        # Placeholder results
        st.markdown("##### Categorization Results")
        
        with st.expander("View Results", expanded=True):
            for file in files:
                col1, col2, col3 = st.columns([4, 3, 3])
                
                with col1:
                    st.write(f"📄 **{file.name}**")
                
                with col2:
                    st.write("Category: *[To be determined]*")
                
                with col3:
                    st.write("Confidence: *[To be calculated]*")
        
        if st.button("✓ Complete & Save Results"):
            st.session_state['uploaded_files'] = []
            st.session_state['upload_source'] = None
            del st.session_state['start_categorization']
            st.success("Results saved successfully!")
            st.rerun()


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