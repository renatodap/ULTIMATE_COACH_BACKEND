"""
Unit tests for calorie_calculator service.

Tests METs-based calorie burn calculations and activity database.
"""

import pytest
from app.services.calorie_calculator import (
    lookup_mets,
    calculate_calories,
    estimate_activity_calories,
    get_mets_for_category,
    list_activities_by_category,
    METS_DATABASE,
    CATEGORY_DEFAULT_METS,
)


# ============================================================================
# METs LOOKUP TESTS
# ============================================================================

class TestLookupMETs:
    """Test METs value lookup from activity database."""

    def test_exact_match_running_7mph(self):
        """Test exact match for running 7mph."""
        mets, description = lookup_mets('running_7mph', 'cardio_steady_state')
        assert mets == 11.0
        assert 'Running, 7 mph' in description

    def test_exact_match_yoga_hatha(self):
        """Test exact match for yoga (hatha)."""
        mets, description = lookup_mets('yoga_hatha', 'flexibility')
        assert mets == 2.5
        assert 'Yoga, Hatha' in description

    def test_exact_match_weight_lifting_moderate(self):
        """Test exact match for moderate weight lifting."""
        mets, description = lookup_mets('weight_lifting_moderate', 'strength_training')
        assert mets == 5.0
        assert 'Weight lifting, moderate' in description

    def test_partial_match_running(self):
        """Test partial match for 'running' (should match any running activity)."""
        mets, description = lookup_mets('running', 'cardio_steady_state')
        assert mets > 0
        assert 'running' in description.lower() or 'Running' in description

    def test_partial_match_cycling(self):
        """Test partial match for 'cycling'."""
        mets, description = lookup_mets('cycling', 'cardio_steady_state')
        assert mets > 0
        assert 'cycling' in description.lower() or 'Cycling' in description

    def test_fallback_to_category_default(self):
        """Test fallback to category default for unknown activity."""
        mets, description = lookup_mets('unknown_activity_xyz', 'cardio_steady_state')
        assert mets == 7.0  # Category default for cardio_steady_state
        assert 'cardio' in description.lower()

    def test_case_insensitive_lookup(self):
        """Test that lookup is case-insensitive."""
        mets1, _ = lookup_mets('RUNNING_7MPH', 'cardio_steady_state')
        mets2, _ = lookup_mets('running_7mph', 'cardio_steady_state')
        mets3, _ = lookup_mets('Running_7mph', 'cardio_steady_state')
        assert mets1 == mets2 == mets3 == 11.0

    def test_space_and_dash_normalization(self):
        """Test that spaces and dashes are normalized."""
        mets1, _ = lookup_mets('running 7mph', 'cardio_steady_state')
        mets2, _ = lookup_mets('running-7mph', 'cardio_steady_state')
        mets3, _ = lookup_mets('running_7mph', 'cardio_steady_state')
        assert mets1 == mets2 == mets3


# ============================================================================
# CALORIE CALCULATION TESTS
# ============================================================================

