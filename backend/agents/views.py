"""
Agent Views - API endpoints for the retrieval agent with conversation memory.
"""
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import logging
from logs.utils import setup_logging
from .retrieval_agent import RetrievalAgent

setup_logging()
logger = logging.getLogger(__name__)

# Store active agent sessions (in production, use Redis or database)
_agent_sessions = {}


def get_or_create_agent(chroma_db_dir: str, conversation_id: str = None):
    """
    Get existing agent session or create new one.
    
    Args:
        chroma_db_dir: ChromaDB directory path
        conversation_id: Optional conversation ID for session management
        
    Returns:
        RetrievalAgent instance
    """
    session_key = f"{chroma_db_dir}:{conversation_id}" if conversation_id else chroma_db_dir
    
    if session_key not in _agent_sessions:
        _agent_sessions[session_key] = RetrievalAgent(chroma_db_dir=chroma_db_dir)
        logger.info(f"Created new agent session: {session_key}")
    
    return _agent_sessions[session_key]


@api_view(['POST'])
def agent_query(request):
    """
    Agent-based query endpoint with conversation memory support.
    Uses RetrievalAgent to handle document querying and answer generation.
    Supports follow-up questions via conversation_id.
    """
    try:
        query_text = request.data.get("query")
        chroma_db_dir = request.data.get("chroma_db_dir")
        k = request.data.get("k", 5)
        doc_type_filter = request.data.get("doc_type")  # Can be string or list
        exclude_doc_types = request.data.get("exclude_doc_types")  # List of types to exclude
        evaluate_retrieval = request.data.get("evaluate", False)
        conversation_id = request.data.get("conversation_id")  # For memory management
        
        logger.info(f"Agent query: '{query_text}', k={k}, doc_type={doc_type_filter}, exclude={exclude_doc_types}, conv_id={conversation_id}")
        
        # Validation
        if not query_text:
            logger.warning("Missing 'query' parameter")
            return Response({"error": "query is required"}, status=status.HTTP_400_BAD_REQUEST)
        if not chroma_db_dir:
            logger.warning("Missing 'chroma_db_dir' parameter")
            return Response({"error": "chroma_db_dir is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get or create agent with conversation memory
        agent = get_or_create_agent(chroma_db_dir=chroma_db_dir, conversation_id=conversation_id)
        
        result = agent.query(
            query_text=query_text,
            k=k,
            doc_type_filter=doc_type_filter,
            exclude_doc_types=exclude_doc_types,
            evaluate_retrieval=evaluate_retrieval,
            conversation_id=conversation_id
        )
        
        logger.info("Agent query completed successfully")
        return Response(result, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in agent_query: {e}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def agent_evaluation_summary(request):
    """
    Get evaluation summary statistics.
    """
    try:
        chroma_db_dir = request.GET.get("chroma_db_dir")
        
        if not chroma_db_dir:
            return Response({"error": "chroma_db_dir is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        agent = RetrievalAgent(chroma_db_dir=chroma_db_dir)
        summary = agent.evaluator.get_evaluation_summary()
        
        logger.info("Evaluation summary retrieved")
        return Response(summary, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error getting evaluation summary: {e}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def clear_conversation(request):
    """
    Clear conversation history for a specific session.
    """
    try:
        chroma_db_dir = request.data.get("chroma_db_dir")
        conversation_id = request.data.get("conversation_id")
        
        if not chroma_db_dir:
            return Response({"error": "chroma_db_dir is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        agent = get_or_create_agent(chroma_db_dir=chroma_db_dir, conversation_id=conversation_id)
        agent.clear_history()
        
        logger.info(f"Conversation cleared for session: {conversation_id}")
        return Response({"message": "Conversation history cleared"}, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error clearing conversation: {e}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_conversation_history(request):
    """
    Get conversation history for a specific session.
    """
    try:
        chroma_db_dir = request.GET.get("chroma_db_dir")
        conversation_id = request.GET.get("conversation_id")
        
        if not chroma_db_dir:
            return Response({"error": "chroma_db_dir is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        session_key = f"{chroma_db_dir}:{conversation_id}" if conversation_id else chroma_db_dir
        
        if session_key in _agent_sessions:
            history = _agent_sessions[session_key].get_history()
            return Response({"history": history, "count": len(history)}, status=status.HTTP_200_OK)
        else:
            return Response({"history": [], "count": 0}, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error getting conversation history: {e}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
