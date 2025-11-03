"""
API endpoint tests for retriever module.

Tests query document endpoint, evaluation summary,
and various filtering and evaluation options.
"""

from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock
import os
import tempfile
import shutil


class QueryDocumentAPITests(APITestCase):
    """Tests for query document endpoint."""
    
    def setUp(self):
        self.client = APIClient()
        self.temp_dir = tempfile.mkdtemp()
        self.chroma_dir = os.path.join(self.temp_dir, 'chroma')
        os.makedirs(self.chroma_dir, exist_ok=True)
    
    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    @patch('retriever.views.chromadb.PersistentClient')
    @patch('retriever.views.AzureOpenAIEmbeddings')
    @patch('retriever.views.query_document_internal')
    def test_query_success(self, mock_query, mock_embeddings, mock_chroma):
        """Test successful document query."""
        mock_query.return_value = {
            'answer': 'The premium is $1000.',
            'sources': [{'id': 'chunk_1', 'content': 'Premium: $1000'}]
        }
        
        with patch.dict(os.environ, {
            'AZURE_OPENAI_ENDPOINT': 'https://fake.openai.azure.com/',
            'AZURE_OPENAI_KEY': 'fake-key',
            'AZURE_OPENAI_TEXT_VERSION': '2023-05-15',
            'AZURE_OPENAI_TEXT_DEPLOYMENT_EMBEDDINGS': 'text-embedding-ada-002',
            'AZURE_OPENAI_CHAT_DEPLOYMENT': 'gpt-35-turbo',
            'AZURE_OPENAI_CHAT_API_VERSION': '2023-05-15'
        }):
            response = self.client.post('/api/retriever/query/', {
                'query': 'What is the premium?',
                'chroma_db_dir': self.chroma_dir,
                'k': 5
            })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('answer', response.data)
        self.assertIn('sources', response.data)
    
    def test_query_missing_query_param(self):
        """Test query without query parameter."""
        response = self.client.post('/api/retriever/query/', {
            'chroma_db_dir': self.chroma_dir,
            'k': 5
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'query is required')
    
    def test_query_missing_chroma_dir(self):
        """Test query without chroma_db_dir parameter."""
        response = self.client.post('/api/retriever/query/', {
            'query': 'What is covered?',
            'k': 5
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'chroma_db_dir is required')
    
    @patch('retriever.views.chromadb.PersistentClient')
    @patch('retriever.views.AzureOpenAIEmbeddings')
    @patch('retriever.views.query_document_internal')
    def test_query_with_doc_type_filter(self, mock_query, mock_embeddings, mock_chroma):
        """Test query with document type filtering."""
        mock_query.return_value = {'answer': 'Test', 'sources': []}
        
        with patch.dict(os.environ, {
            'AZURE_OPENAI_ENDPOINT': 'https://fake.openai.azure.com/',
            'AZURE_OPENAI_KEY': 'fake-key',
            'AZURE_OPENAI_TEXT_VERSION': '2023-05-15',
            'AZURE_OPENAI_TEXT_DEPLOYMENT_EMBEDDINGS': 'text-embedding-ada-002',
            'AZURE_OPENAI_CHAT_DEPLOYMENT': 'gpt-35-turbo',
            'AZURE_OPENAI_CHAT_API_VERSION': '2023-05-15'
        }):
            response = self.client.post('/api/retriever/query/', {
                'query': 'What is covered?',
                'chroma_db_dir': self.chroma_dir,
                'k': 5,
                'doc_type': 'policy'
            })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        call_kwargs = mock_query.call_args[1]
        self.assertEqual(call_kwargs['doc_type_filter'], 'policy')
    
    @patch('retriever.views.chromadb.PersistentClient')
    @patch('retriever.views.AzureOpenAIEmbeddings')
    @patch('retriever.views.query_document_internal')
    def test_query_with_evaluation(self, mock_query, mock_embeddings, mock_chroma):
        """Test query with evaluation enabled."""
        mock_query.return_value = {
            'answer': 'Test',
            'sources': [],
            'evaluation': {'avg_semantic_similarity': 0.85}
        }
        
        with patch.dict(os.environ, {
            'AZURE_OPENAI_ENDPOINT': 'https://fake.openai.azure.com/',
            'AZURE_OPENAI_KEY': 'fake-key',
            'AZURE_OPENAI_TEXT_VERSION': '2023-05-15',
            'AZURE_OPENAI_TEXT_DEPLOYMENT_EMBEDDINGS': 'text-embedding-ada-002',
            'AZURE_OPENAI_CHAT_DEPLOYMENT': 'gpt-35-turbo',
            'AZURE_OPENAI_CHAT_API_VERSION': '2023-05-15'
        }):
            response = self.client.post('/api/retriever/query/', {
                'query': 'Test',
                'chroma_db_dir': self.chroma_dir,
                'k': 5,
                'evaluate': True
            })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('evaluation', response.data)


class EvaluationSummaryAPITests(APITestCase):
    """Tests for evaluation summary endpoint."""
    
    def setUp(self):
        self.client = APIClient()
    
    @patch('retriever.views.evaluator.get_evaluation_summary')
    def test_evaluation_summary_success(self, mock_summary):
        """Test evaluation summary retrieval."""
        mock_summary.return_value = {
            'total_queries': 100,
            'avg_similarity': 0.82
        }
        
        response = self.client.get('/api/retriever/evaluation-summary/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_queries', response.data)
    
    @patch('retriever.views.evaluator.get_evaluation_summary')
    def test_evaluation_summary_error_handling(self, mock_summary):
        """Test evaluation summary handles errors."""
        mock_summary.side_effect = Exception("Evaluation error")
        
        response = self.client.get('/api/retriever/evaluation-summary/')
        
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('error', response.data)
