"""AI Analysis component - combines upload and AI categorization process."""
import streamlit as st
import json
import time
import random
import base64
from io import BytesIO
from datetime import datetime
from app.components.system_status import prepare_ollama_models_background, check_system_ready_for_upload
from database.db_models import create_connection, Batch, Document, DocumentCategory
from utils.utils_system_specs import get_system_specs
from utils.ocr_processing import process_document_with_available_ocr


# --------------------------------------------------------------
#  Helper – turn a bytes object into a data-uri that st.components.v1.html can display
# --------------------------------------------------------------
def _pdf_to_data_uri(pdf_bytes: bytes) -> str:
    """Encode PDF bytes to a base64 data-uri that can be embedded in HTML."""
    b64 = base64.b64encode(pdf_bytes).decode()
    return f"data:application/pdf;base64,{b64}"


def render_ai_analysis_page():
    """Main render function for combined AI Analysis tab."""
    print("\n" + "="*80)
    print("RENDER_AI_ANALYSIS_PAGE - Starting")
    print("="*80)
    
    if 'uploaded_files' not in st.session_state:
        print("Initializing 'uploaded_files' in session state")
        st.session_state['uploaded_files'] = []
    
    start_categorization = st.session_state.get('start_categorization', False)
    print(f"Start categorization flag: {start_categorization}")
    
    # Always render upload section (disabled if started)
    print("Rendering upload section...")
    render_upload_section(disabled=start_categorization)
    
    if start_categorization:
        print("Rendering analysis workflow elements...")
        st.markdown("---")
        render_batch_metrics()
        st.markdown("---")
        render_analysis_content()
        # st.markdown("---")
        render_button_row()
    
    print("="*80 + "\n")


def render_upload_section(disabled: bool = False):
    """Render document upload section, disabled if processing started."""
    print("\n" + "="*80)
    print(f"RENDER_UPLOAD_SECTION - Starting (disabled={disabled})")
    print("="*80)
    
    col_upload, _, col_process = st.columns([5, 1, 4])
    
    with col_upload:
        st.markdown("#### Upload Files")
        
        if not disabled:
            uploaded_files = st.file_uploader(
                "Choose files",
                accept_multiple_files=True,
                key="files_upload",
                type=['pdf'],
                label_visibility="collapsed"
            )
            
            if uploaded_files:
                print(f"Files uploaded: {len(uploaded_files)}")
                for idx, f in enumerate(uploaded_files, 1):
                    print(f"  {idx}. {f.name} ({len(f.getvalue())} bytes)")
                st.session_state['uploaded_files'] = uploaded_files
                st.session_state['number_of_files'] = len(uploaded_files)
        else:
            # Disabled state: show static info
            file_count = len(st.session_state.get('uploaded_files', []))
            st.info(f"{file_count} document(s) uploaded and processing...")
    
    with col_process:
        uploaded_files = st.session_state.get('uploaded_files', [])
        if uploaded_files:
            file_count = len(uploaded_files)
            
            st.markdown("#### Ready to Process")
            st.info(f"{file_count} document(s) uploaded")
            
            if not disabled:
                print(f"Checking system readiness...")
                is_ready, missing_items = check_system_ready_for_upload()
                print(f"System ready: {is_ready}")
                
                if not is_ready:
                    print(f"System not ready. Missing items: {missing_items}")
                    st.warning("Warning: System not ready")
                    st.error("Missing requirements:")
                    for item in missing_items:
                        st.write(f"• {item}")
                    st.info("Check sidebar for system status")
                    
                    # Two disabled buttons side-by-side
                    btn_col1, btn_col2 = st.columns(2)
                    with btn_col1:
                        st.button("Start AI Analysis", type="primary", disabled=True, width='stretch')
                    with btn_col2:
                        if st.button("Clear Upload", width='stretch'):
                            print("User clicked 'Clear Upload' button")
                            st.session_state['uploaded_files'] = []
                            clear_analysis_session()
                            st.rerun()
                else:
                    print("System ready - enabling Start AI Analysis button")
                    
                    # Two active buttons side-by-side
                    btn_col1, btn_col2 = st.columns(2)
                    with btn_col1:
                        if st.button("Start AI Analysis", type="primary", width='stretch'):
                            print("User clicked 'Start AI Analysis' button")
                            create_batch_and_documents()
                            st.session_state['start_categorization'] = True
                            print("Set start_categorization to True, triggering rerun")
                            st.rerun()
                    with btn_col2:
                        if st.button("Clear Upload", width='stretch'):
                            print("User clicked 'Clear Upload' button")
                            st.session_state['uploaded_files'] = []
                            clear_analysis_session()
                            st.rerun()

            # No buttons when disabled
        else:
            st.markdown("#### Ready to Process")
            st.info("Upload files to begin processing")
            print("No files uploaded yet")
    
    print("="*80 + "\n")


