"""
Calculators Module

Evidence-based nutrition and physiology calculations.
"""

from .tdee import TDEECalculator, TDEEResult, ActivityFactor, calculate_tdee
from .macros import MacroCalculator, MacroTargets, Goal

__all__ = [
    "TDEECalculator",
    "TDEEResult",
    "ActivityFactor",
    "calculate_tdee",
    "MacroCalculator",
    "MacroTargets",
    "Goal",
]
