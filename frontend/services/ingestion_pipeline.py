"""
Ingestion Pipeline Service

Orchestrates the complete document ingestion workflow.
"""
from typing import Dict, Tuple, Optional
import os
import pdfplumber
from .api_client import APIClient
from .file_manager import FileManager


class IngestionPipeline:
    """
    Orchestrates the document ingestion workflow.
    
    Manages extraction, embedding, and processing of documents through the backend API.
    """
    
    def __init__(
        self, 
        api_client: Optional[APIClient] = None,
        file_manager: Optional[FileManager] = None,
        base_output_dir: str = None
    ):
        """
        Initialize ingestion pipeline.
        
        Args:
            api_client: Optional APIClient instance (creates default if not provided)
            file_manager: Optional FileManager instance
            base_output_dir: Base output directory
            
        Example:
            >>> pipeline = IngestionPipeline()
            >>> pipeline.extract_tables("/path/to/doc.pdf", "/path/to/output")
        """
        self.api_client = api_client or APIClient()
        self.file_manager = file_manager or FileManager(base_output_dir)
        self.base_output_dir = base_output_dir
    
    def extract_tables(
        self, 
        pdf_path: str, 
        output_dir: str, 
        force_reextract: bool = False
    ) -> Tuple[bool, str]:
        """
        Extract tables from PDF.
        
        Args:
            pdf_path: Path to PDF file
            output_dir: Directory for outputs
            force_reextract: Force re-extraction even if files exist
            
        Returns:
            Tuple of (success, message)
            
        Example:
            >>> pipeline = IngestionPipeline()
            >>> success, msg = pipeline.extract_tables("/path/to/doc.pdf", "/out")
            >>> success
            True
        """
        # Check existing extractions
        existing = self.file_manager.check_existing_extractions(output_dir)
        if existing["has_csv_files"] and not force_reextract:
            return False, f"Found existing table extractions ({existing['csv_file_count']} CSV files)"
        
        # Call API
        result = self.api_client.extract_tables(pdf_path, output_dir)
        if result["success"]:
            return True, result["message"]
        return False, result.get("error", "Unknown error")
    
    def extract_text_content(
        self, 
        pdf_path: str, 
        output_dir: str, 
        force_reextract: bool = False
    ) -> Tuple[bool, str]:
        """
        Extract text content from PDF.
        
        Args:
            pdf_path: Path to PDF file
            output_dir: Directory for outputs
            force_reextract: Force re-extraction even if files exist
            
        Returns:
            Tuple of (success, message)
            
        Example:
            >>> success, msg = pipeline.extract_text_content("/path/to/doc.pdf", "/out")
            >>> success
            True
        """
        # Check existing extractions
        existing = self.file_manager.check_existing_extractions(output_dir)
        if existing["has_text_files"] and not force_reextract:
            return False, f"Found existing text extractions ({existing['text_file_count']} text files)"
        
        # Call API
        result = self.api_client.extract_text(pdf_path, output_dir)
        if result["success"]:
            return True, result["message"]
        return False, result.get("error", "Unknown error")
    
    def chunk_and_embed(
        self, 
        output_dir: str, 
        chroma_db_dir: str, 
        doc_type: str = "unknown", 
        doc_name: str = "unknown"
    ) -> Tuple[Optional[object], str]:
        """
        Run chunking and embedding process.
        
        Args:
            output_dir: Directory containing extracted content
            chroma_db_dir: ChromaDB storage directory
            doc_type: Type of document
            doc_name: Name of document
            
        Returns:
            Tuple of (chunker_object, message)
            Chunker object has collection.count() method, or None on error
            
        Example:
            >>> chunker, msg = pipeline.chunk_and_embed(
            ...     output_dir="/path/to/output",
            ...     chroma_db_dir="/path/to/chroma",
            ...     doc_type="policy",
            ...     doc_name="ActivAssure"
            ... )
            >>> chunker.collection.count()
            150
        """
        result = self.api_client.chunk_and_embed(
            output_dir, chroma_db_dir, doc_type, doc_name
        )
        
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
    
    def upload_premium_excel(
        self, 
        file_path: str, 
        product_name: str, 
        filename: str
    ) -> Tuple[bool, str]:
        """
        Upload premium rate Excel file.
        
        Args:
            file_path: Path to Excel file
            product_name: Product/database name
            filename: Original filename
            
        Returns:
            Tuple of (success, message)
            
        Example:
            >>> success, msg = pipeline.upload_premium_excel(
            ...     file_path="/tmp/rates.xlsx",
            ...     product_name="ActivAssure",
            ...     filename="premium_rates.xlsx"
            ... )
            >>> success
            True
        """
        result = self.api_client.upload_premium_excel(file_path, product_name, filename)
        if result["success"]:
            return True, result["message"]
        return False, result.get("error", "Unknown error")
    
    def setup_directories(
        self, 
        pdf_path: str, 
        product_name: str, 
        base_output_dir: str = None
    ) -> Dict[str, str]:
        """
        Setup directory structure for ingestion.
        
        Args:
            pdf_path: Path to PDF file
            product_name: Product database name
            base_output_dir: Base output directory
            
        Returns:
            Dict with 'output_dir' and 'chroma_db_dir' paths
        """
        if base_output_dir is None:
            base_output_dir = self.base_output_dir
        
        pdf_name = self.file_manager.clean_filename(pdf_path)
        
        # Organize output under product name
        output_dir = os.path.join(base_output_dir, product_name, pdf_name)
        chroma_db_dir = os.path.join(base_output_dir, "chroma_db", product_name)
        
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(chroma_db_dir, exist_ok=True)
        
        return {
            'output_dir': output_dir,
            'chroma_db_dir': chroma_db_dir
        }
    
    def analyze_pdf(self, pdf_path: str) -> Dict:
        """
        Analyze PDF to detect tables and get basic stats.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dict with 'total_pages', 'table_count', 'has_tables'
        """
        table_count = 0
        total_pages = 0
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
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
        except Exception as e:
            return {
                'total_pages': 0,
                'table_count': 0,
                'has_tables': False,
                'error': str(e)
            }
        
        return {
            'total_pages': total_pages,
            'table_count': table_count,
            'has_tables': table_count > 0
        }
    
    def extract_text_and_tables(
        self,
        pdf_path: str,
        output_dir: str,
        enable_table_detection: bool = True
    ) -> Dict:
        """
        Extract both text and tables from PDF.
        
        Args:
            pdf_path: Path to PDF file
            output_dir: Output directory
            enable_table_detection: Whether to extract tables
            
        Returns:
            Dict with 'success' and optional 'error'
        """
        try:
            # Extract text
            text_result = self.api_client.extract_text(pdf_path, output_dir)
            if not text_result["success"]:
                return {
                    'success': False,
                    'error': f"Text extraction failed: {text_result.get('error')}"
                }
            
            # Extract tables if enabled
            if enable_table_detection:
                table_result = self.api_client.extract_tables(pdf_path, output_dir)
                if not table_result["success"]:
                    return {
                        'success': False,
                        'error': f"Table extraction failed: {table_result.get('error')}"
                    }
            
            return {'success': True}
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
