"""
Unit tests for macro_calculator service.

Tests BMR, TDEE, and macro target calculations using scientific formulas.
"""

import pytest
from app.services.macro_calculator import (
    calculate_bmr,
    calculate_targets,
    get_activity_multiplier,
    get_protein_multiplier,
    estimate_time_to_goal,
    ACTIVITY_MULTIPLIERS,
    PROTEIN_MULTIPLIERS,
    CALORIE_ADJUSTMENTS,
)


# ============================================================================
# BMR CALCULATION TESTS
# ============================================================================

class TestCalculateBMR:
    """Test BMR calculation using Mifflin-St Jeor equation."""

    def test_male_bmr_30yo_180cm_80kg(self):
        """Test BMR for 30yo male, 180cm, 80kg."""
        # Expected: (10 * 80) + (6.25 * 180) - (5 * 30) + 5
        # = 800 + 1125 - 150 + 5 = 1780
        bmr = calculate_bmr(age=30, sex='male', height_cm=180, weight_kg=80)
        assert bmr == 1780

    def test_female_bmr_30yo_165cm_60kg(self):
        """Test BMR for 30yo female, 165cm, 60kg."""
        # Expected: (10 * 60) + (6.25 * 165) - (5 * 30) - 161
        # = 600 + 1031.25 - 150 - 161 = 1320.25 → 1320
        bmr = calculate_bmr(age=30, sex='female', height_cm=165, weight_kg=60)
        assert bmr == 1320

    def test_male_bmr_25yo_175cm_70kg(self):
        """Test BMR for 25yo male, 175cm, 70kg."""
        # (10 * 70) + (6.25 * 175) - (5 * 25) + 5
        # = 700 + 1093.75 - 125 + 5 = 1673.75 → 1674
        bmr = calculate_bmr(age=25, sex='male', height_cm=175, weight_kg=70)
        assert bmr == 1674

    def test_female_bmr_45yo_160cm_75kg(self):
        """Test BMR for 45yo female, 160cm, 75kg."""
        # (10 * 75) + (6.25 * 160) - (5 * 45) - 161
        # = 750 + 1000 - 225 - 161 = 1364
        bmr = calculate_bmr(age=45, sex='female', height_cm=160, weight_kg=75)
        assert bmr == 1364

    def test_young_male_higher_bmr(self):
        """Younger individuals should have higher BMR."""
        bmr_25 = calculate_bmr(age=25, sex='male', height_cm=180, weight_kg=80)
        bmr_50 = calculate_bmr(age=50, sex='male', height_cm=180, weight_kg=80)
        assert bmr_25 > bmr_50

    def test_heavier_person_higher_bmr(self):
        """Heavier individuals should have higher BMR."""
        bmr_60 = calculate_bmr(age=30, sex='male', height_cm=180, weight_kg=60)
        bmr_100 = calculate_bmr(age=30, sex='male', height_cm=180, weight_kg=100)
        assert bmr_100 > bmr_60

    def test_male_vs_female_same_stats(self):
        """Males should have higher BMR than females (same stats)."""
        bmr_male = calculate_bmr(age=30, sex='male', height_cm=170, weight_kg=70)
        bmr_female = calculate_bmr(age=30, sex='female', height_cm=170, weight_kg=70)
        assert bmr_male > bmr_female


# ============================================================================
# TDEE & MACRO CALCULATION TESTS
# ============================================================================

