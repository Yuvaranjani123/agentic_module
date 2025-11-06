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
from .comparison_agent import PolicyComparisonAgent
from .orchestrator import AgentOrchestrator
from .calculators import PremiumCalculator

setup_logging()
logger = logging.getLogger(__name__)

# Store active agent sessions (in production, use Redis or database)
_agent_sessions = {}
_comparison_agent = None  # Singleton comparison agent
_orchestrator = None  # Singleton orchestrator
_premium_calculator = None  # Singleton premium calculator


# ==========================================
# Helper Functions for Agent Query Routing
# ==========================================

def _format_premium_answer(result: dict, query_text: str) -> str:
    """Format premium calculation result as human-readable answer."""
    if result.get('error'):
        return f"❌ Error calculating premium: {result['error']}"
    
    policy_type = result.get('policy_type', 'family_floater')
    
    if policy_type == 'family_floater':
        answer = f"**Premium Calculation Result**\n\n"
        answer += f"**Policy Type:** Family Floater\n"
        answer += f"**Composition:** {result.get('composition', 'N/A')}\n"
        answer += f"**Sum Insured:** ₹{result['sum_insured']:,}\n"
        answer += f"**Eldest Age:** {result.get('eldest_age')} ({result.get('age_band', 'N/A')})\n\n"
        answer += f"**Gross Premium:** ₹{result['gross_premium']:,.2f}\n"
        answer += f"**GST ({result['gst_rate']*100:.0f}%):** ₹{result['gst_amount']:,.2f}\n"
        answer += f"**Total Premium:** ₹{result['total_premium']:,.2f}"
    else:
        answer = f"**Premium Calculation Result**\n\n"
        answer += f"**Policy Type:** Individual\n"
        answer += f"**Sum Insured:** ₹{result['sum_insured']:,}\n\n"
        for i, member_premium in enumerate(result['breakdown'], 1):
            if member_premium.get('error'):
                answer += f"Member {i}: Error - {member_premium['error']}\n"
            else:
                answer += f"Member {i}: Age {member_premium['age']} ({member_premium.get('age_band', 'N/A')}) - ₹{member_premium['premium']:,.2f}\n"
        answer += f"\n**Gross Premium:** ₹{result['gross_premium']:,.2f}\n"
        answer += f"**GST ({result['gst_rate']*100:.0f}%):** ₹{result['gst_amount']:,.2f}\n"
        answer += f"**Total Premium:** ₹{result['total_premium']:,.2f}"
    
    return answer


def _handle_premium_route(query_text: str, routing_decision: dict) -> Response:
    """Handle premium calculator routing."""
    calculator = get_premium_calculator()
    orchestrator = get_orchestrator()
    
    # Extract parameters from query
    params = orchestrator.extract_premium_params(query_text)
    
    # If we have sufficient info, calculate directly
    if params.get('members') and params.get('sum_insured'):
        members = [{'age': age} for age in params['members']]
        policy_type = params.get('policy_type', 'family_floater')
        
        result = calculator.calculate_premium(
            policy_type=policy_type,
            members=members,
            sum_insured=params['sum_insured']
        )
        
        result['answer'] = _format_premium_answer(result, query_text)
        result['agent'] = 'premium_calculator'
        result['intent'] = routing_decision['intent']
        result['query'] = query_text
        
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


