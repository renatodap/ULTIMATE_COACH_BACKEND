"""
Services package for ULTIMATE COACH backend.

Contains all external service integrations:
- Supabase (database)
- AI providers (Anthropic, OpenAI, Groq)
- Storage
- etc.
"""

from app.services.supabase_service import SupabaseService, supabase_service

__all__ = ["SupabaseService", "supabase_service"]
