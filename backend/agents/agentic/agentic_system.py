"""
Agentic System Integration with ReAct
Main orchestrator that uses ReAct (Reasoning + Acting) for dynamic multi-step task execution
"""

import logging
from typing import Dict, List, Any, Optional

from langchain_openai import AzureChatOpenAI

from .intent_learner import LearningIntentClassifier
from .react_agent import ReActAgent
from .react_tools import (
    PremiumCalculatorTool,
    PolicyComparatorTool,
    DocumentRetrieverTool,
    ProductListTool
)

logger = logging.getLogger(__name__)


class AgenticSystem:
    """
    ReAct-based Agentic System Orchestrator.
    
    Pure ReAct architecture with:
    - ReAct (Reasoning + Acting) for iterative problem solving
    - Learning intent classification for pattern recognition
    - Dynamic tool selection and execution
    
    ReAct enables dynamic multi-step queries like:
    "Calculate premium for age 32, then compare with ActivFit"
    """
    
    def __init__(self, llm: AzureChatOpenAI, calculator, comparator, retriever):
        """
        Initialize ReAct-based agentic system.
        
        Args:
            llm: Azure OpenAI instance
            calculator: PremiumCalculator instance
            comparator: PremiumComparator instance
            retriever: DocumentRetriever instance
        """
        # Intent learning (for pattern recognition)
        self.classifier = LearningIntentClassifier(llm)
        self.llm = llm
        
        # Store retriever for dynamic product switching
        self.retriever = retriever
        
        # Create ReAct tools
        self.react_tools = {
            'list_products': ProductListTool(),
            'premium_calculator': PremiumCalculatorTool(calculator),
            'policy_comparator': PolicyComparatorTool(comparator),
            'document_retriever': DocumentRetrieverTool(retriever)
        }
        
        # Create ReAct agent (primary execution)
        self.react_agent = ReActAgent(llm, self.react_tools)
        
        logger.info("ReAct Agentic System initialized with 4 tools")
    
    def process_query(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process query using ReAct agent with iterative reasoning.
        
        Args:
            query: User query
            context: Conversation context
            
        Returns:
            Complete response with reasoning trace and metadata
        """
        logger.info(f"=== ReAct System Processing: {query[:100]} ===")
        
        # Run ReAct loop for dynamic multi-step execution
        react_result = self.react_agent.run(query, context, max_iterations=10)
        
        # Classify intent for learning (tracks patterns over time)
        classification = self.classifier.classify(query, context)
        
        # Learn from execution
        inferred_intent = self._infer_intent_from_react(react_result)
        self.classifier.learn_from_feedback(
            query,
            classification['intent'],
            inferred_intent,
            context
        )
        
        # Compile response
        response = {
            'query': query,
            'mode': 'react',
            'intent_classification': classification,
            'reasoning_trace': react_result['reasoning_trace'],
            'final_answer': react_result['final_answer'],
            'success': react_result['success'],
            'agentic_metadata': {
                'reasoning_iterations': react_result['iterations'],
                'total_steps': len(react_result['reasoning_trace'].get('steps', [])),
                'tools_used': react_result['tools_used'],
                'learning_applied': True,
                'react_enabled': True,
                'dynamic_routing': len(react_result['tools_used']) > 1
            }
        }
        
        return response
    
    def _infer_intent_from_react(self, react_result: Dict[str, Any]) -> str:
        """
        Infer actual intent from ReAct execution.
        Looks at which tools were used.
        """
        tools_used = react_result.get('tools_used', [])
        
        if not tools_used:
            return 'UNKNOWN'
        
        # Map tools to intents
        tool_intent_map = {
            'premium_calculator': 'PREMIUM_CALCULATION',
            'policy_comparator': 'POLICY_COMPARISON',
            'document_retriever': 'DOCUMENT_RETRIEVAL'
        }
        
        # If multiple tools used, prioritize by last tool
        if len(tools_used) > 1:
            # Multi-step query - check combination
            if 'premium_calculator' in tools_used and 'policy_comparator' in tools_used:
                return 'PREMIUM_AND_COMPARISON'
            elif 'document_retriever' in tools_used:
                return 'COMPLEX_QUERY'
        
        # Single tool
        return tool_intent_map.get(tools_used[0], 'UNKNOWN')
    
    def evaluate(self) -> Dict[str, Any]:
        """Run evaluation with ReAct and learning metrics."""
        react_stats = self.react_agent.get_stats()
        learning_stats = self.classifier.get_learning_stats()
        
        return {
            'react_metrics': react_stats,
            'learning_metrics': learning_stats,
            'total_queries': react_stats.get('total_queries', 0),
            'success_rate': react_stats.get('success_rate', 0.0),
            'avg_iterations': react_stats.get('avg_iterations', 0),
            'tool_usage': {
                name: {'usage_count': tool.usage_count}
                for name, tool in self.react_tools.items()
            }
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get system statistics with ReAct and learning metrics."""
        return {
            'classifier': self.classifier.get_learning_stats(),
            'react': self.react_agent.get_stats(),
            'tools': {
                name: {'usage_count': tool.usage_count}
                for name, tool in self.react_tools.items()
            }
        }
    
    def reset_stats(self) -> Dict[str, str]:
        """Reset all system statistics."""
        logger.info("Resetting all system statistics")
        
        # Reset ReAct agent stats
        self.react_agent.reset_stats()
        
        # Reset tool usage counts
        for tool in self.react_tools.values():
            tool.usage_count = 0
        
        # Reset classifier stats (if method exists)
        if hasattr(self.classifier, 'reset_stats'):
            self.classifier.reset_stats()
        
        logger.info("All statistics reset successfully")
        return {'message': 'Statistics reset successfully'}
