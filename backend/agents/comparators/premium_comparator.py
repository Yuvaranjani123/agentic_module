"""
Premium Comparison Module

Handles premium calculations and premium-based product comparisons.
"""
import logging
from typing import List, Dict, Optional, Any

logger = logging.getLogger(__name__)


class PremiumComparator:
    """
    Handles premium calculations and comparisons across insurance products.
    
    Integrates with PremiumCalculator to compute actual premiums for products
    and formats results for comparison.
    """
    
    def __init__(self, premium_calculator=None):
        """
        Initialize premium comparator.
        
        Args:
            premium_calculator: Optional PremiumCalculator instance
            
        Example:
            >>> from agents.calculators import PremiumCalculator
            >>> calculator = PremiumCalculator()
            >>> comparator = PremiumComparator(calculator)
        """
        self.premium_calculator = premium_calculator
        logger.info("PremiumComparator initialized")
    
    def is_available(self) -> bool:
        """
        Check if premium calculation is available.
        
        Returns:
            True if premium calculator is configured
            
        Example:
            >>> comparator.is_available()
            True
        """
        return self.premium_calculator is not None
    
    def get_available_workbooks(self) -> Dict[str, Any]:
        """
        Get available premium calculation workbooks.
        
        Returns:
            Dictionary of available workbooks
            
        Example:
            >>> workbooks = comparator.get_available_workbooks()
            >>> 'ActivAssure' in workbooks
            True
        """
        if not self.is_available():
            return {}
        
        if hasattr(self.premium_calculator, 'get_available_workbooks'):
            try:
                workbooks = self.premium_calculator.get_available_workbooks()
                logger.info(f"Available premium workbooks: {list(workbooks.keys())}")
                return workbooks
            except Exception as e:
                logger.warning(f"Could not get available workbooks: {e}")
                return {}
        
        return {}
    
    def find_matching_workbook(self, product_name: str, available_workbooks: Dict) -> Optional[str]:
        """
        Find a workbook matching the product name.
        
        Args:
            product_name: Name of the product
            available_workbooks: Dictionary of available workbooks
            
        Returns:
            Matching workbook name or None
            
        Example:
            >>> workbook = comparator.find_matching_workbook(
            ...     'ActivAssure',
            ...     {'ActivAssure_Premium.xlsx': {...}}
            ... )
            >>> workbook
            'ActivAssure_Premium.xlsx'
        """
        for wb_name in available_workbooks.keys():
            # Case-insensitive partial match
            if product_name.lower() in wb_name.lower() or wb_name.lower() in product_name.lower():
                logger.info(f"Found matching workbook '{wb_name}' for product '{product_name}'")
                return wb_name
        
        return None
    
    def categorize_products_by_premium_data(
        self, 
        product_names: List[str]
    ) -> tuple[List[str], List[str]]:
        """
        Categorize products by whether they have premium data available.
        
        Args:
            product_names: List of product names to check
            
        Returns:
            Tuple of (products_with_data, products_without_data)
            
        Example:
            >>> with_data, without = comparator.categorize_products_by_premium_data(
            ...     ['ActivAssure', 'UnknownProduct']
            ... )
            >>> 'ActivAssure' in with_data
            True
        """
        available_workbooks = self.get_available_workbooks()
        
        products_with_data = []
        products_without_data = []
        
        for product in product_names:
            has_workbook = any(
                product.lower() in wb_name.lower() or wb_name.lower() in product.lower()
                for wb_name in available_workbooks.keys()
            ) if available_workbooks else True  # Assume available if we can't check
            
            if has_workbook:
                products_with_data.append(product)
            else:
                products_without_data.append(product)
        
        return products_with_data, products_without_data
    
    def calculate_premium_for_product(
        self, 
        product_name: str, 
        premium_params: Dict
    ) -> Dict:
        """
        Calculate premium for a specific product.
        
        Args:
            product_name: Name of the product
            premium_params: Parameters for calculation (members, sum_insured, policy_type)
            
        Returns:
            Dictionary with premium calculation results
            
        Example:
            >>> result = comparator.calculate_premium_for_product(
            ...     product_name='ActivAssure',
            ...     premium_params={
            ...         'policy_type': 'family_floater',
            ...         'members': [{'age': 30}, {'age': 28}],
            ...         'sum_insured': 500000
            ...     }
            ... )
            >>> result['success']
            True
            >>> result['total_premium']
            19563.0
        """
        if not self.is_available():
            return {
                'success': False,
                'error': 'Premium calculator not available'
            }
        
        try:
            # Get available workbooks
            available_workbooks = self.get_available_workbooks()
            
            # Check if product has premium data
            matching_workbook = self.find_matching_workbook(product_name, available_workbooks)
            
            if not matching_workbook:
                return {
                    'success': False,
                    'error': f'Premium data not available for {product_name}',
                    'message': f'Please upload premium rate Excel file for {product_name}'
                }
            
            # Create product-specific calculator
            from agents.calculators import PremiumCalculator
            product_calculator = PremiumCalculator(doc_name=matching_workbook)
            logger.info(f"Created calculator for product '{product_name}' using workbook '{matching_workbook}'")
            
            # Calculate premium
            result = product_calculator.calculate_premium(
                policy_type=premium_params.get('policy_type', 'family_floater'),
                members=premium_params.get('members', []),
                sum_insured=premium_params.get('sum_insured', 500000)
            )
            
            # Check if calculation succeeded (no 'error' key means success)
            if 'error' not in result and result.get('total_premium') is not None:
                formatted_result = {
                    'success': True,
                    'total_premium': result.get('total_premium'),
                    'base_premium': result.get('gross_premium'),  # Note: 'gross_premium' not 'base_premium'
                    'gst_amount': result.get('gst_amount'),
                    'gst_rate': result.get('gst_rate', 0) * 100  # Convert to percentage
                }
                logger.info(f"Premium calculated for {product_name}: ₹{result.get('total_premium'):,.2f}")
                return formatted_result
            else:
                logger.warning(f"Premium calculation failed for {product_name}: {result.get('error')}")
                return {
                    'success': False,
                    'error': result.get('error', 'Calculation failed')
                }
        
        except Exception as e:
            logger.error(f"Premium calculation failed for {product_name}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def calculate_premiums_for_multiple_products(
        self, 
        product_names: List[str], 
        premium_params: Dict
    ) -> Dict[str, Dict]:
        """
        Calculate premiums for multiple products.
        
        Args:
            product_names: List of product names
            premium_params: Parameters for calculation
            
        Returns:
            Dictionary mapping product names to their premium results
            
        Example:
            >>> results = comparator.calculate_premiums_for_multiple_products(
            ...     product_names=['ActivAssure', 'ActivFit'],
            ...     premium_params={
            ...         'policy_type': 'family_floater',
            ...         'members': [{'age': 30}, {'age': 28}],
            ...         'sum_insured': 500000
            ...     }
            ... )
            >>> results['ActivAssure']['success']
            True
        """
        premium_results = {}
        
        for product in product_names:
            result = self.calculate_premium_for_product(product, premium_params)
            premium_results[product] = result
        
        return premium_results
    
    def has_any_successful_calculation(self, premium_results: Dict[str, Dict]) -> bool:
        """
        Check if any premium calculation succeeded.
        
        Args:
            premium_results: Dictionary of premium calculation results
            
        Returns:
            True if at least one calculation succeeded
            
        Example:
            >>> results = {'ProductA': {'success': True}, 'ProductB': {'success': False}}
            >>> comparator.has_any_successful_calculation(results)
            True
        """
        return any(
            result.get('success', False) and 'error' not in result
            for result in premium_results.values()
        )
    
    def get_failed_products(self, premium_results: Dict[str, Dict]) -> List[str]:
        """
        Get list of products where premium calculation failed.
        
        Args:
            premium_results: Dictionary of premium calculation results
            
        Returns:
            List of product names with failed calculations
            
        Example:
            >>> results = {'ProductA': {'success': True}, 'ProductB': {'success': False}}
            >>> comparator.get_failed_products(results)
            ['ProductB']
        """
        return [
            product for product, result in premium_results.items()
            if not result.get('success', False) or 'error' in result
        ]
