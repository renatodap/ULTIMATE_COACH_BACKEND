Planning + Adaptive API (Frontend‑Optimized)

Audience: Frontend (or AI agent) implementing calendar UI, plan views, adherence marking, and daily adjustments. No coach in the loop — user or system acts.

Key Concepts
- Program: 14‑day baseline plan snapshot (immutable), produced by AI generator.
- Plan instances: normalized scheduled items for calendar (sessions + meals).
- Adherence: user marks planned items as completed/similar/skipped; optionally attaches actual logs.
- Overrides: day‑level nutrition/training adjustments (missed session, poor sleep, etc.).
- Calendar events: denormalized view for fast UI rendering per day.

Data Model (DB Tables)
- programs: id, user_id, primary_goal, program_start_date, program_duration_weeks, full_bundle(JSON), provenance(JSON), tdee(JSON), macros(JSON), safety(JSON), feasibility(JSON), next_reassessment_date
- session_instances: id, program_id, week_index(1..N), day_index(1..7), day_of_week, time_of_day, start_hour, end_hour, session_kind(resistance|endurance|hiit|sport), modality, session_name, estimated_duration_minutes, parameters_json(intervals/drills), state
- exercise_plan_items: id, session_instance_id, order_index, name, muscle_groups[], sets, rep_range, rest_seconds, rir, is_compound, notes
- meal_instances: id, program_id, week_index, day_index, day_name, order_index, meal_type, meal_name, targets_json, totals_json, notes
- meal_item_plan: id, meal_instance_id, order_index, food_name, serving_size, serving_unit, targets_json
- adherence_records: id, user_id, planned_entity_type(session|meal), planned_entity_id, status(completed|similar|skipped), similarity_score, adherence_json, actual_ref_type(activity|meal), actual_ref_id, assessed_at
- plan_change_events: id, program_id, user_id, change_type(swap|edit|move|cancel|reschedule), planned_entity_type, planned_entity_id, new_entity_id, effective_date, reason_code, reason_text, diff_json, created_at
- day_overrides: id, user_id, date, override_type(nutrition|training|both), reason_code, reason_details, confidence, nutrition_override(JSON), training_override(JSON), created_at
- calendar_events: id, user_id, program_id, date(YYYY‑MM‑DD), start_time_utc, end_time_utc, local_tz, event_type(training|multimodal|meal), ref_table, ref_id, title, details(JSON), status(planned|completed|similar|skipped|modified)
- activities (existing): add planned_session_instance_id, similarity_score
- meals (existing): add planned_meal_instance_id, adherence_json

Event Types (UI)
- training: resistance sessions (from training_plan)
- multimodal: endurance/HIIT/sport sessions (from modality planner)
- meal: planned meals (nutrition plan)

Statuses
- planned (default)
- completed (user action)
- similar (user action)
- skipped (user action or system after day passes)
- modified (system/user overrides or swaps)

Core Flows
1) Create plan (server‑side)
- Backend calls AI generator → ProgramBundle
- Persist: POST server uses ProgramPersistenceService to write programs, session_instances, meal_instances, etc.
Frontend: No direct call required unless you initiate generation from UI.

2) Calendar (frontend)
- GET /calendar?date=YYYY‑MM‑DD&range=week
  - Returns array of calendar_events with embedded display fields:
    - id, date, event_type, status
    - title (e.g., “Upper A”, “Easy Run 45’”, “Lunch”)
    - time_of_day or start/end (if fixed)
    - plan refs: {ref_table, ref_id}
    - details: { planned_macros | intervals | drills | notes }

3) Adherence (user marks planned item)
- POST /adherence
  - body:
    {
      "planned_entity_type": "session" | "meal",
      "planned_entity_id": "uuid",
      "status": "completed" | "similar" | "skipped",
      "actual_ref_type": "activity" | "meal" | null,
      "actual_ref_id": "uuid" | null,
      "adherence_json": { … },
      "similarity_score": 0.0..1.0
    }
  - server writes adherence_records, updates calendar_events.status, and sets session_instances.state
  - response: adherence record

