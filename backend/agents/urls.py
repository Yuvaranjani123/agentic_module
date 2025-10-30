"""
Agent URLs - URL routing for agent endpoints with conversation memory.

All queries (including premium calculations) are handled through the unified
/agents/query/ endpoint which uses the orchestrator for intelligent routing.
"""
from django.urls import path
from . import views

urlpatterns = [
    # Unified agent endpoint - handles all query types (document Q&A + premium calculations)
    path('query/', views.agent_query, name='agent_query'),
    
    # Conversation management
    path('clear-conversation/', views.clear_conversation, name='clear_conversation'),
    path('conversation-history/', views.get_conversation_history, name='get_conversation_history'),
    
    # Evaluation
    path('evaluation-summary/', views.agent_evaluation_summary, name='agent_evaluation_summary'),
]
