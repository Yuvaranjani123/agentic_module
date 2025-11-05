"""
Agentic Module - ReAct-Based Intelligent Query Processing

This module implements a pure ReAct (Reasoning + Acting) architecture:
- Iterative Thought→Action→Observation loop
- Dynamic multi-step query handling
- Learning intent classification
- Tool-based execution

Structure:
- intent_learner.py: Learning intent classification with pattern recognition
- react_agent.py: ReAct agent with Thought-Action-Observation loop
- react_tools.py: Tool wrappers for premium calculation, comparison, and retrieval
- agentic_system.py: Main system orchestrator
"""

from .intent_learner import LearningIntentClassifier
from .react_agent import ReActAgent, ReActTrace, ReActStep
from .react_tools import (
    ReActTool,
    PremiumCalculatorTool,
    PolicyComparatorTool,
    DocumentRetrieverTool
)
from .agentic_system import AgenticSystem

__all__ = [
    'LearningIntentClassifier',
    'ReActAgent',
    'ReActTrace',
    'ReActStep',
    'ReActTool',
    'PremiumCalculatorTool',
    'PolicyComparatorTool',
    'DocumentRetrieverTool',
    'AgenticSystem',
]
