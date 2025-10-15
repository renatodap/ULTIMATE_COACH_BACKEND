"""
Adapters for transforming external data formats.

The consultation bridge transforms consultation data into the UserProfile
format expected by the existing Phase 1 program generator.
"""

from .consultation_bridge import (
    consultation_to_user_profile,
    validate_consultation_data,
)

__all__ = [
    "consultation_to_user_profile",
    "validate_consultation_data",
]
