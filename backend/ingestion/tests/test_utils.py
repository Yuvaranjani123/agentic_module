"""
Utility function tests for ingestion module.

Tests table extraction and text extraction utility functions.
"""

from django.test import TestCase
from unittest.mock import patch, MagicMock
import os
import tempfile
import shutil

from ingestion.utils import extract_and_save_tables, extract_text


class TableExtractionUtilsTests(TestCase):
    """Tests for table extraction utilities."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = os.path.join(self.temp_dir, 'output')
    
    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    @patch('ingestion.utils.pdfplumber.open')
    def test_extract_tables_creates_output_dir(self, mock_pdf):
        """Test table extraction creates output directory."""
        mock_page = MagicMock()
        mock_page.extract_tables.return_value = []
        mock_pdf.return_value.__enter__.return_value.pages = [mock_page]
        
        extract_and_save_tables('/fake/path.pdf', self.output_dir)
        
        self.assertTrue(os.path.exists(self.output_dir))
    
    @patch('ingestion.utils.pdfplumber.open')
    def test_extract_tables_handles_empty_pdf(self, mock_pdf):
        """Test table extraction with PDF containing no tables."""
        mock_page = MagicMock()
        mock_page.extract_tables.return_value = []
        mock_pdf.return_value.__enter__.return_value.pages = [mock_page]
        
        # Should not raise exception
        extract_and_save_tables('/fake/path.pdf', self.output_dir)


class TextExtractionUtilsTests(TestCase):
    """Tests for text extraction utilities."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = os.path.join(self.temp_dir, 'output')
    
    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    @patch('ingestion.utils.pdfplumber.open')
    def test_extract_text_creates_output_dir(self, mock_pdf):
        """Test text extraction creates output directory."""
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Sample text"
        mock_pdf.return_value.__enter__.return_value.pages = [mock_page]
        
        extract_text('/fake/path.pdf', self.output_dir)
        
        self.assertTrue(os.path.exists(self.output_dir))
    
    @patch('ingestion.utils.pdfplumber.open')
    def test_extract_text_handles_empty_pages(self, mock_pdf):
        """Test text extraction with empty pages."""
        mock_page = MagicMock()
        mock_page.extract_text.return_value = ""
        mock_pdf.return_value.__enter__.return_value.pages = [mock_page]
        
        # Should not raise exception
        extract_text('/fake/path.pdf', self.output_dir)