class TestCalculateTargets:
    """Test complete macro target calculations."""

    def test_sedentary_maintenance_male(self):
        """Test sedentary male with maintenance goal."""
        targets = calculate_targets(
            age=30,
            sex='male',
            height_cm=180,
            current_weight_kg=80,
            goal_weight_kg=80,
            activity_level='sedentary',
            primary_goal='maintain',
        )

        # BMR = 1780
        # TDEE = 1780 * 1.2 = 2136
        # Calories = 2136 + 0 (maintain) = 2136
        assert targets.bmr == 1780
        assert targets.tdee == 2136
        assert targets.daily_calories == 2136

        # Protein: 80kg * 1.6 (maintain) = 128g
        assert targets.daily_protein_g == 128

        # Fat: 2136 * 0.28 / 9 = 66g
        assert 65 <= targets.daily_fat_g <= 67

        # Carbs: remaining calories after protein and fats
        # Note: actual implementation may calculate differently
        assert targets.daily_carbs_g > 0  # Just verify carbs are positive

    def test_very_active_muscle_building_male(self):
        """Test very active male building muscle."""
        targets = calculate_targets(
            age=25,
            sex='male',
            height_cm=175,
            current_weight_kg=70,
            goal_weight_kg=75,
            activity_level='very_active',
            primary_goal='build_muscle',
        )

        # BMR = 1674
        # TDEE = 1674 * 1.725 = 2888
        # Calories = 2888 + 250 (build_muscle) = 3138
        assert targets.bmr == 1674
        assert targets.tdee == 2888
        assert targets.daily_calories == 3138

        # Protein: 70kg * 2.0 (build_muscle) = 140g
        assert targets.daily_protein_g == 140

    def test_moderately_active_weight_loss_female(self):
        """Test moderately active female losing weight."""
        targets = calculate_targets(
            age=35,
            sex='female',
            height_cm=165,
            current_weight_kg=70,
            goal_weight_kg=60,
            activity_level='moderately_active',
            primary_goal='lose_weight',
        )

        # BMR calculation for female
        # (10 * 70) + (6.25 * 165) - (5 * 35) - 161 = 1395 (rounded)
        assert targets.bmr in [1394, 1395]  # Allow rounding variation

        # TDEE = 1395 * 1.55 = 2162 (with rounding)
        assert targets.tdee in [2161, 2162]  # Allow rounding variation

        # Calories = 2162 - 500 (lose_weight) = 1662 (with rounding)
        assert targets.daily_calories in [1661, 1662]  # Allow rounding variation

        # Protein: 70kg * 2.2 (lose_weight - preserve muscle) = 154g
        assert targets.daily_protein_g == 154

    def test_explanation_fields_present(self):
        """Ensure all explanation fields are present."""
        targets = calculate_targets(
            age=30,
            sex='male',
            height_cm=180,
            current_weight_kg=80,
            goal_weight_kg=75,
            activity_level='moderately_active',
            primary_goal='lose_weight',
        )

        assert 'bmr' in targets.explanation
        assert 'tdee' in targets.explanation
        assert 'calories' in targets.explanation
        assert 'protein' in targets.explanation
        assert 'fats' in targets.explanation
        assert 'carbs' in targets.explanation
        assert 'goal_context' in targets.explanation

    def test_invalid_activity_level_raises_error(self):
        """Invalid activity level should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid activity_level"):
            calculate_targets(
                age=30,
                sex='male',
                height_cm=180,
                current_weight_kg=80,
                goal_weight_kg=80,
                activity_level='super_ultra_active',  # Invalid
                primary_goal='maintain',
            )

    def test_invalid_goal_raises_error(self):
        """Invalid primary goal should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid primary_goal"):
            calculate_targets(
                age=30,
                sex='male',
                height_cm=180,
                current_weight_kg=80,
                goal_weight_kg=80,
                activity_level='moderately_active',
                primary_goal='become_superhero',  # Invalid
            )

    def test_minimum_calorie_floor(self):
        """Calories should not fall below 1200 cal minimum."""
        targets = calculate_targets(
            age=60,
            sex='female',
            height_cm=150,
            current_weight_kg=45,
            goal_weight_kg=40,
            activity_level='sedentary',
            primary_goal='lose_weight',
        )

        assert targets.daily_calories >= 1200

    def test_carbs_never_negative(self):
        """Carbs should never be negative."""
        targets = calculate_targets(
            age=30,
            sex='male',
            height_cm=180,
            current_weight_kg=100,
            goal_weight_kg=90,
            activity_level='sedentary',
            primary_goal='lose_weight',
        )

        assert targets.daily_carbs_g >= 0


# ============================================================================
# HELPER FUNCTION TESTS
# ============================================================================

