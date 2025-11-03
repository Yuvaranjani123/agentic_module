"""
Comparison Response Builder

Handles LLM invocations and response formatting for comparisons.
"""
import logging
from typing import Dict, List
from config.prompts.comparison_prompts import (
    ASPECT_COMPARISON_TEMPLATE,
    CUSTOM_COMPARISON_TEMPLATE,
    PREMIUM_COMPARISON_TEMPLATE,
    build_aspect_sections,
    build_product_contexts,
    build_premium_data_section,
    build_member_info
)

logger = logging.getLogger(__name__)


class ComparisonResponseBuilder:
    """
    Builds and executes comparison prompts using LLM.
    
    Formats retrieved data into prompts and generates comparison responses.
    """
    
    def __init__(self, llm):
        """
        Initialize response builder.
        
        Args:
            llm: Language model for generating comparisons
        """
        self.llm = llm
        logger.info("ComparisonResponseBuilder initialized")
    
    def build_aspect_based_comparison(
        self, 
        product_data: Dict, 
        product_names: List[str],
        aspects: List[str]
    ) -> Dict:
        """
        Build aspect-based comparison response.
        
        Args:
            product_data: Nested dict of product->aspect->chunks
            product_names: List of product names
            aspects: List of aspects being compared
            
        Returns:
            Dictionary with comparison results
        """
        try:
            aspect_sections = build_aspect_sections(product_data, aspects)
            prompt = ASPECT_COMPARISON_TEMPLATE.format(aspect_sections=aspect_sections)
            
            response = self.llm.invoke(prompt)
            
            return {
                'success': True,
                'products': product_names,
                'aspects': aspects,
                'comparison': response.content,
                'raw_data': product_data
            }
        except Exception as e:
            logger.error(f"Error generating aspect comparison: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def build_custom_comparison(
        self, 
        query: str,
        product_names: List[str],
        product_contexts: Dict
    ) -> Dict:
        """
        Build custom query-based comparison response.
        
        Args:
            query: User's comparison query
            product_names: List of product names
            product_contexts: Dict mapping products to chunks
            
        Returns:
            Dictionary with comparison results
        """
        try:
            context_section = build_product_contexts(product_contexts, max_chunks=5)
            prompt = CUSTOM_COMPARISON_TEMPLATE.format(
                query=query,
                product_contexts=context_section
            )
            
            response = self.llm.invoke(prompt)
            
            return {
                'success': True,
                'query': query,
                'products': product_names,
                'comparison': response.content,
                'sources': product_contexts
            }
        except Exception as e:
            logger.error(f"Error in custom comparison: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def build_premium_comparison(
        self,
        query: str,
        product_names: List[str],
        product_contexts: Dict,
        premium_results: Dict,
        premium_params: Dict,
        premium_comparator
    ) -> Dict:
        """
        Build premium-inclusive comparison response.
        
        Args:
            query: User's comparison query
            product_names: List of product names
            product_contexts: Dict mapping products to chunks
            premium_results: Dict mapping products to premium calculations
            premium_params: Parameters used for calculation
            premium_comparator: PremiumComparator instance for helpers
            
        Returns:
            Dictionary with comparison results including premiums
        """
        try:
            # Build prompt sections
            doc_section = build_product_contexts(product_contexts, max_chunks=3)
            premium_section = build_premium_data_section(premium_results)
            member_section = build_member_info(premium_params)
            
            prompt = PREMIUM_COMPARISON_TEMPLATE.format(
                query=query,
                document_contexts=doc_section,
                premium_data=premium_section,
                member_info=member_section
            )
            
            response = self.llm.invoke(prompt)
            
            # Add helpful notes
            failed_products = premium_comparator.get_failed_products(premium_results)
            additional_notes = []
            
            if failed_products:
                additional_notes.append(
                    f"\n\n---\n**Note:** Premium calculation data is not available for: {', '.join(failed_products)}. "
                    f"To enable premium comparison for these products, please upload their premium rate Excel files during ingestion."
                )
            
            available_workbooks = premium_comparator.get_available_workbooks()
            if available_workbooks:
                available_list = ', '.join(available_workbooks.keys())
                additional_notes.append(
                    f"\n**Available Premium Workbooks:** {available_list}"
                )
            
            final_comparison = response.content
            if additional_notes:
                final_comparison += ''.join(additional_notes)
            
            has_any_premium = premium_comparator.has_any_successful_calculation(premium_results)
            
            return {
                'success': True,
                'query': query,
                'products': product_names,
                'comparison': final_comparison,
                'sources': product_contexts,
                'premium_calculations': premium_results if has_any_premium else None,
                'includes_premiums': has_any_premium,
                'missing_premium_data': failed_products,
                'available_workbooks': list(available_workbooks.keys())
            }
        except Exception as e:
            logger.error(f"Error in premium comparison: {e}")
            return {
                'success': False,
                'error': str(e)
            }