def create_batch_and_documents():
    """Create batch record and insert all uploaded documents into database."""
    print("\n" + "="*80)
    print("CREATE_BATCH_AND_DOCUMENTS - Starting")
    print("="*80)
    
    org_uuid = st.session_state.get('org_uuid', '')
    user_uuid = st.session_state.get('user_uuid')
    uploaded_files = st.session_state.get('uploaded_files', [])
    number_of_files = len(uploaded_files)

    print(f"Organization UUID: {org_uuid}")
    print(f"User UUID: {user_uuid}")
    print(f"Number of files to process: {number_of_files}")
    
    if not org_uuid or not user_uuid or not uploaded_files:
        print("ERROR: Missing required information")
        st.error("Missing required information to create batch")
        return None
    
    print("\nGathering system specs...")
    system_specs = get_system_specs()
    system_metadata_json = system_specs
    print(f"System specs gathered: {len(system_metadata_json)} characters")
    
    # --- STEP 1: Create Batch (metadata auto-filled) ---
    print("\n--- STEP 1: Creating Batch Record ---")
    batch = Batch()
    batch_data = {
        "organization_uuid": org_uuid,
        "automation_uuid": None,
        "system_metadata": json.dumps(system_metadata_json, indent=4, default=str),
        "status": "started",
        "number_of_files": number_of_files,
        "process_time": 0
    }

    print("Batch data prepared:")
    print(json.dumps(batch_data, indent=4, default=str))
    
    print("\nInserting batch into database...")
    batch_uuid = batch.insert(st.session_state, '/ai-analyze', batch_data)
    print(f"Success: Batch created successfully: {batch_uuid}")
    
    st.session_state['batch_uuid'] = batch_uuid
    st.session_state['batch_start_time'] = time.time()
    print(f"Batch start time recorded: {st.session_state['batch_start_time']}")
    
    # --- STEP 2: Insert Documents ---
    print("\n--- STEP 2: Inserting Documents ---")
    document_model = Document()
    document_uuids = []
    
    for idx, uploaded_file in enumerate(uploaded_files, 1):
        print(f"\nProcessing document {idx}/{len(uploaded_files)}: {uploaded_file.name}")
        pdf_bytes = uploaded_file.getvalue()
        print(f"  PDF size: {len(pdf_bytes)} bytes")
        
        document_data = {
            "organization_uuid": org_uuid,
            "batch_uuid": batch_uuid,
            "upload_name": uploaded_file.name,
            "upload_folder": None,
            "pdf": pdf_bytes
        }
        
        print(f"  Inserting document into database...")
        document_uuid = document_model.insert(st.session_state, '/ai-analyze', document_data)
        document_uuids.append(document_uuid)
        print(f"  Success: Document inserted: {document_uuid}")
    
    st.session_state['document_uuids'] = document_uuids
    print(f"\nSuccess: All {len(document_uuids)} documents inserted successfully")
    
    # --- STEP 3: Update Batch Status ---
    print("\n--- STEP 3: Updating Batch Status ---")
    print("Updating batch status to 'processing'...")
    batch.update(st.session_state, '/ai-analyze', batch_uuid, {"status": "processing"})
    print("Success: Batch status updated to 'processing'")
    
    print("\n" + "="*80)
    print("CREATE_BATCH_AND_DOCUMENTS - Complete")
    print(f"Batch UUID: {batch_uuid}")
    print(f"Documents created: {len(document_uuids)}")
    print("="*80 + "\n")
    
    return batch_uuid


