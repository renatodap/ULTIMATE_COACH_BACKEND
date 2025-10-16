"""
Integration tests for activities API endpoints.

Tests the complete flow of activity creation, retrieval, update, and deletion.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient


@pytest.mark.integration
class TestActivitiesEndpoints:
    """Test activities API endpoints with mocked database."""

    @patch('app.services.supabase_service.SupabaseService')
    def test_create_activity_cardio(self, mock_supabase_service, client):
        """Test creating a cardio activity."""
        # Mock authentication
        mock_user = {'id': 'test-user-123', 'weight_kg': 75}

        # Mock database response
        created_activity = {
            'id': 'activity-001',
            'user_id': 'test-user-123',
            'category': 'cardio_steady_state',
            'activity_name': 'Morning Run',
            'start_time': '2025-10-16T06:00:00Z',
            'end_time': '2025-10-16T06:45:00Z',
            'duration_minutes': 45,
            'calories_burned': 400,
            'intensity_mets': 8.0,
            'metrics': {'distance_km': 6.5},
            'created_at': '2025-10-16T06:45:00Z',
        }

        mock_supabase_service.return_value.supabase.table.return_value.insert.return_value.execute.return_value = Mock(
            data=[created_activity]
        )

        # Make request
        with patch('app.api.dependencies.get_current_user', return_value=mock_user):
            response = client.post(
                '/api/v1/activities',
                json={
                    'category': 'cardio_steady_state',
                    'activity_name': 'Morning Run',
                    'start_time': '2025-10-16T06:00:00Z',
                    'end_time': '2025-10-16T06:45:00Z',
                    'intensity_mets': 8.0,
                    'metrics': {'distance_km': 6.5},
                },
            )

        assert response.status_code == 201
        data = response.json()
        assert data['category'] == 'cardio_steady_state'
        assert data['activity_name'] == 'Morning Run'
        assert data['duration_minutes'] == 45
        assert data['calories_burned'] > 0

    @patch('app.services.supabase_service.SupabaseService')
    def test_create_activity_strength_training(self, mock_supabase_service, client):
        """Test creating a strength training activity."""
        mock_user = {'id': 'test-user-123', 'weight_kg': 80}

        created_activity = {
            'id': 'activity-002',
            'user_id': 'test-user-123',
            'category': 'strength_training',
            'activity_name': 'Upper Body Workout',
            'start_time': '2025-10-16T18:00:00Z',
            'end_time': '2025-10-16T19:00:00Z',
            'duration_minutes': 60,
            'calories_burned': 300,
            'intensity_mets': 5.0,
            'metrics': {
                'exercises': [
                    {'name': 'Bench Press', 'sets': 3, 'reps': 8, 'weight_kg': 100},
                    {'name': 'Pull-ups', 'sets': 3, 'reps': 10, 'weight_kg': 0},
                ]
            },
            'created_at': '2025-10-16T19:00:00Z',
        }

        mock_supabase_service.return_value.supabase.table.return_value.insert.return_value.execute.return_value = Mock(
            data=[created_activity]
        )

        with patch('app.api.dependencies.get_current_user', return_value=mock_user):
            response = client.post(
                '/api/v1/activities',
                json={
                    'category': 'strength_training',
                    'activity_name': 'Upper Body Workout',
                    'start_time': '2025-10-16T18:00:00Z',
                    'end_time': '2025-10-16T19:00:00Z',
                    'intensity_mets': 5.0,
                    'metrics': {
                        'exercises': [
                            {'name': 'Bench Press', 'sets': 3, 'reps': 8, 'weight_kg': 100},
                            {'name': 'Pull-ups', 'sets': 3, 'reps': 10, 'weight_kg': 0},
                        ]
                    },
                },
            )

        assert response.status_code == 201
        data = response.json()
        assert data['category'] == 'strength_training'
        assert 'exercises' in data['metrics']
        assert len(data['metrics']['exercises']) == 2

    @patch('app.services.supabase_service.SupabaseService')
    def test_get_activities_list(self, mock_supabase_service, client):
        """Test retrieving list of activities."""
        mock_user = {'id': 'test-user-123'}

        activities = [
            {
                'id': 'activity-001',
                'user_id': 'test-user-123',
                'category': 'cardio_steady_state',
                'activity_name': 'Morning Run',
                'start_time': '2025-10-16T06:00:00Z',
                'duration_minutes': 45,
                'calories_burned': 400,
            },
            {
                'id': 'activity-002',
                'user_id': 'test-user-123',
                'category': 'strength_training',
                'activity_name': 'Workout',
                'start_time': '2025-10-15T18:00:00Z',
                'duration_minutes': 60,
                'calories_burned': 300,
            },
        ]

        mock_supabase_service.return_value.supabase.table.return_value.select.return_value.eq.return_value.is_.return_value.order.return_value.limit.return_value.execute.return_value = Mock(
            data=activities, count=2
        )

        with patch('app.api.dependencies.get_current_user', return_value=mock_user):
            response = client.get('/api/v1/activities')

        assert response.status_code == 200
        data = response.json()
        assert len(data['data']) == 2
        assert data['total'] == 2

    @patch('app.services.supabase_service.SupabaseService')
    def test_get_activities_with_date_filter(self, mock_supabase_service, client):
        """Test retrieving activities with date range filter."""
        mock_user = {'id': 'test-user-123'}

        activities = [
            {
                'id': 'activity-001',
                'category': 'cardio_steady_state',
                'start_time': '2025-10-16T06:00:00Z',
                'duration_minutes': 45,
                'calories_burned': 400,
            }
        ]

        mock_supabase_service.return_value.supabase.table.return_value.select.return_value.eq.return_value.is_.return_value.gte.return_value.lte.return_value.order.return_value.limit.return_value.execute.return_value = Mock(
            data=activities, count=1
        )

        with patch('app.api.dependencies.get_current_user', return_value=mock_user):
            response = client.get(
                '/api/v1/activities',
                params={
                    'start_date': '2025-10-16',
                    'end_date': '2025-10-16',
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data['data']) == 1

    @patch('app.services.supabase_service.SupabaseService')
    def test_get_daily_summary(self, mock_supabase_service, client):
        """Test retrieving daily activity summary."""
        mock_user = {'id': 'test-user-123'}

        activities = [
            {
                'calories_burned': 400,
                'duration_minutes': 45,
                'intensity_mets': 8.0,
            },
            {
                'calories_burned': 300,
                'duration_minutes': 60,
                'intensity_mets': 5.0,
            },
        ]

        mock_supabase_service.return_value.supabase.table.return_value.select.return_value.eq.return_value.is_.return_value.gte.return_value.lte.return_value.execute.return_value = Mock(
            data=activities
        )

        with patch('app.api.dependencies.get_current_user', return_value=mock_user):
            response = client.get(
                '/api/v1/activities/summary',
                params={'target_date': '2025-10-16'},
            )

        assert response.status_code == 200
        data = response.json()
        assert data['total_calories'] == 700
        assert data['total_duration'] == 105
        assert data['activity_count'] == 2
        assert 6.0 <= data['avg_intensity'] <= 7.0  # Average of 8.0 and 5.0

    @patch('app.services.supabase_service.SupabaseService')
    def test_update_activity(self, mock_supabase_service, client):
        """Test updating an activity."""
        mock_user = {'id': 'test-user-123', 'weight_kg': 75}

        # Mock existing activity
        existing_activity = {
            'id': 'activity-001',
            'user_id': 'test-user-123',
            'category': 'cardio_steady_state',
            'activity_name': 'Morning Run',
            'duration_minutes': 45,
        }

        updated_activity = {
            **existing_activity,
            'duration_minutes': 50,
            'notes': 'Felt strong today!',
        }

        mock_supabase_service.return_value.supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = Mock(
            data=existing_activity
        )
        mock_supabase_service.return_value.supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock(
            data=[updated_activity]
        )

        with patch('app.api.dependencies.get_current_user', return_value=mock_user):
            response = client.patch(
                '/api/v1/activities/activity-001',
                json={
                    'duration_minutes': 50,
                    'notes': 'Felt strong today!',
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data['duration_minutes'] == 50
        assert data['notes'] == 'Felt strong today!'

    @patch('app.services.supabase_service.SupabaseService')
    def test_delete_activity(self, mock_supabase_service, client):
        """Test soft-deleting an activity."""
        mock_user = {'id': 'test-user-123'}

        # Mock existing activity
        existing_activity = {
            'id': 'activity-001',
            'user_id': 'test-user-123',
            'category': 'cardio_steady_state',
        }

        mock_supabase_service.return_value.supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = Mock(
            data=existing_activity
        )
        mock_supabase_service.return_value.supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock(
            data=[{**existing_activity, 'deleted_at': '2025-10-16T12:00:00Z'}]
        )

        with patch('app.api.dependencies.get_current_user', return_value=mock_user):
            response = client.delete('/api/v1/activities/activity-001')

        assert response.status_code == 204

    @patch('app.services.supabase_service.SupabaseService')
    def test_cannot_update_other_users_activity(self, mock_supabase_service, client):
        """Test that users cannot update activities they don't own."""
        mock_user = {'id': 'test-user-123'}

        # Activity owned by different user
        other_users_activity = {
            'id': 'activity-001',
            'user_id': 'other-user-456',
            'category': 'cardio_steady_state',
        }

        mock_supabase_service.return_value.supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = Mock(
            data=other_users_activity
        )

        with patch('app.api.dependencies.get_current_user', return_value=mock_user):
            response = client.patch(
                '/api/v1/activities/activity-001',
                json={'duration_minutes': 50},
            )

        assert response.status_code in [403, 404]  # Forbidden or not found

    @patch('app.services.supabase_service.SupabaseService')
    def test_invalid_category_returns_422(self, mock_supabase_service, client):
        """Test that invalid activity category returns validation error."""
        mock_user = {'id': 'test-user-123', 'weight_kg': 75}

        with patch('app.api.dependencies.get_current_user', return_value=mock_user):
            response = client.post(
                '/api/v1/activities',
                json={
                    'category': 'invalid_category',
                    'activity_name': 'Test',
                    'start_time': '2025-10-16T06:00:00Z',
                },
            )

        assert response.status_code == 422  # Validation error

    @patch('app.services.supabase_service.SupabaseService')
    def test_mets_validation_by_category(self, mock_supabase_service, client):
        """Test that METs are validated based on category ranges."""
        mock_user = {'id': 'test-user-123', 'weight_kg': 75}

        # Cardio should be 3.0-15.0 METs
        with patch('app.api.dependencies.get_current_user', return_value=mock_user):
            response = client.post(
                '/api/v1/activities',
                json={
                    'category': 'cardio_steady_state',
                    'activity_name': 'Test',
                    'start_time': '2025-10-16T06:00:00Z',
                    'intensity_mets': 20.0,  # Too high for cardio
                },
            )

        assert response.status_code == 422


