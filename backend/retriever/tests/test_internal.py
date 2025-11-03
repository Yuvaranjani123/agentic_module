"""
Internal query function tests.

Tests the core query_document_internal function with various
scenarios including filtering, evaluation, and error handling.
"""

from django.test import TestCase
from unittest.mock import patch, MagicMock
import os
import tempfile
import shutil

from retriever.views import query_document_internal


class QueryInternalBasicTests(TestCase):
    """Basic tests for query_document_internal function."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    @patch('retriever.views.AzureChatOpenAI')
    def test_query_no_results(self, mock_llm):
        """Test query when no documents found."""
        mock_collection = MagicMock()
        mock_collection.query.return_value = {'documents': [[]], 'metadatas': [[]]}
        
        mock_embedding = MagicMock()
        mock_embedding.embed_query.return_value = [0.1, 0.2]
        
        result = query_document_internal(
            collection=mock_collection,
            embedding_model=mock_embedding,
            query="Test",
            k=5
        )
        
        self.assertEqual(result['answer'], 'No relevant documents found.')
        self.assertEqual(len(result['sources']), 0)
    
    @patch('retriever.views.AzureChatOpenAI')
    def test_query_with_results(self, mock_llm_class):
        """Test query with successful results."""
        mock_collection = MagicMock()
        mock_collection.query.return_value = {
            'documents': [['Doc 1', 'Doc 2']],
            'metadatas': [[
                {'chunk_idx': '1', 'page_num': 1, 'type': 'text'},
                {'chunk_idx': '2', 'page_num': 2, 'type': 'table'}
            ]]
        }
        
        mock_embedding = MagicMock()
        mock_embedding.embed_query.return_value = [0.1, 0.2]
        
        mock_llm = MagicMock()
        mock_llm.invoke.return_value.content = "Answer"
        mock_llm_class.return_value = mock_llm
        
        with patch.dict(os.environ, {
            'AZURE_OPENAI_ENDPOINT': 'https://fake.openai.azure.com/',
            'AZURE_OPENAI_KEY': 'fake-key',
            'AZURE_OPENAI_CHAT_DEPLOYMENT': 'gpt-35-turbo',
            'AZURE_OPENAI_CHAT_API_VERSION': '2023-05-15'
        }):
            result = query_document_internal(
                collection=mock_collection,
                embedding_model=mock_embedding,
                query="Test",
                k=5
            )
        
        self.assertEqual(result['answer'], 'Answer')
        self.assertEqual(len(result['sources']), 2)
    
    def test_query_embedding_error(self):
        """Test handling of embedding errors."""
        mock_collection = MagicMock()
        mock_embedding = MagicMock()
        mock_embedding.embed_query.side_effect = Exception("API error")
        
        result = query_document_internal(
            collection=mock_collection,
            embedding_model=mock_embedding,
            query="Test",
            k=5
        )
        
        self.assertEqual(result['answer'], 'Error getting embedding.')


class QueryInternalFilteringTests(TestCase):
    """Tests for document filtering in queries."""
    
    @patch('retriever.views.AzureChatOpenAI')
    def test_query_with_doc_type_filter(self, mock_llm_class):
        """Test query applies document type filter."""
        mock_collection = MagicMock()
        mock_collection.query.return_value = {
            'documents': [['Policy doc']],
            'metadatas': [[{'chunk_idx': '1', 'doc_type': 'policy'}]]
        }
        
        mock_embedding = MagicMock()
        mock_embedding.embed_query.return_value = [0.1, 0.2]
        
        mock_llm = MagicMock()
        mock_llm.invoke.return_value.content = "Answer"
        mock_llm_class.return_value = mock_llm
        
        with patch.dict(os.environ, {
            'AZURE_OPENAI_ENDPOINT': 'https://fake.openai.azure.com/',
            'AZURE_OPENAI_KEY': 'fake-key',
            'AZURE_OPENAI_CHAT_DEPLOYMENT': 'gpt-35-turbo',
            'AZURE_OPENAI_CHAT_API_VERSION': '2023-05-15'
        }):
            query_document_internal(
                collection=mock_collection,
                embedding_model=mock_embedding,
                query="Test",
                k=5,
                doc_type_filter='policy'
            )
        
        call_kwargs = mock_collection.query.call_args[1]
        self.assertIn('where', call_kwargs)
        self.assertEqual(call_kwargs['where']['doc_type'], 'policy')


class QueryInternalEvaluationTests(TestCase):
    """Tests for evaluation integration in queries."""
    
    @patch('retriever.views.AzureChatOpenAI')
    @patch('retriever.views.evaluator')
    def test_query_with_evaluation(self, mock_evaluator, mock_llm_class):
        """Test query performs evaluation when requested."""
        mock_collection = MagicMock()
        mock_collection.query.return_value = {
            'documents': [['Doc']],
            'metadatas': [[{'chunk_idx': '1', 'page_num': 1}]]
        }
        
        mock_embedding = MagicMock()
        mock_embedding.embed_query.return_value = [0.1, 0.2]
        
        mock_llm = MagicMock()
        mock_llm.invoke.return_value.content = "Answer"
        mock_llm_class.return_value = mock_llm
        
        mock_evaluator.comprehensive_evaluation.return_value = {
            'avg_semantic_similarity': 0.85
        }
        
        with patch.dict(os.environ, {
            'AZURE_OPENAI_ENDPOINT': 'https://fake.openai.azure.com/',
            'AZURE_OPENAI_KEY': 'fake-key',
            'AZURE_OPENAI_CHAT_DEPLOYMENT': 'gpt-35-turbo',
            'AZURE_OPENAI_CHAT_API_VERSION': '2023-05-15'
        }):
            result = query_document_internal(
                collection=mock_collection,
                embedding_model=mock_embedding,
                query="Test",
                k=5,
                evaluate_retrieval=True
            )
        
        self.assertIn('evaluation', result)
        self.assertEqual(result['evaluation']['avg_semantic_similarity'], 0.85)
        mock_evaluator.comprehensive_evaluation.assert_called_once()