def render_document_processing():
    """Render document processing step - separated into OCR and LLM phases."""
    print("\n" + "="*80)
    print("RENDER_DOCUMENT_PROCESSING - Starting")
    print("="*80)
    
    files = st.session_state['uploaded_files']
    document_uuids = st.session_state.get('document_uuids', [])
    total_files = len(files)
    
    print(f"Total files to process: {total_files}")
    print(f"Document UUIDs available: {len(document_uuids)}")
    
    # Initialize processing state
    if 'current_file_index' not in st.session_state:
        print("Initializing processing state...")
        st.session_state['current_file_index'] = 0
        st.session_state['categorization_results'] = []
        st.session_state['ocr_complete'] = False
        print("Processing state initialized")
    
    current_index = st.session_state['current_file_index']
    ocr_complete = st.session_state.get('ocr_complete', False)
    
    print(f"Current file index: {current_index}")
    print(f"OCR phase complete: {ocr_complete}")
    
    # PHASE 1: OCR Processing
    if not ocr_complete:
        st.markdown("### Step 2A: OCR Text Extraction")
        print("\n--- PHASE 1: OCR Processing ---")
        
        progress = current_index / total_files
        st.progress(progress, text=f"Extracting text from {current_index}/{total_files} documents")
        
        if current_index < total_files:
            current_file = files[current_index]
            current_doc_uuid = document_uuids[current_index]
            
            print(f"\nProcessing file {current_index + 1}/{total_files}: {current_file.name}")
            print(f"Document UUID: {current_doc_uuid}")
            
            st.info(f"Extracting text: {current_file.name}")
            
            print("Reading PDF bytes...")
            pdf_bytes = current_file.getvalue()
            print(f"PDF size: {len(pdf_bytes)} bytes")
            
            print("Starting OCR processing...")
            ocr_results = process_document_with_available_ocr(pdf_bytes)
            print(f"OCR processing complete. Results: {len(str(ocr_results))} characters")
            
            org_uuid = st.session_state.get('org_uuid')
            
            print(f"\nPreparing document_category record...")
            print(f"  Organization UUID: {org_uuid}")
            print(f"  Document UUID: {current_doc_uuid}")
            
            # Insert document_category with OCR results only
            doc_category = DocumentCategory()
            doc_category_data = {
                "organization_uuid": org_uuid,
                "document_uuid": current_doc_uuid,
                "category_uuid": None,
                "stamps_uuid": None,
                "category_confidence": None,
                "all_category_confidence": None,
                "ocr_text": json.dumps(ocr_results, indent=4, default=str),
                "ocr_text_confidence": None,
                "override_category_uuid": None,
                "override_context": None
            }
            
            print("Inserting document_category with OCR results...")
            doc_category_uuid = doc_category.insert(st.session_state, '/ai-analyze', doc_category_data)
            print(f"Success: Document_category created: {doc_category_uuid}")
            
            # Store minimal result for now
            result = {
                'filename': current_file.name,
                'document_uuid': current_doc_uuid,
                'document_category_uuid': doc_category_uuid,
                'ocr_text': json.dumps(ocr_results, indent=4, default=str),
                'category': None,
                'confidence': None,
                'subcategory': None,
                'stamp_detected': None
            }
            
            st.session_state['categorization_results'].append(result)
            st.session_state['current_file_index'] += 1
            
            print(f"Moving to next file. New index: {st.session_state['current_file_index']}")
            print("="*80 + "\n")
            st.rerun()
        else:
            # OCR phase complete
            print("\nSuccess: OCR phase complete for all documents")
            print(f"Total documents processed: {total_files}")
            st.session_state['ocr_complete'] = True
            st.session_state['current_file_index'] = 0
            print("Resetting index for LLM phase")
            print("="*80 + "\n")
            st.success(f"Success: Text extracted from {total_files} documents")
            time.sleep(1)
            st.rerun()
    
    # PHASE 2: LLM Categorization
    else:
        st.markdown("### Step 2B: AI Categorization")
        print("\n--- PHASE 2: LLM Categorization ---")
        
        progress = current_index / total_files
        st.progress(progress, text=f"Categorizing {current_index}/{total_files} documents")
        
        if current_index < total_files:
            result = st.session_state['categorization_results'][current_index]
            
            print(f"\nCategorizing document {current_index + 1}/{total_files}: {result['filename']}")
            print(f"Document UUID: {result['document_uuid']}")
            print(f"Document Category UUID: {result['document_category_uuid']}")
            
            st.info(f"Analyzing: {result['filename']}")
            
            # Query the OCR text from the database
            print("Querying OCR text from database...")
            org_uuid = st.session_state.get('org_uuid')
            
            conn = create_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT ocr_text 
                FROM document_category 
                WHERE document_category_uuid = ? AND organization_uuid = ?
            """
            print(f"Executing query for document_category_uuid: {result['document_category_uuid']}")
            cursor.execute(query, (result['document_category_uuid'], org_uuid))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                ocr_text_json = row[0]
                print(f"Success: OCR text retrieved from database: {len(ocr_text_json)} characters")
                
                # TODO: Feed OCR text to LLM for categorization
                print("\nTODO: Feeding OCR text to LLM models for categorization...")
                print("  - This is where you would call your LLM categorization function")
                print("  - Pass the OCR text to multiple LLM models")
                print("  - Aggregate confidence scores")
                print("  - Determine final category")
                
                # Placeholder LLM results
                llm_category = random.choice(['Garnishments', 'Transcript of Judgments', 'Service'])
                llm_confidence = random_number = random.uniform(0.50, 0.90)
                llm_subcategory = random.choice(['Bank Garn', 'Wage Garn', 'Rejected TOJ', 'Accepted TOJ'])
                llm_stamp = random.choice(['FILED', 'SERVED', 'RECORDED', 'ISSUED', '', '', '', ''])
                
                print(f"\nLLM Results (placeholder):")
                print(f"  Category: {llm_category}")
                print(f"  Confidence: {llm_confidence}")
                print(f"  Subcategory: {llm_subcategory}")
                print(f"  Stamp: {llm_stamp}")
                
                # Update result
                result['category'] = llm_category
                result['confidence'] = llm_confidence
                result['subcategory'] = llm_subcategory
                result['stamp_detected'] = llm_stamp
                
                # Update document_category with LLM results
                print("\nUpdating document_category with LLM results...")
                doc_category = DocumentCategory()
                update_data = {
                    "category_uuid": None,
                    "category_confidence": llm_confidence,
                    "all_category_confidence": json.dumps({"placeholder": llm_confidence}, indent=4, default=str)
                }
                
                doc_category.update(
                    st.session_state, 
                    '/ai-analyze', 
                    result['document_category_uuid'], 
                    update_data
                )
                print("Success: Document_category updated with LLM results")
                
            else:
                print("ERROR: Could not retrieve OCR text from database")
            
            st.session_state['current_file_index'] += 1
            print(f"Moving to next document. New index: {st.session_state['current_file_index']}")
            print("="*80 + "\n")
            st.rerun()
        else:
            # LLM phase complete - update batch
            print("\nSuccess: LLM categorization complete for all documents")
            print(f"Total documents categorized: {total_files}")
            
            batch_uuid = st.session_state.get('batch_uuid')
            batch_start_time = st.session_state.get('batch_start_time')
            
            if batch_uuid and batch_start_time:
                process_time = int(time.time() - batch_start_time)
                st.session_state['process_time'] = process_time
                print(f"\nUpdating batch record...")
                print(f"  Batch UUID: {batch_uuid}")
                print(f"  Process time: {process_time} seconds")
                
                batch = Batch()
                batch.update(st.session_state, '/ai-analyze', batch_uuid, {
                    "status": "completed",
                    "process_time": process_time
                })
                print("Success: Batch status updated to 'completed'")
            
            print("\n" + "="*80)
            print("RENDER_DOCUMENT_PROCESSING - Complete")
            print(f"Total documents processed: {total_files}")
            print("="*80 + "\n")
            
            st.success(f"Success: Processed {total_files} documents")
            st.session_state['processing_complete'] = True
            st.rerun()


def render_batch_metrics():
    """Render the batch metrics in a table-like structure."""
    batch_uuid = st.session_state.get('batch_uuid', 'N/A')
    num_files = st.session_state.get('number_of_files', 0)
    start_time = st.session_state.get('batch_start_time')
    start_str = datetime.fromtimestamp(start_time).strftime("%Y-%m-%d %H:%M:%S") if start_time else 'N/A'
    status = get_processing_status()
    process_time = f"{st.session_state.get('process_time', 0)}s" if st.session_state.get('processing_complete', False) else "In Progress"
    
    batch_header_row_spacing = [30, 15, 25, 15, 20]

    # ---------- Header ----------
    batch_hdr = st.columns(batch_header_row_spacing)
    batch_hdr[0].markdown("### Batch UUID")
    batch_hdr[1].markdown("### File Count")
    batch_hdr[2].markdown("### Start")
    batch_hdr[3].markdown("### Status")
    batch_hdr[4].markdown("### Process Time")  

    # --- Custom text size (adjust '1.1rem' as needed) ---
    text_size = "1.2rem"  # Options: 0.9rem, 1rem, 1.1rem, 1.2rem, etc.

    batch_hdr[0].markdown(f"<span style='font-size:{text_size}'>{batch_uuid}</span>", unsafe_allow_html=True)
    batch_hdr[1].markdown(f"<span style='font-size:{text_size}'>{num_files}</span>", unsafe_allow_html=True)
    batch_hdr[2].markdown(f"<span style='font-size:{text_size}'>{start_str}</span>", unsafe_allow_html=True)
    batch_hdr[3].markdown(f"<span style='font-size:{text_size}'>{status}</span>", unsafe_allow_html=True)
    batch_hdr[4].markdown(f"<span style='font-size:{text_size}'>{process_time}</span>", unsafe_allow_html=True)     


def render_button_row():
    """Render the button row, only if processing complete."""
    if st.session_state.get('processing_complete', False):
        btn_col1, btn_col2, btn_col3 = st.columns(3)
        with btn_col1:
            if st.button("Save Results", type="primary", width="stretch"):
                save_results_to_database()
                st.success("Results saved!")
        with btn_col2:
            if st.button("Export CSV", width="stretch"):
                export_results_csv()
        with btn_col3:
            if st.button("Process More", width="stretch"):
                clear_analysis_session()
                st.rerun()


def render_analysis_content():
    """Render the main content: model prep, processing, or results."""
    models_prepared = st.session_state.get('models_prepared', False)
    processing_complete = st.session_state.get('processing_complete', False)
    
    print(f"Models prepared: {models_prepared}")
    print(f"Processing complete: {processing_complete}")
    
    if not models_prepared:
        print("Rendering model preparation step...")
        render_model_preparation()
        return
    
    if not processing_complete:
        print("Rendering document processing step...")
        render_document_processing()
        return
    
    print("Rendering categorization results...")
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
        st.success("Success: Models Ready")
        st.session_state['models_prepared'] = True
        st.rerun()
    else:
        st.error("Error: Model Preparation Failed")
        
        if result.get('failed'):
            with st.expander("View Errors"):
                for failure in result['failed']:
                    st.text(f"• {failure['model']}: {failure['error']}")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Retry"):
                st.rerun()
        with col2:
            if st.button("Continue Anyway"):
                st.session_state['models_prepared'] = True
                st.rerun()


def render_categorization_results():
    """Table with an expander that replaces the old modal."""
    results = st.session_state.get('categorization_results', [])
    if not results:
        st.warning("No results available")
        return

    row_spacing = [3, 3, 2, 2, 1]          # 5 columns now (no View/Edit button)

    # ---------- Header ----------
    hdr = st.columns(row_spacing)
    hdr[0].markdown("### File")
    hdr[1].markdown("### Category")
    hdr[2].markdown("### Confidence")
    hdr[3].markdown("### Stamp")
    hdr[4].markdown("")                 # Confirm button column

    # ---------- Each row ----------
    for i, res in enumerate(results):
        row_container = st.container()
        with row_container:
            cols = st.columns(row_spacing, vertical_alignment="center")

            # --- Custom text size (adjust '1.1rem' as needed) ---
            text_size = "1.0rem"  # Options: 0.9rem, 1rem, 1.1rem, 1.2rem, etc.

            # File name
            filename = res.get('filename', 'N/A')
            cols[0].markdown(f"<span style='font-size:{text_size}'>{filename}</span>", unsafe_allow_html=True)

            # Category
            cat = f"{res.get('category','')} {res.get('subcategory','')}".strip()
            cols[1].markdown(f"<span style='font-size:{text_size}'>{cat}</span>", unsafe_allow_html=True)

            # Confidence badge (badge size is fixed, but label is readable)
            conf = res.get('confidence')
            if isinstance(conf, (int, float)):
                pct = f"{conf*100:.1f}%"
                if conf >= 0.75:
                    c, ico = "green", ":material/check:"
                elif conf >= 0.65:
                    c, ico = "orange", ":material/warning:"
                else:
                    c, ico = "red", ":material/error:"
                cols[2].badge(pct, icon=ico, color=c)
            else:
                cols[2].badge("N/A", color="gray")

            # Stamp badge
            stamp = res.get('stamp_detected', False)
            label = "Detected" if stamp else "Not Detected"
            scol = "green" if stamp else "red"
            sico = ":material/check:" if stamp else ":material/close:"
            cols[3].badge(label, icon=sico, color=scol)

            # Confirm button
            if cols[4].button("Confirm", key=f"confirm_{i}"):
                pass

        # --- Expander ---
        with st.expander(f"Details – {res.get('filename','Item '+str(i))}", expanded=False):
            _render_expander_content(res, i)

        st.markdown("---")


def _render_expander_content(result: dict, row_idx: int):
    """All the UI that used to be in the modal – now inside an expander."""
    st.markdown("---")

    # ---------- Row 1 – Filename | Category | Subcategory ----------
    r1_col1, r1_col2, r1_col3 = st.columns(3)

    with r1_col1:
        st.text_input(
            "Filename",
            value=result.get('filename', ''),
            disabled=True,
            key=f"exp_filename_{row_idx}"
        )

    with r1_col2:
        categories = ["Garnishments", "Transcript of Judgments", "Service", "Invoices", "Contracts"]
        cur_idx = categories.index(result.get('category')) if result.get('category') in categories else 0
        new_category = st.selectbox(
            "Category",
            categories,
            index=cur_idx,
            key=f"exp_category_{row_idx}"
        )

    with r1_col3:
        subcategories = ["Wage Garn", "Bank Garn", "Accepted TOJ", "Rejected TOJ"]
        cur_sub = result.get('subcategory')
        sub_idx = subcategories.index(cur_sub) + 1 if cur_sub in subcategories else 0
        new_subcategory = st.selectbox(
            "Subcategory",
            ["None"] + subcategories,
            index=sub_idx,
            key=f"exp_subcategory_{row_idx}"
        )

    # ---------- Row 2 – Confidence + All LLM confidences ----------
    r2_col1, r2_col2, r2_col3 = st.columns([2, 1, 7])

    with r2_col1:
        st.markdown("**Confidence Levels:**")
        confidence = result.get('confidence', 0.0)
        if confidence >= 0.8:
            conf_color = "Green"
        elif confidence >= 0.6:
            conf_color = "Yellow"
        else:
            conf_color = "Red"
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
        llm_confidences = result.get('all_llm_confidences', {})
        items = list(llm_confidences.items())
        if not items:
            st.caption("No models evaluated")
        else:
            cols = st.columns(min(len(items), 3))
            for j, (model, conf) in enumerate(items):
                with cols[j % len(cols)]:
                    st.metric(label=model.split(':')[0], value=f"{conf:.1%}")

    # ---------- Row 3 – OCR text + PDF preview ----------
    r3_col1, r3_col2 = st.columns([4, 6])
    row_height_default = 600

    # ---- OCR Text -------------------------------------------------
    with r3_col1:
        st.markdown("**Extracted Text (OCR)**")
        ocr_text = result.get('ocr_text',
            "Placeholder OCR text … (real OCR would be here)")
        new_ocr_text = st.text_area(
            "OCR Text",
            value=ocr_text,
            height=row_height_default,
            key=f"exp_ocr_{row_idx}",
            label_visibility="collapsed"
        )

    # ---- PDF Preview (with streamlit-pdf-viewer) -----------------------------
    with r3_col2:
        st.markdown("**Document Preview**")

        # 1. Try to get the PDF bytes from the *uploaded* file list (fastest)
        pdf_bytes = None
        if 'uploaded_files' in st.session_state:
            # match by filename (case-insensitive)
            name = result.get('filename')
            for f in st.session_state['uploaded_files']:
                if f.name.lower() == name.lower():
                    pdf_bytes = f.getvalue()
                    break

        # 2. Fallback: query the DB column `pdf` (you already store it)
        if pdf_bytes is None and result.get('document_uuid'):
            conn = create_connection()
            cur = conn.cursor()
            cur.execute(
                "SELECT pdf FROM document WHERE document_uuid = ? AND organization_uuid = ?",
                (result['document_uuid'], st.session_state.get('org_uuid'))
            )
            row = cur.fetchone()
            conn.close()
            if row:
                pdf_bytes = row[0]

        # 3. Render the PDF with streamlit-pdf-viewer
        if pdf_bytes:
            from streamlit_pdf_viewer import pdf_viewer  # Import inside function to avoid global issues
            
            # Wrap in st.container() for better sizing in columns/expanders
            pdf_container = st.container(height=row_height_default, width='stretch')
            with pdf_container:
                pdf_viewer(
                    input=pdf_bytes,
                    width="100%",
                    height=row_height_default - 50,
                    zoom_level="auto-height",           # This is the key!
                    # render_mode="canvas",              # Required for fit-height to work
                    show_page_separator=True,
                    viewer_align="center"
                )
        else:
            st.info(
                "PDF preview would be displayed here\n\n"
                "- Rendered PDF pages\n"
                "- Page navigation\n"
                "- Zoom controls\n"
                "- Highlighted stamps"
            )

    st.markdown("---")

    # ---------- Action buttons ----------
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Save Changes", type="primary", key=f"exp_save_{row_idx}", use_container_width=True):
            result['category'] = new_category
            result['subcategory'] = new_subcategory if new_subcategory != "None" else None
            result['ocr_text'] = new_ocr_text
            st.success("Changes saved!")
            st.rerun()

    with col2:
        if st.button("Discard Changes", key=f"exp_discard_{row_idx}", use_container_width=True):
            st.rerun()

    with col3:
        if st.button("Delete Document", key=f"exp_delete_{row_idx}", use_container_width=True):
            st.session_state['categorization_results'].pop(row_idx)
            st.success("Document deleted!")
            st.rerun()


def save_results_to_database():
    """Save categorization results to database (placeholder)."""
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
        label="Download CSV",
        data=csv,
        file_name="categorization_results.csv",
        mime="text/csv"
    )


def clear_analysis_session():
    """Clear all analysis session state."""
    print("\n" + "="*80)
    print("CLEAR_ANALYSIS_SESSION - Starting")
    print("="*80)
    
    keys_to_clear = [
        'models_prepared',
        'processing_complete',
        'current_file_index',
        'categorization_results',
        'viewing_result',
        'start_categorization',
        'uploaded_files',
        'batch_uuid',
        'batch_start_time',
        'document_uuids',
        'ocr_complete',
        'process_time'
    ]
    
    print(f"Keys to clear: {len(keys_to_clear)}")
    cleared_count = 0
    
    for key in keys_to_clear:
        if key in st.session_state:
            print(f"  Clearing: {key}")
            del st.session_state[key]
            cleared_count += 1
    
    print(f"\nSuccess: Cleared {cleared_count} session state keys")
    print("="*80 + "\n")