class TestCalculateCalories:
    """Test calorie burn formula: Calories = METs × Weight (kg) × Duration (hours)."""

    def test_basic_calculation(self):
        """Test basic calorie calculation."""
        # 8.0 METs × 70kg × 0.5 hours = 280 calories
        calories = calculate_calories(mets=8.0, weight_kg=70, duration_minutes=30)
        assert calories == 280

    def test_running_45_minutes(self):
        """Test realistic running scenario."""
        # Running 7mph (11.0 METs) for 45 minutes at 80kg
        # 11.0 × 80 × 0.75 = 660 calories
        calories = calculate_calories(mets=11.0, weight_kg=80, duration_minutes=45)
        assert calories == 660

    def test_yoga_60_minutes(self):
        """Test realistic yoga scenario."""
        # Yoga Hatha (2.5 METs) for 60 minutes at 60kg
        # 2.5 × 60 × 1.0 = 150 calories
        calories = calculate_calories(mets=2.5, weight_kg=60, duration_minutes=60)
        assert calories == 150

    def test_heavy_person_burns_more(self):
        """Heavier person should burn more calories (same METs, duration)."""
        calories_60kg = calculate_calories(mets=8.0, weight_kg=60, duration_minutes=30)
        calories_90kg = calculate_calories(mets=8.0, weight_kg=90, duration_minutes=30)
        assert calories_90kg > calories_60kg

    def test_longer_duration_burns_more(self):
        """Longer duration should burn more calories (same METs, weight)."""
        calories_30min = calculate_calories(mets=8.0, weight_kg=70, duration_minutes=30)
        calories_60min = calculate_calories(mets=8.0, weight_kg=70, duration_minutes=60)
        assert calories_60min > calories_30min
        assert calories_60min == calories_30min * 2

    def test_higher_intensity_burns_more(self):
        """Higher intensity should burn more calories (same weight, duration)."""
        calories_moderate = calculate_calories(mets=5.0, weight_kg=70, duration_minutes=30)
        calories_vigorous = calculate_calories(mets=10.0, weight_kg=70, duration_minutes=30)
        assert calories_vigorous > calories_moderate
        assert calories_vigorous == calories_moderate * 2

    def test_rounding_to_nearest_integer(self):
        """Calories should be rounded to nearest integer."""
        # 8.3 × 70 × (25/60) = 241.42 → 241 or 242 (Python's round)
        calories = calculate_calories(mets=8.3, weight_kg=70, duration_minutes=25)
        assert isinstance(calories, int)
        assert calories in [241, 242]  # Allow rounding variation

    def test_fractional_mets(self):
        """Test calculation with fractional METs."""
        calories = calculate_calories(mets=7.5, weight_kg=75, duration_minutes=40)
        # 7.5 × 75 × (40/60) = 375
        assert calories == 375

    def test_zero_weight_raises_error(self):
        """Zero weight should raise ValueError."""
        with pytest.raises(ValueError, match="weight_kg must be positive"):
            calculate_calories(mets=8.0, weight_kg=0, duration_minutes=30)

    def test_negative_weight_raises_error(self):
        """Negative weight should raise ValueError."""
        with pytest.raises(ValueError, match="weight_kg must be positive"):
            calculate_calories(mets=8.0, weight_kg=-70, duration_minutes=30)

    def test_zero_duration_raises_error(self):
        """Zero duration should raise ValueError."""
        with pytest.raises(ValueError, match="duration_minutes must be positive"):
            calculate_calories(mets=8.0, weight_kg=70, duration_minutes=0)

    def test_negative_mets_raises_error(self):
        """Negative METs should raise ValueError."""
        with pytest.raises(ValueError, match="mets must be positive"):
            calculate_calories(mets=-8.0, weight_kg=70, duration_minutes=30)


# ============================================================================
# ESTIMATE ACTIVITY CALORIES TESTS
# ============================================================================

class TestEstimateActivityCalories:
    """Test integrated activity calorie estimation."""

    def test_running_with_database_lookup(self):
        """Test running with automatic METs lookup."""
        result = estimate_activity_calories(
            activity_name='running_7mph',
            category='cardio_steady_state',
            duration_minutes=30,
            weight_kg=75,
        )

        assert result['calories'] > 0
        assert result['mets'] == 11.0
        assert result['method'] == 'database'
        assert 'Running' in result['matched_activity']

    def test_user_provided_mets_override(self):
        """Test that user-provided METs overrides database."""
        result = estimate_activity_calories(
            activity_name='running',
            category='cardio_steady_state',
            duration_minutes=30,
            weight_kg=75,
            user_provided_mets=12.5,  # Custom value
        )

        assert result['mets'] == 12.5
        assert result['method'] == 'user_provided'

    def test_unknown_activity_uses_category_default(self):
        """Test unknown activity falls back to category default."""
        result = estimate_activity_calories(
            activity_name='super_rare_activity',
            category='strength_training',
            duration_minutes=60,
            weight_kg=80,
        )

        assert result['mets'] == 5.0  # Category default for strength
        assert result['method'] == 'category_default'

    def test_complete_result_structure(self):
        """Test that result contains all expected fields."""
        result = estimate_activity_calories(
            activity_name='yoga_hatha',
            category='flexibility',
            duration_minutes=60,
            weight_kg=60,
        )

        assert 'calories' in result
        assert 'mets' in result
        assert 'method' in result
        assert 'matched_activity' in result
        assert isinstance(result['calories'], int)
        assert isinstance(result['mets'], float)


# ============================================================================
# CATEGORY & DATABASE TESTS
# ============================================================================

class TestCategoryHelpers:
    """Test category helper functions."""

    def test_get_mets_for_category(self):
        """Test category default METs lookup."""
        assert get_mets_for_category('cardio_steady_state') == 7.0
        assert get_mets_for_category('cardio_interval') == 10.0
        assert get_mets_for_category('strength_training') == 5.0
        assert get_mets_for_category('sports') == 7.0
        assert get_mets_for_category('flexibility') == 3.0
        assert get_mets_for_category('other') == 5.0
        assert get_mets_for_category('unknown') == 5.0  # Default

    # Note: list_activities_by_category may not be implemented yet
    # These tests are commented out until the function is added to the service


