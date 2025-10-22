"""
Public API for ultimate_ai_consultation.

This package provides the stable interface for external systems
to generate and adjust fitness/nutrition programs.
"""

__version__ = "1.0.0"

# Import schemas (always available)
from .schemas.inputs import (
    ConsultationTranscript,
    GenerationOptions,
)

from .schemas.outputs import (
    ProgramBundle,
)

# Import main API function
from .generate_program import (
    generate_program_from_consultation,
    ProgramGenerationError,
)

# Import adapter functions
from .adapters import (
    consultation_to_user_profile,
    validate_consultation_data,
    ConsultationValidationError,
)

__all__ = [
    # Main API function
    "generate_program_from_consultation",
    # Input models
    "ConsultationTranscript",
    "GenerationOptions",
    # Output models
    "ProgramBundle",
    # Adapter functions
    "consultation_to_user_profile",
    "validate_consultation_data",
    # Exceptions
    "ProgramGenerationError",
    "ConsultationValidationError",
    # Version
    "__version__",
]
