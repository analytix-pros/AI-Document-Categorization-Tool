"""AI Analysis component - combines upload and AI categorization process."""
import streamlit as st
import json
import time
from app.components.system_status import prepare_ollama_models_background, check_system_ready_for_upload
from database.db_models import Batch, Document, DocumentCategory
from utils.utils_system_specs import get_system_specs
from utils.ocr_processing import process_document_with_all_ocr_models


def render_ai_analysis_page():
    """Main render function for combined AI Analysis tab."""
    
    # Initialize session state for uploads
    if 'uploaded_files' not in st.session_state:
        st.session_state['uploaded_files'] = []
    
    # Check if analysis has been started
    if not st.session_state.get('start_categorization', False):
        # Show upload section
        render_upload_section()
    else:
        # Show AI analysis workflow
        render_analysis_workflow()


def render_upload_section():
    """Render document upload section."""
    # Create two columns: upload section and ready to process section
    col_upload, _, col_process = st.columns([5, 1, 4])
    
    with col_upload:
        st.markdown("#### Upload Files")
        
        uploaded_files = st.file_uploader(
            "Choose files",
            accept_multiple_files=True,
            key="files_upload",
            type=['pdf'],
            label_visibility="collapsed"
        )
        
        if uploaded_files:
            st.session_state['uploaded_files'] = uploaded_files
    
    with col_process:
        # Show Ready to Process section if files are uploaded
        if st.session_state['uploaded_files']:
            file_count = len(st.session_state['uploaded_files'])
            
            st.markdown("#### Ready to Process")
            st.info(f"{file_count} document(s) uploaded")
            
            # Check if system is ready
            is_ready, missing_items = check_system_ready_for_upload()
            
            if not is_ready:
                st.warning("⚠️ System not ready")
                st.error("Missing requirements:")
                for item in missing_items:
                    st.write(f"• {item}")
                st.info("Check sidebar for system status")
                
                st.button("Start AI Analysis", type="primary", width='stretch', disabled=True)
            else:
                if st.button("Start AI Analysis", type="primary", width='stretch'):
                    # Create batch and insert documents into database
                    create_batch_and_documents()
                    st.session_state['start_categorization'] = True
                    st.rerun()
            
            if st.button("Clear Upload", width='stretch'):
                st.session_state['uploaded_files'] = []
                clear_analysis_session()
                st.rerun()
        else:
            st.markdown("#### Ready to Process")
            st.info("Upload files to begin processing")


def create_batch_and_documents():
    """Create batch record and insert all uploaded documents into database."""
    org_uuid = st.session_state.get('org_uuid', '')
    user_uuid = st.session_state.get('user_uuid')
    uploaded_files = st.session_state.get('uploaded_files', [])
    
    if not org_uuid or not user_uuid or not uploaded_files:
        st.error("Missing required information to create batch")
        return None
    
    # Get system specs for batch metadata
    system_specs = get_system_specs()
    system_metadata_json = json.dumps(system_specs)
    
    # Create batch record
    batch = Batch()
    batch_uuid = batch.insert(
        organization_uuid=org_uuid,
        automation_uuid=None,  # Manual upload, no automation
        system_metadata=system_metadata_json,
        status='started',
        process_time=0,  # Will be updated when complete
        created_by=user_uuid
    )
    
    # Store batch info in session state
    st.session_state['batch_uuid'] = batch_uuid
    st.session_state['batch_start_time'] = time.time()
    
    # Insert each document into database
    document_model = Document()
    document_uuids = []
    
    for uploaded_file in uploaded_files:
        # Read PDF bytes
        pdf_bytes = uploaded_file.getvalue()
        
        # Insert document record
        document_uuid = document_model.insert(
            organization_uuid=org_uuid,
            batch_uuid=batch_uuid,
            upload_name=uploaded_file.name,
            upload_folder=None,
            pdf=pdf_bytes,
            is_active=1,
            created_by=user_uuid,
            updated_by=user_uuid
        )
        
        document_uuids.append(document_uuid)
    
    # Store document UUIDs in session state
    st.session_state['document_uuids'] = document_uuids
    
    # Update batch status
    batch.update(batch_uuid, status='processing')
    
    return batch_uuid


