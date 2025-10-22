"""
Constraint Solver Module

Validates program feasibility using mathematical optimization.
"""

from .constraint_solver import (
    ConstraintSolver,
    FeasibilityStatus,
    SolverResult,
    Diagnostic,
    TradeOffOption,
)

__all__ = [
    "ConstraintSolver",
    "FeasibilityStatus",
    "SolverResult",
    "Diagnostic",
    "TradeOffOption",
]
