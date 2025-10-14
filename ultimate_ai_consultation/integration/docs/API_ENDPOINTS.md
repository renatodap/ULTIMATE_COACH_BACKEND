# 📡 API ENDPOINTS REFERENCE
## Context-Aware Adaptive Program System

**Last Updated:** October 14, 2025
**Version:** 1.0
**Base URL:** `http://localhost:8000/api/v1` (development)

---

## Authentication

All endpoints require Bearer token authentication:

```bash
Authorization: Bearer <token>
```

---

## Context Endpoints

### GET /context/timeline/{user_id}

Get user's context timeline with all life events.

**Parameters:**
- `user_id` (path) - UUID of user
- `days_back` (query, optional) - Number of days to look back (default: 14)

**Response:**
```json
{
  "user_id": "uuid",
  "period_days": 14,
  "context_logs": [
    {
      "id": "uuid",
      "user_id": "uuid",
      "context_type": "stress",
      "severity": "high",
      "sentiment_score": -0.6,
      "description": "Work deadline causing high stress",
      "affects_training": true,
      "affects_nutrition": false,
      "suggested_adaptation": "Reduce volume by 10-15%",
      "extraction_confidence": 0.92,
      "created_at": "2025-10-10T10:30:00Z"
    }
  ],
  "summary": {
    "total_events": 12,
    "stress_events": 3,
    "travel_events": 1,
    "injury_events": 0,
    "informal_activities": 5,
    "avg_sentiment": 0.3
  }
}
```

**Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/context/timeline/uuid?days_back=14" \
  -H "Authorization: Bearer <token>"
