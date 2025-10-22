"""
API Adapters Package

Adapters for transforming external data into internal domain models.
"""

from .consultation_adapter import (
    consultation_to_user_profile,
    validate_consultation_data,
    ConsultationValidationError,
)

__all__ = [
    "consultation_to_user_profile",
    "validate_consultation_data",
    "ConsultationValidationError",
]
