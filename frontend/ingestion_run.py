import streamlit as st
import os
import sys
import re
from pathlib import Path
import pandas as pd
import time
from datetime import datetime
import pdfplumber
import requests
from dotenv import load_dotenv
import zipfile
import tempfile
import shutil

# Load environment variables from .env file
load_dotenv()

# Add current directory to path
sys.path.append(str(Path(__file__).parent))
DJANGO_API = os.getenv("API_BASE")


@st.cache_resource
def get_cached_chunker_embedder(chroma_db_dir: str, output_dir: str, doc_type: str = "unknown", doc_name: str = "unknown"):
    """Cached function to call Django API for chunking and embedding."""
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        # Call Django API for chunking and embedding
        resp = requests.post(
            f"{DJANGO_API}/api/chunk_and_embed/",
            json={"output_dir": output_dir, "chroma_db_dir": chroma_db_dir, "doc_type": doc_type, "doc_name": doc_name}
        )
        
        if resp.status_code == 200:
            result = resp.json()
            return {"success": True, "message": result.get("message"), "collection_size": result.get("collection_size")}
        else:
            error_msg = resp.json().get("error", "Unknown error") if resp.headers.get('content-type') == 'application/json' else resp.text
            return {"success": False, "error": error_msg}
        
    except Exception as e:
        return {"success": False, "error": f"Error during chunking and embedding: {str(e)}"}


