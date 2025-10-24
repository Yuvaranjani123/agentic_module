"""
Agent URLs - URL routing for agent endpoints with conversation memory.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('query/', views.agent_query, name='agent_query'),
    path('evaluation-summary/', views.agent_evaluation_summary, name='agent_evaluation_summary'),
    path('clear-conversation/', views.clear_conversation, name='clear_conversation'),
    path('conversation-history/', views.get_conversation_history, name='get_conversation_history'),
]
