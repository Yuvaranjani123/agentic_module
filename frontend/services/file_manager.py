"""
File Manager Service

Handles file operations, directory management, and PDF analysis.
"""
import os
import re
import pdfplumber
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional


class FileManager:
    """
    Manages file operations and directory structure for document processing.
    
    Handles directory setup, file naming, and PDF content analysis.
    """
    
    @staticmethod
    def clean_pdf_name(pdf_path: str) -> str:
        """
        Clean PDF filename to create valid folder name.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Cleaned folder-safe name
            
        Example:
            >>> FileManager.clean_pdf_name("/path/to/My Document (2024).pdf")
            'My_Document_2024'
        """
        filename = Path(pdf_path).stem
        cleaned = re.sub(r'[<>:"/\\|?*]', '_', filename)
        cleaned = re.sub(r'[_\s]+', '_', cleaned)
        cleaned = cleaned.strip('_')
        if len(cleaned) > 50:
            cleaned = cleaned[:50].rstrip('_')
        return cleaned if cleaned else "unnamed_pdf"
    
    @staticmethod
    def setup_directories(
        pdf_path: str, 
        base_output_dir: str, 
        product_name: str
    ) -> Dict[str, str]:
        """
        Setup directory structure for document processing.
        
        Args:
            pdf_path: Path to PDF file
            base_output_dir: Base directory for outputs
            product_name: Product/database name
            
        Returns:
            Dict with pdf_name, output_dir, chroma_db_dir
            
        Example:
            >>> dirs = FileManager.setup_directories(
            ...     pdf_path="/tmp/policy.pdf",
            ...     base_output_dir="/media/output",
            ...     product_name="ActivAssure"
            ... )
            >>> dirs['output_dir']
            '/media/output/ActivAssure/policy/'
        """
        if not product_name or not product_name.strip():
            raise ValueError("Product name is required")
        
        pdf_name = FileManager.clean_pdf_name(pdf_path)
        
        # Organize output under product name: output/ProductName/DocumentName/
        output_dir = os.path.join(base_output_dir, product_name, pdf_name)
        
        # ChromaDB also under product name: output/chroma_db/ProductName/
        chroma_db_dir = os.path.join(base_output_dir, "chroma_db", product_name)
        
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(chroma_db_dir, exist_ok=True)
        
        return {
            "pdf_name": pdf_name,
            "output_dir": output_dir,
            "chroma_db_dir": chroma_db_dir
        }
    
    @staticmethod
    def analyze_pdf_content(pdf_path: str) -> Dict:
        """
        Analyze PDF to detect tables and get basic stats.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dict with has_tables, table_count, total_pages, tables_per_page
            
        Example:
            >>> stats = FileManager.analyze_pdf_content("/path/to/doc.pdf")
            >>> stats['has_tables']
            True
            >>> stats['table_count']
            5
        """
        table_count = 0
        total_pages = 0
        
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
        
        return {
            "has_tables": table_count > 0,
            "table_count": table_count,
            "total_pages": total_pages,
            "tables_per_page": round(table_count / total_pages, 2) if total_pages > 0 else 0
        }
    
    @staticmethod
    def check_existing_extractions(output_dir: str) -> Dict:
        """
        Check what extractions already exist.
        
        Args:
            output_dir: Directory to check
            
        Returns:
            Dict with extraction status flags and counts
            
        Example:
            >>> status = FileManager.check_existing_extractions("/path/to/output")
            >>> status['has_text_files']
            True
        """
        if not os.path.exists(output_dir):
            return {
                "has_table_map": False,
                "has_text_files": False,
                "has_csv_files": False,
                "text_file_count": 0,
                "csv_file_count": 0
            }
        
        table_map_path = os.path.join(output_dir, "table_file_map.csv")
        text_files = [f for f in os.listdir(output_dir) if f.endswith("_text.txt")]
        csv_files = [f for f in os.listdir(output_dir) if f.endswith(".csv") and f != "table_file_map.csv"]
        
        return {
            "has_table_map": os.path.exists(table_map_path),
            "has_text_files": len(text_files) > 0,
            "has_csv_files": len(csv_files) > 0,
            "text_file_count": len(text_files),
            "csv_file_count": len(csv_files)
        }
    
    @staticmethod
    def load_table_mapping(output_dir: str) -> pd.DataFrame:
        """
        Load the table file mapping.
        
        Args:
            output_dir: Directory containing table_file_map.csv
            
        Returns:
            DataFrame with table mapping or empty DataFrame
            
        Example:
            >>> df = FileManager.load_table_mapping("/path/to/output")
            >>> len(df)
            5
        """
        table_map_path = os.path.join(output_dir, "table_file_map.csv")
        if os.path.exists(table_map_path):
            return pd.read_csv(table_map_path)
        return pd.DataFrame()
    
    @staticmethod
    def save_table_mapping(output_dir: str, df: pd.DataFrame):
        """
        Save the updated table file mapping.
        
        Args:
            output_dir: Directory for table_file_map.csv
            df: DataFrame to save
            
        Example:
            >>> df = pd.DataFrame({'table': ['t1'], 'filename': ['f1']})
            >>> FileManager.save_table_mapping("/path/to/output", df)
        """
        table_map_path = os.path.join(output_dir, "table_file_map.csv")
        df.to_csv(table_map_path, index=False)
    
    @staticmethod
    def get_extracted_tables(output_dir: str) -> List[str]:
        """
        Get list of extracted table files.
        
        Args:
            output_dir: Directory to check
            
        Returns:
            List of CSV filenames (excluding table_file_map.csv)
            
        Example:
            >>> tables = FileManager.get_extracted_tables("/path/to/output")
            >>> tables
            ['table_page_5_1.csv', 'table_page_7_1.csv']
        """
        if not os.path.exists(output_dir):
            return []
        return [f for f in os.listdir(output_dir) if f.endswith(".csv") and f != "table_file_map.csv"]
    
    @staticmethod
    def check_manual_review_status(output_dir: str) -> bool:
        """
        Check if manual review has been completed.
        
        Args:
            output_dir: Directory to check
            
        Returns:
            True if review completed
            
        Example:
            >>> FileManager.check_manual_review_status("/path/to/output")
            False
        """
        marker_file = os.path.join(output_dir, ".manual_review_completed")
        return os.path.exists(marker_file)
    
    @staticmethod
    def mark_review_completed(output_dir: str, table_map_path: Optional[str] = None):
        """
        Mark manual review as completed.
        
        Args:
            output_dir: Directory for marker file
            table_map_path: Optional path to table map for timestamp
            
        Example:
            >>> FileManager.mark_review_completed("/path/to/output")
        """
        import time
        marker_file = os.path.join(output_dir, ".manual_review_completed")
        
        if table_map_path is None:
            table_map_path = os.path.join(output_dir, "table_file_map.csv")
        
        with open(marker_file, 'w') as f:
            timestamp = os.path.getmtime(table_map_path) if os.path.exists(table_map_path) else time.time()
            f.write(f"Manual review completed at {timestamp}")
    
    def __init__(self, base_output_dir: str = None):
        """
        Initialize FileManager with base output directory.
        
        Args:
            base_output_dir: Base directory for outputs
        """
        self.base_output_dir = base_output_dir
    
    def save_uploaded_file(self, uploaded_file, product_name: str) -> str:
        """
        Save uploaded file to temporary location.
        
        Args:
            uploaded_file: Streamlit uploaded file object
            product_name: Product database name
            
        Returns:
            Path to saved file
        """
        import tempfile
        
        # Create temp directory for uploaded file
        temp_dir = tempfile.mkdtemp()
        file_path = os.path.join(temp_dir, uploaded_file.name)
        
        # Save file
        with open(file_path, 'wb') as f:
            f.write(uploaded_file.getbuffer())
        
        return file_path
    
    def clean_filename(self, filename: str) -> str:
        """
        Clean filename to create valid folder name.
        
        Args:
            filename: Original filename
            
        Returns:
            Cleaned name
        """
        # Remove extension
        name = Path(filename).stem
        # Clean special characters
        cleaned = re.sub(r'[<>:"/\\|?*]', '_', name)
        cleaned = re.sub(r'[_\s]+', '_', cleaned)
        cleaned = cleaned.strip('_')
        if len(cleaned) > 50:
            cleaned = cleaned[:50].rstrip('_')
        return cleaned if cleaned else "unnamed"
    
    def list_product_databases(self) -> List[str]:
        """
        List all product databases in chroma_db directory.
        
        Returns:
            List of product database names
        """
        if not self.base_output_dir:
            return []
        
        chroma_base = os.path.join(self.base_output_dir, "chroma_db")
        
        if not os.path.exists(chroma_base):
            return []
        
        products = []
        for item in os.listdir(chroma_base):
            item_path = os.path.join(chroma_base, item)
            if os.path.isdir(item_path):
                # Check if it has a chroma database
                db_file = os.path.join(item_path, "chroma.sqlite3")
                if os.path.exists(db_file):
                    products.append(item)
        
        return sorted(products)
    
    def get_database_info(self, product_name: str) -> Dict:
        """
        Get information about a product database.
        
        Args:
            product_name: Product database name
            
        Returns:
            Dict with database information
        """
        if not self.base_output_dir:
            return {}
        
        chroma_path = os.path.join(
            self.base_output_dir, "chroma_db", product_name
        )
        product_path = os.path.join(self.base_output_dir, product_name)
        
        info = {
            'path': chroma_path,
            'document_count': 0,
            'documents': []
        }
        
        # Count documents in product directory
        if os.path.exists(product_path):
            docs = [d for d in os.listdir(product_path) 
                   if os.path.isdir(os.path.join(product_path, d))]
            info['document_count'] = len(docs)
            info['documents'] = sorted(docs)
        
        return info