4) Plan change (user swaps/edits schedule)
- POST /plan_changes
  - body:
    {
      "planned_entity_type": "session" | "meal",
      "planned_entity_id": "uuid",
      "change_type": "swap" | "move" | "edit" | "cancel" | "reschedule",
      "new_entity": { … optional new session/meal definition … },
      "reason_code": "user_request" | "injury" | "time_conflict" | "other",
      "reason_text": "free text"
    }
  - server creates new planned instance if needed, marks old as superseded, creates plan_change_events with diff_json, and updates calendar
  - response: { new_entity_id, change_event_id }

5) Daily overrides (system)
- Cron triggers server to run DailyAdjuster (scripts/daily_adjuster.py)
- Writes day_overrides for today when applicable and updates calendar
- Frontend pulls overrides for badges/banners
  - GET /overrides/today → { date, overrides: ["nutrition", "training"], details per type }

Similarity/Adherence UI (no coach, user decides)
- For each calendar card, show CTA group:
  - “Completed” → POST /adherence { status:"completed" }
  - “Similar” → open modal to capture free text summary and optional similarity slider (0.5–0.9), then POST /adherence { status:"similar", adherence_json, similarity_score }
  - “Skipped” → POST /adherence { status:"skipped" }
- For meals, optionally show macro deltas in the modal.

Session Details UI
- Resistance: list exercises from exercise_plan_items (sets, reps, rest, RIR, notes)
- Multimodal: show intervals/drills from session_instances.parameters_json; show intensity_target and duration
- Time info: show time_of_day or exact start_hour–end_hour

Meal Details UI
- Per meal: show targets (calories/macros), items (food_name, serving), and planned totals
- Day overview: daily totals and adherence % (from nutrition plan or computed actuals)

Overlays / Banners
- If calendar_events.status = modified or a day_overrides exists for date → show a top banner on that day/cards: 
  - Example: “Adjusted today: HIIT → Easy Z1/Z2 (poor sleep)”, “Nutrition: −7% kcal (missed workout yesterday)”

Example Calendar Event JSON
{
  "id": "evt-uuid",
  "date": "2025-10-16",
  "event_type": "training",
  "status": "planned",
  "ref_table": "session_instances",
  "ref_id": "sess-uuid",
  "title": "Upper Body A",
  "details": {
    "day_of_week": "monday",
    "time_of_day": "morning"
  }
}

Example Adherence POST
{
  "planned_entity_type": "session",
  "planned_entity_id": "sess-uuid",
  "status": "similar",
  "adherence_json": { "notes": "Did push instead of pull", "duration_min": 60 },
  "similarity_score": 0.7
}

Endpoints (suggested, implement server‑side)
- POST /programs/save (server) → persists ProgramBundle via ProgramPersistenceService
- GET /calendar?date&range → lists calendar_events for user
- POST /adherence → AdherenceService.set_adherence
- POST /plan_changes → creates plan_change_events and new planned instance (server computes diff)
- GET /overrides/today → returns latest day_overrides for current date
- GET /programs/current → returns the latest program snapshot and summary metrics

Plan Logs (attach existing logs to planned instances)
- POST /planlogs/attach_activity
  - body: { user_id, activity_id, planned_session_instance_id, similarity_score? }
  - effect: updates activities row with planned link; use afterward POST /adherence to set status
- POST /planlogs/attach_meal
  - body: { user_id, meal_id, planned_meal_instance_id, adherence_json? }
  - effect: updates meals row with planned link; use afterward POST /adherence to set status

Client Responsibilities
- Timezone: provide user tz or rely on server to resolve; display local time accordingly
- Optimistic UI: immediately set card status (completed/similar/skipped) and reconcile on response
- Similarity: user is the authority; backend just stores status + optional similarity_score/adherence_json

Backend Responsibilities
- Enforce RLS (auth.uid() = user_id) on all tables
- Validate planned_entity_id belongs to the user
- Optionally compute smart similarity if actual logs are present
- Respect safety bounds in daily overrides

Generator Integration (already done)
- Training sessions include day_of_week/time_of_day
- Multimodal sessions include time_of_day and optional start/end hours for fixed windows
- Meal plan covers 14 days; meals_per_day honored when provided

Open Extensions (future)
- Auto‑similarity: infer similarity from logged activity vs planned template (sets/distance/HR zones)
- Habit engine: propose time-of-day shifts if user repeatedly misses the same slot
- Notifications: “Your plan was adjusted for today” push