class StreamlitRAGPipeline:
    def __init__(self):
        self.pdf_path = None
        self.pdf_name = None
        self.base_output_dir = None
        self.output_dir = None
        self.chroma_db_dir = None
        self.has_tables_flag = False
        self.table_count = 0
        
    def clean_pdf_name(self, pdf_path: str) -> str:
        """Clean PDF filename to create valid folder name."""
        filename = Path(pdf_path).stem
        cleaned = re.sub(r'[<>:"/\\|?*]', '_', filename)
        cleaned = re.sub(r'[_\s]+', '_', cleaned)
        cleaned = cleaned.strip('_')
        if len(cleaned) > 50:
            cleaned = cleaned[:50].rstrip('_')
        return cleaned if cleaned else "unnamed_pdf"
    
    def setup_directories(self, pdf_path: str, base_output_dir: str):
        """Setup directory structure for the pipeline."""
        self.pdf_path = pdf_path
        self.pdf_name = self.clean_pdf_name(pdf_path)
        self.base_output_dir = base_output_dir
        self.output_dir = os.path.join(base_output_dir, self.pdf_name)
        
        # Use unified ChromaDB database for all documents (product-based)
        # Product name must be provided in session state
        product_name = st.session_state.get('product_name', '')
        if not product_name or not product_name.strip():
            raise ValueError("Product name is required. Please enter a product database name.")
        self.chroma_db_dir = os.path.join(base_output_dir, "chroma_db", product_name)
        
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.chroma_db_dir, exist_ok=True)
        
    def analyze_pdf_content(self) -> dict:
        """Analyze PDF to detect tables and get basic stats."""
        table_count = 0
        total_pages = 0
        
        with pdfplumber.open(self.pdf_path) as pdf:
            total_pages = len(pdf.pages)
            for page in pdf.pages:
                tables = page.find_tables(
                    table_settings={
                        "vertical_strategy": "lines", 
                        "horizontal_strategy": "lines", 
                        "snap_tolerance": 3
                    }
                )
                table_count += len(tables)
        
        self.has_tables_flag = table_count > 0
        self.table_count = table_count
        
        return {
            "has_tables": self.has_tables_flag,
            "table_count": table_count,
            "total_pages": total_pages,
            "tables_per_page": round(table_count / total_pages, 2) if total_pages > 0 else 0
        }
    
    def check_existing_extractions(self) -> dict:
        """Check what extractions already exist."""
        if not os.path.exists(self.output_dir):
            return {"has_table_map": False, "has_text_files": False, "has_csv_files": False, 
                   "text_file_count": 0, "csv_file_count": 0}
            
        table_map_path = os.path.join(self.output_dir, "table_file_map.csv")
        text_files = [f for f in os.listdir(self.output_dir) if f.endswith("_text.txt")]
        csv_files = [f for f in os.listdir(self.output_dir) if f.endswith(".csv") and f != "table_file_map.csv"]
        
        return {
            "has_table_map": os.path.exists(table_map_path),
            "has_text_files": len(text_files) > 0,
            "has_csv_files": len(csv_files) > 0,
            "text_file_count": len(text_files),
            "csv_file_count": len(csv_files)
        }
    
    def check_manual_review_status(self) -> bool:
        """Check if manual review has been completed."""
        marker_file = os.path.join(self.output_dir, ".manual_review_completed")
        return os.path.exists(marker_file)
    
    def mark_review_completed(self):
        """Mark manual review as completed."""
        marker_file = os.path.join(self.output_dir, ".manual_review_completed")
        table_map_path = os.path.join(self.output_dir, "table_file_map.csv")
        
        with open(marker_file, 'w') as f:
            timestamp = os.path.getmtime(table_map_path) if os.path.exists(table_map_path) else time.time()
            f.write(f"Manual review completed at {timestamp}")
    
    def extract_tables(self, force_reextract=False):
        existing = self.check_existing_extractions()
        if existing["has_csv_files"] and not force_reextract:
            return False, f"Found existing table extractions ({existing['csv_file_count']} CSV files)"

        resp = requests.post(
            f"{DJANGO_API}/api/extract_tables/",
            json={"pdf_path": self.pdf_path, "output_dir": self.output_dir}
        )
        if resp.status_code == 200:
            return True, resp.json().get("message")
        return False, resp.json().get("error", "Unknown error")
    
    def extract_text_content(self, force_reextract=False):
        existing = self.check_existing_extractions()
        if existing["has_text_files"] and not force_reextract:
            return False, f"Found existing text extractions ({existing['text_file_count']} text files)"

        resp = requests.post(
            f"{DJANGO_API}/api/extract_text/",
            json={"pdf_path": self.pdf_path, "output_dir": self.output_dir}
        )
        if resp.status_code == 200:
            return True, resp.json().get("message")
        return False, resp.json().get("error", "Unknown error")
    
    def load_table_mapping(self):
        """Load the table file mapping."""
        table_map_path = os.path.join(self.output_dir, "table_file_map.csv")
        if os.path.exists(table_map_path):
            return pd.read_csv(table_map_path)
        return pd.DataFrame()
    
    def save_table_mapping(self, df):
        """Save the updated table file mapping."""
        table_map_path = os.path.join(self.output_dir, "table_file_map.csv")
        df.to_csv(table_map_path, index=False)
    
    def get_extracted_tables(self):
        """Get list of extracted table files."""
        if not os.path.exists(self.output_dir):
            return []
        return [f for f in os.listdir(self.output_dir) if f.endswith(".csv") and f != "table_file_map.csv"]
    
    def chunk_and_embed(self, doc_type: str = "unknown"):
        """Run chunking and embedding process via Django API."""
        result = get_cached_chunker_embedder(self.chroma_db_dir, self.output_dir, doc_type, self.pdf_name)
        
        if result["success"]:
            # Create a mock chunker object to maintain compatibility
            class MockChunker:
                def __init__(self, collection_size):
                    self.collection_size = collection_size
                    
                @property
                def collection(self):
                    class MockCollection:
                        def __init__(self, size):
                            self._size = size
                        def count(self):
                            return self._size
                    return MockCollection(self.collection_size)
            
            chunker = MockChunker(result.get("collection_size", 0))
            return chunker, result["message"]
        else:
            return None, result["error"]


