"""
Agent Views - API endpoints for the retrieval agent with conversation memory.
"""
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import logging
import os
from logs.utils import setup_logging
from .retrieval_agent import RetrievalAgent
from .orchestrator import AgentOrchestrator
from .premium_calculator import PremiumCalculator

setup_logging()
logger = logging.getLogger(__name__)

# Store active agent sessions (in production, use Redis or database)
_agent_sessions = {}
_orchestrator = None  # Singleton orchestrator
_premium_calculator = None  # Singleton premium calculator


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


def get_orchestrator():
    """Get or create singleton orchestrator."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgentOrchestrator()
        logger.info("Created orchestrator singleton")
    return _orchestrator


def get_premium_calculator():
    """Get or create singleton premium calculator."""
    global _premium_calculator
    if _premium_calculator is None:
        # Try to load from registry (dynamic)
        try:
            _premium_calculator = PremiumCalculator()  # Will auto-discover from registry
            logger.info(f"Created premium calculator with workbook: {_premium_calculator.excel_path}")
        except FileNotFoundError as e:
            logger.warning(f"No premium workbook found in registry: {e}")
            # Try fallback path for backward compatibility
            fallback_path = os.path.join("media", "logs", "activ_assure_premium_chart.xlsx")
            if os.path.exists(fallback_path):
                _premium_calculator = PremiumCalculator(excel_path=fallback_path)
                logger.info(f"Using fallback premium workbook: {fallback_path}")
            else:
                raise FileNotFoundError(
                    "No premium workbook available. Please upload one via /api/upload_premium_excel/"
                )
    return _premium_calculator


@api_view(['POST'])
def agent_query(request):
    """
    Orchestrated agent query endpoint with intelligent routing.
    Routes queries to appropriate specialized agent:
    - Premium calculation queries → PremiumCalculator
    - Document/policy queries → RetrievalAgent
    
    Supports conversation memory for retrieval agent.
    """
    try:
        query_text = request.data.get("query")
        chroma_db_dir = request.data.get("chroma_db_dir")
        k = request.data.get("k", 5)
        doc_type_filter = request.data.get("doc_type")  
        exclude_doc_types = request.data.get("exclude_doc_types")
        evaluate_retrieval = request.data.get("evaluate", False)
        conversation_id = request.data.get("conversation_id")
        
        logger.info(f"Orchestrated query: '{query_text}'")
        
        # Validation
        if not query_text:
            logger.warning("Missing 'query' parameter")
            return Response({"error": "query is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get orchestrator and route query
        orchestrator = get_orchestrator()
        routing_decision = orchestrator.route_query(
            query=query_text,
            chroma_db_dir=chroma_db_dir,
            k=k,
            doc_type_filter=doc_type_filter,
            exclude_doc_types=exclude_doc_types
        )
        
        logger.info(f"Routing decision: {routing_decision['agent']} (intent: {routing_decision['intent']})")
        
        # Route to premium calculator
        if routing_decision['agent'] == 'premium_calculator':
            calculator = get_premium_calculator()
            
            # Extract parameters from query
            params = orchestrator.extract_premium_params(query_text)
            
            # If we have sufficient info, calculate directly
            if params.get('members') and params.get('sum_insured'):
                members = [{'age': age} for age in params['members']]
                policy_type = params.get('policy_type', 'family_floater')  # Default to family_floater if not specified
                
                result = calculator.calculate_premium(
                    policy_type=policy_type,
                    members=members,
                    sum_insured=params['sum_insured']
                )
                result['agent'] = 'premium_calculator'
                result['intent'] = routing_decision['intent']
                result['query'] = query_text
                # Add composition info from params for display (not calculation)
                if params.get('composition'):
                    result['composition_description'] = params['composition']
                return Response(result, status=status.HTTP_200_OK)
            else:
                # Need more information
                return Response({
                    'agent': 'premium_calculator',
                    'intent': routing_decision['intent'],
                    'query': query_text,
                    'answer': "I can help you calculate the premium! I need:\n\n"
                              "1. **Ages** of all members to be insured\n"
                              "2. **Sum insured** (coverage amount like 2L, 5L, 10L)\n"
                              "3. **Policy type**: Individual or Family Floater\n\n"
                              "For family floater, please mention composition like '2 Adults + 1 Child'.\n\n"
                              "Example: 'Calculate premium for 2 adults aged 35 and 40 with 1 child aged 7, sum insured 10L'",
                    'missing_params': ['members', 'sum_insured'] if not params.get('members') else ['sum_insured'],
                    'extracted_params': params
                }, status=status.HTTP_200_OK)
        
        # Route to retrieval agent
        else:
            if not chroma_db_dir:
                logger.warning("Missing 'chroma_db_dir' parameter for retrieval")
                return Response({"error": "chroma_db_dir is required for document queries"}, 
                              status=status.HTTP_400_BAD_REQUEST)
            
            agent = get_or_create_agent(chroma_db_dir=chroma_db_dir, conversation_id=conversation_id)
            
            result = agent.query(
                query_text=query_text,
                k=k,
                doc_type_filter=doc_type_filter,
                exclude_doc_types=exclude_doc_types,
                evaluate_retrieval=evaluate_retrieval,
                conversation_id=conversation_id
            )
            
            result['agent'] = 'retrieval'
            result['intent'] = routing_decision['intent']
            
            logger.info("Retrieval agent query completed successfully")
            return Response(result, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in orchestrated agent_query: {e}", exc_info=True)
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
