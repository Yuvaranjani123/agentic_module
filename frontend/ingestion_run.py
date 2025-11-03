import streamlit as st
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

# Import modularized services
from services.api_client import APIClient
from services.ingestion_pipeline import IngestionPipeline
from services.file_manager import FileManager

# Import UI components
from components.ingestion.file_uploader import (
    render_product_config,
    render_upload_mode_selector,
    render_single_file_uploader,
    render_azure_openai_status,
    render_chunking_info
)
from components.ingestion.pdf_processor import (
    render_pdf_upload_workflow,
    render_workflow_overview
)
from components.ingestion.zip_processor import (
    render_zip_upload_workflow,
    handle_zip_upload_detection
)

# For backward compatibility with existing UI code
DJANGO_API = os.getenv("API_BASE")


@st.cache_resource
def get_cached_chunker_embedder(chroma_db_dir: str, output_dir: str, doc_type: str = "unknown", doc_name: str = "unknown"):
    """Cached function to call Django API for chunking and embedding."""
    try:
        api_client = APIClient()
        result = api_client.chunk_and_embed(output_dir, chroma_db_dir, doc_type, doc_name)
        return result
    except Exception as e:
        return {"success": False, "error": f"Error during chunking and embedding: {str(e)}"}


class StreamlitRAGPipeline:
    """
    Wrapper class for backward compatibility with existing UI code.
    Delegates to modularized services.
    """
    def __init__(self, base_output_dir: str = None):
        self.pdf_path = None
        self.pdf_name = None
        self.base_output_dir = base_output_dir
        self.output_dir = None
        self.chroma_db_dir = None
        self.has_tables_flag = False
        self.table_count = 0
        
        # Initialize modularized services
        self.api_client = APIClient()
        self.file_manager = FileManager(base_output_dir)
        self.pipeline = IngestionPipeline(self.api_client, self.file_manager, base_output_dir)
        
    def clean_pdf_name(self, pdf_path: str) -> str:
        """Clean PDF filename to create valid folder name."""
        return self.file_manager.clean_filename(pdf_path)
    
    def setup_directories(self, pdf_path: str, base_output_dir: str):
        """Setup directory structure for the pipeline."""
        self.pdf_path = pdf_path
        self.pdf_name = self.clean_pdf_name(pdf_path)
        self.base_output_dir = base_output_dir
        
        # Use product-based organization for both output files and ChromaDB
        # Product name must be provided in session state
        product_name = st.session_state.get('product_name', '')
        if not product_name or not product_name.strip():
            raise ValueError("Product name is required. Please enter a product database name.")
        
        # Use pipeline's setup_directories method
        dirs = self.pipeline.setup_directories(pdf_path, product_name, base_output_dir)
        self.output_dir = dirs['output_dir']
        self.chroma_db_dir = dirs['chroma_db_dir']
        
    def analyze_pdf_content(self) -> dict:
        """Analyze PDF to detect tables and get basic stats."""
        result = self.pipeline.analyze_pdf(self.pdf_path)
        
        if 'error' not in result:
            self.has_tables_flag = result['has_tables']
            self.table_count = result['table_count']
        
        return {
            "has_tables": result.get('has_tables', False),
            "table_count": result.get('table_count', 0),
            "total_pages": result.get('total_pages', 0),
            "tables_per_page": round(result.get('table_count', 0) / result.get('total_pages', 1), 2) if result.get('total_pages', 0) > 0 else 0
        }
    
    def check_existing_extractions(self) -> dict:
        """Check what extractions already exist."""
        return self.file_manager.check_existing_extractions(self.output_dir)
    
    def check_manual_review_status(self) -> bool:
        """Check if manual review has been completed."""
        return self.file_manager.check_manual_review_status(self.output_dir)
    
    def mark_review_completed(self):
        """Mark manual review as completed."""
        self.file_manager.mark_review_completed(self.output_dir)
    
    def extract_tables(self, force_reextract=False):
        """Extract tables from PDF."""
        return self.pipeline.extract_tables(self.pdf_path, self.output_dir, force_reextract)
    
    def extract_text_content(self, force_reextract=False):
        """Extract text content from PDF."""
        return self.pipeline.extract_text_content(self.pdf_path, self.output_dir, force_reextract)
    
    def load_table_mapping(self):
        """Load the table file mapping."""
        return self.file_manager.load_table_mapping(self.output_dir)
    
    def save_table_mapping(self, df):
        """Save the updated table file mapping."""
        self.file_manager.save_table_mapping(self.output_dir, df)
    
    def get_extracted_tables(self):
        """Get list of extracted table files."""
        return self.file_manager.get_extracted_tables(self.output_dir)
    
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
            return None, result.get("error", "Unknown error")


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
    
    # Auto-detect output directory (define early for use throughout)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)  # Go up from frontend to project root
    base_output_dir = os.path.join(project_root, "media", "output")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Use modularized UI components
        product_name = render_product_config()
        st.divider()
        
        upload_mode = render_upload_mode_selector()
        
        # File Upload
        if upload_mode == "Single PDF":
            uploaded_file = st.file_uploader(
                "Upload PDF Document",
                type=['pdf'],
                help="Upload the PDF document you want to process"
            )
            
            # Document Type Selection (for single file)
            if uploaded_file:
                from components.ingestion.file_uploader import render_doc_type_selector
                selected_doc_type = render_doc_type_selector()
        else:
            from components.ingestion.file_uploader import render_zip_file_uploader
            uploaded_zip = render_zip_file_uploader()
            
            # Detect if a new ZIP file is uploaded and reset session state
            handle_zip_upload_detection(uploaded_zip, base_output_dir)
            
            uploaded_file = None  # Will handle ZIP separately
            selected_doc_type = "unknown"  # Will be set per file during labeling
        
        # Use modularized UI components for chunking info and Azure status
        render_chunking_info()
        render_azure_openai_status()
    
    # Main content area
    if upload_mode == "Multiple PDFs (ZIP)" and 'uploaded_zip' in locals() and uploaded_zip is not None:
        # Use modularized ZIP processing component
        render_zip_upload_workflow(pipeline, uploaded_zip, base_output_dir, DJANGO_API)
    
    elif uploaded_file is not None:
        # Use modularized PDF processing component
        render_pdf_upload_workflow(pipeline, uploaded_file, selected_doc_type, base_output_dir)
    
    else:
        # Use modularized workflow overview component
        render_workflow_overview()


if __name__ == "__main__":
    main()