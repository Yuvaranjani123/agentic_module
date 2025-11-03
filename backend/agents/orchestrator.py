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
from config.prompts.orchestrator_prompts import (
    INTENT_CLASSIFICATION_PROMPT,
    PREMIUM_PARAMETER_EXTRACTION_PROMPT,
    get_comparison_parameter_extraction_prompt,
    VALID_INTENTS,
    DEFAULT_INTENT
)

setup_logging()
logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """
    Orchestrates routing between specialized agents:
    - RetrievalAgent: For document Q&A, policy information, coverage details
    - PremiumCalculator: For premium calculations
    
    Uses LLM-based intent classification for intelligent routing.
    """
    
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
            # Create prompt using config
            prompt = INTENT_CLASSIFICATION_PROMPT.format(query=query)
            
            # Get classification
            response = self.llm.invoke([HumanMessage(content=prompt)])
            intent = response.content.strip().upper()
            
            # Validate and default
            if intent not in VALID_INTENTS:
                logger.warning(f"Invalid intent '{intent}', defaulting to {DEFAULT_INTENT}")
                intent = DEFAULT_INTENT
            
            logger.info(f"Classified query intent: {intent}")
            return intent
            
        except Exception as e:
            logger.error(f"Error classifying intent: {e}, defaulting to {DEFAULT_INTENT}")
            return DEFAULT_INTENT
    
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
        try:
            prompt = PREMIUM_PARAMETER_EXTRACTION_PROMPT.format(query=query)
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
        try:
            prompt = get_comparison_parameter_extraction_prompt(available_products).format(query=query)
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