def _handle_comparison_route(query_text: str, routing_decision: dict, chroma_db_dir: str, k: int) -> Response:
    """Handle comparison agent routing."""
    # Get chroma base directory
    if chroma_db_dir:
        chroma_base_dir = os.path.dirname(chroma_db_dir)
    else:
        from django.conf import settings
        chroma_base_dir = os.path.join(settings.MEDIA_ROOT, "output", "chroma_db")
    
    comparison_agent = get_comparison_agent(chroma_base_dir)
    orchestrator = get_orchestrator()
    available_products = comparison_agent.get_available_products()
    
    if len(available_products) < 2:
        return Response({
            'agent': 'comparison',
            'intent': routing_decision['intent'],
            'query': query_text,
            'answer': f"I need at least 2 insurance products to make a comparison. Currently, I only have access to: {available_products}.\n\n"
                      f"Please ingest more products using the Ingestion interface with different product names.",
            'available_products': available_products,
            'error': 'insufficient_products'
        }, status=status.HTTP_200_OK)
    
    # Extract comparison parameters
    params = orchestrator.extract_comparison_params(query_text, available_products)
    products_to_compare = params.get('products')
    
    if not products_to_compare or len(products_to_compare) < 2:
        products_to_compare = available_products
    
    aspects = params.get('aspects')
    
    # Check if premium calculation is needed
    premium_keywords = ['premium', 'cost', 'price', 'how much', 'expensive', 'cheaper', 'affordable']
    needs_premium_calc = any(keyword in query_text.lower() for keyword in premium_keywords)
    
    if needs_premium_calc and comparison_agent.premium_calculator:
        logger.info("Premium comparison detected - attempting to extract parameters")
        premium_params = orchestrator.extract_premium_params(query_text)
        
        if premium_params.get('members') and premium_params.get('sum_insured'):
            members = [{'age': age} for age in premium_params['members']]
            result = comparison_agent.compare_with_premium_calculation(
                query=query_text,
                product_names=products_to_compare,
                premium_params={
                    'policy_type': premium_params.get('policy_type', 'family_floater'),
                    'members': members,
                    'sum_insured': premium_params['sum_insured']
                },
                k=k
            )
        else:
            return Response({
                'agent': 'comparison',
                'intent': routing_decision['intent'],
                'query': query_text,
                'answer': f"I can compare premiums for {', '.join(products_to_compare)}!\n\n"
                          "To calculate and compare premiums, I need:\n\n"
                          "1. **Ages** of all members to be insured\n"
                          "2. **Sum insured** (coverage amount like 2L, 5L, 10L)\n"
                          "3. **Policy type**: Individual or Family Floater\n\n"
                          "Example: 'Compare premiums for 2 adults aged 35 and 40 with 5L cover'",
                'products_to_compare': products_to_compare,
                'missing_params': ['members', 'sum_insured'],
                'available_products': available_products
            }, status=status.HTTP_200_OK)
    else:
        # Regular document-based comparison
        if not aspects:
            result = comparison_agent.quick_compare(products_to_compare, k=k)
        else:
            result = comparison_agent.compare_products(products_to_compare, aspects, k=k)
    
    if result.get('success'):
        response_data = {
            'agent': 'comparison',
            'intent': routing_decision['intent'],
            'query': query_text,
            'answer': result['comparison'],
            'products_compared': result.get('products', products_to_compare),
            'aspects': result.get('aspects', aspects) if aspects else result.get('aspects'),
            'available_products': available_products,
            'comparison_type': 'with_premiums' if result.get('includes_premiums') else 'document_only'
        }
        
        if result.get('includes_premiums'):
            response_data['premium_calculations'] = result.get('premium_calculations')
        
        return Response(response_data, status=status.HTTP_200_OK)
    else:
        return Response({
            'agent': 'comparison',
            'intent': routing_decision['intent'],
            'query': query_text,
            'answer': f"I encountered an error while comparing: {result.get('error')}",
            'error': result.get('error'),
            'available_products': available_products
        }, status=status.HTTP_200_OK)


def _handle_retrieval_route(query_text: str, routing_decision: dict, chroma_db_dir: str, 
                            k: int, doc_type_filter: str, exclude_doc_types: list, 
                            evaluate_retrieval: bool, conversation_id: str) -> Response:
    """Handle retrieval agent routing."""
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


def get_comparison_agent(chroma_base_dir: str):
    """Get or create singleton comparison agent."""
    global _comparison_agent
    if _comparison_agent is None:
        # Get premium calculator if available
        try:
            calculator = get_premium_calculator()
        except:
            calculator = None
            logger.warning("Premium calculator not available for comparison agent")
        
        _comparison_agent = PolicyComparisonAgent(
            chroma_base_dir=chroma_base_dir,
            premium_calculator=calculator
        )
        logger.info(f"Created comparison agent with base dir: {chroma_base_dir}")
    return _comparison_agent


@api_view(['POST'])
def agent_query(request):
    """
    Orchestrated agent query endpoint with intelligent routing.
    Routes queries to appropriate specialized agent:
    - Premium calculation queries → PremiumCalculator
    - Comparison queries → PolicyComparisonAgent
    - Document/policy queries → RetrievalAgent
    """
    try:
        # Extract parameters
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
        
        # Route to appropriate handler
        if routing_decision['agent'] == 'premium_calculator':
            return _handle_premium_route(query_text, routing_decision)
        
        elif routing_decision['agent'] == 'comparison':
            return _handle_comparison_route(query_text, routing_decision, chroma_db_dir, k)
        
        else:  # retrieval
            return _handle_retrieval_route(
                query_text, routing_decision, chroma_db_dir, k, 
                doc_type_filter, exclude_doc_types, evaluate_retrieval, conversation_id
            )
        
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
