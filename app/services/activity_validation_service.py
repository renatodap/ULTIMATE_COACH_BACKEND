"""
Activity Metrics Validation Service

Validates JSONB metrics for different activity types.
Prevents inconsistent data from entering the database.
"""

import logging
from typing import Dict, Any, Optional
from jsonschema import validate, ValidationError

logger = logging.getLogger(__name__)


# JSON Schemas for each activity type
ACTIVITY_SCHEMAS = {
    'running': {
        'type': 'object',
        'properties': {
            'distance_km': {'type': 'number', 'minimum': 0, 'maximum': 500},
            'avg_pace': {'type': 'string', 'pattern': r'^\d+:\d{2}(/km|/mi)?$'},  # e.g., "5:30/km"
            'avg_heart_rate': {'type': 'integer', 'minimum': 40, 'maximum': 220},
            'max_heart_rate': {'type': 'integer', 'minimum': 40, 'maximum': 220},
            'elevation_gain_m': {'type': 'number', 'minimum': 0},
            'cadence_spm': {'type': 'integer', 'minimum': 100, 'maximum': 220}
        },
        'additionalProperties': True  # Allow custom fields
    },

    'cycling': {
        'type': 'object',
        'properties': {
            'distance_km': {'type': 'number', 'minimum': 0},
            'avg_speed_kph': {'type': 'number', 'minimum': 0, 'maximum': 100},
            'elevation_gain_m': {'type': 'number', 'minimum': 0},
            'avg_cadence': {'type': 'integer', 'minimum': 0, 'maximum': 200},
            'avg_power_watts': {'type': 'integer', 'minimum': 0, 'maximum': 2000},
            'max_power_watts': {'type': 'integer', 'minimum': 0, 'maximum': 3000},
            'avg_heart_rate': {'type': 'integer', 'minimum': 40, 'maximum': 220},
            'max_heart_rate': {'type': 'integer', 'minimum': 40, 'maximum': 220}
        },
        'additionalProperties': True
    },

    'swimming': {
        'type': 'object',
        'properties': {
            'laps': {'type': 'integer', 'minimum': 1},
            'pool_length_meters': {'type': 'number', 'enum': [25, 50, 33.3]},  # Common pool lengths
            'distance_m': {'type': 'number', 'minimum': 0},
            'stroke_type': {'type': 'string', 'enum': ['freestyle', 'backstroke', 'breaststroke', 'butterfly', 'mixed']},
            'avg_pace': {'type': 'string'},  # e.g., "1:45/100m"
            'avg_heart_rate': {'type': 'integer', 'minimum': 40, 'maximum': 220}
        },
        'additionalProperties': True
    },

    'strength_training': {
        'type': 'object',
        'properties': {
            'total_volume_kg': {'type': 'number', 'minimum': 0},
            'sets_completed': {'type': 'integer', 'minimum': 0},
            'exercises_count': {'type': 'integer', 'minimum': 0},
            'avg_rest_seconds': {'type': 'integer', 'minimum': 0},
            'exercises': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'name': {'type': 'string'},
                        'sets': {'type': 'integer', 'minimum': 1},
                        'reps': {'type': 'integer', 'minimum': 1},
                        'weight_kg': {'type': 'number', 'minimum': 0},
                        'rpe': {'type': 'integer', 'minimum': 1, 'maximum': 10}
                    },
                    'required': ['name']
                }
            }
        },
        'additionalProperties': True
    },

    'sports': {
        'type': 'object',
        'properties': {
            'sport_type': {'type': 'string'},
            'score_us': {'type': ['integer', 'string']},  # Can be "3-1" for sets
            'score_them': {'type': ['integer', 'string']},
            'opponent': {'type': 'string'},
            'stats': {'type': 'object'}  # Flexible stats (points, rebounds, etc.)
        },
        'additionalProperties': True
    }
}


class ActivityValidationService:
    """Validates activity metrics JSONB against schemas."""

    def validate_metrics(
        self,
        activity_type: str,
        metrics: Dict[str, Any]
    ) -> tuple[bool, Optional[str]]:
        """
        Validate activity metrics against schema.

        Args:
            activity_type: Activity type (running, cycling, etc.)
            metrics: Metrics dictionary to validate

        Returns:
            Tuple of (is_valid, error_message)

        Example:
            >>> validator.validate_metrics('running', {'distance_km': 5.2, 'avg_pace': '5:30/km'})
            (True, None)

            >>> validator.validate_metrics('running', {'distance_km': -5})
            (False, "distance_km: -5 is less than the minimum of 0")
        """
        # Unknown activity types are allowed (no validation)
        if activity_type not in ACTIVITY_SCHEMAS:
            logger.debug(f"[ActivityValidation] No schema for {activity_type}, skipping validation")
            return (True, None)

        schema = ACTIVITY_SCHEMAS[activity_type]

        try:
            # Validate against JSON Schema
            validate(instance=metrics, schema=schema)
            logger.debug(f"[ActivityValidation] ✅ Metrics valid for {activity_type}")
            return (True, None)
        except ValidationError as e:
            error_msg = f"{e.json_path}: {e.message}"
            logger.warning(f"[ActivityValidation] ❌ Validation failed for {activity_type}: {error_msg}")
            return (False, error_msg)

    def get_schema(self, activity_type: str) -> Optional[Dict[str, Any]]:
        """Get JSON schema for activity type."""
        return ACTIVITY_SCHEMAS.get(activity_type)

    def get_supported_types(self) -> list[str]:
        """Get list of activity types with schemas."""
        return list(ACTIVITY_SCHEMAS.keys())


# Singleton
_validation_service: Optional[ActivityValidationService] = None

def get_activity_validation_service() -> ActivityValidationService:
    """Get singleton ActivityValidationService instance."""
    global _validation_service
    if _validation_service is None:
        _validation_service = ActivityValidationService()
    return _validation_service
