"""
File Uploader Component

Streamlit UI component for file uploads and product configuration.
"""
import streamlit as st
import os
from typing import Optional, Dict


def render_product_config() -> str:
    """
    Render product database name configuration.
    
    Returns:
        Cleaned product name or empty string
        
    Example:
        >>> product_name = render_product_config()
        >>> if product_name:
        ...     st.success(f"Using product: {product_name}")
    """
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
        return clean_product_name
    else:
        st.session_state.product_name = ""
        st.error("❌ Product name is required to proceed")
        return ""


def render_upload_mode_selector() -> str:
    """
    Render upload mode selection.
    
    Returns:
        Selected upload mode string
        
    Example:
        >>> mode = render_upload_mode_selector()
        >>> mode
        'Single File (PDF/Excel)'
    """
    st.subheader("📤 Upload Mode")
    upload_mode = st.radio(
        "Choose upload mode:",
        ["Single File (PDF/Excel)", "Multiple PDFs (ZIP)"],
        help="Upload one file (PDF or Excel) or a ZIP containing multiple PDFs"
    )
    return upload_mode


def render_single_file_uploader(product_name: str) -> Optional[Dict]:
    """
    Render single file uploader (PDF or Excel).
    
    Args:
        product_name: Product database name
        
    Returns:
        Dict with uploaded_file, file_type, doc_type, or None
        
    Example:
        >>> file_info = render_single_file_uploader("ActivAssure")
        >>> if file_info:
        ...     print(f"File type: {file_info['file_type']}")
    """
    uploaded_file = st.file_uploader(
        "Upload Document",
        type=['pdf', 'xlsx', 'xls'],
        help="Upload PDF document or Excel premium rate file"
    )
    
    if not uploaded_file:
        return None
    
    file_extension = os.path.splitext(uploaded_file.name)[1].lower()
    
    # Handle Excel files (premium rates)
    if file_extension in ['.xlsx', '.xls']:
        st.info("📊 **Excel file detected** - This will be uploaded as a premium rate workbook")
        st.caption(f"Product: **{product_name}**")
        
        if not product_name:
            st.error("⚠️ Please enter a Product Name first to associate this premium workbook")
            return None
        
        return {
            "uploaded_file": uploaded_file,
            "file_type": "excel",
            "doc_type": "premium_excel"
        }
    
    # Handle PDF files
    elif file_extension == '.pdf':
        doc_type = render_doc_type_selector()
        return {
            "uploaded_file": uploaded_file,
            "file_type": "pdf",
            "doc_type": doc_type
        }
    
    else:
        st.error(f"❌ Unsupported file type: {file_extension}")
        return None


def render_doc_type_selector() -> str:
    """
    Render document type selector for PDF files.
    
    Returns:
        Selected document type string
        
    Example:
        >>> doc_type = render_doc_type_selector()
        >>> doc_type
        'policy'
    """
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
            doc_type = custom_doc_type.strip().lower().replace(' ', '-')
        else:
            doc_type = "custom"
            if 'custom_type_warning_shown' not in st.session_state:
                st.warning("⚠️ Please enter a custom document type")
                st.session_state.custom_type_warning_shown = True
    else:
        doc_type = doc_type_options[selected_doc_type_label]
        if 'custom_type_warning_shown' in st.session_state:
            del st.session_state.custom_type_warning_shown
    
    return doc_type


def render_zip_file_uploader() -> Optional[object]:
    """
    Render ZIP file uploader.
    
    Returns:
        Uploaded ZIP file object or None
        
    Example:
        >>> zip_file = render_zip_file_uploader()
        >>> if zip_file:
        ...     print(f"Uploaded: {zip_file.name}")
    """
    uploaded_zip = st.file_uploader(
        "Upload ZIP File",
        type=['zip'],
        help="Upload a ZIP file containing multiple PDF documents"
    )
    
    return uploaded_zip


def render_azure_openai_status():
    """
    Render Azure OpenAI configuration status.
    
    Example:
        >>> render_azure_openai_status()
        # Shows ✅ or ❌ based on env configuration
    """
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


def render_chunking_info():
    """
    Render chunking configuration information.
    
    Example:
        >>> render_chunking_info()
        # Displays chunking features and details
    """
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
