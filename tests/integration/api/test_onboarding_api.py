"""
Integration tests for onboarding API endpoints.

Tests the complete onboarding flow including BMR, TDEE, and macro calculations.
"""

import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient


@pytest.mark.integration
class TestOnboardingFlow:
    """Test complete onboarding flow."""

    @patch('app.services.supabase_service.SupabaseService')
    def test_complete_onboarding_male_build_muscle(self, mock_supabase_service, client):
        """Test complete onboarding for male trying to build muscle."""
        mock_user = {
            'id': 'test-user-123',
            'email': 'test@example.com',
            'onboarding_completed': False,
        }

        # Mock user update response
        updated_user = {
            **mock_user,
            'age': 25,
            'sex': 'male',
            'height_cm': 180,
            'weight_kg': 75,
            'goal_weight_kg': 80,
            'primary_goal': 'build_muscle',
            'activity_level': 'moderately_active',
            'onboarding_completed': True,
            'daily_calorie_goal': 2850,  # Calculated
            'daily_protein_g': 150,
            'daily_carbs_g': 320,
            'daily_fat_g': 89,
        }

        mock_supabase_service.return_value.supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock(
            data=[updated_user]
        )

        with patch('app.api.dependencies.get_current_user', return_value=mock_user):
            response = client.post(
                '/api/v1/onboarding/complete',
                json={
                    'age': 25,
                    'sex': 'male',
                    'height_cm': 180,
                    'current_weight_kg': 75,
                    'goal_weight_kg': 80,
                    'primary_goal': 'build_muscle',
                    'activity_level': 'moderately_active',
                },
            )

        assert response.status_code == 200
        data = response.json()

        # Verify user profile updated
        assert data['user']['onboarding_completed'] is True
        assert data['user']['age'] == 25
        assert data['user']['weight_kg'] == 75

        # Verify macro targets calculated
        assert 'targets' in data
        assert data['targets']['bmr'] > 1500  # Reasonable BMR for 25yo male
        assert data['targets']['tdee'] > 2000  # TDEE should be higher
        assert data['targets']['daily_calories'] > data['targets']['tdee']  # Surplus for muscle building
        assert data['targets']['daily_protein_g'] >= 120  # High protein for muscle building

    @patch('app.services.supabase_service.SupabaseService')
    def test_complete_onboarding_female_lose_weight(self, mock_supabase_service, client):
        """Test complete onboarding for female trying to lose weight."""
        mock_user = {
            'id': 'test-user-456',
            'email': 'test2@example.com',
            'onboarding_completed': False,
        }

        updated_user = {
            **mock_user,
            'age': 30,
            'sex': 'female',
            'height_cm': 165,
            'weight_kg': 70,
            'goal_weight_kg': 60,
            'primary_goal': 'lose_weight',
            'activity_level': 'lightly_active',
            'onboarding_completed': True,
            'daily_calorie_goal': 1450,  # Calculated (deficit)
            'daily_protein_g': 154,  # High protein for muscle preservation
            'daily_carbs_g': 120,
            'daily_fat_g': 45,
        }

        mock_supabase_service.return_value.supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock(
            data=[updated_user]
        )

        with patch('app.api.dependencies.get_current_user', return_value=mock_user):
            response = client.post(
                '/api/v1/onboarding/complete',
                json={
                    'age': 30,
                    'sex': 'female',
                    'height_cm': 165,
                    'current_weight_kg': 70,
                    'goal_weight_kg': 60,
                    'primary_goal': 'lose_weight',
                    'activity_level': 'lightly_active',
                },
            )

        assert response.status_code == 200
        data = response.json()

        # Verify deficit applied
        assert data['targets']['daily_calories'] < data['targets']['tdee']
        # Deficit should be ~500 cal
        deficit = data['targets']['tdee'] - data['targets']['daily_calories']
        assert 450 <= deficit <= 550

    @patch('app.services.supabase_service.SupabaseService')
    def test_preview_targets_without_saving(self, mock_supabase_service, client):
        """Test previewing macro targets without completing onboarding."""
        mock_user = {
            'id': 'test-user-123',
            'onboarding_completed': False,
        }

        with patch('app.api.dependencies.get_current_user', return_value=mock_user):
            response = client.post(
                '/api/v1/onboarding/preview-targets',
                json={
                    'age': 25,
                    'sex': 'male',
                    'height_cm': 180,
                    'current_weight_kg': 75,
                    'goal_weight_kg': 80,
                    'primary_goal': 'build_muscle',
                    'activity_level': 'moderately_active',
                },
            )

        assert response.status_code == 200
        data = response.json()

        # Should return calculated targets
        assert 'bmr' in data
        assert 'tdee' in data
        assert 'daily_calories' in data
        assert 'daily_protein_g' in data
        assert 'daily_carbs_g' in data
        assert 'daily_fat_g' in data
        assert 'explanation' in data

        # User should still not be onboarded
        # (This endpoint doesn't modify user profile)

    @patch('app.services.supabase_service.SupabaseService')
    def test_get_onboarding_status_incomplete(self, mock_supabase_service, client):
        """Test checking onboarding status for incomplete user."""
        mock_user = {
            'id': 'test-user-123',
            'onboarding_completed': False,
        }

        with patch('app.api.dependencies.get_current_user', return_value=mock_user):
            response = client.get('/api/v1/onboarding/status')

        assert response.status_code == 200
        data = response.json()
        assert data['onboarding_completed'] is False

    @patch('app.services.supabase_service.SupabaseService')
    def test_get_onboarding_status_complete(self, mock_supabase_service, client):
        """Test checking onboarding status for completed user."""
        mock_user = {
            'id': 'test-user-123',
            'onboarding_completed': True,
            'age': 25,
            'primary_goal': 'build_muscle',
        }

        with patch('app.api.dependencies.get_current_user', return_value=mock_user):
            response = client.get('/api/v1/onboarding/status')

        assert response.status_code == 200
        data = response.json()
        assert data['onboarding_completed'] is True

    @patch('app.services.supabase_service.SupabaseService')
    def test_onboarding_validation_age_too_young(self, mock_supabase_service, client):
        """Test validation rejects unrealistic age."""
        mock_user = {'id': 'test-user-123'}

        with patch('app.api.dependencies.get_current_user', return_value=mock_user):
            response = client.post(
                '/api/v1/onboarding/complete',
                json={
                    'age': 10,  # Too young
                    'sex': 'male',
                    'height_cm': 180,
                    'current_weight_kg': 75,
                    'goal_weight_kg': 80,
                    'primary_goal': 'build_muscle',
                    'activity_level': 'moderately_active',
                },
            )

        assert response.status_code == 422  # Validation error

    @patch('app.services.supabase_service.SupabaseService')
    def test_onboarding_validation_invalid_activity_level(self, mock_supabase_service, client):
        """Test validation rejects invalid activity level."""
        mock_user = {'id': 'test-user-123'}

        with patch('app.api.dependencies.get_current_user', return_value=mock_user):
            response = client.post(
                '/api/v1/onboarding/complete',
                json={
                    'age': 25,
                    'sex': 'male',
                    'height_cm': 180,
                    'current_weight_kg': 75,
                    'goal_weight_kg': 80,
                    'primary_goal': 'build_muscle',
                    'activity_level': 'super_active',  # Invalid
                },
            )

        assert response.status_code == 422


