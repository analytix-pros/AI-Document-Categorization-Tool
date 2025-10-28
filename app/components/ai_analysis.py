"""AI Analysis component - condensed view for AI categorization process."""
import streamlit as st
from app.components.system_status import prepare_ollama_models_background


def render_ai_analysis_page():
    """Main render function for AI Analysis tab."""
    
    # Check if there are files to process
    if not st.session_state.get('uploaded_files'):
        st.info("📁 No documents uploaded. Please upload files in the Documents tab.")
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
        if st.button("🗑️ Clear", use_container_width=True):
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
            if st.button("🔄 Retry", use_container_width=True):
                st.rerun()
        with col2:
            if st.button("⚠️ Continue Anyway", use_container_width=True):
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
        if st.button("Save Results", type="primary", use_container_width=True):
            save_results_to_database()
            st.success("Results saved!")
    
    with col2:
        if st.button("Export CSV", use_container_width=True):
            export_results_csv()
    
    with col3:
        if st.button("Process More", use_container_width=True):
            clear_analysis_session()
            st.rerun()


def render_result_card(result, idx):
    """Render a single condensed result card."""
    confidence = result['confidence']
    
    # Determine confidence color
    if confidence >= 0.8:
        conf_color = "#28a745"  # Green
        conf_emoji = "🟢"
    elif confidence >= 0.6:
        conf_color = "#ffc107"  # Yellow
        conf_emoji = "🟡"
    else:
        conf_color = "#dc3545"  # Red
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
        
        # Action buttons (3 columns, no icons)
        btn_col1, btn_col2, btn_col3 = st.columns(3)
        
        with btn_col1:
            if st.button("View/Edit", key=f"view_{idx}", use_container_width=True, type="secondary"):
                st.session_state['viewing_result'] = idx
                st.session_state['editing_mode'] = True
                st.rerun()
        
        with btn_col2:
            if st.button("Delete", key=f"delete_{idx}", use_container_width=True):
                if st.session_state.get(f'confirm_delete_{idx}', False):
                    # Actually delete
                    st.session_state['categorization_results'].pop(idx)
                    st.session_state[f'confirm_delete_{idx}'] = False
                    st.success(f"Deleted {result['filename']}")
                    st.rerun()
                else:
                    # Ask for confirmation
                    st.session_state[f'confirm_delete_{idx}'] = True
                    st.rerun()
        
        with btn_col3:
            if st.button("Confirm", key=f"confirm_{idx}", use_container_width=True, type="primary"):
                result['confirmed'] = True
                st.success(f"Confirmed!")
                st.rerun()
        
        # Show delete confirmation if needed
        if st.session_state.get(f'confirm_delete_{idx}', False):
            st.warning(f"Click Delete again to confirm removal of {result['filename']}")


@st.dialog("Document Classification Details", width="large")
def render_result_modal_dialog(result):
    """Render modal dialog for viewing/editing classification details."""
    
    # st.markdown("### Classification Information")
    st.markdown("---")
    
    # Top section: File info
    r1_col1, r1_col2, r1_col3 = st.columns(3)
    
    with r1_col1:
        # st.markdown("**File Information**")
        st.text_input("Filename", value=result['filename'], disabled=True, key="modal_filename")
    
    with r1_col2:
        # Editable category dropdown (placeholder - replace with actual categories from DB)
        categories = ["Garnishments", "Transcript of Judgments", "Service", "Invoices", "Contracts"]
        current_category_idx = categories.index(result['category']) if result['category'] in categories else 0
        
        new_category = st.selectbox(
            "Category",
            categories,
            index=current_category_idx,
            key="modal_category"
        )
    with r1_col3:
        # Subcategory (if applicable)
        subcategories = ["Wage Garn", "Bank Garn", "Accepted TOJ", "Rejected TOJ"]
        new_subcategory = st.selectbox(
            "Subcategory",
            ["None"] + subcategories,
            key="modal_subcategory"
        )

    # st.markdown("---")

    r2_col1, r2_col2, r2_col3 = st.columns([2, 1, 7])
    
    with r2_col1:
        st.markdown("**Confidence Levels:**")
        
        # Highest confidence
        confidence = result['confidence']
        if confidence >= 0.8:
            conf_color = "🟢"
        elif confidence >= 0.6:
            conf_color = "🟡"
        else:
            conf_color = "🔴"
        
        st.metric("Highest Confidence", f"{conf_color} {confidence:.1%}")

    with r2_col2:
        # Vertical line using CSS
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
            # Responsive grid: max 3 per row in col3 (fits nicely)
            cols = st.columns(min(n_items, 3))
            for i, (model_name, conf) in enumerate(items):
                with cols[i % len(cols)]:
                    # Optional: color-code metric
                    delta_color = "normal"
                    if conf >= 0.8:
                        delta_color = "normal"
                    elif conf >= 0.6:
                        delta_color = "normal"
                    else:
                        delta_color = "normal"  # or use "inverse" for red
                    
                    st.metric(
                        label=model_name.split(':')[0],  # Shorten name if needed
                        value=f"{conf:.1%}",
                        delta=None
                    )
    
    st.markdown("---")
    
    r3_col1, r3_col2 = st.columns([4, 6])

    with r3_col1:
    # OCR Text section
        st.markdown("**Extracted Text (OCR)**")
        
        # Large text box with OCR text
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
        # PDF Preview section
        st.markdown("**Document Preview**")
        
        # Placeholder for PDF preview
        # In real implementation, you would render the actual PDF here
        pdf_data = result.get('pdf_data', None)
        
        if pdf_data:
            # Display actual PDF
            st.write("PDF preview would be rendered here using st.write() or an iframe")
            # Example: st.write(pdf_data)
        else:
            # Placeholder
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
        if st.button("Save Changes", type="primary", use_container_width=True, key="modal_save"):
            # Update result with new values
            result['category'] = new_category
            result['subcategory'] = new_subcategory if new_subcategory != "None" else None
            result['ocr_text'] = new_ocr_text
            
            st.success("Changes saved!")
            del st.session_state['viewing_result']
            st.rerun()
    
    with col2:
        if st.button("Discard Changes", use_container_width=True, key="modal_discard"):
            del st.session_state['viewing_result']
            st.rerun()
    
    with col3:
        if st.button("Delete Document", use_container_width=True, key="modal_delete"):
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
    # Save to database here
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
        'start_categorization'
    ]
    
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]