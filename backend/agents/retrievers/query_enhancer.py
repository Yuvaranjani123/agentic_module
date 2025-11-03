"""
Query Enhancer

Detects intent and enhances queries for better retrieval.
"""
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class QueryEnhancer:
    """
    Enhances user queries by detecting intent and preprocessing.
    
    Handles premium calculation detection, query normalization,
    and context-aware query enhancement.
    """
    
    def __init__(self):
        """
        Initialize query enhancer.
        
        Example:
            >>> enhancer = QueryEnhancer()
        """
        # Premium calculation keywords
        self.premium_keywords = [
            'premium', 'cost', 'price', 'amount', 'pay', 'payment',
            'calculate', 'computation', 'expense', 'charge', 'fee'
        ]
        
        # Age-related keywords
        self.age_keywords = [
            'age', 'years old', 'year old', 'aged', 'yr', 'yrs'
        ]
        
        logger.info("QueryEnhancer initialized")
    
    def detect_premium_intent(self, query: str) -> Dict:
        """
        Detect if query is asking for premium calculation.
        
        Args:
            query: User query string
            
        Returns:
            Dict with 'is_premium_query' bool and optional 'age' int
            
        Example:
            >>> enhancer = QueryEnhancer()
            >>> result = enhancer.detect_premium_intent("What is premium for 35 year old?")
            >>> result
            {'is_premium_query': True, 'age': 35}
            
            >>> result = enhancer.detect_premium_intent("What is maternity coverage?")
            >>> result
            {'is_premium_query': False, 'age': None}
        """
        query_lower = query.lower()
        
        # Check for premium keywords
        has_premium_keyword = any(
            keyword in query_lower for keyword in self.premium_keywords
        )
        
        # Check for age keywords
        has_age_keyword = any(
            keyword in query_lower for keyword in self.age_keywords
        )
        
        # Extract age if present
        age = self._extract_age(query)
        
        # It's a premium query if it has premium keywords OR age mention
        is_premium_query = has_premium_keyword or (has_age_keyword and age is not None)
        
        result = {
            'is_premium_query': is_premium_query,
            'age': age
        }
        
        logger.info(f"Intent detection for '{query[:50]}...': {result}")
        return result
    
    def _extract_age(self, text: str) -> Optional[int]:
        """
        Extract age number from text.
        
        Args:
            text: Text containing potential age
            
        Returns:
            Extracted age or None
            
        Example:
            >>> enhancer = QueryEnhancer()
            >>> enhancer._extract_age("I am 35 years old")
            35
            >>> enhancer._extract_age("What is maternity coverage?")
            None
        """
        import re
        
        # Patterns to match age
        patterns = [
            r'(\d+)\s*(?:year|yr)s?\s*old',  # "35 years old"
            r'age\s*(?:of\s*)?(\d+)',         # "age 35" or "age of 35"
            r'aged\s*(\d+)',                  # "aged 35"
            r'(?:^|\s)(\d+)\s*yr',            # "35 yr"
        ]
        
        text_lower = text.lower()
        
        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                try:
                    age = int(match.group(1))
                    # Validate age range (insurance typically 18-100)
                    if 18 <= age <= 100:
                        return age
                except ValueError:
                    continue
        
        return None
    
    def enhance_query(
        self, 
        query: str, 
        context: Optional[str] = None
    ) -> str:
        """
        Enhance query with context if available.
        
        Args:
            query: Original query
            context: Optional conversation context
            
        Returns:
            Enhanced query string
            
        Example:
            >>> enhancer = QueryEnhancer()
            >>> context = "Previous: User asked about ActivAssure policy"
            >>> enhanced = enhancer.enhance_query(
            ...     "What is the maternity coverage?",
            ...     context=context
            ... )
            >>> "ActivAssure" in enhanced
            True
        """
        # If we have context, prepend it
        if context:
            return f"{context}\n\nCurrent Question: {query}"
        
        return query
    
    def normalize_query(self, query: str) -> str:
        """
        Normalize query text (trim, lowercase for matching).
        
        Args:
            query: Raw query string
            
        Returns:
            Normalized query
            
        Example:
            >>> enhancer = QueryEnhancer()
            >>> enhancer.normalize_query("  What is PREMIUM?  ")
            'what is premium?'
        """
        return query.strip().lower()
