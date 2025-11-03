"""
Premium Calculator - Main Orchestration.

This module provides the main PremiumCalculator class that orchestrates
premium calculations using the AgeBandMatcher and ExcelWorkbookParser.

Features:
- Individual policy premium calculation
- Family floater policy premium calculation
- GST calculation (default 18%)
- Smart policy type detection and routing

Example:
    >>> calculator = PremiumCalculator(doc_name='ActivAssure')
    >>> result = calculator.calculate_premium(
    ...     policy_type='family_floater',
    ...     members=[{'age': 40}, {'age': 38}, {'age': 7}],
    ...     sum_insured=1000000
    ... )
    >>> print(result['total_premium'])  # 19563.0
"""

import logging
from typing import List, Dict, Any, Optional
from .age_matcher import AgeBandMatcher
from .excel_parser import ExcelWorkbookParser

logger = logging.getLogger(__name__)


class PremiumCalculator:
    """
    Calculate insurance premiums from Excel workbooks.
    
    This is the main calculator class that orchestrates premium calculations
    for both individual and family floater policies. It uses AgeBandMatcher
    for age matching and ExcelWorkbookParser for workbook operations.
    
    Attributes:
        parser (ExcelWorkbookParser): Excel workbook parser
        age_matcher (AgeBandMatcher): Age band matcher
        gst_rate (float): GST rate (default 0.18 for 18%)
        
    Example:
        >>> calc = PremiumCalculator(doc_name='ActivAssure')
        >>> result = calc.calculate_premium(
        ...     policy_type='individual',
        ...     members=[{'age': 35}],
        ...     sum_insured=500000
        ... )
        >>> print(result['total_premium'])
    """
    
    def __init__(
        self,
        excel_path: Optional[str] = None,
        doc_name: Optional[str] = None,
        gst_rate: float = 0.18
    ):
        """
        Initialize premium calculator.
        
        Args:
            excel_path: Direct path to Excel file (optional)
            doc_name: Product name for registry lookup (optional)
            gst_rate: GST rate as decimal (default 0.18 for 18%)
            
        Raises:
            FileNotFoundError: If workbook not found
            ValueError: If neither excel_path nor doc_name provided
            
        Example:
            >>> calc = PremiumCalculator(doc_name='ActivAssure')
            >>> # OR
            >>> calc = PremiumCalculator(excel_path='/path/to/workbook.xlsx')
        """
        self.parser = ExcelWorkbookParser(excel_path=excel_path, doc_name=doc_name)
        self.age_matcher = AgeBandMatcher()
        self.gst_rate = gst_rate
        
        # Expose some parser properties for backward compatibility
        self.excel_path = self.parser.excel_path
        self.doc_name = self.parser.doc_name
        self.sheets = self.parser.sheets
    
    @staticmethod
    def get_available_workbooks() -> Dict[str, Dict]:
        """
        Get list of all available premium workbooks from registry.
        
        Returns:
            Dictionary mapping doc_name to workbook metadata
            
        Example:
            >>> workbooks = PremiumCalculator.get_available_workbooks()
            >>> print(list(workbooks.keys()))  # ['ActivAssure', 'ActivFit']
        """
        return ExcelWorkbookParser.get_available_workbooks()
    
    def calculate_individual_premium(
        self,
        members: List[Dict[str, Any]],
        sum_insured: int,
        include_gst: bool = True
    ) -> Dict[str, Any]:
        """
        Calculate premium for individual policy (per-person premium).
        
        Each member gets their own premium based on their age.
        Total premium = sum of all individual premiums + GST.
        
        Args:
            members: List of member dicts with 'age' key
            sum_insured: Sum insured per person in INR
            include_gst: Whether to add GST to final premium
            
        Returns:
            Dict with breakdown and total:
            {
                'policy_type': 'individual',
                'gross_premium': float,
                'gst_amount': float,
                'total_premium': float,
                'breakdown': [
                    {'age': 35, 'age_band': '26-35', 'premium': 6887, ...},
                    ...
                ]
            }
            
        Example:
            >>> result = calc.calculate_individual_premium(
            ...     members=[{'age': 35}, {'age': 40}],
            ...     sum_insured=500000
            ... )
            >>> print(result['total_premium'])
        """
        if not members:
            return {
                'error': 'No members provided',
                'policy_type': 'individual',
                'gross_premium': 0,
                'gst_amount': 0,
                'total_premium': 0
            }
        
        breakdown = []
        gross_total = 0
        
        for member in members:
            age = member.get('age')
            if age is None:
                breakdown.append({
                    'member': member,
                    'error': 'Age not provided',
                    'premium': 0
                })
                continue
            
            premium = self.parser.lookup_premium('Individual', age, sum_insured, self.age_matcher)
            if premium is None:
                breakdown.append({
                    'member': member,
                    'age': age,
                    'error': 'Premium not found',
                    'premium': 0
                })
                continue
            
            # Find age band for display
            df = self.parser.sheets['Individual']
            row_idx = self.age_matcher.find_age_band_row(df, age)
            age_band = df.loc[row_idx, 'Age Band'] if row_idx is not None else 'Unknown'
            
            breakdown.append({
                'member': member,
                'age': age,
                'age_band': str(age_band),
                'sum_insured': sum_insured,
                'premium': premium
            })
            gross_total += premium
        
        gst_amount = gross_total * self.gst_rate if include_gst else 0
        total_premium = gross_total + gst_amount
        
        return {
            'policy_type': 'individual',
            'sum_insured': sum_insured,
            'gross_premium': gross_total,
            'gst_rate': self.gst_rate if include_gst else 0,
            'gst_amount': gst_amount,
            'total_premium': total_premium,
            'breakdown': breakdown
        }
    
    def calculate_family_floater_premium(
        self,
        num_adults: int,
        num_children: int,
        eldest_age: int,
        sum_insured: int,
        include_gst: bool = True
    ) -> Dict[str, Any]:
        """
        Calculate premium for family floater policy.
        
        Family floater has single premium for entire family based on:
        - Family composition (adults/children count)
        - Age of eldest member
        - Total sum insured for family
        
        Args:
            num_adults: Number of adults (1-2 typically)
            num_children: Number of children (0-4 typically)
            eldest_age: Age of eldest member (used for age band lookup)
            sum_insured: Total sum insured for family in INR
            include_gst: Whether to add GST to final premium
            
        Returns:
            Dict with premium details:
            {
                'policy_type': 'family_floater',
                'composition': '2 Adults + 1 Child',
                'gross_premium': float,
                'gst_amount': float,
                'total_premium': float,
                ...
            }
            
        Example:
            >>> result = calc.calculate_family_floater_premium(
            ...     num_adults=2,
            ...     num_children=1,
            ...     eldest_age=40,
            ...     sum_insured=1000000
            ... )
            >>> print(result['total_premium'])  # 19563.0
        """
        # Determine sheet name based on composition
        if num_children == 0:
            if num_adults == 1:
                sheet_name = 'Individual'
            elif num_adults == 2:
                sheet_name = '2 Adults'
            else:
                return {'error': f'Unsupported composition: {num_adults} adults, {num_children} children'}
        elif num_adults == 1:
            sheet_name = f'1 Adult + {num_children} Child' if num_children == 1 else f'1 Adult + {num_children} Children'
        elif num_adults == 2:
            sheet_name = f'2 Adults + {num_children} Child' if num_children == 1 else f'2 Adults + {num_children} Children'
        else:
            return {'error': f'Unsupported composition: {num_adults} adults, {num_children} children'}
        
        # Check if sheet exists
        if sheet_name not in self.parser.sheets:
            return {
                'error': f"Sheet '{sheet_name}' not found in workbook. Available sheets: {list(self.parser.sheets.keys())}",
                'policy_type': 'family_floater'
            }
        
        # Lookup premium
        gross_premium = self.parser.lookup_premium(sheet_name, eldest_age, sum_insured, self.age_matcher)
        if gross_premium is None:
            return {
                'error': f'Premium not found for age {eldest_age}, sum insured {sum_insured} in sheet {sheet_name}',
                'policy_type': 'family_floater',
                'composition': sheet_name
            }
        
        # Find age band for display
        df = self.parser.sheets[sheet_name]
        row_idx = self.age_matcher.find_age_band_row(df, eldest_age)
        age_band = df.loc[row_idx, 'Age Band'] if row_idx is not None else 'Unknown'
        
        gst_amount = gross_premium * self.gst_rate if include_gst else 0
        total_premium = gross_premium + gst_amount
        
        return {
            'policy_type': 'family_floater',
            'composition': sheet_name,
            'num_adults': num_adults,
            'num_children': num_children,
            'eldest_age': eldest_age,
            'age_band': str(age_band),
            'sum_insured': sum_insured,
            'gross_premium': gross_premium,
            'gst_rate': self.gst_rate if include_gst else 0,
            'gst_amount': gst_amount,
            'total_premium': total_premium
        }
    
    def calculate_premium(
        self,
        policy_type: str,
        members: Optional[List[Dict[str, Any]]] = None,
        num_adults: Optional[int] = None,
        num_children: Optional[int] = None,
        sum_insured: int = 500000,
        include_gst: bool = True
    ) -> Dict[str, Any]:
        """
        Smart premium calculator that routes to individual or family floater.
        
        This is the main entry point for premium calculations. It automatically
        detects the composition from members list if not explicitly provided.
        
        Args:
            policy_type: 'individual' or 'family_floater'
            members: List of member dicts with 'age' (for individual) or for auto-detection
            num_adults: Number of adults (for family floater)
            num_children: Number of children (for family floater)
            sum_insured: Sum insured in INR
            include_gst: Whether to add GST
            
        Returns:
            Premium calculation result dict
            
        Example:
            >>> # Individual policy
            >>> result = calc.calculate_premium(
            ...     policy_type='individual',
            ...     members=[{'age': 35}],
            ...     sum_insured=500000
            ... )
            
            >>> # Family floater with auto-detection
            >>> result = calc.calculate_premium(
            ...     policy_type='family_floater',
            ...     members=[{'age': 40}, {'age': 38}, {'age': 7}],
            ...     sum_insured=1000000
            ... )
            
            >>> # Family floater with explicit counts
            >>> result = calc.calculate_premium(
            ...     policy_type='family_floater',
            ...     num_adults=2,
            ...     num_children=1,
            ...     members=[{'age': 40}],  # Just need eldest age
            ...     sum_insured=1000000
            ... )
        """
        if policy_type == 'individual':
            return self.calculate_individual_premium(members or [], sum_insured, include_gst)
        
        elif policy_type == 'family_floater':
            # If members provided, auto-detect composition
            if members and (num_adults is None or num_children is None):
                adult_threshold = 18
                adults = [m for m in members if m.get('age', 0) >= adult_threshold]
                children = [m for m in members if m.get('age', 0) < adult_threshold]
                num_adults = len(adults)
                num_children = len(children)
                eldest_age = max([m['age'] for m in adults]) if adults else 18
            else:
                # Use provided counts
                if members:
                    eldest_age = max([m['age'] for m in members])
                else:
                    return {'error': 'Must provide members or eldest_age for family floater'}
            
            return self.calculate_family_floater_premium(
                num_adults, num_children, eldest_age, sum_insured, include_gst
            )
        
        else:
            return {'error': f"Unknown policy_type: {policy_type}. Use 'individual' or 'family_floater'"}
