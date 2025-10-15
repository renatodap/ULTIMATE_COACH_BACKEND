Migration 036 — Planning + Adaptive (Apply Order)

Summary
- Adds normalized plan tables (programs, session_instances, exercise_plan_items, meal_instances, meal_item_plan)
- Adds adherence_records, plan_change_events, day_overrides, and calendar_events
- Adds planned_* link columns to activities and meals tables
- Enforces RLS policies tied to user_id via programs and profiles

Prerequisites
- Existing `profiles`, `activities`, `meals` tables and auth.users
- Supabase environment with service role key for server-side writes

Apply
1) Run migration SQL:
   - Execute `migrations/036_planning_and_adaptive.sql` in your DB (psql or Supabase SQL editor)

2) Verify tables and policies:
   - SELECT count(*) FROM programs;
   - CHECK RLS policies: ensure SELECT/INSERT allowed only for same user_id

3) Rollback (if needed):
   - Drop created tables in reverse dependency order (calendar_events → day_overrides → plan_change_events → adherence_records → meal_item_plan → meal_instances → exercise_plan_items → session_instances → programs)

Usage Notes
- Use `ProgramPersistenceService.save_program_bundle()` to persist outputs of `ultimate_ai_consultation` generator
- Attach logs to plan:
  - Set `activities.planned_session_instance_id` when logging a workout
  - Set `meals.planned_meal_instance_id` when logging a meal
- Record user-marked adherence via `AdherenceService.set_adherence()`
- Run daily overrides via `scripts/daily_adjuster.py` (cron)

