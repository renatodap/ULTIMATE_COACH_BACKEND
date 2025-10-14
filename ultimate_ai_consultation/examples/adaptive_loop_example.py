"""
Adaptive Loop Example

Demonstrates the complete Phase 2 adaptive system:
1. Initial plan generation (Phase 1)
2. User follows plan for 2 weeks (simulated)
3. Bi-weekly reassessment triggers
4. PID controllers calculate adjustments
5. New plan version created
6. Process repeats
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.adaptive import (
    ReassessmentOrchestrator,
    DataAggregator,
    SentimentAnalyzer,
)


def simulate_user_data():
    """
    Simulate 2 weeks of user data for demonstration.

    In production, this would come from the database.
    """
    return {
        "meals": [
            {
                "created_at": (datetime.now() - timedelta(days=i)).isoformat(),
                "calories": 2450 + (i % 3) * 50,  # Slightly under target
                "protein_g": 175 + (i % 3) * 5,
                "carbs_g": 295,
                "fat_g": 68,
            }
            for i in range(12)  # 12 out of 14 days logged
        ],
        "activities": [
            {
                "created_at": (datetime.now() - timedelta(days=i * 2)).isoformat(),
                "activity_type": "workout",
                "total_sets": 22 + (i % 2) * 2,
            }
            for i in range(6)  # 6 workouts completed (out of 7 planned)
        ],
        "body_metrics": [
            {
                "recorded_at": (datetime.now() - timedelta(days=i * 3)).isoformat(),
                "weight_kg": 82.0 + (i * 0.15),  # Gaining 0.3 kg/week
                "measurements": {},
            }
            for i in range(5)  # 5 weigh-ins over 2 weeks
        ],
        "coach_messages": [
            {
                "timestamp": (datetime.now() - timedelta(days=10)).isoformat(),
                "role": "user",
                "content": "Feeling great! Hit a new PR on bench press today. Motivation is high.",
            },
            {
                "timestamp": (datetime.now() - timedelta(days=7)).isoformat(),
                "role": "user",
                "content": "A bit tired today but pushed through the workout. Loving the progress so far.",
            },
            {
                "timestamp": (datetime.now() - timedelta(days=3)).isoformat(),
                "role": "user",
                "content": "Missed Friday's workout - work was crazy and I had no time.",
            },
        ],
    }


def main():
    """Run adaptive loop demonstration"""

    print("=" * 80)
    print("ADAPTIVE LOOP DEMONSTRATION - Phase 2 Complete System")
    print("=" * 80)
    print()

    # ========================================================================
    # SCENARIO: User has been following plan for 2 weeks
    # ========================================================================
    print("SCENARIO:")
    print("-" * 80)
    print("User: Male, 28yo, 82kg")
    print("Goal: Muscle gain (target +0.35 kg/week)")
    print("Plan: 5x/week training, 2,500 kcal/day")
    print("Time: 2 weeks into program")
    print()

    # ========================================================================
    # STEP 1: Trigger Bi-Weekly Reassessment
    # ========================================================================
    print("STEP 1: Bi-Weekly Reassessment Triggered")
    print("-" * 80)
    print("  System automatically runs reassessment every 14 days...")
    print()

    # Initialize orchestrator (without database for demo)
    orchestrator = ReassessmentOrchestrator(supabase_client=None)

    # Simulate aggregated data
    print("STEP 2: Data Aggregation")
    print("-" * 80)
    simulated_data = simulate_user_data()
    print(f"  ✓ Meals logged: {len(simulated_data['meals'])} days (86% adherence)")
    print(f"  ✓ Workouts completed: {len(simulated_data['activities'])} sessions (86% adherence)")
    print(f"  ✓ Weight tracked: {len(simulated_data['body_metrics'])} weigh-ins")
    print()

    # ========================================================================
    # STEP 3: Calculate Progress Metrics
    # ========================================================================
    print("STEP 3: Progress Analysis")
    print("-" * 80)

    # Simulate aggregated metrics
    start_weight = 82.0
    current_weight = 82.6
    weight_change = current_weight - start_weight
    weeks_elapsed = 2.0
    actual_rate = weight_change / weeks_elapsed  # 0.3 kg/week
    target_rate = 0.35  # kg/week

    print(f"  Weight Progress:")
    print(f"    Start weight: {start_weight} kg")
    print(f"    Current weight: {current_weight} kg")
    print(f"    Change: +{weight_change} kg over {weeks_elapsed} weeks")
    print(f"    Actual rate: +{actual_rate:.2f} kg/week")
    print(f"    Target rate: +{target_rate:.2f} kg/week")
    print(f"    Status: SLIGHTLY SLOW (86% of target)")
    print()

    print(f"  Adherence:")
    print(f"    Meal logging: 86% (good)")
    print(f"    Training: 86% (6 out of 7 sessions)")
    print(f"    Data quality: HIGH (sufficient for adjustments)")
    print()

    # ========================================================================
    # STEP 4: Sentiment Analysis
    # ========================================================================
    print("STEP 4: Coach Message Sentiment Analysis")
    print("-" * 80)

    analyzer = SentimentAnalyzer()
    sentiment_result = analyzer.analyze_messages(
        simulated_data["coach_messages"], analysis_period_days=14
    )

    print(f"  Messages analyzed: {sentiment_result.total_messages}")
    print(f"  Signals detected: {len(sentiment_result.signals_detected)}")
    print(f"  Overall sentiment: {sentiment_result.overall_adherence_sentiment.upper()}")
    print()

    if sentiment_result.signals_detected:
        print(f"  Key signals:")
        for signal in sentiment_result.signals_detected[:5]:
            print(f"    - {signal.signal_type.value}: {signal.message_text[:60]}...")

    print()

    if sentiment_result.key_barriers:
        print(f"  Barriers identified:")
        for barrier in sentiment_result.key_barriers:
            print(f"    ⚠️  {barrier}")
        print()

    # ========================================================================
    # STEP 5: PID Controller Adjustments
    # ========================================================================
    print("STEP 5: PID Controller Calculations")
    print("-" * 80)

    from services.adaptive.controllers import (
        CaloriePIDController,
        VolumePIDController,
    )

    # Calorie adjustment
    calorie_controller = CaloriePIDController()
    calorie_adj = calorie_controller.calculate_adjustment(
        target_rate_kg_per_week=0.35,
        actual_rate_kg_per_week=0.3,
        current_calories=2500,
        weeks_elapsed=2.0,
        confidence=0.9,
    )

    print("  Calorie Adjustment:")
    print(f"    Current: {calorie_adj.current_calories} kcal/day")
    print(f"    Recommended: {calorie_adj.recommended_calories} kcal/day")
    print(f"    Change: {calorie_adj.adjustment_amount:+d} kcal/day ({calorie_adj.adjustment_percentage:+.1f}%)")
    print(f"    Rationale: {calorie_adj.rationale}")
    print()

    # Volume adjustment
    volume_controller = VolumePIDController()
    volume_adj = volume_controller.calculate_adjustment(
        current_volume_per_week=80,  # Total sets across all muscles
        target_adherence=0.85,
        actual_adherence=0.86,
        weeks_since_deload=2,
        confidence=0.9,
    )

    print("  Volume Adjustment:")
    print(f"    Current: {volume_adj.current_volume_per_week} sets/week")
    print(f"    Recommended: {volume_adj.recommended_volume_per_week} sets/week")
    print(f"    Change: {volume_adj.adjustment_amount:+d} sets/week ({volume_adj.adjustment_percentage:+.1f}%)")
    print(f"    Rationale: {volume_adj.rationale}")
    print()

    # ========================================================================
    # STEP 6: Generate User Message
    # ========================================================================
    print("STEP 6: User Notification")
    print("-" * 80)

    user_message = f"""
