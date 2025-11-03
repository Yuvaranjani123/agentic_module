"""
ZIP Batch Processing Component for RAG Pipeline

This module contains all UI components for handling ZIP file uploads,
file labeling, and batch processing workflows.
"""

import streamlit as st
import os
import zipfile
import shutil
import pdfplumber
import requests
from typing import List, Dict


def render_zip_upload_workflow(pipeline, uploaded_zip, base_output_dir: str, django_api: str):
    """
    Main orchestrator for ZIP file upload and batch processing workflow.
    
    Args:
        pipeline: StreamlitRAGPipeline instance
        uploaded_zip: Uploaded ZIP file from Streamlit
        base_output_dir: Base output directory path
        django_api: Django API base URL
    """
    # Check if product name is provided
    if not st.session_state.product_name or not st.session_state.product_name.strip():
        st.error("❌ Please enter a Product Database Name in the sidebar before uploading ZIP file")
        st.stop()
    
    # Handle ZIP file upload
    st.header("📦 ZIP File Processing")
    st.info(f"📂 Files will be extracted to: `temp/{st.session_state.product_name}/extracted/`")
    
    # Extract ZIP file
    if not st.session_state.uploaded_files_list:
        _extract_zip_file(uploaded_zip, base_output_dir)
    
    # Display labeling interface
    if st.session_state.uploaded_files_list:
        _render_labeling_interface()
    
    # Show processing options after labeling
    if st.session_state.labeling_complete:
        _render_batch_processing_interface(pipeline, base_output_dir, django_api)


def _extract_zip_file(uploaded_zip, base_output_dir: str):
    """Extract ZIP file and discover all processable files."""
    with st.spinner("Extracting ZIP file..."):
        # Use product-specific temp extraction directory
        temp_extract_dir = os.path.join(base_output_dir, "temp", st.session_state.product_name, "extracted")
        
        # Clean the extraction directory before extracting new ZIP
        if os.path.exists(temp_extract_dir):
            try:
                shutil.rmtree(temp_extract_dir)
                st.info("🧹 Cleaned previous extraction folder")
            except Exception as e:
                st.warning(f"⚠️ Could not clean previous extraction folder: {str(e)}")
        
        # Create fresh extraction directory
        os.makedirs(temp_extract_dir, exist_ok=True)
        
        # Save ZIP temporarily in product-specific folder
        temp_zip_dir = os.path.join(base_output_dir, "temp", st.session_state.product_name)
        os.makedirs(temp_zip_dir, exist_ok=True)
        temp_zip_path = os.path.join(temp_zip_dir, uploaded_zip.name)
        with open(temp_zip_path, "wb") as f:
            f.write(uploaded_zip.getbuffer())
        
        # Extract ZIP
        try:
            with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_extract_dir)
            
            # Find all processable files in extracted folder (PDFs and Excel)
            extracted_files = []
            for root, dirs, files in os.walk(temp_extract_dir):
                for file in files:
                    file_lower = file.lower()
                    # Support PDF and Excel files
                    if file_lower.endswith('.pdf') or file_lower.endswith(('.xlsx', '.xls')):
                        file_path = os.path.join(root, file)
                        # Get relative path for display
                        rel_path = os.path.relpath(file_path, temp_extract_dir)
                        
                        # Determine file type
                        if file_lower.endswith('.pdf'):
                            file_type = 'pdf'
                            default_label = 'unknown'
                        else:
                            file_type = 'excel'
                            default_label = 'premium-calculation'  # Excel files default to premium
                        
                        extracted_files.append({
                            "filename": file,
                            "display_name": rel_path,
                            "full_path": file_path,
                            "file_type": file_type,
                            "default_label": default_label
                        })
            
            st.session_state.uploaded_files_list = extracted_files
            
            # Initialize labels with appropriate defaults
            for file_info in extracted_files:
                if file_info["filename"] not in st.session_state.file_labels:
                    st.session_state.file_labels[file_info["filename"]] = file_info["default_label"]
            
            # Count by type
            pdf_count = sum(1 for f in extracted_files if f['file_type'] == 'pdf')
            excel_count = sum(1 for f in extracted_files if f['file_type'] == 'excel')
            st.success(f"✅ Extracted {len(extracted_files)} files: {pdf_count} PDF(s), {excel_count} Excel file(s)")
            
        except Exception as e:
            st.error(f"❌ Error extracting ZIP: {str(e)}")


