"""
Age Band Matcher for Premium Calculator.

This module provides functionality to parse and match customer ages
to insurance premium bands in Excel workbooks.

Handles:
- Age ranges: "18-25", "26-35"
- Exact ages: "18", "35", "40"
- Open-ended bands: "76+", "> 75"
- Infant ages in days: "91 days", "91-180 days" (converts to years)

Example:
    >>> matcher = AgeBandMatcher()
    >>> lower, upper = matcher.parse_age_band("18-25")
    >>> print(lower, upper)  # (18, 25)
    >>> 
    >>> lower, upper = matcher.parse_age_band("91 days")
    >>> print(lower, upper)  # (0, 0) - infant < 1 year
"""

import re
import logging
from typing import Optional, Tuple
import pandas as pd

logger = logging.getLogger(__name__)


class AgeBandMatcher:
    """
    Parse and match customer ages to premium bands.
    
    This class handles various age band formats found in insurance
    premium Excel workbooks, including exact ages, age ranges,
    open-ended bands, and infant ages specified in days.
    
    Example:
        >>> matcher = AgeBandMatcher()
        >>> row_idx = matcher.find_age_band_row(df, age=35)
        >>> format_type = matcher.detect_sheet_age_format(df)
    """
    
    @staticmethod
    def parse_age_band(age_band: str) -> Tuple[int, Optional[int]]:
        """
        Parse age band string to (lower, upper) bounds in YEARS.
        
        Handles both exact ages, age ranges, and days (converts to years).
        
        Args:
            age_band: Age band string from Excel (e.g., "18-25", "91 days", "76+")
            
        Returns:
            Tuple of (lower_bound, upper_bound) where:
            - Both bounds are in YEARS
            - upper_bound is None for open-ended bands (e.g., "76+")
            - Both bounds are equal for exact ages (e.g., "35" -> (35, 35))
            
        Raises:
            ValueError: If age band format cannot be parsed
            
        Examples:
            >>> AgeBandMatcher.parse_age_band("18-25")
            (18, 25)
            >>> AgeBandMatcher.parse_age_band("35")
            (35, 35)
            >>> AgeBandMatcher.parse_age_band("76+")
            (76, None)
            >>> AgeBandMatcher.parse_age_band("91 days")
            (0, 0)
            >>> AgeBandMatcher.parse_age_band("> 75")
            (76, None)
        """
        age_band = str(age_band).strip().lower()  # Convert to lowercase for matching
        
        # Handle age in DAYS (infants/newborns)
        # Pattern: "91 days", "91days", "91-180 days", etc.
        if 'day' in age_band:
            # Extract numeric values from the days pattern
            day_match = re.search(r'(\d+)\s*-?\s*(\d+)?\s*days?', age_band)
            if day_match:
                lower_days = int(day_match.group(1))
                upper_days = int(day_match.group(2)) if day_match.group(2) else lower_days
                
                # Convert days to years (365 days = 1 year)
                # For infants < 1 year, we represent as age 0
                lower_years = lower_days // 365  # Integer division
                upper_years = upper_days // 365
                
                logger.debug(
                    f"Parsed days: '{age_band}' -> {lower_days}-{upper_days} days "
                    f"-> age {lower_years}-{upper_years} years"
                )
                return (lower_years, upper_years)
        
        # Restore original for year-based parsing
        age_band = str(age_band).strip()
        
        # Handle open-ended bands: "76+", "> 75", ">=76"
        if '+' in age_band or '>' in age_band:
            match = re.search(r'(\d+)', age_band)
            if match:
                lower = int(match.group(1))
                # Normalize "> 75" to mean >=76
                if '>' in age_band and '+' not in age_band:
                    lower += 1
                return (lower, None)
        
        # Handle range bands: "18-25", "26-35"
        match = re.match(r'(\d+)\s*-\s*(\d+)', age_band)
        if match:
            return (int(match.group(1)), int(match.group(2)))
        
        # Handle exact age: "35", "40", etc. (single number without range)
        # This supports age-wise premium sheets where each row is a specific age
        match = re.match(r'^(\d+)$', age_band)
        if match:
            num = int(match.group(1))
            return (num, num)  # Exact age match (lower = upper)
        
        raise ValueError(f"Cannot parse age band: {age_band}")
    
    @classmethod
    def find_age_band_row(cls, df: pd.DataFrame, age: int) -> Optional[int]:
        """
        Find the row index in dataframe that matches the given age.
        
        Intelligently handles both exact age and age band formats.
        Uses two-pass matching: first tries exact match, then range match.
        
        Args:
            df: DataFrame with 'Age Band' column
            age: Integer age to match
            
        Returns:
            Row index (integer) or None if not found
            
        Raises:
            ValueError: If DataFrame missing 'Age Band' column
            
        Examples:
            For exact age sheet (Age Band: 18, 19, 20, ...):
            >>> row_idx = AgeBandMatcher.find_age_band_row(df, age=35)
            
            For age band sheet (Age Band: 18-25, 26-35, ...):
            >>> row_idx = AgeBandMatcher.find_age_band_row(df, age=30)
        """
        age_col = 'Age Band'
        if age_col not in df.columns:
            raise ValueError(f"DataFrame missing '{age_col}' column")
        
        # First pass: try to find exact age match (for age-wise premium sheets)
        for idx, row in df.iterrows():
            age_band_str = str(row[age_col]).strip()
            try:
                lower, upper = cls.parse_age_band(age_band_str)
                # Exact match for single-age rows
                if lower == upper == age:
                    return idx
            except ValueError:
                continue
        
        # Second pass: find age band range that contains the age
        for idx, row in df.iterrows():
            age_band_str = str(row[age_col]).strip()
            try:
                lower, upper = cls.parse_age_band(age_band_str)
                if upper is None:  # Open-ended (e.g., "76+")
                    if age >= lower:
                        return idx
                elif lower <= age <= upper:  # Range (e.g., "18-25")
                    return idx
            except ValueError as e:
                logger.warning(f"Skipping unparseable age band '{age_band_str}': {e}")
                continue
        
        return None
    
    @classmethod
    def detect_sheet_age_format(cls, df: pd.DataFrame) -> str:
        """
        Detect whether sheet uses exact ages or age bands.
        
        Samples the first few rows to determine format.
        
        Args:
            df: DataFrame with 'Age Band' column
            
        Returns:
            'exact' for age-wise sheets (18, 19, 20, ...)
            'bands' for age band sheets (18-25, 26-35, ...)
            
        Examples:
            >>> format_type = AgeBandMatcher.detect_sheet_age_format(df)
            >>> if format_type == 'exact':
            ...     print("This sheet has one row per age")
            ... else:
            ...     print("This sheet has age ranges")
        """
        age_col = 'Age Band'
        if age_col not in df.columns:
            return 'unknown'
        
        # Sample first 5 rows
        sample_size = min(5, len(df))
        exact_count = 0
        range_count = 0
        
        for idx in range(sample_size):
            age_band_str = str(df.iloc[idx][age_col]).strip()
            try:
                lower, upper = cls.parse_age_band(age_band_str)
                if lower == upper:
                    exact_count += 1
                else:
                    range_count += 1
            except ValueError:
                continue
        
        # If majority are exact ages, it's an exact age sheet
        if exact_count > range_count:
            return 'exact'
        else:
            return 'bands'