def render_document_processing():
    """Render condensed document processing step with OCR."""
    st.markdown("### Step 2: Processing Documents")
    
    files = st.session_state['uploaded_files']
    document_uuids = st.session_state.get('document_uuids', [])
    total_files = len(files)
    
    # Initialize processing state
    if 'current_file_index' not in st.session_state:
        st.session_state['current_file_index'] = 0
        st.session_state['categorization_results'] = []
    
    current_index = st.session_state['current_file_index']
    
    # Progress bar
    progress = current_index / total_files
    st.progress(progress, text=f"Processing {current_index}/{total_files} documents")
    
    # Current file processing
    if current_index < total_files:
        current_file = files[current_index]
        current_doc_uuid = document_uuids[current_index]
        
        st.info(f"📄 Analyzing: {current_file.name}")
        
        # Process with OCR models
        pdf_bytes = current_file.getvalue()
        ocr_results = process_document_with_all_ocr_models(pdf_bytes)
        
        # Store OCR results in document_category table
        org_uuid = st.session_state.get('org_uuid')
        user_uuid = st.session_state.get('user_uuid')
        
        doc_category = DocumentCategory()
        doc_category_uuid = doc_category.insert(
            organization_uuid=org_uuid,
            document_uuid=current_doc_uuid,
            category_uuid=None,  # Will be set after LLM categorization
            stamps_uuid=None,
            category_confidence=None,
            all_category_confidence=None,
            ocr_text=json.dumps(ocr_results),  # Store as JSON
            ocr_text_confidence=None,
            override_category_uuid=None,
            override_context=None,
            is_active=1,
            created_by=user_uuid,
            updated_by=user_uuid
        )
        
        # TODO: Add LLM categorization here
        # For now, use placeholder
        result = {
            'filename': current_file.name,
            'document_uuid': current_doc_uuid,
            'document_category_uuid': doc_category_uuid,
            'category': '[AI Category Placeholder]',
            'confidence': 0.85,
            'subcategory': '[Subcategory Placeholder]',
            'stamp_detected': 'FILED',
            'ocr_text': ocr_results
        }
        
        st.session_state['categorization_results'].append(result)
        st.session_state['current_file_index'] += 1
        
        st.rerun()
    else:
        # Processing complete - update batch
        batch_uuid = st.session_state.get('batch_uuid')
        batch_start_time = st.session_state.get('batch_start_time')
        
        if batch_uuid and batch_start_time:
            process_time = int(time.time() - batch_start_time)
            batch = Batch()
            batch.update(batch_uuid, status='completed', process_time=process_time)
        
        st.success(f"✅ Processed {total_files} documents")
        st.session_state['processing_complete'] = True
        st.rerun()


def render_analysis_workflow():
    """Render AI analysis workflow after files are uploaded."""
    
    if not st.session_state.get('uploaded_files'):
        st.info("📁 No documents uploaded.")
        if st.button("Back to Upload"):
            st.session_state['start_categorization'] = False
            st.rerun()
        return
    
    files = st.session_state['uploaded_files']
    
    # Condensed header
    col1, col2, col3 = st.columns([2, 3, 1])
    with col1:
        st.metric("Documents", len(files))
    with col2:
        status = get_processing_status()
        st.metric("Status", status)
    with col3:
        if st.button("🗑️ Clear", width='stretch'):
            clear_analysis_session()
            st.rerun()
    
    st.markdown("---")
    
    # Step 1: Model Preparation
    if not st.session_state.get('models_prepared', False):
        render_model_preparation()
        return
    
    # Step 2: Document Processing
    if not st.session_state.get('processing_complete', False):
        render_document_processing()
        return
    
    # Step 3: Results
    render_categorization_results()


def get_processing_status():
    """Get current processing status string."""
    if not st.session_state.get('models_prepared', False):
        return "Preparing Models"
    elif not st.session_state.get('processing_complete', False):
        return "Processing Documents"
    else:
        return "Complete"


def render_model_preparation():
    """Render condensed model preparation step."""
    st.markdown("### Step 1: Preparing AI Models")
    
    progress_container = st.container()
    
    with progress_container:
        result = prepare_ollama_models_background(progress_container=progress_container)
    
    if result['success']:
        st.success("✅ Models Ready")
        st.session_state['models_prepared'] = True
        st.rerun()
    else:
        st.error("❌ Model Preparation Failed")
        
        # Compact error display
        if result.get('failed'):
            with st.expander("View Errors"):
                for failure in result['failed']:
                    st.text(f"• {failure['model']}: {failure['error']}")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Retry", width='stretch'):
                st.rerun()
        with col2:
            if st.button("⚠️ Continue Anyway", width='stretch'):
                st.session_state['models_prepared'] = True
                st.rerun()


def render_document_processing():
    """Render condensed document processing step."""
    st.markdown("### Step 2: Processing Documents")
    
    files = st.session_state['uploaded_files']
    total_files = len(files)
    
    # Initialize processing state
    if 'current_file_index' not in st.session_state:
        st.session_state['current_file_index'] = 0
        st.session_state['categorization_results'] = []
    
    current_index = st.session_state['current_file_index']
    
    # Progress bar
    progress = current_index / total_files
    st.progress(progress, text=f"Processing {current_index}/{total_files} documents")
    
    # Current file processing (placeholder for actual AI logic)
    if current_index < total_files:
        current_file = files[current_index]
        
        st.info(f"📄 Analyzing: {current_file.name}")
        
        # Placeholder for actual AI categorization
        # TODO: Replace with actual AI categorization logic
        result = {
            'filename': current_file.name,
            'category': '[AI Category Placeholder]',
            'confidence': 0.85,
            'subcategory': '[Subcategory Placeholder]',
            'stamp_detected': 'FILED'
        }
        
        st.session_state['categorization_results'].append(result)
        st.session_state['current_file_index'] += 1
        
        st.rerun()
    else:
        # Processing complete
        st.success(f"✅ Processed {total_files} documents")
        st.session_state['processing_complete'] = True
        st.rerun()