🎯 Your 2-Week Progress Check-In

📊 Progress Summary:
  • Weight: {start_weight} kg → {current_weight} kg (+{weight_change} kg)
  • Rate: +{actual_rate:.2f} kg/week (target: +{target_rate:.2f} kg/week)
  • Meal logging: 86%
  • Training adherence: 86%

🔄 Plan Adjustments:
  • Calories: {calorie_adj.current_calories} → {calorie_adj.recommended_calories} kcal/day ({calorie_adj.adjustment_percentage:+.0f}%)
    Why: {calorie_adj.rationale}

  • Training Volume: {volume_adj.current_volume_per_week} → {volume_adj.recommended_volume_per_week} sets/week ({volume_adj.adjustment_percentage:+.0f}%)
    Why: {volume_adj.rationale}

💪 Overall: You're making good progress! We've made small adjustments to optimize
your rate of gain. Keep up the great work with logging and training consistency.

Next check-in: 2 weeks from today. Keep logging!
    """.strip()

    print(user_message)
    print()

    # ========================================================================
    # STEP 7: Database Storage (Simulated)
    # ========================================================================
    print("STEP 7: Database Updates (Simulated)")
    print("-" * 80)
    print("  ✓ New plan version created (v2)")
    print("  ✓ Old plan marked inactive")
    print("  ✓ Adjustment record stored in plan_adjustments table")
    print("  ✓ User notified via coach conversation")
    print()

    # ========================================================================
    # SUMMARY
    # ========================================================================
    print("=" * 80)
    print("ADAPTIVE LOOP COMPLETE")
    print("=" * 80)
    print()
    print("What just happened:")
    print("  1. System pulled 2 weeks of meal, training, and body weight data")
    print("  2. Analyzed coach messages for sentiment and barriers")
    print("  3. PID controllers calculated optimal adjustments")
    print("  4. New plan version generated with updated targets")
    print("  5. User notified with clear explanation of changes")
    print()
    print("Next cycle:")
    print("  - User follows updated plan for 2 more weeks")
    print("  - System automatically reassesses again in 14 days")
    print("  - Process repeats indefinitely")
    print()
    print("Benefits:")
    print("  ✓ No manual coach intervention required")
    print("  ✓ Adjustments based on data, not guesses")
    print("  ✓ Smooth, gradual changes (PID control)")
    print("  ✓ User stays accountable with regular check-ins")
    print()
    print("=" * 80)


if __name__ == "__main__":
    main()
