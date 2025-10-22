"""
Data models for the public API.

Organized into:
- inputs: Request models (ConsultationTranscript, GenerationOptions, etc.)
- outputs: Response models (ProgramBundle, etc.)
- meta: Metadata models (Version, Provenance, etc.)
"""

from .inputs import *
from .outputs import *
from .meta import *
