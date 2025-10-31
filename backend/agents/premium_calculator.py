"""
Deterministic Premium Calculator using Excel workbook.

Supports:
- Individual policies: per-person premium lookup
- Family floater policies: single premium for family composition
- GST calculation (default 18%)
- Dynamic workbook loading from registry
"""
import pandas as pd
import re
import os
import json
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class PremiumCalculator:
    """Excel-based premium calculator for individual and family floater policies."""
    
    def __init__(self, excel_path: str = None, doc_name: str = None, gst_rate: float = 0.18):
        """
        Initialize calculator with Excel workbook.
        
        Args:
            excel_path: Direct path to premium chart Excel file (optional)
            doc_name: Document name to lookup in registry (optional, used if excel_path not provided)
            gst_rate: GST rate (default 0.18 for 18%)
        """
        # If no path provided, try to find from registry
        if excel_path is None:
            excel_path = self._find_premium_workbook(doc_name)
        
        self.excel_path = Path(excel_path)
        self.doc_name = doc_name or self.excel_path.stem
        self.gst_rate = gst_rate
        self.workbook = None
        self.sheets = {}
        self._load_workbook()
    
    @staticmethod
    def _find_premium_workbook(doc_name: str = None) -> str:
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
        """
        premium_dir = os.path.join(settings.MEDIA_ROOT, 'premium_workbooks')
        registry_path = os.path.join(premium_dir, 'premium_workbooks_registry.json')
        
        if not os.path.exists(registry_path):
            return {}
        
        with open(registry_path, 'r') as f:
            return json.load(f)
    
    def _load_workbook(self):
        """Load Excel workbook and all sheets into memory."""
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
    
    def _parse_age_band(self, age_band: str) -> Tuple[int, Optional[int]]:
        """
        Parse age band string to (lower, upper) bounds in YEARS.
        Handles both exact ages, age ranges, and days (converts to years).
        
        Examples:
            "18-25" -> (18, 25)      # Age band in years
            "35" -> (35, 35)         # Exact age in years
            "76+" -> (76, None)      # Open-ended
            "> 75" -> (76, None)     # Greater than
            "91 days" -> (0, 0)      # Days (< 1 year) -> age 0
            "91days" -> (0, 0)       # Days without space
            "91-365 days" -> (0, 0)  # Day range (< 1 year) -> age 0
            "1-5" -> (1, 5)          # Years
        
        Returns:
            (lower_bound, upper_bound) where upper_bound is None for open-ended
            Both bounds are in YEARS
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
                
                logger.debug(f"Parsed days: '{age_band}' -> {lower_days}-{upper_days} days -> age {lower_years}-{upper_years} years")
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
    
    def _find_age_band_row(self, df: pd.DataFrame, age: int) -> Optional[int]:
        """
        Find the row index in dataframe that matches the given age.
        Intelligently handles both exact age and age band formats.
        
        Examples:
            - Exact age sheet: Age Band column has "18", "19", "20", ...
            - Age band sheet: Age Band column has "18-25", "26-35", ...
        
        Args:
            df: DataFrame with 'Age Band' column
            age: Integer age to match
            
        Returns:
            Row index (integer) or None if not found
        """
        age_col = 'Age Band'
        if age_col not in df.columns:
            raise ValueError(f"DataFrame missing '{age_col}' column")
        
        # First pass: try to find exact age match (for age-wise premium sheets)
        for idx, row in df.iterrows():
            age_band_str = str(row[age_col]).strip()
            try:
                lower, upper = self._parse_age_band(age_band_str)
                # Exact match for single-age rows
                if lower == upper == age:
                    return idx
            except ValueError:
                continue
        
        # Second pass: find age band range that contains the age
        for idx, row in df.iterrows():
            age_band_str = str(row[age_col]).strip()
            try:
                lower, upper = self._parse_age_band(age_band_str)
                if upper is None:  # Open-ended (e.g., "76+")
                    if age >= lower:
                        return idx
                elif lower <= age <= upper:  # Range (e.g., "18-25")
                    return idx
            except ValueError as e:
                logger.warning(f"Skipping unparseable age band '{age_band_str}': {e}")
                continue
        
        return None
    
    def _parse_sum_insured(self, sum_insured_input: Any) -> int:
        """
        Parse sum insured input to integer INR value.
        
        Examples:
            "2L" -> 200000
            "10L" -> 1000000
            500000 -> 500000
            "5 lakh" -> 500000
        
        Returns:
            Integer value in INR
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
    
    def _find_sum_insured_column(self, df: pd.DataFrame, sum_insured: int) -> Optional[str]:
        """
        Find the column name that matches the sum insured.
        Uses ceiling rule: if exact match not found, use next higher column.
        
        Args:
            df: DataFrame with sum insured columns
            sum_insured: Target sum insured in INR
            
        Returns:
            Column name or None if no suitable column found
        """
        # Parse all column headers (skip 'Age Band')
        candidates = []
        for col in df.columns:
            if col == 'Age Band':
                continue
            try:
                col_value = self._parse_sum_insured(col)
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
    
    def _detect_sheet_age_format(self, df: pd.DataFrame) -> str:
        """
        Detect whether a sheet uses exact ages or age bands.
        
        Args:
            df: DataFrame with 'Age Band' column
            
        Returns:
            'exact' if sheet has exact ages (18, 19, 20...)
            'bands' if sheet has age ranges (18-25, 26-35...)
        """
        age_col = 'Age Band'
        if age_col not in df.columns:
            return 'unknown'
        
        # Sample first few rows to detect format
        sample_size = min(5, len(df))
        band_count = 0
        exact_count = 0
        
        for idx in range(sample_size):
            age_band_str = str(df.iloc[idx][age_col]).strip()
            try:
                lower, upper = self._parse_age_band(age_band_str)
                if lower == upper:
                    exact_count += 1
                else:
                    band_count += 1
            except ValueError:
                continue
        
        return 'exact' if exact_count > band_count else 'bands'
    
    def _lookup_premium(self, sheet_name: str, age: int, sum_insured: int) -> Optional[float]:
        """
        Lookup premium from a specific sheet.
        
        Args:
            sheet_name: Sheet name (e.g., 'Individual', '2 Adults')
            age: Age for row lookup
            sum_insured: Sum insured for column lookup
            
        Returns:
            Premium value or None if not found
        """
        if sheet_name not in self.sheets:
            logger.error(f"Sheet '{sheet_name}' not found in workbook")
            return None
        
        df = self.sheets[sheet_name]
        
        # Detect and log sheet format for debugging
        age_format = self._detect_sheet_age_format(df)
        logger.debug(f"Sheet '{sheet_name}' detected as '{age_format}' age format")
        
        # Find row by age (handles both exact ages and age bands)
        row_idx = self._find_age_band_row(df, age)
        if row_idx is None:
            logger.error(f"No age match found for age {age} in sheet '{sheet_name}' "
                        f"(format: {age_format})")
            return None
        
        # Get the matched age band for logging
        age_band_matched = str(df.loc[row_idx, 'Age Band']).strip()
        logger.debug(f"Age {age} matched to row '{age_band_matched}' in sheet '{sheet_name}'")
        
        # Find column by sum insured
        col_name = self._find_sum_insured_column(df, sum_insured)
        if col_name is None:
            logger.error(f"No column found for sum insured {sum_insured} in sheet '{sheet_name}'")
            return None
        
        # Get premium value
        try:
            premium = df.loc[row_idx, col_name]
            # Clean numeric value (remove any formatting)
            if pd.isna(premium):
                logger.warning(f"Premium value is NaN for [{age_band_matched}, {col_name}] "
                             f"in sheet '{sheet_name}'")
                return None
            premium_value = float(premium)
            logger.info(f"Premium lookup successful: Sheet='{sheet_name}', Age={age} "
                       f"(matched '{age_band_matched}'), SumInsured={sum_insured} (column '{col_name}'), "
                       f"Premium=₹{premium_value:,.0f}")
            return premium_value
        except Exception as e:
            logger.error(f"Error reading premium from [{row_idx}, {col_name}]: {e}")
            return None
    
    def calculate_individual_premium(
        self,
        members: List[Dict[str, Any]],
        sum_insured: int,
        include_gst: bool = True
    ) -> Dict[str, Any]:
        """
        Calculate premium for individual policy (each person separately).
        
        Args:
            members: List of dicts with 'age' key
                Example: [{'age': 35, 'name': 'John'}, {'age': 40, 'name': 'Jane'}]
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
            
            premium = self._lookup_premium('Individual', age, sum_insured)
            if premium is None:
                breakdown.append({
                    'member': member,
                    'age': age,
                    'error': 'Premium not found',
                    'premium': 0
                })
                continue
            
            # Find age band for display
            df = self.sheets['Individual']
            row_idx = self._find_age_band_row(df, age)
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
        if sheet_name not in self.sheets:
            return {
                'error': f"Sheet '{sheet_name}' not found in workbook. Available sheets: {list(self.sheets.keys())}",
                'policy_type': 'family_floater'
            }
        
        # Lookup premium
        gross_premium = self._lookup_premium(sheet_name, eldest_age, sum_insured)
        if gross_premium is None:
            return {
                'error': f'Premium not found for age {eldest_age}, sum insured {sum_insured} in sheet {sheet_name}',
                'policy_type': 'family_floater',
                'composition': sheet_name
            }
        
        # Find age band for display
        df = self.sheets[sheet_name]
        row_idx = self._find_age_band_row(df, eldest_age)
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
        
        Args:
            policy_type: 'individual' or 'family_floater'
            members: List of member dicts with 'age' (for individual) or for auto-detection
            num_adults: Number of adults (for family floater)
            num_children: Number of children (for family floater)
            sum_insured: Sum insured in INR
            include_gst: Whether to add GST
            
        Returns:
            Premium calculation result dict
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