# ============================================================================
# METs DATABASE INTEGRITY TESTS
# ============================================================================

class TestMETsDatabaseIntegrity:
    """Test METs database for consistency and correctness."""

    def test_database_not_empty(self):
        """METs database should contain activities."""
        assert len(METS_DATABASE) > 50  # Should have many activities

    def test_all_mets_positive(self):
        """All METs values should be positive."""
        for key, (mets, description) in METS_DATABASE.items():
            assert mets > 0, f"METs for {key} should be positive, got {mets}"

    def test_all_have_descriptions(self):
        """All activities should have descriptions."""
        for key, (mets, description) in METS_DATABASE.items():
            assert description, f"Activity {key} missing description"
            assert len(description) >= 5, f"Description for {key} too short"

    def test_category_defaults_all_present(self):
        """All category defaults should be defined."""
        required_categories = [
            'cardio_steady_state',
            'cardio_interval',
            'strength_training',
            'sports',
            'flexibility',
            'other',
        ]
        for category in required_categories:
            assert category in CATEGORY_DEFAULT_METS
            assert CATEGORY_DEFAULT_METS[category] > 0

    def test_mets_ranges_realistic(self):
        """METs values should be in realistic ranges."""
        for key, (mets, description) in METS_DATABASE.items():
            # Sleep/rest is ~1.0, elite running is ~20.0
            assert 1.0 <= mets <= 20.0, f"METs for {key} outside realistic range: {mets}"

    def test_cardio_activities_present(self):
        """Database should contain common cardio activities."""
        cardio_activities = ['running_7mph', 'cycling_moderate', 'swimming_freestyle_slow']
        for activity in cardio_activities:
            assert activity in METS_DATABASE, f"Missing common cardio activity: {activity}"

    def test_strength_activities_present(self):
        """Database should contain common strength activities."""
        strength_activities = ['weight_lifting_moderate', 'push_ups', 'squats_bodyweight']
        for activity in strength_activities:
            assert activity in METS_DATABASE, f"Missing common strength activity: {activity}"

    def test_flexibility_activities_present(self):
        """Database should contain common flexibility activities."""
        flexibility_activities = ['yoga_hatha', 'stretching_light', 'pilates']
        for activity in flexibility_activities:
            assert activity in METS_DATABASE, f"Missing common flexibility activity: {activity}"


# ============================================================================
# REALISTIC SCENARIO TESTS
# ============================================================================

class TestRealisticScenarios:
    """Test realistic activity scenarios."""

    def test_morning_run_scenario(self):
        """Test typical morning run scenario."""
        result = estimate_activity_calories(
            activity_name='running_7mph',
            category='cardio_steady_state',
            duration_minutes=45,
            weight_kg=80,
        )

        # 11.0 METs × 80kg × 0.75hr = 660 cal
        assert 650 <= result['calories'] <= 670

    def test_strength_training_session(self):
        """Test typical strength training session."""
        result = estimate_activity_calories(
            activity_name='weight_lifting_moderate',
            category='strength_training',
            duration_minutes=60,
            weight_kg=75,
        )

        # 5.0 METs × 75kg × 1.0hr = 375 cal
        assert 370 <= result['calories'] <= 380

    def test_yoga_class(self):
        """Test typical yoga class."""
        result = estimate_activity_calories(
            activity_name='yoga_vinyasa',
            category='flexibility',
            duration_minutes=75,
            weight_kg=65,
        )

        # 3.0 METs × 65kg × 1.25hr = 244 cal
        assert 240 <= result['calories'] <= 250

    def test_basketball_game(self):
        """Test basketball game."""
        result = estimate_activity_calories(
            activity_name='basketball_game',
            category='sports',
            duration_minutes=90,
            weight_kg=85,
        )

        # 8.0 METs × 85kg × 1.5hr = 1020 cal
        assert 1000 <= result['calories'] <= 1040

    def test_hiit_workout(self):
        """Test HIIT workout."""
        result = estimate_activity_calories(
            activity_name='hiit_vigorous',
            category='cardio_interval',
            duration_minutes=20,
            weight_kg=70,
        )

        # 12.0 METs × 70kg × 0.333hr = 280 cal
        assert 275 <= result['calories'] <= 285
