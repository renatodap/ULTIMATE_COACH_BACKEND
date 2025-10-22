"""
Lightweight LLM client with cost controls and caching.

Design goals:
- Strictly optional: no network calls unless enabled and API key present
- Tiny outputs: require compact JSON, validate upstream
- Caching: best-effort in-memory cache keyed by (task, payload hash)
"""

from __future__ import annotations

import hashlib
import json
import threading
from typing import Any, Dict, Optional

from ultimate_ai_consultation.config import get_settings
import httpx

_cache_lock = threading.Lock()
_cache: Dict[str, str] = {}


def _cache_key(task: str, payload: Dict[str, Any]) -> str:
    h = hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
    return f"{task}:{h}"


def call_llm(task: str, prompt: str, *, max_tokens: Optional[int] = None, cache_payload: Optional[Dict[str, Any]] = None) -> Optional[str]:
    """Call the configured LLM provider. Returns raw text or None if disabled.

    This implementation intentionally avoids adding heavy SDK dependencies. If
    personalization is disabled or API key is missing, it returns None.

    For Groq, you can add a thin HTTP call here later; for now, we rely on
    enablement flags so tests run without network.
    """
    settings = get_settings()
    if not settings.ENABLE_LLM_PERSONALIZATION:
        return None

    # Best-effort cache
    if settings.LLM_CACHE_ENABLED and cache_payload is not None:
        key = _cache_key(task, cache_payload)
        with _cache_lock:
            if key in _cache:
                return _cache[key]

    # Guard: require API key to make external calls
    if settings.LLM_PROVIDER == "groq":
        if not settings.GROQ_API_KEY:
            return None
        try:
            headers = {
                "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                "Content-Type": "application/json",
            }
            body = {
                "model": settings.GROQ_MODEL,
                "messages": [
                    {"role": "system", "content": "You output only the requested minimal JSON or text."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.2,
                "max_tokens": max_tokens or settings.LLM_MAX_TOKENS_PER_CALL,
            }
            with httpx.Client(timeout=8.0) as client:
                resp = client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=body)
                resp.raise_for_status()
                data = resp.json()
                text = data["choices"][0]["message"]["content"].strip()
        except Exception:
            return None

        # Populate cache
        if settings.LLM_CACHE_ENABLED and cache_payload is not None:
            key = _cache_key(task, cache_payload)
            with _cache_lock:
                _cache[key] = text
        return text

    return None


def put_cache(task: str, payload: Dict[str, Any], response: str) -> None:
    settings = get_settings()
    if not settings.LLM_CACHE_ENABLED:
        return
    key = _cache_key(task, payload)
    with _cache_lock:
        _cache[key] = response