def _render_labeling_interface():
    """Render the document type labeling interface."""
    st.subheader("🏷️ Step 1: Label Documents")
    st.info("Please assign a document type to each file. PDF files are processed for text/table extraction. Excel files are registered as premium calculators.")
    
    # Document type options
    doc_type_options = {
        "Unknown": "unknown",
        "Policy Document": "policy",
        "Brochure": "brochure", 
        "Prospectus": "prospectus",
        "Terms & Conditions": "terms",
        "Premium Calculation": "premium-calculation",
        "Claim Form": "claim-form",
        "Certificate": "certificate",
        "Other (Custom)": "custom"
    }
    
    # Create a table for labeling
    st.write(f"**Total Files:** {len(st.session_state.uploaded_files_list)}")
    
    # Use columns for better layout
    for idx, file_info in enumerate(st.session_state.uploaded_files_list):
        file_type_icon = "📊" if file_info['file_type'] == 'excel' else "📄"
        file_type_label = file_info['file_type'].upper()
        
        with st.expander(f"{file_type_icon} [{file_type_label}] {file_info['display_name']}", expanded=(idx < 3)):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write(f"**File:** {file_info['filename']}")
                st.write(f"**Type:** {file_type_label}")
                
                # Show preview for PDFs
                if file_info['file_type'] == 'pdf':
                    try:
                        with pdfplumber.open(file_info['full_path']) as pdf:
                            st.write(f"**Pages:** {len(pdf.pages)}")
                    except:
                        pass
                # Show info for Excel
                else:
                    st.info("💡 Excel files are used for premium calculations. They will be uploaded to the premium workbook registry.")
            
            with col2:
                current_label = st.session_state.file_labels.get(file_info['filename'], file_info['default_label'])
                
                # Check if current label is a custom value (not in predefined options)
                is_custom = current_label not in doc_type_options.values() or current_label == 'custom'
                
                # Find the key for current value or default to custom
                if is_custom and current_label != 'unknown':
                    current_label_key = "Other (Custom)"
                    # Store the actual custom value temporarily
                    if f"custom_value_{file_info['filename']}" not in st.session_state:
                        st.session_state[f"custom_value_{file_info['filename']}"] = current_label
                else:
                    current_label_key = [k for k, v in doc_type_options.items() if v == current_label][0]
                
                selected_label = st.selectbox(
                    "Document Type",
                    options=list(doc_type_options.keys()),
                    index=list(doc_type_options.keys()).index(current_label_key),
                    key=f"label_{idx}_{file_info['filename']}"
                )
                
                # If "Other (Custom)" is selected, show text input
                if selected_label == "Other (Custom)":
                    custom_value = st.text_input(
                        "Enter custom type",
                        value=st.session_state.get(f"custom_value_{file_info['filename']}", ""),
                        placeholder="e.g., rider-document, addendum",
                        key=f"custom_input_{idx}_{file_info['filename']}",
                        help="Enter a custom document type (lowercase, use hyphens for spaces)"
                    )
                    if custom_value and custom_value.strip():
                        # Clean and store custom value
                        custom_clean = custom_value.strip().lower().replace(' ', '-')
                        st.session_state.file_labels[file_info['filename']] = custom_clean
                        st.session_state[f"custom_value_{file_info['filename']}"] = custom_clean
                    else:
                        # Default to 'custom' if no value entered yet
                        st.session_state.file_labels[file_info['filename']] = "custom"
                else:
                    # Use predefined option
                    st.session_state.file_labels[file_info['filename']] = doc_type_options[selected_label]
                    # Clear custom value if exists
                    if f"custom_value_{file_info['filename']}" in st.session_state:
                        del st.session_state[f"custom_value_{file_info['filename']}"]
    
    # Show labeling summary
    _render_labeling_summary(doc_type_options)


