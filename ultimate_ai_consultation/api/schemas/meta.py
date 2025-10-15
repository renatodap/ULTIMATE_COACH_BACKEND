"""
Metadata schemas for versioning, provenance, and validation results.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class ProgramVersion(BaseModel):
    """Semantic versioning for programs."""
    
    major: int = Field(default=1, ge=0, description="Major version (breaking changes)")
    minor: int = Field(default=0, ge=0, description="Minor version (new features)")
    patch: int = Field(default=0, ge=0, description="Patch version (bug fixes)")
    
    def __str__(self) -> str:
        """Return version string."""
        return f"{self.major}.{self.minor}.{self.patch}"
    
    @classmethod
    def from_string(cls, version_str: str) -> "ProgramVersion":
        """Parse version from string like '1.2.3'."""
        parts = version_str.split('.')
        return cls(
            major=int(parts[0]),
            minor=int(parts[1]) if len(parts) > 1 else 0,
            patch=int(parts[2]) if len(parts) > 2 else 0
        )
    
    def increment_major(self) -> "ProgramVersion":
        """Increment major version (for reassessments)."""
        return ProgramVersion(major=self.major + 1, minor=0, patch=0)
    
    def increment_minor(self) -> "ProgramVersion":
        """Increment minor version (for adjustments)."""
        return ProgramVersion(major=self.major, minor=self.minor + 1, patch=0)
    
    def increment_patch(self) -> "ProgramVersion":
        """Increment patch version (for bug fixes)."""
        return ProgramVersion(major=self.major, minor=self.minor, patch=self.patch + 1)


class Provenance(BaseModel):
    """
    Generation metadata for reproducibility and audit trails.
    
    Tracks how and when a program was generated.
    """
    
    # Generation info
    generated_at: datetime = Field(default_factory=datetime.now, description="When generated")
    generated_by: str = Field(default="ultimate_ai_consultation", description="System that generated")
    generator_version: str = Field(default="0.1.0", description="Module version used")
    
    # Models used (for future LLM integration)
    llm_model: Optional[str] = Field(None, description="LLM model if used")
    llm_provider: Optional[str] = Field(None, description="LLM provider if used")
    llm_cost_usd: Optional[float] = Field(None, ge=0, description="LLM cost if applicable")
    
    # Generation parameters
    generation_options: Dict[str, Any] = Field(
        default_factory=dict,
        description="Options used for generation"
    )
    
    # PID parameters (for Phase 2)
    pid_parameters: Optional[Dict[str, float]] = Field(
        None,
        description="PID controller parameters if adaptive adjustment"
    )
    
    # Randomness control
    random_seed: Optional[int] = Field(None, description="Random seed if used")
    
    # Data sources
    consultation_session_id: Optional[str] = Field(None, description="Source consultation session")
    parent_program_id: Optional[str] = Field(None, description="Previous program version if adjustment")
    
    # Computation metrics
    generation_time_ms: Optional[int] = Field(None, ge=0, description="Generation duration")
    
    # Notes
    notes: Optional[str] = Field(None, description="Additional generation notes")


class ValidationError(BaseModel):
    """Single validation error."""
    
    field_name: str = Field(..., description="Field that failed validation")
    error_type: str = Field(..., description="Error type (required, invalid, etc.)")
    message: str = Field(..., description="Human-readable error message")
    suggested_fix: Optional[str] = Field(None, description="How to fix this error")


class ValidationResult(BaseModel):
    """
    Validation results with field-level errors.
    
    Used by validate_consultation_data() to return actionable errors.
    """
    
    valid: bool = Field(..., description="Whether validation passed")
    
    # Errors by field
    errors: List[ValidationError] = Field(default_factory=list, description="Validation errors")
    
    # Warnings (non-blocking)
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    
    # Summary
    error_count: int = Field(default=0, ge=0, description="Number of errors")
    warning_count: int = Field(default=0, ge=0, description="Number of warnings")
    
    # Recommendations
    recommendations: List[str] = Field(
        default_factory=list,
        description="Suggestions for improving input data"
    )
    
    def add_error(self, field: str, error_type: str, message: str, fix: Optional[str] = None):
        """Add a validation error."""
        self.errors.append(ValidationError(
            field_name=field,
            error_type=error_type,
            message=message,
            suggested_fix=fix
        ))
        self.error_count = len(self.errors)
        self.valid = False
    
    def add_warning(self, message: str):
        """Add a validation warning."""
        self.warnings.append(message)
        self.warning_count = len(self.warnings)


__all__ = [
    "ProgramVersion",
    "Provenance",
    "ValidationError",
    "ValidationResult",
]