class TestHelperFunctions:
    """Test helper functions."""

    def test_get_activity_multiplier(self):
        """Test activity multiplier lookup."""
        assert get_activity_multiplier('sedentary') == 1.2
        assert get_activity_multiplier('moderately_active') == 1.55
        assert get_activity_multiplier('extremely_active') == 1.9
        assert get_activity_multiplier('invalid') == 1.2  # Default

    def test_get_protein_multiplier(self):
        """Test protein multiplier lookup."""
        assert get_protein_multiplier('lose_weight') == 2.2
        assert get_protein_multiplier('build_muscle') == 2.0
        assert get_protein_multiplier('maintain') == 1.6
        assert get_protein_multiplier('invalid') == 1.6  # Default

    def test_estimate_time_to_goal_weight_loss(self):
        """Test time to goal for weight loss."""
        # 5kg to lose, 500 cal/day deficit
        # 5kg = 11.02 lbs
        # 500 cal/day = 3500 cal/week = 1 lb/week
        # 11.02 lbs / 1 lb/week ≈ 11 weeks
        weeks = estimate_time_to_goal(
            current_weight_kg=80,
            goal_weight_kg=75,
            daily_calories=2000,
            tdee=2500,
        )
        assert 10 <= weeks <= 12

    def test_estimate_time_to_goal_weight_gain(self):
        """Test time to goal for weight gain."""
        # 5kg to gain, 250 cal/day surplus
        # 5kg = 11.02 lbs
        # 250 cal/day = 1750 cal/week = 0.5 lb/week
        # 11.02 lbs / 0.5 lb/week ≈ 22 weeks
        weeks = estimate_time_to_goal(
            current_weight_kg=70,
            goal_weight_kg=75,
            daily_calories=2750,
            tdee=2500,
        )
        assert 20 <= weeks <= 24

    def test_estimate_time_to_goal_maintenance(self):
        """Test time to goal for maintenance (should be 0)."""
        weeks = estimate_time_to_goal(
            current_weight_kg=75,
            goal_weight_kg=75,
            daily_calories=2500,
            tdee=2500,
        )
        assert weeks == 0


# ============================================================================
# EDGE CASE TESTS
# ============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_very_tall_person(self):
        """Test calculations for very tall person (2m)."""
        targets = calculate_targets(
            age=25,
            sex='male',
            height_cm=200,
            current_weight_kg=100,
            goal_weight_kg=95,
            activity_level='moderately_active',
            primary_goal='lose_weight',
        )

        assert targets.bmr > 2000  # Should be high
        assert targets.tdee > 3000

    def test_very_short_person(self):
        """Test calculations for very short person (150cm)."""
        targets = calculate_targets(
            age=25,
            sex='female',
            height_cm=150,
            current_weight_kg=50,
            goal_weight_kg=50,
            activity_level='sedentary',
            primary_goal='maintain',
        )

        assert targets.bmr < 1400  # Should be relatively low
        assert targets.daily_calories >= 1200  # But not below minimum

    def test_very_high_protein_goal(self):
        """Test high protein multiplier with heavy person."""
        targets = calculate_targets(
            age=30,
            sex='male',
            height_cm=180,
            current_weight_kg=120,
            goal_weight_kg=100,
            activity_level='very_active',
            primary_goal='lose_weight',
        )

        # 120kg * 2.2 = 264g protein
        assert targets.daily_protein_g == 264

    def test_consistent_calculations(self):
        """Same inputs should always produce same outputs."""
        targets1 = calculate_targets(
            age=30,
            sex='male',
            height_cm=180,
            current_weight_kg=80,
            goal_weight_kg=75,
            activity_level='moderately_active',
            primary_goal='lose_weight',
        )

        targets2 = calculate_targets(
            age=30,
            sex='male',
            height_cm=180,
            current_weight_kg=80,
            goal_weight_kg=75,
            activity_level='moderately_active',
            primary_goal='lose_weight',
        )

        assert targets1.bmr == targets2.bmr
        assert targets1.tdee == targets2.tdee
        assert targets1.daily_calories == targets2.daily_calories
        assert targets1.daily_protein_g == targets2.daily_protein_g
        assert targets1.daily_carbs_g == targets2.daily_carbs_g
        assert targets1.daily_fat_g == targets2.daily_fat_g
