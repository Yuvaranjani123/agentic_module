"""
Agent Orchestrator - Routes queries to appropriate specialized agents.
Uses LangChain for intelligent intent detection and routing.
"""
import os
import logging
from dotenv import load_dotenv
load_dotenv()

from langchain_openai import AzureChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage
from logs.utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """
    Orchestrates routing between specialized agents:
    - RetrievalAgent: For document Q&A, policy information, coverage details
    - PremiumCalculator: For premium calculations
    
    Uses LLM-based intent classification for intelligent routing.
    """
    
    INTENT_CLASSIFICATION_PROMPT = """You are an intent classifier for an insurance assistant system.
Analyze the user's query and classify it into ONE of these categories:

1. PREMIUM_CALCULATION - User wants to calculate insurance premium/cost
   Keywords: calculate premium, how much, cost, price, what will i pay, premium for, quote
   
2. POLICY_COMPARISON - User wants to compare different insurance products/policies
   Keywords: compare, difference between, which is better, vs, versus, contrast, similar to
   
3. DOCUMENT_RETRIEVAL - User wants information from policy documents
   Keywords: what is covered, explain, benefits, terms, conditions, eligibility, coverage details
   
4. GENERAL_INSURANCE - General insurance questions that need document search
   Default category if not premium calculation or comparison

Examples:
- "Calculate premium for 2 adults aged 35 and 40 with 5L cover" → PREMIUM_CALCULATION
- "Compare ActivAssure with HealthShield" → POLICY_COMPARISON
- "What are the differences between these two policies?" → POLICY_COMPARISON
- "What are the vaccination benefits for children?" → DOCUMENT_RETRIEVAL
- "How much will I pay for family floater with 10L cover?" → PREMIUM_CALCULATION
- "Explain the claim process" → DOCUMENT_RETRIEVAL
- "Which policy has better maternity coverage?" → POLICY_COMPARISON

User Query: {query}

Classification (respond with only the category name):"""
    
    def __init__(self):
        """Initialize the orchestrator with LLM for intent classification."""
        self.llm = AzureChatOpenAI(
            deployment_name=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT"),
            openai_api_key=os.getenv("AZURE_OPENAI_KEY"),
            openai_api_version=os.getenv("AZURE_OPENAI_CHAT_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            temperature=0.0  # Deterministic classification
        )
        logger.info("AgentOrchestrator initialized with LLM-based intent classifier")
    
    def classify_intent(self, query: str) -> str:
        """
        Classify user intent using LLM.
        
        Args:
            query: User's query text
            
        Returns:
            Intent category: 'PREMIUM_CALCULATION', 'DOCUMENT_RETRIEVAL', or 'GENERAL_INSURANCE'
        """
        try:
            # Create prompt
            prompt = self.INTENT_CLASSIFICATION_PROMPT.format(query=query)
            
            # Get classification
            response = self.llm.invoke([HumanMessage(content=prompt)])
            intent = response.content.strip().upper()
            
            # Validate and default
            valid_intents = ['PREMIUM_CALCULATION', 'POLICY_COMPARISON', 'DOCUMENT_RETRIEVAL', 'GENERAL_INSURANCE']
            if intent not in valid_intents:
                logger.warning(f"Invalid intent '{intent}', defaulting to DOCUMENT_RETRIEVAL")
                intent = 'DOCUMENT_RETRIEVAL'
            
            logger.info(f"Classified query intent: {intent}")
            return intent
            
        except Exception as e:
            logger.error(f"Error classifying intent: {e}, defaulting to DOCUMENT_RETRIEVAL")
            return 'DOCUMENT_RETRIEVAL'
    
    def route_query(self, query: str, **kwargs):
        """
        Route query to appropriate agent based on intent classification.
        
        Args:
            query: User's query
            **kwargs: Additional parameters (chroma_db_dir, chroma_base_dir, k, doc_type_filter, etc.)
            
        Returns:
            Dictionary with routing decision and parameters
        """
        intent = self.classify_intent(query)
        
        if intent == 'PREMIUM_CALCULATION':
            return {
                'agent': 'premium_calculator',
                'intent': intent,
                'query': query,
                'action': 'ROUTE_TO_CALCULATOR',
                'message': 'Routing to Premium Calculator Agent'
            }
        elif intent == 'POLICY_COMPARISON':
            return {
                'agent': 'comparison',
                'intent': intent,
                'query': query,
                'action': 'ROUTE_TO_COMPARISON',
                'message': 'Routing to Policy Comparison Agent',
                'params': kwargs
            }
        else:
            return {
                'agent': 'retrieval',
                'intent': intent,
                'query': query,
                'action': 'ROUTE_TO_RETRIEVAL',
                'message': 'Routing to Document Retrieval Agent',
                'params': kwargs
            }
    
    def extract_premium_params(self, query: str) -> dict:
        """
        Extract premium calculation parameters from query using LLM.
        
        Args:
            query: User's query about premium calculation
            
        Returns:
            Dictionary with extracted parameters:
            - policy_type: 'individual' or 'family_floater'
            - members: list of ages
            - sum_insured: coverage amount
            - plan: plan name if specified
        """
        extraction_prompt = """Extract premium calculation parameters from the user's query.

Return a JSON object with these fields:
- policy_type: "individual" or "family_floater"
- members: list of member ages (integers) - e.g., [35, 40, 7] for 2 adults and 1 child
- sum_insured: coverage amount in lakhs (convert to number) - e.g., "5L" → 500000, "10L" → 1000000
- composition: family composition if specified - e.g., "2 Adults + 1 Child"
- plan: plan name if mentioned (e.g., "Diamond")

If information is missing, set field to null.

Examples:
Query: "Calculate premium for 35 year old with 5L cover"
Output: {{"policy_type": "individual", "members": [35], "sum_insured": 500000, "composition": null, "plan": null}}

Query: "Premium for family floater 2 adults aged 35, 40 and 1 child aged 7 with 10L Diamond plan"
Output: {{"policy_type": "family_floater", "members": [35, 40, 7], "sum_insured": 1000000, "composition": "2 Adults + 1 Child", "plan": "Diamond"}}

User Query: {query}

JSON Output:"""
        
        try:
            prompt = extraction_prompt.format(query=query)
            response = self.llm.invoke([HumanMessage(content=prompt)])
            
            import json
            params = json.loads(response.content.strip())
            logger.info(f"Extracted premium parameters: {params}")
            return params
            
        except Exception as e:
            logger.error(f"Error extracting premium params: {e}")
            return {
                'policy_type': None,
                'members': None,
                'sum_insured': None,
                'composition': None,
                'plan': None,
                'error': str(e)
            }
    
    def extract_comparison_params(self, query: str, available_products: list) -> dict:
        """
        Extract policy comparison parameters from query using LLM.
        
        Args:
            query: User's query about policy comparison
            available_products: List of available product names
            
        Returns:
            Dictionary with extracted parameters:
            - products: list of product names to compare
            - aspects: specific aspects to compare (if mentioned)
            - comparison_type: 'specific' or 'general'
        """
        extraction_prompt = f"""Extract policy comparison parameters from the user's query.

Available products in the system: {available_products}

Return a JSON object with these fields:
- products: list of product names mentioned (match with available products, null if not specified)
- aspects: list of specific aspects to compare if mentioned (e.g., ["coverage", "premium", "exclusions"])
- comparison_type: "specific" if products are mentioned, "general" if asking about all products

Examples:
Query: "Compare ActivAssure with HealthShield"
Output: {{"products": ["ActivAssure", "HealthShield"], "aspects": null, "comparison_type": "specific"}}

Query: "What are the differences in maternity coverage between all policies?"
Output: {{"products": null, "aspects": ["maternity coverage"], "comparison_type": "general"}}

Query: "Which policy has better claim process and premium?"
Output: {{"products": null, "aspects": ["claim process", "premium"], "comparison_type": "general"}}

User Query: {{query}}

JSON Output:"""
        
        try:
            prompt = extraction_prompt.format(query=query)
            response = self.llm.invoke([HumanMessage(content=prompt)])
            
            import json
            params = json.loads(response.content.strip())
            logger.info(f"Extracted comparison parameters: {params}")
            return params
            
        except Exception as e:
            logger.error(f"Error extracting comparison params: {e}")
            return {
                'products': None,
                'aspects': None,
                'comparison_type': 'general',
                'error': str(e)
            }
