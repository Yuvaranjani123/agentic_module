"""
Premium Calculator Modules.

This package provides modular components for premium calculation:
- AgeBandMatcher: Age band parsing and matching
- ExcelWorkbookParser: Excel workbook loading and premium lookup
- PremiumCalculator: Main calculator orchestration
"""

from .age_matcher import AgeBandMatcher
from .excel_parser import ExcelWorkbookParser
from .calculator_base import PremiumCalculator

__all__ = ['AgeBandMatcher', 'ExcelWorkbookParser', 'PremiumCalculator']
