"""
Excel Workbook Parser for Premium Calculator.

This module handles loading and querying premium Excel workbooks,
including registry management and premium lookup operations.

Features:
- Workbook loading and sheet parsing
- Premium workbook registry management
- Sum insured column matching
- Premium value lookup

Example:
    >>> parser = ExcelWorkbookParser(doc_name='ActivAssure')
    >>> premium = parser.lookup_premium('Individual', age=35, sum_insured=500000)
    >>> print(premium)  # 12500.0
"""

import os
import json
import re
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd
from django.conf import settings

logger = logging.getLogger(__name__)


class ExcelWorkbookParser:
    """
    Load and parse premium Excel workbooks.
    
    This class manages Excel workbook loading, sheet parsing,
    and premium lookups for insurance calculations.
    
    Attributes:
        excel_path (Path): Path to the Excel workbook
        doc_name (str): Document/product name
        workbook (pd.ExcelFile): Loaded Excel workbook
        sheets (Dict[str, pd.DataFrame]): Parsed sheets
        
    Example:
        >>> parser = ExcelWorkbookParser(doc_name='ActivAssure')
        >>> sheets = parser.get_sheet_names()
        >>> premium = parser.lookup_premium('Individual', 35, 500000)
    """
    
    def __init__(self, excel_path: Optional[str] = None, doc_name: Optional[str] = None):
        """
        Initialize Excel workbook parser.
        
        Args:
            excel_path: Direct path to Excel file (optional)
            doc_name: Product name for registry lookup (optional)
            
        Raises:
            FileNotFoundError: If workbook not found
            ValueError: If neither excel_path nor doc_name provided
        """
        if excel_path is None:
            excel_path = self._find_premium_workbook(doc_name)
        
        self.excel_path = Path(excel_path)
        self.doc_name = doc_name or self.excel_path.stem
        self.workbook = None
        self.sheets = {}
        self._load_workbook()
    
    @staticmethod
    def _find_premium_workbook(doc_name: Optional[str] = None) -> str:
        """
        Find premium workbook from registry.
        
        Args:
            doc_name: Specific document name to lookup (optional)
            
        Returns:
            Path to Excel file
            
        Raises:
            FileNotFoundError: If no workbook found
        """
        premium_dir = os.path.join(settings.MEDIA_ROOT, 'premium_workbooks')
        registry_path = os.path.join(premium_dir, 'premium_workbooks_registry.json')
        
        # Check registry exists
        if not os.path.exists(registry_path):
            # Fallback to hardcoded path for backward compatibility
            fallback_path = os.path.join(settings.MEDIA_ROOT, 'logs', 'activ_assure_premium_chart.xlsx')
            if os.path.exists(fallback_path):
                logger.warning(f"Registry not found, using fallback: {fallback_path}")
                return fallback_path
            raise FileNotFoundError(
                f"No premium workbook registry found at {registry_path}. "
                "Please upload a premium Excel workbook first via /api/upload_premium_excel/"
            )
        
        # Load registry
        with open(registry_path, 'r') as f:
            registry = json.load(f)
        
        if not registry:
            raise FileNotFoundError("Premium workbook registry is empty. Please upload a premium Excel workbook.")
        
        # If doc_name specified, lookup that specific workbook
        if doc_name:
            if doc_name not in registry:
                available = ', '.join(registry.keys())
                raise FileNotFoundError(
                    f"Premium workbook '{doc_name}' not found in registry. "
                    f"Available: {available}"
                )
            return registry[doc_name]['excel_path']
        
        # Otherwise, use the first available workbook
        first_doc = list(registry.keys())[0]
        excel_path = registry[first_doc]['excel_path']
        logger.info(f"Using first available premium workbook: {first_doc} -> {excel_path}")
        return excel_path
    
    @staticmethod
    def get_available_workbooks() -> Dict[str, Dict]:
        """
        Get list of all available premium workbooks from registry.
        
        Returns:
            Dictionary mapping doc_name to workbook metadata
            
        Example:
            >>> workbooks = ExcelWorkbookParser.get_available_workbooks()
            >>> print(workbooks.keys())  # ['ActivAssure', 'ActivFit']
        """
        premium_dir = os.path.join(settings.MEDIA_ROOT, 'premium_workbooks')
        registry_path = os.path.join(premium_dir, 'premium_workbooks_registry.json')
        
        if not os.path.exists(registry_path):
            return {}
        
        with open(registry_path, 'r') as f:
            return json.load(f)
    
    def _load_workbook(self) -> None:
        """
        Load Excel workbook and all sheets into memory.
        
        Raises:
            Exception: If workbook loading fails
        """
        try:
            self.workbook = pd.ExcelFile(self.excel_path)
            for sheet_name in self.workbook.sheet_names:
                df = pd.read_excel(self.workbook, sheet_name)
                # Clean column names and ensure proper types
                df.columns = [str(c).strip() for c in df.columns]
                self.sheets[sheet_name] = df
            logger.info(f"Loaded workbook with {len(self.sheets)} sheets: {list(self.sheets.keys())}")
        except Exception as e:
            logger.error(f"Error loading workbook {self.excel_path}: {e}")
            raise
    
    def get_sheet_names(self) -> list:
        """
        Get list of all sheet names in workbook.
        
        Returns:
            List of sheet names
        """
        return list(self.sheets.keys())
    
    def get_sheet(self, sheet_name: str) -> Optional[pd.DataFrame]:
        """
        Get a specific sheet by name.
        
        Args:
            sheet_name: Name of the sheet
            
        Returns:
            DataFrame or None if sheet not found
        """
        return self.sheets.get(sheet_name)
    
    @staticmethod
    def parse_sum_insured(sum_insured_input: Any) -> int:
        """
        Parse sum insured input to integer INR value.
        
        Args:
            sum_insured_input: Sum insured value (can be string, int, or float)
            
        Returns:
            Integer value in INR
            
        Raises:
            ValueError: If sum insured cannot be parsed
            
        Examples:
            >>> ExcelWorkbookParser.parse_sum_insured("2L")
            200000
            >>> ExcelWorkbookParser.parse_sum_insured("10L")
            1000000
            >>> ExcelWorkbookParser.parse_sum_insured(500000)
            500000
            >>> ExcelWorkbookParser.parse_sum_insured("5 lakh")
            500000
        """
        if isinstance(sum_insured_input, (int, float)):
            return int(sum_insured_input)
        
        s = str(sum_insured_input).strip().upper().replace(',', '').replace(' ', '')
        
        # Handle "2L", "10L" format
        match = re.match(r'(\d+\.?\d*)L', s)
        if match:
            return int(float(match.group(1)) * 100000)
        
        # Handle "LAKH" or "LAC" suffix
        match = re.match(r'(\d+\.?\d*)(LAKH|LAC)', s)
        if match:
            return int(float(match.group(1)) * 100000)
        
        # Try direct numeric parse
        try:
            return int(float(s))
        except:
            raise ValueError(f"Cannot parse sum insured: {sum_insured_input}")
    
    def find_sum_insured_column(self, df: pd.DataFrame, sum_insured: int) -> Optional[str]:
        """
        Find the column name that matches the sum insured.
        
        Uses ceiling rule: if exact match not found, use next higher column.
        
        Args:
            df: DataFrame with sum insured columns
            sum_insured: Target sum insured in INR
            
        Returns:
            Column name or None if no suitable column found
            
        Example:
            >>> df = parser.get_sheet('Individual')
            >>> col = parser.find_sum_insured_column(df, 500000)
            >>> print(col)  # '5L' or '500000'
        """
        # Parse all column headers (skip 'Age Band')
        candidates = []
        for col in df.columns:
            if col == 'Age Band':
                continue
            try:
                col_value = self.parse_sum_insured(col)
                candidates.append((col_value, col))
            except:
                continue
        
        if not candidates:
            return None
        
        # Sort by value
        candidates.sort(key=lambda x: x[0])
        
        # Find exact match
        for val, col in candidates:
            if val == sum_insured:
                return col
        
        # Ceiling rule: find next higher
        for val, col in candidates:
            if val > sum_insured:
                logger.info(f"Using ceiling column {col} ({val}) for requested {sum_insured}")
                return col
        
        # No higher value, use highest available
        highest_col = candidates[-1][1]
        logger.info(f"Using highest column {highest_col} for requested {sum_insured}")
        return highest_col
    
    def lookup_premium(
        self,
        sheet_name: str,
        age: int,
        sum_insured: int,
        age_matcher
    ) -> Optional[float]:
        """
        Lookup premium from a specific sheet.
        
        Args:
            sheet_name: Sheet name (e.g., 'Individual', '2 Adults')
            age: Age for row lookup
            sum_insured: Sum insured for column lookup
            age_matcher: AgeBandMatcher instance for age matching
            
        Returns:
            Premium value or None if not found
            
        Example:
            >>> from .age_matcher import AgeBandMatcher
            >>> matcher = AgeBandMatcher()
            >>> premium = parser.lookup_premium('Individual', 35, 500000, matcher)
        """
        if sheet_name not in self.sheets:
            logger.error(f"Sheet '{sheet_name}' not found in workbook")
            return None
        
        df = self.sheets[sheet_name]
        
        # Detect and log sheet format for debugging
        age_format = age_matcher.detect_sheet_age_format(df)
        logger.debug(f"Sheet '{sheet_name}' detected as '{age_format}' age format")
        
        # Find row by age (handles both exact ages and age bands)
        row_idx = age_matcher.find_age_band_row(df, age)
        if row_idx is None:
            logger.error(
                f"No age match found for age {age} in sheet '{sheet_name}' "
                f"(format: {age_format})"
            )
            return None
        
        # Get the matched age band for logging
        age_band_matched = str(df.loc[row_idx, 'Age Band']).strip()
        logger.debug(f"Age {age} matched to row '{age_band_matched}' in sheet '{sheet_name}'")
        
        # Find column by sum insured
        col_name = self.find_sum_insured_column(df, sum_insured)
        if col_name is None:
            logger.error(f"No column found for sum insured {sum_insured} in sheet '{sheet_name}'")
            return None
        
        # Get premium value
        try:
            premium = df.loc[row_idx, col_name]
            # Clean numeric value (remove any formatting)
            if pd.isna(premium):
                logger.warning(
                    f"Premium value is NaN for [{age_band_matched}, {col_name}] "
                    f"in sheet '{sheet_name}'"
                )
                return None
            premium_value = float(premium)
            logger.info(
                f"Premium lookup successful: Sheet='{sheet_name}', Age={age} "
                f"(matched '{age_band_matched}'), SumInsured={sum_insured} "
                f"(column '{col_name}'), Premium=₹{premium_value:,.0f}"
            )
            return premium_value
        except Exception as e:
            logger.error(
                f"Error extracting premium value for [{age_band_matched}, {col_name}] "
                f"in sheet '{sheet_name}': {e}"
            )
            return None
