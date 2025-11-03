"""
API Client Service

Handles all communication with the Django backend API.
"""
import requests
import os
from typing import Dict, Optional
from dotenv import load_dotenv

load_dotenv()

DJANGO_API = os.getenv("API_BASE")


class APIClient:
    """
    Client for communicating with Django backend API.
    
    Handles all HTTP requests to backend endpoints for document processing.
    """
    
    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize API client.
        
        Args:
            base_url: Optional base URL for API (defaults to env variable)
        """
        self.base_url = base_url or DJANGO_API
        if not self.base_url:
            raise ValueError("API_BASE environment variable not set")
    
    def extract_tables(self, pdf_path: str, output_dir: str) -> Dict:
        """
        Extract tables from PDF via API.
        
        Args:
            pdf_path: Path to PDF file
            output_dir: Directory for table outputs
            
        Returns:
            Dict with success status and message/error
            
        Example:
            >>> client = APIClient()
            >>> result = client.extract_tables("/path/to/doc.pdf", "/path/to/output")
            >>> result['success']
            True
        """
        try:
            resp = requests.post(
                f"{self.base_url}/api/extract_tables/",
                json={"pdf_path": pdf_path, "output_dir": output_dir}
            )
            
            if resp.status_code == 200:
                return {"success": True, "message": resp.json().get("message")}
            else:
                error_msg = resp.json().get("error", "Unknown error") if resp.headers.get('content-type') == 'application/json' else resp.text
                return {"success": False, "error": error_msg}
        except Exception as e:
            return {"success": False, "error": f"API request failed: {str(e)}"}
    
    def extract_text(self, pdf_path: str, output_dir: str) -> Dict:
        """
        Extract text content from PDF via API.
        
        Args:
            pdf_path: Path to PDF file
            output_dir: Directory for text outputs
            
        Returns:
            Dict with success status and message/error
            
        Example:
            >>> result = client.extract_text("/path/to/doc.pdf", "/path/to/output")
            >>> result['success']
            True
        """
        try:
            resp = requests.post(
                f"{self.base_url}/api/extract_text/",
                json={"pdf_path": pdf_path, "output_dir": output_dir}
            )
            
            if resp.status_code == 200:
                return {"success": True, "message": resp.json().get("message")}
            else:
                error_msg = resp.json().get("error", "Unknown error") if resp.headers.get('content-type') == 'application/json' else resp.text
                return {"success": False, "error": error_msg}
        except Exception as e:
            return {"success": False, "error": f"API request failed: {str(e)}"}
    
    def chunk_and_embed(
        self, 
        output_dir: str, 
        chroma_db_dir: str, 
        doc_type: str = "unknown", 
        doc_name: str = "unknown"
    ) -> Dict:
        """
        Chunk and embed document via API.
        
        Args:
            output_dir: Directory containing extracted content
            chroma_db_dir: ChromaDB storage directory
            doc_type: Type of document (policy, brochure, etc.)
            doc_name: Name of document
            
        Returns:
            Dict with success status, message, and collection_size
            
        Example:
            >>> result = client.chunk_and_embed(
            ...     output_dir="/path/to/output",
            ...     chroma_db_dir="/path/to/chroma",
            ...     doc_type="policy",
            ...     doc_name="ActivAssure"
            ... )
            >>> result['collection_size']
            150
        """
        try:
            resp = requests.post(
                f"{self.base_url}/api/chunk_and_embed/",
                json={
                    "output_dir": output_dir,
                    "chroma_db_dir": chroma_db_dir,
                    "doc_type": doc_type,
                    "doc_name": doc_name
                }
            )
            
            if resp.status_code == 200:
                result = resp.json()
                return {
                    "success": True,
                    "message": result.get("message"),
                    "collection_size": result.get("collection_size")
                }
            else:
                error_msg = resp.json().get("error", "Unknown error") if resp.headers.get('content-type') == 'application/json' else resp.text
                return {"success": False, "error": error_msg}
        except Exception as e:
            return {"success": False, "error": f"API request failed: {str(e)}"}
    
    def upload_premium_excel(
        self, 
        file_path: str, 
        product_name: str,
        filename: str
    ) -> Dict:
        """
        Upload premium rate Excel file to backend.
        
        Args:
            file_path: Path to Excel file
            product_name: Product/database name
            filename: Original filename
            
        Returns:
            Dict with success status and message/error
            
        Example:
            >>> result = client.upload_premium_excel(
            ...     file_path="/tmp/rates.xlsx",
            ...     product_name="ActivAssure",
            ...     filename="premium_rates.xlsx"
            ... )
            >>> result['success']
            True
        """
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (filename, f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
                data = {'product_name': product_name}
                
                resp = requests.post(
                    f"{self.base_url}/api/upload_premium_excel/",
                    files=files,
                    data=data
                )
            
            if resp.status_code == 200:
                return {"success": True, "message": resp.json().get("message")}
            else:
                error_msg = resp.json().get("error", "Unknown error") if resp.headers.get('content-type') == 'application/json' else resp.text
                return {"success": False, "error": error_msg}
        except Exception as e:
            return {"success": False, "error": f"API request failed: {str(e)}"}

    def check_health(self) -> Dict:
        """
        Check health of the backend API.
        
        Returns:
            Dict with success status and message/error
            
        Example:
            >>> result = client.check_health()
            >>> result['success']
            True
        """
        try:
            resp = requests.get(f"{self.base_url}/api/health_check/")
            
            if resp.status_code == 200:
                return {"success": True, "message": resp.json().get("message")}
            else:
                error_msg = resp.json().get("error", "Unknown error") if resp.headers.get('content-type') == 'application/json' else resp.text
                return {"success": False, "error": error_msg}
        except Exception as e:
            return {"success": False, "error": f"API request failed: {str(e)}"}