```

---

### GET /context/informal-activities/{user_id}

Get AI-extracted informal activities from chat.

**Parameters:**
- `user_id` (path) - UUID of user
- `days_back` (query, optional) - Number of days (default: 14)

**Response:**
```json
{
  "user_id": "uuid",
  "period_days": 14,
  "activities": [
    {
      "id": "uuid",
      "category": "sports",
      "activity_name": "Tennis",
      "start_time": "2025-10-12T14:00:00Z",
      "duration_minutes": 60,
      "perceived_exertion": 7,
      "source": "coach_chat",
      "ai_confidence": 0.95,
      "notes": "Original message: 'Played tennis today'"
    }
  ],
  "total": 5
}
```

---

### GET /context/summary/{user_id}

Get high-level context summary for period.

**Parameters:**
- `user_id` (path) - UUID of user
- `days_back` (query, optional) - Number of days (default: 14)

**Response:**
```json
{
  "user_id": "uuid",
  "period_days": 14,
  "summary": {
    "avg_sentiment": 0.45,
    "sentiment_trend": "improving",
    "stress_level": "moderate",
    "energy_level": "good",
    "informal_activities_count": 5,
    "training_affecting_events": 3,
    "major_disruptions": ["travel", "illness"]
  },
  "recommendations": [
    "Consider reducing volume this week due to travel",
    "User has been very active outside gym (tennis 3x)"
  ]
}
```

---

### POST /context/log

Manually log a context event.

**Request Body:**
```json
{
  "user_id": "uuid",
  "context_type": "stress",
  "description": "Big work presentation tomorrow",
  "severity": "moderate",
  "affects_training": true,
  "affects_nutrition": false
}
```

**Response:**
```json
{
  "success": true,
  "context_id": "uuid",
  "message": "Context logged successfully"
}
```

---

### GET /context/affects-training/{user_id}

Get all context events that affect training.

**Parameters:**
- `user_id` (path) - UUID of user
- `days_back` (query, optional) - Number of days (default: 14)

**Response:**
```json
{
  "user_id": "uuid",
  "period_days": 14,
  "context_logs": [
    {
      "id": "uuid",
      "context_type": "injury",
      "severity": "moderate",
      "description": "Lower back tweak",
      "suggested_adaptation": "Avoid loaded spinal movements",
      "created_at": "2025-10-11T08:00:00Z"
    }
  ],
  "total": 3
}
```

---

### DELETE /context/{context_id}

Delete a context log entry.

**Parameters:**
- `context_id` (path) - UUID of context log
- `user_id` (query) - UUID of user (authorization check)

**Response:**
```json
{
  "success": true,
  "message": "Context log deleted"
}
```

---

## Program Endpoints

### GET /programs/templates/{user_id}

Get user's active activity templates.

**Response:**
```json
{
  "templates": [
    {
      "id": "uuid",
      "user_id": "uuid",
      "template_name": "Upper Body A",
      "activity_type": "strength_training",
      "description": "Push-focused upper body",
      "default_exercises": [
        {
          "exercise_id": "uuid",
          "exercise_name": "Bench Press",
          "target_sets": 4,
          "target_reps": 8,
          "target_weight_kg": 80
        }
      ],
      "auto_match_enabled": true,
      "use_count": 12,
      "last_used_at": "2025-10-13T10:00:00Z",
      "is_active": true
    }
  ],
  "total": 4
}
```

---

### GET /programs/templates/{user_id}/today

Get today's recommended template.

**Response:**
```json
{
  "template": {
    "id": "uuid",
    "template_name": "Lower Body A",
    "default_exercises": [...],
    "expected_duration_minutes": 60
  },
  "reasoning": "Next in rotation, last lower body was 3 days ago"
}
```

---

### POST /programs/templates

Create new activity template.

**Request Body:**
```json
{
  "user_id": "uuid",
  "template_name": "Upper Body A",
  "activity_type": "strength_training",
  "description": "Push-focused upper body",
  "default_exercises": [
    {
      "exercise_id": "uuid",
      "exercise_name": "Bench Press",
      "target_sets": 4,
      "target_reps": 8,
      "target_weight_kg": 80
    }
  ],
  "auto_match_enabled": true,
  "expected_duration_minutes": 60
}
```

**Response:**
```json
{
  "success": true,
  "template_id": "uuid",
  "message": "Template created successfully"
}
```

---

### GET /programs/activities/{user_id}

Get user's activities with filters.

**Parameters:**
- `days_back` (query, optional) - Number of days (default: 14)
- `category` (query, optional) - Filter by category
- `include_exercise_sets` (query, optional) - Include sets (default: false)
- `include_template` (query, optional) - Include template info (default: false)

**Response:**
```json
{
  "activities": [
    {
      "id": "uuid",
      "category": "strength_training",
      "activity_name": "Upper Body A",
      "start_time": "2025-10-13T10:00:00Z",
      "duration_minutes": 62,
      "template_id": "uuid",
      "template_match_score": 0.95,
      "perceived_exertion": 8,
      "exercise_sets": [
        {
          "exercise_id": "uuid",
          "set_number": 1,
          "reps": 8,
          "weight_kg": 80,
          "rpe": 8,
          "completed": true
        }
      ]
    }
  ],
  "total": 24
}
```

---

### POST /programs/activities

Create new activity.

**Request Body:**
```json
{
  "user_id": "uuid",
  "category": "strength_training",
  "activity_name": "Upper Body A",
  "start_time": "2025-10-14T10:00:00Z",
  "duration_minutes": 60,
  "template_id": "uuid",
  "perceived_exertion": 8,
  "notes": "Felt strong today"
}
```

**Response:**
```json
{
  "success": true,
  "activity_id": "uuid",
  "message": "Activity created successfully"
}
```

---

### POST /programs/exercise-sets

Create exercise set.

**Request Body:**
```json
{
  "activity_id": "uuid",
  "exercise_id": "uuid",
  "set_number": 1,
  "reps": 8,
  "weight_kg": 80,
  "rpe": 8,
  "completed": true,
  "notes": "Good form"
}
```

**Response:**
```json
{
  "success": true,
  "set_id": "uuid",
  "message": "Exercise set created"
}
```

---

### POST /programs/exercise-sets/batch

Create multiple exercise sets at once.

**Request Body:**
```json
{
  "sets": [
    {
      "activity_id": "uuid",
      "exercise_id": "uuid",
      "set_number": 1,
      "reps": 8,
      "weight_kg": 80
    },
    {
      "activity_id": "uuid",
      "exercise_id": "uuid",
      "set_number": 2,
      "reps": 8,
      "weight_kg": 80
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "set_ids": ["uuid1", "uuid2"],
  "message": "2 sets created"
}
```

---

### GET /programs/exercises/search

Search exercises by name.

**Parameters:**
- `q` (query) - Search query
- `limit` (query, optional) - Max results (default: 20)

**Response:**
```json
{
  "exercises": [
    {
      "id": "uuid",
      "name": "Barbell Bench Press",
      "category": "chest",
      "primary_muscle_groups": ["pectorals"],
      "equipment_needed": ["barbell", "bench"],
      "difficulty_level": "intermediate"
    }
  ]
}
```

---

### GET /programs/adherence/{user_id}

Get adherence metrics.

**Parameters:**
- `days_back` (query, optional) - Number of days (default: 14)

**Response:**
```json
{
  "planned_count": 10,
  "completed_count": 8,
  "adherence_pct": 80.0,
  "context_adjusted_adherence_pct": 95.0,
  "completed_with_template": 7,
  "completed_without_template": 1,
  "informal_activities": 3,
  "context_summary": {
    "stress_days": 3,
    "travel_days": 2,
    "illness_days": 0
  }
}
```

---

### GET /programs/history/{user_id}/{exercise_id}

Get exercise history for specific exercise.

**Parameters:**
- `limit` (query, optional) - Max results (default: 50)

**Response:**
```json
{
  "history": [
    {
      "activity_id": "uuid",
      "activity_name": "Upper Body A",
      "start_time": "2025-10-13T10:00:00Z",
      "set_number": 1,
      "reps": 8,
      "weight_kg": 80,
      "rpe": 8,
      "estimated_1rm": 100,
      "set_volume": 640
    }
  ]
}
```

---

### GET /programs/personal-records/{user_id}/{exercise_id}

Get personal records for exercise.

**Response:**
```json
{
  "max_weight_kg": 85,
  "max_weight_reps": 8,
  "max_weight_date": "2025-10-10",
  "max_estimated_1rm": 106,
  "max_1rm_date": "2025-10-10",
  "max_set_volume": 680,
  "max_volume_date": "2025-10-12"
}
```

---

### GET /programs/volume/{user_id}

Get weekly volume statistics.

**Parameters:**
- `weeks_back` (query, optional) - Number of weeks (default: 12)

**Response:**
```json
{
  "weeks": [
    {
      "week_start": "2025-10-07",
      "total_activities": 4,
      "total_sets": 120,
      "total_volume": 48000,
      "avg_rpe": 7.5
    }
  ]
}
```

---

### GET /programs/status/{user_id}

Get program generation status.

**Response:**
```json
{
  "has_program": true,
  "program_created_at": "2025-10-01T10:00:00Z",
  "last_adjustment_at": "2025-10-08T10:00:00Z",
  "next_reassessment": "2025-10-15T10:00:00Z",
  "persona_type": "9-to-5 Hustler",
  "persona_confidence": 0.87
}
```

---

### POST /programs/generate/{user_id}

Trigger program generation.

**Request Body:**
```json
{
  "consultation_data": {
    "age": 32,
    "fitness_goals": "Build muscle",
    "available_days": 4,
    "session_duration": 60,
    "equipment_access": ["gym_full"],
    "notes": "Work 9-5, can train before or after work"
  }
}
```

**Response:**
```json
{
  "success": true,
  "program_id": "uuid",
  "templates_created": 4,
  "persona_detected": "9-to-5 Hustler",
  "message": "Program generated successfully"
}
```

---

### POST /programs/reassess/{user_id}

Trigger manual reassessment.

**Response:**
```json
{
  "success": true,
  "adjustment_made": true,
  "reason": "Adherence 92%, increase volume by 5%",
  "changes": {
    "volume_adjustment": "+5%",
    "intensity_adjustment": "maintain",
    "templates_updated": 4
  },
  "message": "Reassessment complete"
}
```

---

## Error Responses

All endpoints return consistent error format:

**400 Bad Request:**
```json
{
  "error": "Bad Request",
  "message": "Missing required field: user_id",
  "status_code": 400
}
```

**401 Unauthorized:**
```json
{
  "error": "Unauthorized",
  "message": "Invalid or missing authentication token",
  "status_code": 401
}
```

**404 Not Found:**
```json
{
  "error": "Not Found",
  "message": "User not found",
  "status_code": 404
}
```

**500 Internal Server Error:**
```json
{
  "error": "Internal Server Error",
  "message": "An unexpected error occurred",
  "status_code": 500
}
```

---

## Rate Limiting

- **Free tier**: 100 requests/minute per user
- **Pro tier**: 1000 requests/minute per user

**Rate limit headers:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1696946400
```

---

## Webhook Support (Future)

Future support for webhooks to notify external systems:

- `program.generated` - New program created
- `program.adjusted` - Program adjusted by reassessment
- `activity.completed` - Activity completed
- `context.logged` - Context event logged

---

## Testing Endpoints

Use included Postman collection:

```bash
# Import collection
postman/ULTIMATE_COACH_API.postman_collection.json

# Set environment variables
- API_BASE_URL: http://localhost:8000
- AUTH_TOKEN: <your-token>
```

---

## Support

For API questions:
- **Documentation**: This file
- **Code**: `backend/app/api/v1/`
- **Tests**: `tests/test_api/`

---

**Built for developers, by developers.**
