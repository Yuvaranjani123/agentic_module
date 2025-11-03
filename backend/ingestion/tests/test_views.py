"""
API endpoint tests for ingestion module.

Tests PDF upload, Excel upload, table extraction, text extraction,
and chunking/embedding endpoints. Each endpoint has success and error tests.
"""

from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from unittest.mock import patch, MagicMock
import os
import tempfile
import shutil
import json


class PDFUploadAPITests(APITestCase):
    """Tests for PDF upload endpoint."""
    
    def setUp(self):
        self.client = APIClient()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_upload_pdf_success(self):
        """Test successful PDF file upload."""
        pdf_content = b"%PDF-1.4\n%fake pdf content"
        pdf_file = SimpleUploadedFile("test.pdf", pdf_content, content_type="application/pdf")
        
        response = self.client.post('/api/upload_pdf/', {'pdf': pdf_file}, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('pdf_path', response.data)
        self.assertIn('pdf_name', response.data)
        
        # Cleanup
        if 'pdf_path' in response.data and os.path.exists(response.data['pdf_path']):
            os.remove(response.data['pdf_path'])
    
    def test_upload_pdf_no_file(self):
        """Test upload without file returns 400."""
        response = self.client.post('/api/upload_pdf/', {})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)


class ExcelUploadAPITests(APITestCase):
    """Tests for premium Excel upload endpoint."""
    
    def setUp(self):
        self.client = APIClient()
    
    def tearDown(self):
        premium_dir = os.path.join(settings.MEDIA_ROOT, 'premium_workbooks')
        if os.path.exists(premium_dir):
            shutil.rmtree(premium_dir)
    
    def test_upload_excel_success(self):
        """Test successful Excel upload."""
        excel_file = SimpleUploadedFile(
            "rates.xlsx", 
            b"fake excel", 
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        response = self.client.post(
            '/api/upload_premium_excel/',
            {'excel': excel_file, 'doc_name': 'TestPolicy'},
            format='multipart'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['doc_name'], 'TestPolicy')
    
    def test_upload_excel_invalid_format(self):
        """Test Excel upload with wrong file type."""
        txt_file = SimpleUploadedFile("not_excel.txt", b"text", content_type="text/plain")
        
        response = self.client.post(
            '/api/upload_premium_excel/',
            {'excel': txt_file, 'doc_name': 'Test'},
            format='multipart'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TableExtractionAPITests(APITestCase):
    """Tests for table extraction endpoint."""
    
    def setUp(self):
        self.client = APIClient()
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = os.path.join(self.temp_dir, 'output')
        os.makedirs(self.output_dir, exist_ok=True)
    
    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    @patch('ingestion.views.extract_and_save_tables')
    def test_extract_tables_success(self, mock_extract):
        """Test successful table extraction."""
        mock_extract.return_value = None
        
        response = self.client.post('/api/extract_tables/', {
            'pdf_path': '/fake/path.pdf',
            'output_dir': self.output_dir
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_extract.assert_called_once()
    
    def test_extract_tables_missing_params(self):
        """Test table extraction without required params."""
        response = self.client.post('/api/extract_tables/', {
            'output_dir': self.output_dir
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TextExtractionAPITests(APITestCase):
    """Tests for text extraction endpoint."""
    
    def setUp(self):
        self.client = APIClient()
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = os.path.join(self.temp_dir, 'output')
        os.makedirs(self.output_dir, exist_ok=True)
    
    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    @patch('ingestion.views.extract_text')
    def test_extract_text_success(self, mock_extract):
        """Test successful text extraction."""
        mock_extract.return_value = None
        
        response = self.client.post('/api/extract_text/', {
            'pdf_path': '/fake/path.pdf',
            'output_dir': self.output_dir
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_extract.assert_called_once()
    
    def test_extract_text_missing_params(self):
        """Test text extraction without required params."""
        response = self.client.post('/api/extract_text/', {})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ChunkAndEmbedAPITests(APITestCase):
    """Tests for chunk and embed endpoint."""
    
    def setUp(self):
        self.client = APIClient()
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = os.path.join(self.temp_dir, 'output')
        self.chroma_dir = os.path.join(self.temp_dir, 'chroma')
        os.makedirs(self.output_dir, exist_ok=True)
    
    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    @patch('ingestion.views.ChunkerEmbedder')
    def test_chunk_and_embed_success(self, mock_chunker_class):
        """Test successful chunking and embedding."""
        mock_chunker = MagicMock()
        mock_chunker.collection.count.return_value = 150
        mock_chunker_class.return_value = mock_chunker
        
        with patch.dict(os.environ, {
            'AZURE_OPENAI_ENDPOINT': 'https://fake.openai.azure.com/',
            'AZURE_OPENAI_KEY': 'fake-key',
            'AZURE_OPENAI_TEXT_VERSION': '2023-05-15',
            'AZURE_OPENAI_TEXT_DEPLOYMENT_EMBEDDINGS': 'text-embedding-ada-002'
        }):
            response = self.client.post('/api/chunk_and_embed/', {
                'output_dir': self.output_dir,
                'chroma_db_dir': self.chroma_dir,
                'doc_type': 'policy',
                'doc_name': 'TestPolicy'
            })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['collection_size'], 150)
    
    def test_chunk_and_embed_missing_params(self):
        """Test chunking without required params."""
        response = self.client.post('/api/chunk_and_embed/', {
            'output_dir': self.output_dir
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    @patch('ingestion.views.ChunkerEmbedder')
    def test_chunk_and_embed_missing_azure_config(self, mock_chunker):
        """Test chunking with missing Azure config."""
        with patch.dict(os.environ, {}, clear=True):
            response = self.client.post('/api/chunk_and_embed/', {
                'output_dir': self.output_dir,
                'chroma_db_dir': self.chroma_dir
            })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