def render_categorization_results():
    """Render condensed categorization results in grid layout."""
    st.markdown("### Results")
    
    results = st.session_state.get('categorization_results', [])
    
    if not results:
        st.warning("No results available")
        return
    
    # Calculate grid dimensions (3 columns for better space usage)
    num_cols = 3
    num_rows = (len(results) + num_cols - 1) // num_cols
    
    # Render results in grid
    for row in range(num_rows):
        cols = st.columns(num_cols)
        
        for col_idx in range(num_cols):
            result_idx = row * num_cols + col_idx
            
            if result_idx < len(results):
                with cols[col_idx]:
                    render_result_card(results[result_idx], result_idx)
    
    # Show modal dialog if viewing/editing a result
    if 'viewing_result' in st.session_state:
        render_result_modal_dialog(results[st.session_state['viewing_result']])
    
    # Action buttons at bottom
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Save Results", type="primary", width='stretch'):
            save_results_to_database()
            st.success("Results saved!")
    
    with col2:
        if st.button("Export CSV", width='stretch'):
            export_results_csv()
    
    with col3:
        if st.button("Process More", width='stretch'):
            clear_analysis_session()
            st.rerun()


def render_result_card(result, idx):
    """Render a single condensed result card."""
    confidence = result['confidence']
    
    # Determine confidence color
    if confidence >= 0.8:
        conf_color = "#28a745"
        conf_emoji = "🟢"
    elif confidence >= 0.6:
        conf_color = "#ffc107"
        conf_emoji = "🟡"
    else:
        conf_color = "#dc3545"
        conf_emoji = "🔴"
    
    # Card container with border
    with st.container():
        st.markdown(f"""
        <div style="
            border: 1px solid #ddd; 
            border-radius: 8px; 
            padding: 12px; 
            margin-bottom: 8px;
            background-color: #f8f9fa;
            height: 150px;
        ">
            <div style="font-size: 13px; font-weight: bold; margin-bottom: 8px; 
                        white-space: nowrap; overflow: hidden; text-overflow: ellipsis;"
                 title="{result['filename']}">
                📄 {result['filename']}
            </div>
            <div style="font-size: 12px; color: #666; margin-bottom: 4px;">
                <strong>Category:</strong> {result['category']}
            </div>
            <div style="font-size: 12px; color: #666; margin-bottom: 8px;">
                <strong>Confidence:</strong> <span style="color: {conf_color}; font-weight: bold;">{conf_emoji} {confidence:.0%}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Action buttons
        btn_col1, btn_col2, btn_col3 = st.columns(3)
        
        with btn_col1:
            if st.button("View/Edit", key=f"view_{idx}", width='stretch', type="secondary"):
                st.session_state['viewing_result'] = idx
                st.session_state['editing_mode'] = True
                st.rerun()
        
        with btn_col2:
            if st.button("Delete", key=f"delete_{idx}", width='stretch'):
                if st.session_state.get(f'confirm_delete_{idx}', False):
                    st.session_state['categorization_results'].pop(idx)
                    st.session_state[f'confirm_delete_{idx}'] = False
                    st.success(f"Deleted {result['filename']}")
                    st.rerun()
                else:
                    st.session_state[f'confirm_delete_{idx}'] = True
                    st.rerun()
        
        with btn_col3:
            if st.button("Confirm", key=f"confirm_{idx}", width='stretch', type="primary"):
                result['confirmed'] = True
                st.success(f"Confirmed!")
                st.rerun()
        
        # Show delete confirmation if needed
        if st.session_state.get(f'confirm_delete_{idx}', False):
            st.warning(f"Click Delete again to confirm removal of {result['filename']}")


@st.dialog("Document Classification Details", width="large")
def render_result_modal_dialog(result):
    """Render modal dialog for viewing/editing classification details."""
    
    st.markdown("---")
    
    # Top section: File info
    r1_col1, r1_col2, r1_col3 = st.columns(3)
    
    with r1_col1:
        st.text_input("Filename", value=result['filename'], disabled=True, key="modal_filename")
    
    with r1_col2:
        # Editable category dropdown
        categories = ["Garnishments", "Transcript of Judgments", "Service", "Invoices", "Contracts"]
        current_category_idx = categories.index(result['category']) if result['category'] in categories else 0
        
        new_category = st.selectbox(
            "Category",
            categories,
            index=current_category_idx,
            key="modal_category"
        )
    
    with r1_col3:
        # Subcategory
        subcategories = ["Wage Garn", "Bank Garn", "Accepted TOJ", "Rejected TOJ"]
        new_subcategory = st.selectbox(
            "Subcategory",
            ["None"] + subcategories,
            key="modal_subcategory"
        )

    r2_col1, r2_col2, r2_col3 = st.columns([2, 1, 7])
    
    with r2_col1:
        st.markdown("**Confidence Levels:**")
        
        confidence = result['confidence']
        if confidence >= 0.8:
            conf_color = "🟢"
        elif confidence >= 0.6:
            conf_color = "🟡"
        else:
            conf_color = "🔴"
        
        st.metric("Highest Confidence", f"{conf_color} {confidence:.1%}")

    with r2_col2:
        st.markdown(
            """
            <div style="
                height: 100%;
                border-left: 2px solid #cccccc;
                margin-left: 10px;
                margin-right: 10px;
            "></div>
            """,
            unsafe_allow_html=True
        )

    with r2_col3:
        st.markdown("**All LLM Confidences:**")
        
        llm_confidences = result.get('all_llm_confidences', {
            'granite3.2-vision': 0.85,
            'llava:7b': 0.82,
            'mistral': 0.78
        })
        
        items = list(llm_confidences.items())
        n_items = len(items)
        
        if n_items == 0:
            st.caption("No models evaluated")
        else:
            cols = st.columns(min(n_items, 3))
            for i, (model_name, conf) in enumerate(items):
                with cols[i % len(cols)]:
                    st.metric(
                        label=model_name.split(':')[0],
                        value=f"{conf:.1%}",
                        delta=None
                    )
    
    st.markdown("---")
    
    r3_col1, r3_col2 = st.columns([4, 6])

    with r3_col1:
        st.markdown("**Extracted Text (OCR)**")
        
        ocr_text = result.get('ocr_text', 
            "This is placeholder OCR text extracted from the document.\n\n" +
            "In a real implementation, this would contain the full text extracted " +
            "from the PDF using the OCR models (Tesseract, EasyOCR, or PaddleOCR).\n\n" +
            "The text would include all readable content from the document, " +
            "which the LLM models used to determine the category and confidence levels."
        )
        
        new_ocr_text = st.text_area(
            "OCR Text",
            value=ocr_text,
            height=300,
            key="modal_ocr_text",
            label_visibility="collapsed"
        )
    
    with r3_col2:    
        st.markdown("**Document Preview**")
        
        pdf_data = result.get('pdf_data', None)
        
        if pdf_data:
            st.write("PDF preview would be rendered here using st.write() or an iframe")
        else:
            st.info("📄 PDF preview would be displayed here\n\n" +
                "In the real implementation, this would show:\n" +
                "- Rendered PDF pages\n" +
                "- Page navigation controls\n" +
                "- Zoom controls\n" +
                "- Detected stamps/annotations highlighted")
    
    st.markdown("---")
    
    # Modal action buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Save Changes", type="primary", width='stretch', key="modal_save"):
            result['category'] = new_category
            result['subcategory'] = new_subcategory if new_subcategory != "None" else None
            result['ocr_text'] = new_ocr_text
            
            st.success("Changes saved!")
            del st.session_state['viewing_result']
            st.rerun()
    
    with col2:
        if st.button("Discard Changes", width='stretch', key="modal_discard"):
            del st.session_state['viewing_result']
            st.rerun()
    
    with col3:
        if st.button("Delete Document", width='stretch', key="modal_delete"):
            idx = st.session_state.get('viewing_result')
            if idx is not None:
                st.session_state['categorization_results'].pop(idx)
                del st.session_state['viewing_result']
                st.success("Document deleted!")
                st.rerun()


def save_results_to_database():
    """Save categorization results to database (placeholder)."""
    # TODO: Implement actual database save logic
    results = st.session_state.get('categorization_results', [])
    pass


def export_results_csv():
    """Export results as CSV (placeholder)."""
    import pandas as pd
    
    results = st.session_state.get('categorization_results', [])
    
    if not results:
        st.warning("No results to export")
        return
    
    df = pd.DataFrame(results)
    csv = df.to_csv(index=False)
    
    st.download_button(
        label="📥 Download CSV",
        data=csv,
        file_name="categorization_results.csv",
        mime="text/csv"
    )


def clear_analysis_session():
    """Clear all analysis session state."""
    keys_to_clear = [
        'models_prepared',
        'processing_complete',
        'current_file_index',
        'categorization_results',
        'viewing_result',
        'start_categorization',
        'uploaded_files'
    ]
    
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]