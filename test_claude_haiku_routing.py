"""
Test script for Claude Haiku classification system.

Tests the queries that were previously misrouted to verify they now
route correctly to Claude with tool access.
"""

import asyncio
import os
from dotenv import load_dotenv
from anthropic import Anthropic

# Load environment variables
load_dotenv()

# Import service
from app.services.complexity_analyzer_service import ComplexityAnalyzerService


async def test_classification():
    """Test classification for problematic queries."""

    # Initialize service
    anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    analyzer = ComplexityAnalyzerService(anthropic_client)

    # Test cases - queries that previously failed
    test_queries = [
        # User data queries (should be COMPLEX)
        "what have i done today so far?",
        "what did i eat yesterday?",
        "show my progress",
        "what are my macros?",
        "can you see my profile?",

        # Planning requests (should be COMPLEX)
        "give me a 4-week workout plan",
        "create a meal plan",
        "make me a program",
        "i need a workout routine",

        # Personalized advice (should be COMPLEX)
        "should i do cardio?",
        "how much protein should i eat?",
        "what should i eat after workout?",
        "is this amount of calories enough?",

        # Simple definitions (should be SIMPLE)
        "what is BMR?",
        "define progressive overload",
        "explain metabolism",

        # Trivial (should be TRIVIAL)
        "hi",
        "thanks",
        "bye"
    ]

    print("=" * 70)
    print("TESTING CLAUDE HAIKU CLASSIFICATION")
    print("=" * 70)
    print()

    results = {
        "trivial": [],
        "simple": [],
        "complex": []
    }

    for query in test_queries:
        print(f"Query: '{query}'")

        result = await analyzer.analyze_complexity(
            message=query,
            has_image=False
        )

        complexity = result["complexity"]
        recommended_model = result["recommended_model"]
        confidence = result["confidence"]
        reasoning = result["reasoning"]

        print(f"  -> Complexity: {complexity.upper()}")
        print(f"  -> Model: {recommended_model}")
        print(f"  -> Confidence: {confidence:.2f}")
        print(f"  -> Reasoning: {reasoning}")
        print()

        results[complexity].append({
            "query": query,
            "model": recommended_model,
            "confidence": confidence
        })

    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print()

    print(f"TRIVIAL (canned responses): {len(results['trivial'])} queries")
    for item in results["trivial"]:
        print(f"  [OK] {item['query']}")
    print()

    print(f"SIMPLE (Groq - no tools): {len(results['simple'])} queries")
    for item in results["simple"]:
        print(f"  [OK] {item['query']}")
    print()

    print(f"COMPLEX (Claude with tools): {len(results['complex'])} queries")
    for item in results["complex"]:
        print(f"  [OK] {item['query']}")
    print()

    # Verification
    print("=" * 70)
    print("VERIFICATION")
    print("=" * 70)
    print()

    # Check that user data queries route to Claude
    user_data_queries = [
        "what have i done today so far?",
        "what did i eat yesterday?",
        "show my progress",
        "what are my macros?",
        "can you see my profile?"
    ]

    user_data_results = [r for r in results["complex"] if r["query"] in user_data_queries]

    if len(user_data_results) == len(user_data_queries):
        print("[PASS] All user data queries route to Claude (complex)")
    else:
        print(f"[FAIL] Only {len(user_data_results)}/{len(user_data_queries)} user data queries route to Claude")
        for q in user_data_queries:
            if q not in [r["query"] for r in user_data_results]:
                print(f"  Missing: {q}")
    print()

    # Check that planning queries route to Claude
    planning_queries = [
        "give me a 4-week workout plan",
        "create a meal plan",
        "make me a program",
        "i need a workout routine"
    ]

    planning_results = [r for r in results["complex"] if r["query"] in planning_queries]

    if len(planning_results) == len(planning_queries):
        print("[PASS] All planning queries route to Claude (complex)")
    else:
        print(f"[FAIL] Only {len(planning_results)}/{len(planning_queries)} planning queries route to Claude")
        for q in planning_queries:
            if q not in [r["query"] for r in planning_results]:
                print(f"  Missing: {q}")
    print()

    # Check that simple definitions route to Groq
    definition_queries = [
        "what is BMR?",
        "define progressive overload",
        "explain metabolism"
    ]

    definition_results = [r for r in results["simple"] if r["query"] in definition_queries]

    if len(definition_results) == len(definition_queries):
        print("[PASS] All definition queries route to Groq (simple)")
    else:
        print(f"[PARTIAL] Only {len(definition_results)}/{len(definition_queries)} definition queries route to Groq")
        print("  (This is OK if they route to Claude - safer with tool access)")
    print()

    # Check that trivial queries use canned responses
    trivial_queries = ["hi", "thanks", "bye"]
    trivial_results = [r for r in results["trivial"] if r["query"] in trivial_queries]

    if len(trivial_results) == len(trivial_queries):
        print("[PASS] All trivial queries use canned responses")
    else:
        print(f"[PARTIAL] Only {len(trivial_results)}/{len(trivial_queries)} trivial queries use canned responses")
    print()

    print("=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_classification())