def main():
    st.set_page_config(
        page_title="Simple RAG Pipeline",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("📚 Simple RAG Pipeline")
    st.markdown("**Intelligent PDF Processing with Table Detection and Human-in-the-Loop Review**")
    
    # Initialize session state
    if 'pipeline' not in st.session_state:
        st.session_state.pipeline = StreamlitRAGPipeline()
    if 'analysis_complete' not in st.session_state:
        st.session_state.analysis_complete = False
    if 'extraction_complete' not in st.session_state:
        st.session_state.extraction_complete = False
    if 'review_complete' not in st.session_state:
        st.session_state.review_complete = False
    if 'chunker_embedder' not in st.session_state:
        st.session_state.chunker_embedder = None
    if 'embedding_complete' not in st.session_state:
        st.session_state.embedding_complete = False
    if 'uploaded_files_list' not in st.session_state:
        st.session_state.uploaded_files_list = []
    if 'file_labels' not in st.session_state:
        st.session_state.file_labels = {}
    if 'labeling_complete' not in st.session_state:
        st.session_state.labeling_complete = False
    
    pipeline = st.session_state.pipeline
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Product/Database Name Configuration
        st.subheader("🏷️ Product Database Name")
        if 'product_name' not in st.session_state:
            st.session_state.product_name = ""
        
        product_name = st.text_input(
            "Database Name: *",
            value=st.session_state.product_name,
            help="Required: Enter the product/database name (e.g., 'ActivAssure', 'HealthShield'). All documents will be stored in this unified database.",
            placeholder="Enter product name (required)"
        )
        
        if product_name and product_name.strip():
            # Clean the product name (remove spaces, special chars)
            clean_product_name = product_name.strip().replace(' ', '_')
            st.session_state.product_name = clean_product_name
            st.caption(f"💾 Documents will be stored in: `chroma_db/{clean_product_name}/`")
        else:
            st.session_state.product_name = ""
            st.error("❌ Product name is required to proceed")
        
        st.divider()
        
        # Upload mode selection
        st.subheader("📤 Upload Mode")
        upload_mode = st.radio(
            "Choose upload mode:",
            ["Single PDF", "Multiple PDFs (ZIP)"],
            help="Upload one PDF or a ZIP containing multiple PDFs"
        )
        
        # File Upload
        if upload_mode == "Single PDF":
            uploaded_file = st.file_uploader(
                "Upload PDF Document",
                type=['pdf'],
                help="Upload the PDF document you want to process"
            )
            
            # Document Type Selection (for single file)
            if uploaded_file:
                st.subheader("🏷️ Document Type")
                doc_type_options = {
                    "Policy Document": "policy",
                    "Brochure": "brochure", 
                    "Prospectus": "prospectus",
                    "Terms & Conditions": "terms",
                    "Other (Custom)": "custom"
                }
                selected_doc_type_label = st.selectbox(
                    "Select Document Type",
                    options=list(doc_type_options.keys()),
                    help="Choose the type of document for better categorization and filtering"
                )
                
                # If "Other (Custom)" is selected, show text input
                if selected_doc_type_label == "Other (Custom)":
                    custom_doc_type = st.text_input(
                        "Enter custom document type",
                        placeholder="e.g., claim-form, certificate, addendum",
                        help="Enter a custom document type (lowercase, use hyphens for spaces)"
                    )
                    if custom_doc_type and custom_doc_type.strip():
                        selected_doc_type = custom_doc_type.strip().lower().replace(' ', '-')
                    else:
                        selected_doc_type = "custom"
                        if 'custom_type_warning_shown' not in st.session_state:
                            st.warning("⚠️ Please enter a custom document type")
                            st.session_state.custom_type_warning_shown = True
                else:
                    selected_doc_type = doc_type_options[selected_doc_type_label]
                    if 'custom_type_warning_shown' in st.session_state:
                        del st.session_state.custom_type_warning_shown
        else:
            uploaded_zip = st.file_uploader(
                "Upload ZIP File",
                type=['zip'],
                help="Upload a ZIP file containing multiple PDF documents"
            )
            uploaded_file = None  # Will handle ZIP separately
            selected_doc_type = "unknown"  # Will be set per file during labeling
        
        # Auto-detect output directory (hidden from user)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)  # Go up from frontend to project root
        base_output_dir = os.path.join(project_root, "media", "output")
        
        # Chunking Configuration
        st.subheader("🧩 Enhanced Chunking")
        st.info("""
        **New Features:**
        - ✅ **Semantic Chunking**: AI-powered content-aware splitting
        - ✅ **Context Overlap**: Maintains continuity between chunks
        - ✅ **Document Type Detection**: Insurance-specific processing
        - ✅ **Evaluation Metrics**: Quality assessment included
        """)
        
        with st.expander("📊 Chunking Details"):
            st.write("""
            - **Overlap Strategy**: 2-sentence overlap for context continuity
            - **Semantic Threshold**: 0.75 similarity for boundary detection  
            - **Max Chunk Size**: 1000 characters with intelligent splitting
            - **Domain-Aware**: Optimized for insurance documents
            """)
        
        # Azure OpenAI Status
        st.subheader("🔑 Azure OpenAI Status")
        from dotenv import load_dotenv
        load_dotenv()
        
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        api_key = os.getenv("AZURE_OPENAI_KEY")
        
        if endpoint and api_key:
            st.success("✅ Credentials configured")
            st.write(f"**Endpoint:** {endpoint[:30]}...")
        else:
            st.error("❌ Credentials missing")
            st.write("Please set up your .env file")
    
    # Main content area
    if upload_mode == "Multiple PDFs (ZIP)" and 'uploaded_zip' in locals() and uploaded_zip is not None:
        # Handle ZIP file upload
        st.header("📦 ZIP File Processing")
        
        # Extract ZIP file
        if not st.session_state.uploaded_files_list:
            with st.spinner("Extracting ZIP file..."):
                temp_extract_dir = os.path.join(base_output_dir, "temp", "extracted")
                os.makedirs(temp_extract_dir, exist_ok=True)
                
                # Save ZIP temporarily
                temp_zip_path = os.path.join(base_output_dir, "temp", uploaded_zip.name)
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
        
        # Display labeling interface
        if st.session_state.uploaded_files_list:
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
        
        # Show processing options after labeling
        if st.session_state.labeling_complete:
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
                                    st.write("⏳ Uploading Excel workbook to premium calculator registry...")
                                    
                                    # Upload to premium registry via API
                                    with open(file_info['full_path'], 'rb') as f:
                                        files = {'excel': (file_info['filename'], f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
                                        data = {'doc_name': os.path.splitext(file_info['filename'])[0]}
                                        
                                        response = requests.post(
                                            f"{DJANGO_API}/api/upload_premium_excel/",
                                            files=files,
                                            data=data,
                                            timeout=30
                                        )
                                        
                                        if response.status_code == 200:
                                            result = response.json()
                                            st.success(f"✅ {file_info['filename']} uploaded to premium registry!")
                                            st.write(f"**Registry Path:** `{result.get('filename', 'N/A')}`")
                                            successful += 1
                                        else:
                                            error_msg = response.json().get('error', 'Unknown error')
                                            st.error(f"❌ Upload failed: {error_msg}")
                                            failed += 1
                                
                                # Handle PDF files
                                else:
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
                                        successful += 1
                                    else:
                                        st.error(f"❌ Chunking failed for {file_info['filename']}: {message}")
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
                st.header("📊 Batch Processing Summary")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("✅ Successful", successful)
                with col2:
                    st.metric("❌ Failed", failed)
                with col3:
                    st.metric("📁 Total", len(files_to_process))
                
                if successful > 0:
                    st.success(f"🎉 Batch processing completed! {successful} documents processed.")
                    st.info("💡 PDFs are now in the knowledge base. Excel files are registered for premium calculations!")
                
                if failed > 0:
                    st.warning(f"⚠️ {failed} documents failed to process. Check the logs above for details.")
    
    elif uploaded_file is not None:
        # Check if product name is provided
        if not st.session_state.product_name or not st.session_state.product_name.strip():
            st.error("❌ Please enter a Product Database Name in the sidebar before processing")
            st.stop()
        
        # Save uploaded file temporarily
        temp_pdf_path = os.path.join(base_output_dir, "temp", uploaded_file.name)
        os.makedirs(os.path.dirname(temp_pdf_path), exist_ok=True)
        
        with open(temp_pdf_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        pipeline.setup_directories(temp_pdf_path, base_output_dir)
        
        # Display file info
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📄 PDF File", uploaded_file.name)
        with col2:
            st.metric("📁 Output Folder", pipeline.pdf_name)
        with col3:
            st.metric("💾 File Size", f"{uploaded_file.size / 1024:.1f} KB")
        
        st.divider()
        
        # Step 1: PDF Analysis
        st.header("🔍 Step 1: PDF Analysis")
        
        if st.button("Analyze PDF Content", type="primary"):
            with st.spinner("Analyzing PDF content..."):
                analysis = pipeline.analyze_pdf_content()
                st.session_state.analysis_complete = True
                st.session_state.analysis_result = analysis
        
        if st.session_state.analysis_complete:
            analysis = st.session_state.analysis_result
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📖 Total Pages", analysis["total_pages"])
            with col2:
                st.metric("📊 Tables Found", analysis["table_count"])
            with col3:
                st.metric("📈 Tables/Page", analysis["tables_per_page"])
            with col4:
                workflow = "Table Workflow" if analysis["has_tables"] else "Text-Only Workflow"
                st.metric("⚙️ Workflow", workflow)
            
            if analysis["has_tables"]:
                st.success(f"✅ {analysis['table_count']} tables detected - Using table extraction workflow")
            else:
                st.info("ℹ️ No tables detected - Using text-only extraction")
            
            st.divider()
            
            # Step 2: Content Extraction
            st.header("📤 Step 2: Content Extraction")
            
            existing = pipeline.check_existing_extractions()
            
            if existing["has_csv_files"] or existing["has_text_files"]:
                st.warning("⚠️ Existing extractions found!")
                col1, col2 = st.columns(2)
                with col1:
                    if existing["has_csv_files"]:
                        st.write(f"📊 {existing['csv_file_count']} CSV files (tables)")
                with col2:
                    if existing["has_text_files"]:
                        st.write(f"📄 {existing['text_file_count']} text files")
            
            col1, col2 = st.columns(2)
            
            with col1:
                force_table_reextract = st.checkbox("Force re-extract tables", value=False)
                if st.button("Extract Tables", disabled=not analysis["has_tables"]):
                    with st.spinner("Extracting tables..."):
                        success, message = pipeline.extract_tables(force_table_reextract)
                        if success:
                            st.success(message)
                        else:
                            st.info(message)
                        
                        # Check if we need to refresh extraction status
                        st.session_state.extraction_complete = True
            
            with col2:
                force_text_reextract = st.checkbox("Force re-extract text", value=False)
                if st.button("Extract Text"):
                    with st.spinner("Extracting text..."):
                        success, message = pipeline.extract_text_content(force_text_reextract)
                        if success:
                            st.success(message)
                        else:
                            st.info(message)
                        
                        st.session_state.extraction_complete = True
            
            # Step 3: Human Review (for tables)
            if analysis["has_tables"]:
                st.divider()
                st.header("👤 Step 3: Human Review (Tables)")
                
                review_completed = pipeline.check_manual_review_status()
                
                if review_completed:
                    st.success("✅ Manual review already completed")
                    st.session_state.review_complete = True
                else:
                    table_mapping = pipeline.load_table_mapping()
                    extracted_tables = pipeline.get_extracted_tables()
                    
                    if not table_mapping.empty:
                        st.subheader("📊 Table File Mapping")
                        
                        # Option to upload custom table mapping CSV
                        with st.expander("📤 Upload Custom Table Mapping (Optional)"):
                            st.write("Upload a CSV file with your own table mapping configuration:")
                            st.write("**Required columns:** `page_num`, `table_idx`, `table_filename`")
                            
                            uploaded_mapping = st.file_uploader(
                                "Choose table mapping CSV file",
                                type=['csv'],
                                key="table_mapping_upload",
                                help="Upload a CSV with columns: page_num, table_idx, table_filename"
                            )
                            
                            if uploaded_mapping is not None:
                                try:
                                    uploaded_df = pd.read_csv(uploaded_mapping)
                                    
                                    # Validate required columns
                                    required_cols = ['page_num', 'table_idx', 'table_filename']
                                    missing_cols = [col for col in required_cols if col not in uploaded_df.columns]
                                    
                                    if missing_cols:
                                        st.error(f"❌ Missing required columns: {missing_cols}")
                                        st.write("**Current columns:**", list(uploaded_df.columns))
                                    else:
                                        st.success("✅ Valid table mapping CSV uploaded!")
                                        st.write("**Preview of uploaded mapping:**")
                                        st.dataframe(uploaded_df.head(), width='stretch')
                                        
                                        col1, col2 = st.columns(2)
                                        with col1:
                                            if st.button("🔄 Use Uploaded Mapping", key="use_uploaded"):
                                                table_mapping = uploaded_df.copy()
                                                pipeline.save_table_mapping(table_mapping)
                                                st.success("Table mapping updated with uploaded file!")
                                                st.rerun()
                                        
                                        with col2:
                                            if st.button("📋 Merge with Existing", key="merge_uploaded"):
                                                # Merge logic: update existing entries, add new ones
                                                merged_mapping = table_mapping.copy()
                                                for _, row in uploaded_df.iterrows():
                                                    mask = ((merged_mapping['page_num'] == row['page_num']) & 
                                                           (merged_mapping['table_idx'] == row['table_idx']))
                                                    if mask.any():
                                                        merged_mapping.loc[mask, 'table_filename'] = row['table_filename']
                                                    else:
                                                        merged_mapping = pd.concat([merged_mapping, pd.DataFrame([row])], ignore_index=True)
                                                
                                                table_mapping = merged_mapping
                                                pipeline.save_table_mapping(table_mapping)
                                                st.success("Table mapping merged with uploaded file!")
                                                st.rerun()
                                        
                                except Exception as e:
                                    st.error(f"❌ Error reading CSV file: {str(e)}")
                                    st.write("Please ensure the CSV file is properly formatted.")
                        
                        st.write("Review and edit the table filenames if needed:")
                        
                        # Editable table mapping
                        edited_mapping = st.data_editor(
                            table_mapping,
                            # width='stretch',
                            num_rows="fixed",
                            disabled=["page_num", "table_idx"],
                            key="table_mapping_editor"
                        )
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            if st.button("💾 Save Mapping"):
                                pipeline.save_table_mapping(edited_mapping)
                                st.success("Table mapping saved!")
                        
                        with col2:
                            if st.button("✅ Complete Review"):
                                pipeline.save_table_mapping(edited_mapping)
                                pipeline.mark_review_completed()
                                st.success("Review marked as complete!")
                                st.session_state.review_complete = True
                                st.rerun()
                        
                        with col3:
                            if st.button("📄 Switch to Text-Only"):
                                pipeline.has_tables_flag = False
                                st.info("Switched to text-only mode")
                        
                        # Display extracted table files
                        if extracted_tables:
                            st.subheader("📁 Extracted Table Files")
                            for i, table_file in enumerate(extracted_tables):
                                with st.expander(f"📊 {table_file}"):
                                    try:
                                        df = pd.read_csv(os.path.join(pipeline.output_dir, table_file))
                                        st.dataframe(df.head(10), width='stretch')
                                        st.write(f"Shape: {df.shape[0]} rows × {df.shape[1]} columns")
                                    except Exception as e:
                                        st.error(f"Error reading file: {e}")
                    
                    else:
                        st.warning("⚠️ No table mapping found. Please extract tables first.")
            
            # Step 4: Chunking and Embedding
            if (not analysis["has_tables"]) or st.session_state.review_complete:
                st.divider()
                st.header("🧠 Step 4: Chunking & Embedding")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Output Directory:** `{pipeline.output_dir}`")
                with col2:
                    st.write(f"**ChromaDB Directory:** `{pipeline.chroma_db_dir}`")
                
                # Check extraction status and show warnings
                current_extractions = pipeline.check_existing_extractions()
                
                # Warning system for missing extractions
                warnings_displayed = False
                
                if analysis["has_tables"] and not current_extractions["has_csv_files"]:
                    st.warning("⚠️ **Tables detected but not extracted!** Please extract tables in Step 2 before chunking.")
                    warnings_displayed = True
                
                if not current_extractions["has_text_files"]:
                    st.warning("⚠️ **No text files found!** Please extract text in Step 2 before chunking.")
                    warnings_displayed = True
                
                if analysis["has_tables"] and current_extractions["has_csv_files"] and not current_extractions["has_text_files"]:
                    st.error("🚨 **Critical:** Only tables extracted, no text content! Both text and tables should be included for comprehensive RAG.")
                    warnings_displayed = True
                
                # Show extraction status summary
                if current_extractions["has_text_files"] or current_extractions["has_csv_files"]:
                    st.subheader("📋 Extraction Status Summary")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if current_extractions["has_text_files"]:
                            st.success(f"✅ Text: {current_extractions['text_file_count']} files")
                        else:
                            st.error("❌ Text: Not extracted")
                    
                    with col2:
                        if analysis["has_tables"]:
                            if current_extractions["has_csv_files"]:
                                st.success(f"✅ Tables: {current_extractions['csv_file_count']} files")
                            else:
                                st.error("❌ Tables: Not extracted")
                        else:
                            st.info("➖ Tables: None detected")
                    
                    with col3:
                        if analysis["has_tables"]:
                            review_status = "✅ Complete" if st.session_state.review_complete else "⏳ Pending"
                            st.write(f"**Review:** {review_status}")
                        else:
                            st.info("**Review:** Not needed")
                
                # Show what will be included in chunking
                if current_extractions["has_text_files"] or current_extractions["has_csv_files"]:
                    with st.expander("� Content to be Chunked", expanded=False):
                        st.write("**The following content will be included in chunking and embedding:**")
                        
                        if current_extractions["has_text_files"]:
                            st.write(f"📝 **Text Content:** {current_extractions['text_file_count']} text files")
                            text_files = [f for f in os.listdir(pipeline.output_dir) if f.endswith("_text.txt")]
                            for text_file in text_files[:3]:  # Show first 3 files
                                st.write(f"   • {text_file}")
                            if len(text_files) > 3:
                                st.write(f"   • ... and {len(text_files) - 3} more files")
                        
                        if current_extractions["has_csv_files"]:
                            st.write(f"📊 **Table Content:** {current_extractions['csv_file_count']} table files")
                            csv_files = [f for f in os.listdir(pipeline.output_dir) if f.endswith(".csv") and f != "table_file_map.csv"]
                            for csv_file in csv_files[:3]:  # Show first 3 files
                                st.write(f"   • {csv_file}")
                            if len(csv_files) > 3:
                                st.write(f"   • ... and {len(csv_files) - 3} more files")
                
                # Disable button if critical extractions are missing
                disable_chunking = False
                if not current_extractions["has_text_files"] and not current_extractions["has_csv_files"]:
                    st.error("🚫 **Cannot proceed:** No content extracted. Please complete Step 2 first.")
                    disable_chunking = True
                
                if st.button("🚀 Start Chunking & Embedding", type="primary", disabled=disable_chunking):
                    with st.spinner("Processing chunks and generating embeddings..."):
                        chunker, message = pipeline.chunk_and_embed(selected_doc_type)
                        
                        if chunker:
                            st.success(message)
                            # Store chunker in session state
                            st.session_state.chunker_embedder = chunker
                            st.session_state.embedding_complete = True
                            
                            # Display results
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("📊 Total Chunks", chunker.collection.count())
                            with col2:
                                # Count text chunks vs table chunks from metadata
                                st.metric("💾 Database", "ChromaDB")
                            with col3:
                                st.metric("✅ Status", "Complete")
                            
                        else:
                            st.error(message)
                
                # Step 5: Query Interface (show if embedding is complete)
                # if st.session_state.embedding_complete and st.session_state.chunker_embedder:
                #     st.divider()
                #     st.header("🔍 Step 5: Query Interface")
                    
                #     chunker = st.session_state.chunker_embedder
                    
                #     # Display embedding stats
                #     col1, col2, col3 = st.columns(3)
                #     with col1:
                #         st.metric("📊 Total Chunks", chunker.collection.count())
                #     with col2:
                #         st.metric("💾 Database", "ChromaDB")
                #     with col3:
                #         st.metric("✅ Status", "Ready for Search")
                    
                #     query = st.text_input(
                #         "Enter your query:",
                #         placeholder="e.g., insurance coverage benefits",
                #         key="query_input"
                #     )
                    
                #     col1, col2 = st.columns([3, 1])
                #     with col1:
                #         n_results = st.slider("Number of results", 1, 10, 3)
                #     with col2:
                #         filter_type = st.selectbox(
                #             "Filter by type",
                #             ["All", "text", "table_row", "table_header"]
                #         )
                    
                #     if st.button("🔎 Search") and query:
                #         filter_param = None if filter_type == "All" else filter_type
                        
                #         with st.spinner("Searching..."):
                #             results = chunker.query_similar(query, n_results, filter_param)
                            
                #             if results and results['documents'][0]:
                #                 st.subheader(f"📋 Search Results for: '{query}'")
                                
                #                 for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
                #                     with st.expander(f"Result {i+1} ({metadata['type']})"):
                #                         st.write("**Content:**")
                #                         st.write(doc[:500] + ("..." if len(doc) > 500 else ""))
                                        
                #                         st.write("**Metadata:**")
                #                         if metadata['type'] == 'text':
                #                             st.write(f"- Source: Page {metadata['page_num']}")
                #                             st.write(f"- File: {metadata['source_file']}")
                #                         elif metadata['type'] in ['table_row', 'table_header']:
                #                             st.write(f"- Source: {metadata['table_file']}")
                #                             if metadata['type'] == 'table_row':
                #                                 st.write(f"- Row: {metadata['row_idx']}")
                                        
                #                         if metadata.get('table_references'):
                #                             st.write(f"- References: {metadata['table_references']}")
                #             else:
                #                 st.warning("No results found for your query.")
    
    else:
        st.info("👆 Please upload a PDF file to get started")
        
        # Display sample workflow
        st.subheader("🔄 Workflow Overview")
        
        workflow_steps = [
            "📤 **Upload PDF** - Select your document",
            "🔍 **Analysis** - Detect tables and content structure", 
            "📊 **Extraction** - Extract tables and text content",
            "👤 **Review** - Human-in-the-loop table verification (if tables found)",
            "🧠 **Processing** - Chunk content and generate embeddings",
            "🔎 **Query** - Search and retrieve relevant information"
        ]
        
        for step in workflow_steps:
            st.markdown(step)


if __name__ == "__main__":
    main()