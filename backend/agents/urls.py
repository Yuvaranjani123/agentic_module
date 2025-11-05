"""
Agent URLs - URL routing for agent endpoints with conversation memory.

All queries (including premium calculations) are handled through the unified
/agents/query/ endpoint which uses the orchestrator for intelligent routing.

NEW: Agentic endpoints demonstrate ReAct (Reasoning + Acting) system with
iterative reasoning, dynamic tool selection, and learning intent classification.
"""
from django.urls import path
from . import views
from . import agentic_views

urlpatterns = [
    # Unified agent endpoint - handles all query types (document Q&A + premium calculations)
    path('query/', views.agent_query, name='agent_query'),
    
    # Conversation management
    path('clear-conversation/', views.clear_conversation, name='clear_conversation'),
    path('conversation-history/', views.get_conversation_history, name='get_conversation_history'),
    
    # Evaluation
    path('evaluation-summary/', views.agent_evaluation_summary, name='agent_evaluation_summary'),
    
    # ReAct Agentic System Endpoints
    # - Thought→Action→Observation loop for dynamic multi-step queries
    # - Learning intent classification with pattern recognition
    # - Comparison with baseline orchestrator
    path('agentic/query/', agentic_views.agentic_query, name='agentic_query'),
    path('agentic/stats/', agentic_views.agentic_stats, name='agentic_stats'),
    path('agentic/reset-stats/', agentic_views.agentic_reset_stats, name='agentic_reset_stats'),
    path('agentic/evaluate/', agentic_views.agentic_evaluate, name='agentic_evaluate'),
    path('agentic/compare/', agentic_views.compare_systems, name='compare_systems'),
]