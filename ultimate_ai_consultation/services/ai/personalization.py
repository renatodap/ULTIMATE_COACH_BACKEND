"""
AI-assisted personalization helpers built on top of the lightweight llm_client.

These are optional and guarded by feature flags. They return safe fallbacks
when LLM is disabled or unavailable.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from ultimate_ai_consultation.libs.calculators.macros import Goal
from .llm_client import call_llm


ALLOWED_GOALS = {
    "fat_loss": Goal.FAT_LOSS,
    "muscle_gain": Goal.MUSCLE_GAIN,
    "recomposition": Goal.RECOMP,
    "recomp": Goal.RECOMP,
    "maintenance": Goal.MAINTENANCE,
}


def maybe_infer_primary_goal(context: Dict[str, Any]) -> Tuple[Optional[Goal], Optional[str]]:
    """Ask LLM to pick a primary goal when rules are ambiguous.

    Returns: (Goal or None, reason or None)
    """
    prompt = (
        "Pick a primary goal from {fat_loss, muscle_gain, recomposition, maintenance}.\n"
        "Consider user age, modalities, stated goals and timeline.\n"
        "Return compact JSON: {goal: <one_of>, reason: <<=20 words>}\n\n"
        f"Context: {context}"
    )
    raw = call_llm("goal_inference", prompt, max_tokens=128, cache_payload=context)
    if not raw:
        return None, None
    try:
        data = _safe_parse_json(raw)
        goal_str = str(data.get("goal", "")).strip().lower()
        if goal_str in ALLOWED_GOALS:
            return ALLOWED_GOALS[goal_str], str(data.get("reason") or None)
    except Exception:
        pass
    return None, None


def explain_tradeoffs(constraints: Dict[str, Any], tradeoffs: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Generate short, coach-like trade-off explanations.

    Returns list of {description, impact} dicts; empty if disabled.
    """
    payload = {"constraints": constraints, "tradeoffs": tradeoffs}
    prompt = (
        "Given constraints and solver trade-offs, produce up to 3 bullets with\n"
        "simple language and impact level (low|medium|high).\n"
        "Output JSON: {items: [{description, impact}]}\n\n"
        f"Input: {payload}"
    )
    raw = call_llm("feasibility_explain", prompt, max_tokens=128, cache_payload=payload)
    if not raw:
        return []
    try:
        data = _safe_parse_json(raw)
        items = data.get("items") or []
        out: List[Dict[str, str]] = []
        for it in items[:3]:
            desc = str(it.get("description", "")).strip()
            imp = str(it.get("impact", "medium")).strip().lower()
            if desc:
                out.append({"description": desc, "impact": imp})
        return out
    except Exception:
        return []


def coach_notes_for_shift_worker(context: Dict[str, Any]) -> Optional[str]:
    """Produce short shift-worker tips (sleep/meal timing)."""
    prompt = (
        "Write 2 short bullet points for shift worker recovery and meal timing.\n"
        "Max 40 tokens, no fluff. Output plain text lines prefixed with '- '.\n\n"
        f"Context: {context}"
    )
    raw = call_llm("coach_notes", prompt, max_tokens=64, cache_payload=context)
    if not raw:
        return None
    return raw.strip()[:400]


def rank_exercise_substitute(exercise: str, candidates: List[str], context: Dict[str, Any]) -> Optional[str]:
    """Ask LLM to pick best substitute from candidates. Returns name or None."""
    payload = {"exercise": exercise, "candidates": candidates, "context": context}
    prompt = (
        "Choose the best exercise substitute from the provided list given user context.\n"
        "Respond with compact JSON: {best: <candidate_name>} only.\n\n"
        f"Input: {payload}"
    )
    raw = call_llm("exercise_sub_rank", prompt, max_tokens=64, cache_payload=payload)
    if not raw:
        return None
    try:
        data = _safe_parse_json(raw)
        best = str(data.get("best") or "").strip()
        return best if best in candidates else None
    except Exception:
        return None


def _safe_parse_json(s: str) -> Dict[str, Any]:
    s = s.strip()
    # Best-effort: sometimes models wrap in code fences
    if s.startswith("```"):
        s = s.strip("`\n ")
        if s.startswith("json"):
            s = s[4:]
    return json.loads(s)  # type: ignore[name-defined]

import json  # defer import to keep top tidy