def _render_labeling_summary(doc_type_options: Dict[str, str]):
    """Render the labeling summary and control buttons."""
    st.divider()
    st.subheader("📊 Labeling Summary")
    
    label_counts = {}
    custom_types = []
    
    for label in st.session_state.file_labels.values():
        label_counts[label] = label_counts.get(label, 0) + 1
        # Track custom types separately
        if label not in ['unknown', 'policy', 'brochure', 'prospectus', 'terms', 'custom']:
            if label not in custom_types:
                custom_types.append(label)
    
    # Show predefined types
    predefined_options = {k: v for k, v in doc_type_options.items() if v != 'custom'}
    cols = st.columns(len(predefined_options))
    for idx, (label_name, label_value) in enumerate(predefined_options.items()):
        with cols[idx]:
            count = label_counts.get(label_value, 0)
            st.metric(label_name, count)
    
    # Show custom types if any
    if custom_types:
        st.write("**Custom Types:**")
        custom_cols = st.columns(min(len(custom_types), 5))
        for idx, custom_type in enumerate(custom_types):
            with custom_cols[idx % 5]:
                count = label_counts.get(custom_type, 0)
                st.metric(f"📌 {custom_type}", count)
    
    # Check if all labeled
    unlabeled_count = label_counts.get('unknown', 0)
    incomplete_custom_count = label_counts.get('custom', 0)  # Custom selected but not specified
    
    if unlabeled_count > 0:
        st.warning(f"⚠️ {unlabeled_count} files still unlabeled (marked as 'Unknown')")
    if incomplete_custom_count > 0:
        st.warning(f"⚠️ {incomplete_custom_count} files marked as 'Other (Custom)' but no custom type entered")
    if unlabeled_count == 0 and incomplete_custom_count == 0:
        st.success("✅ All files have been labeled!")
    
    # Proceed button
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Confirm Labels & Proceed", type="primary"):
            # Check for incomplete custom entries
            if incomplete_custom_count > 0:
                st.error("❌ Please enter custom document types for all files marked as 'Other (Custom)'")
            else:
                st.session_state.labeling_complete = True
                st.success("Labels confirmed! You can now process each document.")
                st.rerun()
    
    with col2:
        if st.button("🔄 Reset Labels"):
            for pdf in st.session_state.uploaded_files_list:
                st.session_state.file_labels[pdf["filename"]] = "unknown"
                # Clear custom values
                if f"custom_value_{pdf['filename']}" in st.session_state:
                    del st.session_state[f"custom_value_{pdf['filename']}"]
            st.success("Labels reset to 'Unknown'")
            st.rerun()


def _render_batch_processing_interface(pipeline, base_output_dir: str, django_api: str):
    """Render the batch processing interface and controls."""
    st.divider()
    st.header("📋 Step 2: Process Documents")
    st.info("PDF files will be processed for text/table extraction. Excel files will be uploaded to the premium calculator registry.")
    
    # Option to process all or select specific files
    process_mode = st.radio(
        "Processing Mode:",
        ["Process All Documents", "Select Specific Documents"],
        help="Choose whether to process all documents or select specific ones"
    )
    
    if process_mode == "Select Specific Documents":
        selected_files = st.multiselect(
            "Select documents to process:",
            options=[f["display_name"] for f in st.session_state.uploaded_files_list],
            default=[f["display_name"] for f in st.session_state.uploaded_files_list[:3]]
        )
    else:
        selected_files = [f["display_name"] for f in st.session_state.uploaded_files_list]
    
    st.write(f"**Selected:** {len(selected_files)} documents")
    
    # Check if product name is provided
    if not st.session_state.product_name or not st.session_state.product_name.strip():
        st.error("❌ Please enter a Product Database Name in the sidebar before processing")
        st.stop()
    
    if st.button("🚀 Start Batch Processing", type="primary"):
        _execute_batch_processing(pipeline, selected_files, base_output_dir, django_api)


