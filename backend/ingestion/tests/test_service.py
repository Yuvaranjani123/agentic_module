"""
Service class tests for ChunkerEmbedder.

Tests initialization, configuration, and core functionality
of the semantic chunking and embedding service.
"""

from django.test import TestCase
from unittest.mock import patch, MagicMock
import os
import tempfile
import shutil

from ingestion.service import ChunkerEmbedder


class ChunkerEmbedderInitTests(TestCase):
    """Tests for ChunkerEmbedder initialization."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.chroma_dir = os.path.join(self.temp_dir, 'chroma')
        os.makedirs(self.chroma_dir, exist_ok=True)
    
    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    @patch('ingestion.service.chromadb.PersistentClient')
    @patch('ingestion.service.AzureOpenAIEmbeddings')
    def test_chunker_initialization(self, mock_embeddings, mock_chroma):
        """Test ChunkerEmbedder initializes correctly."""
        mock_collection = MagicMock()
        mock_chroma.return_value.create_collection.return_value = mock_collection
        
        chunker = ChunkerEmbedder(
            azure_endpoint='https://fake.openai.azure.com/',
            azure_api_key='fake-key',
            azure_api_version='2023-05-15',
            embedding_model='text-embedding-ada-002',
            chroma_persist_dir=self.chroma_dir,
            semantic_threshold=0.75,
            doc_type='policy',
            doc_name='TestDoc'
        )
        
        self.assertEqual(chunker.semantic_threshold, 0.75)
        self.assertEqual(chunker.doc_type, 'policy')
        self.assertEqual(chunker.doc_name, 'TestDoc')
        mock_embeddings.assert_called_once()
        mock_chroma.assert_called_once_with(path=self.chroma_dir)
    
    @patch('ingestion.service.chromadb.PersistentClient')
    @patch('ingestion.service.AzureOpenAIEmbeddings')
    def test_default_semantic_threshold(self, mock_embeddings, mock_chroma):
        """Test default semantic threshold is 0.75."""
        mock_collection = MagicMock()
        mock_chroma.return_value.create_collection.return_value = mock_collection
        
        chunker = ChunkerEmbedder(
            azure_endpoint='https://fake.openai.azure.com/',
            azure_api_key='fake-key',
            azure_api_version='2023-05-15',
            embedding_model='text-embedding-ada-002',
            chroma_persist_dir=self.chroma_dir
        )
        
        self.assertEqual(chunker.semantic_threshold, 0.75)
    
    @patch('ingestion.service.chromadb.PersistentClient')
    @patch('ingestion.service.AzureOpenAIEmbeddings')
    def test_custom_semantic_threshold(self, mock_embeddings, mock_chroma):
        """Test custom semantic threshold is respected."""
        mock_collection = MagicMock()
        mock_chroma.return_value.create_collection.return_value = mock_collection
        
        chunker = ChunkerEmbedder(
            azure_endpoint='https://fake.openai.azure.com/',
            azure_api_key='fake-key',
            azure_api_version='2023-05-15',
            embedding_model='text-embedding-ada-002',
            chroma_persist_dir=self.chroma_dir,
            semantic_threshold=0.85
        )
        
        self.assertEqual(chunker.semantic_threshold, 0.85)
    
    @patch('ingestion.service.chromadb.PersistentClient')
    @patch('ingestion.service.AzureOpenAIEmbeddings')
    def test_doc_metadata_stored(self, mock_embeddings, mock_chroma):
        """Test document type and name metadata is stored."""
        mock_collection = MagicMock()
        mock_chroma.return_value.create_collection.return_value = mock_collection
        
        chunker = ChunkerEmbedder(
            azure_endpoint='https://fake.openai.azure.com/',
            azure_api_key='fake-key',
            azure_api_version='2023-05-15',
            embedding_model='text-embedding-ada-002',
            chroma_persist_dir=self.chroma_dir,
            doc_type='brochure',
            doc_name='ProductBrochure'
        )
        
        self.assertEqual(chunker.doc_type, 'brochure')
        self.assertEqual(chunker.doc_name, 'ProductBrochure')
