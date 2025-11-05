"""
Tests for the Agents Module

This module contains tests for:
1. Traditional Orchestrator (intent classification and routing)
2. ReAct Agentic System (multi-step reasoning)
3. Agentic Endpoints (query, stats, compare, evaluate)

Run with:
    python manage.py test agents
    python manage.py test agents.tests.TraditionalOrchestratorTests
    python manage.py test agents.tests.ReActAgenticTests
    python manage.py test agents.tests.AgenticEndpointsTests
"""

from django.test import TestCase, Client
from django.urls import reverse
import json
from unittest.mock import patch, MagicMock


class TraditionalOrchestratorTests(TestCase):
    """Tests for the Traditional Orchestrator system."""
    
    def setUp(self):
        """Set up test client."""
        self.client = Client()
        self.query_url = reverse('agents:orchestrated_query')
    
    def test_simple_premium_calculation(self):
        """Test simple premium calculation intent."""
        response = self.client.post(
            self.query_url,
            data=json.dumps({
                "query": "Calculate premium for age 35",
                "chroma_db_dir": "C:/repo/certification/project_2/rag_module/media/output/chroma_db/ActivAssure"
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check response structure
        self.assertIn('answer', data)
        self.assertIn('agent', data)
        self.assertIn('intent', data)
    
    def test_document_retrieval_intent(self):
        """Test document retrieval intent classification."""
        response = self.client.post(
            self.query_url,
            data=json.dumps({
                "query": "What is the waiting period for pre-existing diseases?",
                "chroma_db_dir": "C:/repo/certification/project_2/rag_module/media/output/chroma_db/ActivAssure"
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should route to document retrieval
        self.assertIn('agent', data)
        self.assertEqual(data['intent'], 'DOCUMENT_RETRIEVAL')
    
    def test_missing_chroma_db_dir(self):
        """Test that chroma_db_dir is required for retrieval queries."""
        response = self.client.post(
            self.query_url,
            data=json.dumps({
                "query": "What is the waiting period?"
            }),
            content_type='application/json'
        )
        
        # Should return 400 for missing chroma_db_dir
        self.assertEqual(response.status_code, 400)


class ReActAgenticTests(TestCase):
    """Tests for the ReAct Agentic System."""
    
    def setUp(self):
        """Set up test client."""
        self.client = Client()
        self.agentic_url = reverse('agents:agentic_query')
    
    def test_react_multi_step_query(self):
        """Test ReAct with multi-step reasoning query."""
        response = self.client.post(
            self.agentic_url,
            data=json.dumps({
                "query": "Calculate premium for ActivAssure age 32 with 10L cover, then compare with ActivFit",
                "use_react": True,
                "conversation_history": []
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check ReAct-specific fields
        self.assertEqual(data.get('mode'), 'react')
        self.assertIn('reasoning_trace', data)
        self.assertIn('final_answer', data)
        
        # Check reasoning trace structure
        trace = data['reasoning_trace']
        self.assertIn('iterations', trace)
        self.assertIn('steps', trace)
        self.assertIn('success', trace)
        
        # Should have multiple reasoning steps
        self.assertGreater(len(trace['steps']), 0)
    
    def test_react_simple_query(self):
        """Test ReAct with simple query (should still work)."""
        response = self.client.post(
            self.agentic_url,
            data=json.dumps({
                "query": "What is the waiting period in ActivAssure?",
                "use_react": True,
                "conversation_history": []
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(data.get('mode'), 'react')
        self.assertIn('final_answer', data)
    
    def test_traditional_mode_fallback(self):
        """Test traditional mode (use_react=false)."""
        response = self.client.post(
            self.agentic_url,
            data=json.dumps({
                "query": "Calculate premium for age 35",
                "use_react": False,
                "conversation_history": []
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should use traditional mode
        self.assertEqual(data.get('mode'), 'traditional')
        self.assertIn('tasks', data)
        self.assertIn('intent_classification', data)


class AgenticEndpointsTests(TestCase):
    """Tests for additional agentic endpoints (stats, compare, evaluate)."""
    
    def setUp(self):
        """Set up test client."""
        self.client = Client()
    
    def test_agentic_stats_endpoint(self):
        """Test the statistics endpoint."""
        response = self.client.get(reverse('agents:agentic_stats'))
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check structure
        self.assertIn('statistics', data)
        self.assertIn('learning_evidence', data)
        self.assertIn('system_status', data)
    
    def test_agentic_compare_endpoint(self):
        """Test the comparison endpoint."""
        response = self.client.post(
            reverse('agents:agentic_compare'),
            data=json.dumps({
                "query": "Calculate premium and compare with ActivFit",
                "conversation_history": []
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check comparison structure
        self.assertIn('comparison', data)
        comparison = data['comparison']
        
        self.assertIn('keyword_based', comparison)
        self.assertIn('agentic', comparison)
        self.assertIn('advantages_of_agentic', comparison)
    
    def test_agentic_evaluate_endpoint(self):
        """Test the evaluation endpoint."""
        response = self.client.post(reverse('agents:agentic_evaluate'))
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check evaluation structure
        self.assertIn('overall_status', data)
        self.assertIn('certification_evidence', data)
        self.assertIn('timestamp', data)
        
        # Check certification evidence
        evidence = data['certification_evidence']
        self.assertIn('agent_reasoning', evidence)
        self.assertIn('dynamic_routing', evidence)
        self.assertIn('multi_step_planning', evidence)


class AgentToolsTests(TestCase):
    """Tests for individual agent tools (calculator, comparator, retriever)."""
    
    def setUp(self):
        """Set up test client."""
        self.client = Client()
    
    @patch('agents.agentic.react_tools.PremiumCalculator')
    def test_premium_calculator_tool(self, mock_calculator):
        """Test premium calculator tool integration."""
        # Mock calculator response
        mock_instance = MagicMock()
        mock_instance.calculate.return_value = {
            'premium': 15000,
            'product': 'ActivAssure',
            'breakdown': {}
        }
        mock_calculator.return_value = mock_instance
        
        # Test through ReAct system
        response = self.client.post(
            reverse('agents:agentic_query'),
            data=json.dumps({
                "query": "Calculate premium for ActivAssure age 30 with 5L cover",
                "use_react": True,
                "conversation_history": []
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should have used premium_calculator tool
        metadata = data.get('agentic_metadata', {})
        tools_used = metadata.get('tools_used', [])
        self.assertIn('premium_calculator', tools_used)
    
    def test_list_products_tool(self):
        """Test list_products tool."""
        response = self.client.post(
            reverse('agents:agentic_query'),
            data=json.dumps({
                "query": "What products are available?",
                "use_react": True,
                "conversation_history": []
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should successfully list products
        self.assertIn('final_answer', data)
        final_answer = data['final_answer'].lower()
        self.assertTrue('activassure' in final_answer or 'activfit' in final_answer)


class IntegrationTests(TestCase):
    """Integration tests for end-to-end scenarios."""
    
    def setUp(self):
        """Set up test client."""
        self.client = Client()
    
    def test_full_workflow_traditional(self):
        """Test complete workflow with traditional orchestrator."""
        # Step 1: Simple premium calculation
        response1 = self.client.post(
            reverse('agents:orchestrated_query'),
            data=json.dumps({
                "query": "Calculate premium for ActivAssure age 35 with 10L cover",
                "chroma_db_dir": "C:/repo/certification/project_2/rag_module/media/output/chroma_db/ActivAssure"
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response1.status_code, 200)
        
        # Step 2: Document retrieval
        response2 = self.client.post(
            reverse('agents:orchestrated_query'),
            data=json.dumps({
                "query": "What is the waiting period in ActivAssure?",
                "chroma_db_dir": "C:/repo/certification/project_2/rag_module/media/output/chroma_db/ActivAssure"
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response2.status_code, 200)
    
    def test_full_workflow_react(self):
        """Test complete workflow with ReAct system."""
        # Complex multi-step query
        response = self.client.post(
            reverse('agents:agentic_query'),
            data=json.dumps({
                "query": "Find the maternity waiting period in ActivFit, calculate premium for age 28 with 5L cover, then compare with ActivAssure",
                "use_react": True,
                "conversation_history": []
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should complete successfully with multiple tools
        self.assertTrue(data.get('success', False))
        
        metadata = data.get('agentic_metadata', {})
        tools_used = metadata.get('tools_used', [])
        
        # Should use multiple tools for this complex query
        self.assertGreater(len(tools_used), 1)
    
    def test_system_comparison(self):
        """Test comparing both systems on same query."""
        query = "Calculate premium for age 35 with 10L cover"
        
        # Traditional
        response_trad = self.client.post(
            reverse('agents:orchestrated_query'),
            data=json.dumps({
                "query": query,
                "chroma_db_dir": "C:/repo/certification/project_2/rag_module/media/output/chroma_db/ActivAssure"
            }),
            content_type='application/json'
        )
        
        # ReAct
        response_react = self.client.post(
            reverse('agents:agentic_query'),
            data=json.dumps({
                "query": query,
                "use_react": True,
                "conversation_history": []
            }),
            content_type='application/json'
        )
        
        # Both should succeed
        self.assertEqual(response_trad.status_code, 200)
        self.assertEqual(response_react.status_code, 200)
        
        # Both should provide answers
        self.assertIn('answer', response_trad.json())
        self.assertIn('final_answer', response_react.json())


class ErrorHandlingTests(TestCase):
    """Tests for error handling and edge cases."""
    
    def setUp(self):
        """Set up test client."""
        self.client = Client()
    
    def test_empty_query(self):
        """Test handling of empty query."""
        response = self.client.post(
            reverse('agents:agentic_query'),
            data=json.dumps({
                "query": "",
                "use_react": True,
                "conversation_history": []
            }),
            content_type='application/json'
        )
        
        # Should handle gracefully
        self.assertIn(response.status_code, [400, 200])
    
    def test_invalid_query_format(self):
        """Test handling of malformed request."""
        response = self.client.post(
            reverse('agents:agentic_query'),
            data="invalid json",
            content_type='application/json'
        )
        
        # Should return error
        self.assertEqual(response.status_code, 400)
    
    def test_timeout_handling(self):
        """Test handling of long-running queries."""
        # Very complex query that might take time
        response = self.client.post(
            reverse('agents:agentic_query'),
            data=json.dumps({
                "query": "Calculate premium for 10 different age groups and compare all of them",
                "use_react": True,
                "conversation_history": []
            }),
            content_type='application/json'
        )
        
        # Should either complete or timeout gracefully
        self.assertIn(response.status_code, [200, 408, 500])