def _execute_batch_processing(pipeline, selected_files: List[str], base_output_dir: str, django_api: str):
    """Execute the batch processing workflow."""
    st.header("🔄 Batch Processing in Progress")
    
    # Get selected files to process
    files_to_process = [f for f in st.session_state.uploaded_files_list 
                       if f["display_name"] in selected_files]
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    results_container = st.container()
    
    successful = 0
    failed = 0
    
    for idx, file_info in enumerate(files_to_process):
        doc_label = st.session_state.file_labels[file_info["filename"]]
        
        with results_container:
            file_type_icon = "📊" if file_info['file_type'] == 'excel' else "📄"
            st.subheader(f"{file_type_icon} Processing: {file_info['filename']}")
            st.write(f"**Document Type:** `{doc_label}`")
            st.write(f"**File Type:** `{file_info['file_type'].upper()}`")
            
            with st.spinner(f"Processing {idx+1}/{len(files_to_process)}..."):
                try:
                    # Handle Excel files differently
                    if file_info['file_type'] == 'excel':
                        success = _process_excel_file(file_info, django_api)
                        if success:
                            successful += 1
                        else:
                            failed += 1
                    
                    # Handle PDF files
                    else:
                        success = _process_pdf_file(file_info, doc_label, pipeline, base_output_dir)
                        if success:
                            successful += 1
                        else:
                            failed += 1
                        
                except Exception as e:
                    st.error(f"❌ Error processing {file_info['filename']}: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())
                    failed += 1
            
            st.divider()
        
        # Update progress
        progress = (idx + 1) / len(files_to_process)
        progress_bar.progress(progress)
        status_text.text(f"Processing: {idx+1}/{len(files_to_process)} files completed")
    
    # Final summary
    _render_batch_summary(successful, failed, len(files_to_process), base_output_dir)


def _process_excel_file(file_info: Dict, django_api: str) -> bool:
    """Process an Excel file by uploading to premium registry."""
    st.write("⏳ Uploading Excel workbook to premium calculator registry...")
    
    try:
        # Upload to premium registry via API
        with open(file_info['full_path'], 'rb') as f:
            files = {'excel': (file_info['filename'], f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
            data = {'doc_name': os.path.splitext(file_info['filename'])[0]}
            
            response = requests.post(
                f"{django_api}/api/upload_premium_excel/",
                files=files,
                data=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                st.success(f"✅ {file_info['filename']} uploaded to premium registry!")
                st.write(f"**Registry Path:** `{result.get('filename', 'N/A')}`")
                return True
            else:
                error_msg = response.json().get('error', 'Unknown error')
                st.error(f"❌ Upload failed: {error_msg}")
                return False
    except Exception as e:
        st.error(f"❌ Excel upload error: {str(e)}")
        return False


def _process_pdf_file(file_info: Dict, doc_label: str, pipeline, base_output_dir: str) -> bool:
    """Process a PDF file through the ingestion pipeline."""
    try:
        # Import here to avoid circular imports
        from ingestion_run import StreamlitRAGPipeline
        
        # Create a temporary pipeline for this file
        temp_pipeline = StreamlitRAGPipeline()
        temp_pipeline.setup_directories(file_info['full_path'], base_output_dir)
        
        # Step 1: Extract tables
        st.write("⏳ Step 1: Extracting tables...")
        temp_pipeline.extract_tables()
        
        # Step 2: Extract text
        st.write("⏳ Step 2: Extracting text...")
        temp_pipeline.extract_text_content()
        
        # Step 3: Chunk and embed with document type
        st.write(f"⏳ Step 3: Chunking and embedding (type: {doc_label})...")
        chunker, message = temp_pipeline.chunk_and_embed(doc_label)
        
        if chunker:
            collection_size = chunker.collection.count()
            st.success(f"✅ {file_info['filename']} processed successfully! Collection size: {collection_size}")
            return True
        else:
            st.error(f"❌ Chunking failed for {file_info['filename']}: {message}")
            return False
    except Exception as e:
        st.error(f"❌ PDF processing error: {str(e)}")
        return False


def _render_batch_summary(successful: int, failed: int, total: int, base_output_dir: str):
    """Render the batch processing summary."""
    st.header("📊 Batch Processing Summary")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("✅ Successful", successful)
    with col2:
        st.metric("❌ Failed", failed)
    with col3:
        st.metric("📁 Total", total)
    
    if successful > 0:
        st.success(f"🎉 Batch processing completed! {successful} documents processed.")
        st.info("💡 PDFs are now in the knowledge base. Excel files are registered for premium calculations!")
        
        # Clean up temp extraction directory after successful batch processing (product-specific)
        if st.session_state.product_name:
            temp_extract_dir = os.path.join(base_output_dir, "temp", st.session_state.product_name, "extracted")
            if os.path.exists(temp_extract_dir):
                try:
                    shutil.rmtree(temp_extract_dir)
                    st.caption("🧹 Cleaned up temporary extraction folder")
                except Exception as e:
                    st.caption(f"⚠️ Note: Could not clean temp folder: {str(e)}")
    
    if failed > 0:
        st.warning(f"⚠️ {failed} documents failed to process. Check the logs above for details.")


def handle_zip_upload_detection(uploaded_zip, base_output_dir: str):
    """
    Detect new ZIP uploads and reset session state accordingly.
    
    Args:
        uploaded_zip: Uploaded ZIP file from Streamlit
        base_output_dir: Base output directory path
    """
    if uploaded_zip is not None:
        current_zip_name = uploaded_zip.name
        if 'last_uploaded_zip' not in st.session_state or st.session_state.last_uploaded_zip != current_zip_name:
            # New ZIP file detected - reset session state
            st.session_state.last_uploaded_zip = current_zip_name
            st.session_state.uploaded_files_list = []
            st.session_state.file_labels = {}
            st.session_state.labeling_complete = False
            
            # Clean up previous extraction folder (product-specific)
            if st.session_state.product_name:
                temp_extract_dir = os.path.join(base_output_dir, "temp", st.session_state.product_name, "extracted")
                if os.path.exists(temp_extract_dir):
                    try:
                        shutil.rmtree(temp_extract_dir)
                    except Exception as e:
                        pass  # Silently fail, will try again during extraction