@pytest.mark.integration
class TestActivitiesCalculations:
    """Test activity calculations (duration, calories)."""

    @patch('app.services.supabase_service.SupabaseService')
    def test_duration_auto_calculated_from_timestamps(self, mock_supabase_service, client):
        """Test that duration is calculated from start/end times."""
        mock_user = {'id': 'test-user-123', 'weight_kg': 75}

        created_activity = {
            'id': 'activity-001',
            'user_id': 'test-user-123',
            'category': 'cardio_steady_state',
            'start_time': '2025-10-16T06:00:00Z',
            'end_time': '2025-10-16T06:45:00Z',
            'duration_minutes': 45,  # Calculated
        }

        mock_supabase_service.return_value.supabase.table.return_value.insert.return_value.execute.return_value = Mock(
            data=[created_activity]
        )

        with patch('app.api.dependencies.get_current_user', return_value=mock_user):
            response = client.post(
                '/api/v1/activities',
                json={
                    'category': 'cardio_steady_state',
                    'activity_name': 'Run',
                    'start_time': '2025-10-16T06:00:00Z',
                    'end_time': '2025-10-16T06:45:00Z',
                    'intensity_mets': 8.0,
                    # duration_minutes not provided
                },
            )

        assert response.status_code == 201
        assert response.json()['duration_minutes'] == 45

    @patch('app.services.supabase_service.SupabaseService')
    def test_calories_calculated_from_mets(self, mock_supabase_service, client):
        """Test that calories are calculated from METs formula."""
        mock_user = {'id': 'test-user-123', 'weight_kg': 70}

        # 8.0 METs × 70kg × 0.5hr = 280 cal
        created_activity = {
            'id': 'activity-001',
            'user_id': 'test-user-123',
            'start_time': '2025-10-16T06:00:00Z',
            'duration_minutes': 30,
            'intensity_mets': 8.0,
            'calories_burned': 280,  # Calculated
        }

        mock_supabase_service.return_value.supabase.table.return_value.insert.return_value.execute.return_value = Mock(
            data=[created_activity]
        )

        with patch('app.api.dependencies.get_current_user', return_value=mock_user):
            response = client.post(
                '/api/v1/activities',
                json={
                    'category': 'cardio_steady_state',
                    'activity_name': 'Run',
                    'start_time': '2025-10-16T06:00:00Z',
                    'duration_minutes': 30,
                    'intensity_mets': 8.0,
                },
            )

        assert response.status_code == 201
        assert response.json()['calories_burned'] == 280
