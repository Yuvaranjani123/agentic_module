"""
Policy Comparison Agent - Orchestrates multi-product comparisons.

This agent coordinates document-based and premium-based comparisons across
multiple insurance products using modular comparator components.
"""
import os
from dotenv import load_dotenv
load_dotenv()

from langchain_openai import AzureOpenAIEmbeddings, AzureChatOpenAI
import logging
from logs.utils import setup_logging
from typing import List, Dict, Optional

# Import comparator modules
from .comparators import DocumentComparator, PremiumComparator, ComparisonResponseBuilder

# Import prompt configurations
from config.prompts.comparison_prompts import (
    DEFAULT_COMPARISON_ASPECTS,
    refine_query_for_aspect
)

setup_logging()
logger = logging.getLogger(__name__)


class PolicyComparisonAgent:
    """
    Agent that orchestrates policy comparisons across multiple products.
    
    Coordinates document retrieval, premium calculations, and LLM-based
    comparison generation.
    
    Example:
        >>> agent = PolicyComparisonAgent(
        ...     chroma_base_dir="media/output/chroma_db",
        ...     premium_calculator=calculator
        ... )
        >>> result = agent.custom_compare(
        ...     query="Compare maternity benefits",
        ...     product_names=["ActivAssure", "ActivFit"]
        ... )
    """
    
    def __init__(self, chroma_base_dir: str, premium_calculator=None):
        """
        Initialize the Policy Comparison Agent.
        
        Args:
            chroma_base_dir: Base directory containing all product databases
            premium_calculator: Optional PremiumCalculator instance for premium comparisons
        """
        self.chroma_base_dir = chroma_base_dir
        
        # Initialize embeddings
        self.embeddings = AzureOpenAIEmbeddings(
            deployment=os.getenv("AZURE_OPENAI_TEXT_DEPLOYMENT_EMBEDDINGS"),
            openai_api_key=os.getenv("AZURE_OPENAI_KEY"),
            openai_api_version=os.getenv("AZURE_OPENAI_TEXT_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        
        # Initialize LLM
        self.llm = AzureChatOpenAI(
            deployment_name=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT"),
            openai_api_key=os.getenv("AZURE_OPENAI_KEY"),
            openai_api_version=os.getenv("AZURE_OPENAI_TEXT_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            temperature=0.3  # Lower temperature for more factual comparisons
        )
        
        # Initialize modular components
        self.doc_comparator = DocumentComparator(chroma_base_dir, self.embeddings, self.llm)
        self.premium_comparator = PremiumComparator(premium_calculator)
        self.response_builder = ComparisonResponseBuilder(self.llm)
        
        logger.info(f"PolicyComparisonAgent initialized with {len(self.doc_comparator.get_available_products())} products")
    
    def get_available_products(self) -> List[str]:
        """
        Get list of available products for comparison.
        
        Returns:
            List of product names
            
        Example:
            >>> agent.get_available_products()
            ['ActivAssure', 'ActivFit', 'HealthPlus']
        """
        return self.doc_comparator.get_available_products()
    
    def compare_products(
        self, 
        product_names: List[str], 
        comparison_aspects: List[str], 
        k: int = 5
    ) -> Dict:
        """
        Compare specific products on given aspects.
        
        Args:
            product_names: List of product names to compare
            comparison_aspects: List of aspects to compare
            k: Number of chunks to retrieve per product
            
        Returns:
            Dictionary with comparison results
            
        Example:
            >>> result = agent.compare_products(
            ...     product_names=['ActivAssure', 'ActivFit'],
            ...     comparison_aspects=['coverage', 'premium'],
            ...     k=5
            ... )
            >>> result['success']
            True
        """
        logger.info(f"Comparing products: {product_names} on aspects: {comparison_aspects}")
        
        # Validate products
        valid_products, invalid_products = self.doc_comparator.validate_products(product_names)
        if invalid_products:
            return {
                'success': False,
                'error': f"Products not found: {invalid_products}",
                'available_products': self.get_available_products()
            }
        
        # Retrieve information for each product and aspect
        product_data = self.doc_comparator.retrieve_by_aspects(
            product_names, comparison_aspects, k
        )
        
        # Build comparison response
        return self.response_builder.build_aspect_based_comparison(
            product_data, product_names, comparison_aspects
        )
    
    def compare_all_products(self, comparison_aspects: List[str], k: int = 5) -> Dict:
        """
        Compare all available products.
        
        Args:
            comparison_aspects: List of aspects to compare
            k: Number of chunks to retrieve per product
            
        Returns:
            Comparison results for all products
            
        Example:
            >>> result = agent.compare_all_products(
            ...     comparison_aspects=['coverage', 'premium']
            ... )
        """
        available = self.get_available_products()
        
        if len(available) < 2:
            return {
                'success': False,
                'error': 'Need at least 2 products for comparison',
                'available_products': available
            }
        
        return self.compare_products(available, comparison_aspects, k)
    
    def quick_compare(self, product_names: List[str], k: int = 5) -> Dict:
        """
        Quick comparison with default aspects.
        
        Args:
            product_names: List of products to compare
            k: Number of chunks to retrieve
            
        Returns:
            Comparison results with default aspects
            
        Example:
            >>> result = agent.quick_compare(['ActivAssure', 'ActivFit'])
        """
        return self.compare_products(product_names, DEFAULT_COMPARISON_ASPECTS, k)
    
    def custom_compare(
        self, 
        query: str, 
        product_names: Optional[List[str]] = None, 
        k: int = 5
    ) -> Dict:
        """
        Free-form comparison based on natural language query.
        
        Args:
            query: Natural language comparison query
            product_names: List of products to compare (None = all products)
            k: Number of chunks to retrieve
            
        Returns:
            Comparison results based on query
            
        Example:
            >>> result = agent.custom_compare(
            ...     query="Compare maternity benefits",
            ...     product_names=['ActivAssure', 'ActivFit']
            ... )
        """
        if product_names is None:
            product_names = self.get_available_products()
        
        if len(product_names) < 2:
            return {
                'success': False,
                'error': 'Need at least 2 products for comparison'
            }
        
        logger.info(f"Custom comparison query: {query} for products: {product_names}")
        
        # Refine query for focused retrieval
        focused_query = refine_query_for_aspect(query)
        logger.info(f"Refined query for retrieval: {focused_query}")
        
        # Retrieve relevant information from each product
        product_contexts = self.doc_comparator.retrieve_from_multiple_products(
            product_names, focused_query, k
        )
        
        # Build comparison response
        return self.response_builder.build_custom_comparison(
            query, product_names, product_contexts
        )
    
    def compare_with_premium_calculation(
        self, 
        query: str, 
        product_names: List[str], 
        premium_params: Dict, 
        k: int = 5
    ) -> Dict:
        """
        Compare products including actual premium calculations.
        
        Args:
            query: Comparison query
            product_names: List of products to compare
            premium_params: Parameters for premium calculation (members, sum_insured, policy_type)
            k: Number of chunks to retrieve
            
        Returns:
            Comparison with document info AND calculated premiums
            
        Example:
            >>> result = agent.compare_with_premium_calculation(
            ...     query="Which is more affordable?",
            ...     product_names=['ActivAssure', 'ActivFit'],
            ...     premium_params={
            ...         'policy_type': 'family_floater',
            ...         'members': [{'age': 30}, {'age': 28}],
            ...         'sum_insured': 500000
            ...     }
            ... )
        """
        # Check if premium calculation is available
        if not self.premium_comparator.is_available():
            logger.warning("Premium calculator not available, falling back to document-only comparison")
            return self.custom_compare(query, product_names, k)
        
        if len(product_names) < 2:
            return {
                'success': False,
                'error': 'Need at least 2 products for comparison'
            }
        
        logger.info(f"Comparison with premium calculation for: {product_names}")
        
        # Check which products have premium data
        products_with_data, products_without_data = \
            self.premium_comparator.categorize_products_by_premium_data(product_names)
        
        # If no products have premium data, inform user
        if not products_with_data and products_without_data:
            available_workbooks = self.premium_comparator.get_available_workbooks()
            return {
                'success': False,
                'error': f"Premium calculation data not available for: {', '.join(products_without_data)}",
                'message': f"To compare premiums across {', '.join(product_names)}, please upload premium rate Excel files for each product.",
                'available_workbooks': list(available_workbooks.keys())
            }
        
        # Get document-based information
        product_contexts = self.doc_comparator.retrieve_from_multiple_products(
            product_names, query, k
        )
        
        # Calculate premiums for all products
        premium_results = self.premium_comparator.calculate_premiums_for_multiple_products(
            product_names, premium_params
        )
        
        # Build enhanced comparison response
        return self.response_builder.build_premium_comparison(
            query, product_names, product_contexts, premium_results, 
            premium_params, self.premium_comparator
        )