@pytest.mark.integration
class TestMacroCalculations:
    """Test macro calculation accuracy in onboarding."""

    @patch('app.services.supabase_service.SupabaseService')
    def test_bmr_calculation_male(self, mock_supabase_service, client):
        """Test BMR calculation for male."""
        mock_user = {'id': 'test-user-123'}

        with patch('app.api.dependencies.get_current_user', return_value=mock_user):
            response = client.post(
                '/api/v1/onboarding/preview-targets',
                json={
                    'age': 30,
                    'sex': 'male',
                    'height_cm': 180,
                    'current_weight_kg': 80,
                    'goal_weight_kg': 75,
                    'primary_goal': 'maintain',
                    'activity_level': 'sedentary',
                },
            )

        assert response.status_code == 200
        data = response.json()

        # Mifflin-St Jeor: (10 * 80) + (6.25 * 180) - (5 * 30) + 5
        # = 800 + 1125 - 150 + 5 = 1780
        assert data['bmr'] == 1780

    @patch('app.services.supabase_service.SupabaseService')
    def test_bmr_calculation_female(self, mock_supabase_service, client):
        """Test BMR calculation for female."""
        mock_user = {'id': 'test-user-123'}

        with patch('app.api.dependencies.get_current_user', return_value=mock_user):
            response = client.post(
                '/api/v1/onboarding/preview-targets',
                json={
                    'age': 30,
                    'sex': 'female',
                    'height_cm': 165,
                    'current_weight_kg': 60,
                    'goal_weight_kg': 60,
                    'primary_goal': 'maintain',
                    'activity_level': 'sedentary',
                },
            )

        assert response.status_code == 200
        data = response.json()

        # Mifflin-St Jeor: (10 * 60) + (6.25 * 165) - (5 * 30) - 161
        # = 600 + 1031.25 - 150 - 161 = 1320.25 → 1320
        assert data['bmr'] == 1320

    @patch('app.services.supabase_service.SupabaseService')
    def test_tdee_calculation(self, mock_supabase_service, client):
        """Test TDEE calculation with activity multiplier."""
        mock_user = {'id': 'test-user-123'}

        with patch('app.api.dependencies.get_current_user', return_value=mock_user):
            response = client.post(
                '/api/v1/onboarding/preview-targets',
                json={
                    'age': 30,
                    'sex': 'male',
                    'height_cm': 180,
                    'current_weight_kg': 80,
                    'goal_weight_kg': 80,
                    'primary_goal': 'maintain',
                    'activity_level': 'moderately_active',  # 1.55 multiplier
                },
            )

        assert response.status_code == 200
        data = response.json()

        # BMR = 1780
        # TDEE = 1780 * 1.55 = 2759
        assert data['tdee'] == 2759

    @patch('app.services.supabase_service.SupabaseService')
    def test_calorie_adjustment_weight_loss(self, mock_supabase_service, client):
        """Test calorie adjustment for weight loss goal."""
        mock_user = {'id': 'test-user-123'}

        with patch('app.api.dependencies.get_current_user', return_value=mock_user):
            response = client.post(
                '/api/v1/onboarding/preview-targets',
                json={
                    'age': 30,
                    'sex': 'male',
                    'height_cm': 180,
                    'current_weight_kg': 80,
                    'goal_weight_kg': 75,
                    'primary_goal': 'lose_weight',
                    'activity_level': 'moderately_active',
                },
            )

        assert response.status_code == 200
        data = response.json()

        # TDEE = 2759
        # Adjustment = -500 (lose_weight)
        # Daily calories = 2759 - 500 = 2259
        assert data['daily_calories'] == 2259

    @patch('app.services.supabase_service.SupabaseService')
    def test_protein_target_high_for_weight_loss(self, mock_supabase_service, client):
        """Test high protein target for weight loss (muscle preservation)."""
        mock_user = {'id': 'test-user-123'}

        with patch('app.api.dependencies.get_current_user', return_value=mock_user):
            response = client.post(
                '/api/v1/onboarding/preview-targets',
                json={
                    'age': 30,
                    'sex': 'male',
                    'height_cm': 180,
                    'current_weight_kg': 80,
                    'goal_weight_kg': 75,
                    'primary_goal': 'lose_weight',
                    'activity_level': 'moderately_active',
                },
            )

        assert response.status_code == 200
        data = response.json()

        # Protein: 80kg * 2.2 (lose_weight multiplier) = 176g
        assert data['daily_protein_g'] == 176

    @patch('app.services.supabase_service.SupabaseService')
    def test_explanation_fields_included(self, mock_supabase_service, client):
        """Test that explanation fields are included for transparency."""
        mock_user = {'id': 'test-user-123'}

        with patch('app.api.dependencies.get_current_user', return_value=mock_user):
            response = client.post(
                '/api/v1/onboarding/preview-targets',
                json={
                    'age': 30,
                    'sex': 'male',
                    'height_cm': 180,
                    'current_weight_kg': 80,
                    'goal_weight_kg': 75,
                    'primary_goal': 'lose_weight',
                    'activity_level': 'moderately_active',
                },
            )

        assert response.status_code == 200
        data = response.json()

        # Verify explanation structure
        assert 'explanation' in data
        assert 'bmr' in data['explanation']
        assert 'tdee' in data['explanation']
        assert 'calories' in data['explanation']
        assert 'protein' in data['explanation']
        assert 'fats' in data['explanation']
        assert 'carbs' in data['explanation']
        assert 'goal_context' in data['explanation']

        # Verify explanations are human-readable
        assert len(data['explanation']['bmr']) > 20
        assert 'Mifflin-St Jeor' in data['explanation']['bmr']
