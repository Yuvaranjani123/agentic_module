"""
Comparators Package

Provides modular components for comparing insurance products:
- DocumentComparator: Document-based retrieval and comparison
- PremiumComparator: Premium calculation and comparison
- ComparisonResponseBuilder: LLM response generation
"""

from .document_comparator import DocumentComparator
from .premium_comparator import PremiumComparator
from .response_builder import ComparisonResponseBuilder

__all__ = ['DocumentComparator', 'PremiumComparator', 'ComparisonResponseBuilder']
