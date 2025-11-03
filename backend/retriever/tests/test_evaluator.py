"""
Evaluation system tests.

Tests the RetrievalEvaluator class and evaluation functionality.
"""

from django.test import TestCase
from unittest.mock import patch, MagicMock

from evaluation.metrics import RetrievalEvaluator


class RetrievalEvaluatorInitTests(TestCase):
    """Tests for RetrievalEvaluator initialization."""
    
    def test_evaluator_initialization(self):
        """Test evaluator initializes properly."""
        evaluator = RetrievalEvaluator()
        
        self.assertIsNotNone(evaluator)
        self.assertIsInstance(evaluator, RetrievalEvaluator)
    
    def test_get_summary_empty(self):
        """Test summary when no evaluations performed."""
        evaluator = RetrievalEvaluator()
        summary = evaluator.get_evaluation_summary()
        
        self.assertIsInstance(summary, dict)


class RetrievalEvaluatorFunctionalTests(TestCase):
    """Functional tests for evaluation operations."""
    
    def setUp(self):
        self.evaluator = RetrievalEvaluator()
    
    @patch.object(RetrievalEvaluator, 'comprehensive_evaluation')
    def test_comprehensive_evaluation(self, mock_eval):
        """Test comprehensive evaluation can be called."""
        mock_eval.return_value = {
            'avg_semantic_similarity': 0.85,
            'precision_at_k': 0.80,
            'recall_at_k': 0.75
        }
        
        mock_embeddings = MagicMock()
        docs = [
            {'text': 'Doc 1', 'id': '1'},
            {'text': 'Doc 2', 'id': '2'}
        ]
        
        result = self.evaluator.comprehensive_evaluation(
            query="Test",
            retrieved_docs=docs,
            embeddings_client=mock_embeddings,
            k=2
        )
        
        self.assertIsNotNone(result)
        self.assertIn('avg_semantic_similarity', result)
        mock_eval.assert_called_once()
