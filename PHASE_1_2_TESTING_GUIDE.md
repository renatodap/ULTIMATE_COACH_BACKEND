# 🚀 PHASE 1 & 2 TESTING GUIDE

Complete testing guide for Program Display System (Phase 1) and Calendar/Progress Tracking (Phase 2).

---

## ⚠️ PREREQUISITES

### 1. Run Migration 045 (REQUIRED)

Before testing, you **MUST** run the database migration that adds `completed_at` columns.

**Via Supabase Dashboard (Recommended):**

1. Go to https://supabase.com/dashboard
2. Click on project: `txuebspgxwtnwmwiwxfo`
3. Navigate to **SQL Editor** → **New Query**
4. Copy/paste from `migrations/045_add_completed_at_columns.sql`
5. Click **Run**
6. Verify: "Success. No rows returned"

**Verification Query:**
```sql
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name IN ('session_instances', 'meal_instances')
  AND column_name = 'completed_at';
```

Should return 2 rows (one for each table).

**What happens if you skip this:**
- "Mark Complete" buttons will return 500 errors
- Error: "column completed_at does not exist"

---

## 🎯 PHASE 1: PROGRAM DISPLAY SYSTEM

### Feature Overview

**What's Included:**
- ✅ Today's Plan page (`/plan/today`)
- ✅ Weekly Schedule page (`/plan/week`)
- ✅ Program Summary page (`/plan`)
- ✅ Workout completion tracking
- ✅ Meal completion tracking
- ✅ Auto-redirect from dashboard after generation

### Backend Endpoints Added

```
GET  /api/v1/programs/today     - Today's workout + meals with full details
GET  /api/v1/programs/week      - 7-day schedule (Monday-Sunday)
PATCH /api/v1/programs/sessions/{id}/complete - Mark workout complete
PATCH /api/v1/programs/meals/{id}/complete    - Mark meal complete
```

### Frontend Pages

```
/plan                - Program summary + navigation
/plan/today          - Today's workout + meals
/plan/week           - Weekly schedule overview
```

### Testing Flow

#### **1. Generate a Program**

**Steps:**
1. Navigate to `/dashboard`
2. Click **"Generate Your Plan"** button
3. Wait for generation (may take 30-60 seconds)
4. Should auto-redirect to `/plan/today`

**Expected Result:**
- Program generated with 12 weeks of sessions + meals
- User redirected to today's plan immediately
- No errors in console

**Troubleshooting:**
- If stuck: Check browser console for errors
- If 500 error: Check backend logs in Railway
- If no redirect: Check `app/dashboard/page.tsx` line 107

---

#### **2. View Today's Plan**

**URL:** `http://localhost:3003/plan/today`

**What You Should See:**

**Header Section:**
- Date (e.g., "Tuesday, October 22, 2025")
- Program goal (e.g., "Muscle Gain")
- Week number (e.g., "Week 1 of 12")
- Day number (e.g., "Day 2")

**Daily Nutrition Targets:**
- 4-column grid: Calories, Protein, Carbs, Fat
- Shows progress: "2150 of 2500" calories
- Targets calculated from program

**Today's Workout:**
- Workout name (e.g., "Upper Body Strength")
- Time of day (morning/afternoon/evening)
- Estimated duration (e.g., "60 min")
- Full exercise list with sets, reps, rest, RIR
- **"Mark Complete"** button (orange)

OR

**Rest Day:**
- 😴 emoji
- "Rest Day" message
- Explanation about muscle recovery

**Today's Meals:**
- 3-4 meal cards (Breakfast, Lunch, Dinner, Snack)
- Each meal shows:
  - Meal type icon (🌅 breakfast, 🍽️ lunch, 🌙 dinner, 🍪 snack)
  - Meal name
  - Food items with quantities
  - Macro totals (calories, protein, carbs, fat)
  - **"Mark Complete"** button

**Bottom Navigation:**
- "View Full Week Schedule" button

---

#### **3. Mark Items Complete**

**Test Workout Completion:**
1. Click **"Mark Complete"** on today's workout
2. Should see: ✓ **Completed** badge appear
3. Button changes to gray
4. Timestamp shows when marked complete

**Test Meal Completion:**
1. Click **"Mark Complete"** on any meal
2. Should see: ✓ **Completed** badge
3. Button disabled
4. Timestamp displayed

**Test Persistence:**
1. Mark workout complete
2. Refresh page (F5)
3. Workout should still show as completed
4. Data persists in database

**API Calls:**
```
Request: PATCH /api/v1/programs/sessions/{id}/complete
Response: {
  "success": true,
  "session_id": "uuid",
  "completed_at": "2025-10-22T14:30:00Z",
  "message": "Upper Body Strength marked complete"
}
```

---

#### **4. View Weekly Schedule**

**URL:** `http://localhost:3003/plan/week`

**What You Should See:**

**Header:**
- Week range (e.g., "Week 1 of 12")
- Date range (e.g., "Oct 21 - Oct 27")
- Program goal

**7-Day Grid:**
- Monday through Sunday cards
- **Today highlighted** with orange border
- **"View Details"** button on today's card

**Each Day Shows:**

**Training Session:**
- 💪 icon
- Session name
- Exercise count (e.g., "6 exercises")
- Duration (e.g., "60 min")
- Time of day
- Completion status (if completed: ✓ Done badge)

OR

**Rest Day:**
- 😴 emoji
- "Rest Day" text

**Meals Summary:**
- 🍽️ icon
- Meal count (e.g., "3 Meals")
- Total calories (e.g., "2150 calories total")
- Meal types listed (Breakfast, Lunch, Dinner)

**Bottom Navigation:**
- "Back to Today" button → Returns to `/plan/today`

---

#### **5. Program Summary Page**

**URL:** `http://localhost:3003/plan`

**What You Should See:**

**Program Overview:**
- 2×2 grid with tiles:
  - Goal (e.g., "Muscle Gain")
  - Duration (e.g., "4 sessions/week")
  - Start Date
  - Next Check-in Date

**Daily Nutrition:**
- 4-column grid: Calories, Protein, Carbs, Fat
- Shows target macros

**Quick Actions:**
- "View Today's Plan" button (orange) → `/plan/today`
- "View Week Schedule" button (gray) → `/plan/week`

---

## 🗓️ PHASE 2: CALENDAR & PROGRESS TRACKING

### Feature Overview

**What's Included:**
- ✅ Calendar view with event status (`/plan/calendar`)
- ✅ Progress tracking with adherence stats (`/plan/progress`)
- ✅ Calendar events auto-created on program generation
- ✅ Calendar status updates when items marked complete

### Backend Endpoints Added

```
GET /api/v1/calendar/full     - Calendar events for day/week with status
GET /api/v1/calendar/summary  - Adherence stats by date range
```

### Frontend Pages

```
/plan/calendar  - Weekly calendar with color-coded events
/plan/progress  - 7-day adherence summary
/plan/log       - Hub linking to activities and nutrition
```

### Testing Flow

#### **6. View Calendar**

**URL:** `http://localhost:3003/plan/calendar`

**What You Should See:**

**Header:**
- Week label (e.g., "Week of Oct 21")
- Date picker input (change date to view different weeks)

**Weekly Events:**
- Events grouped by date
- Each date shows day name and date (e.g., "Tuesday, Oct 22")

**Event Cards:**

**Training Events:**
- Event type: "training"
- Title: Session name
- Time of day displayed
- Status badge (top-right):
  - **Planned** - Gray
  - **Completed** - Green background
  - **Similar** - Blue background
  - **Skipped** - Red background
  - **Modified** - Amber background

**Meal Events:**
- Event type: "meal"
- Title: Meal name
- Start hour displayed if set
- Status badge

**Color Coding:**
- Green border: Completed events
- Blue border: Similar adherence
- Red border: Skipped
- Amber border: Modified
- Gray border: Planned (not yet done)

**Interaction:**
- Click event → Navigate to detail page

**Testing Calendar Status Updates:**
1. Mark workout complete on `/plan/today`
2. Navigate to `/plan/calendar`
3. Find today's workout event
4. Should show: ✓ **completed** status with green border
5. Verify meal events show planned status (not yet completed)

---

#### **7. View Progress**

**URL:** `http://localhost:3003/plan/progress`

**What You Should See:**

**Header:**
- "Last 7 days" label

**7-Day Grid:**
- 7 columns (one per day)
- Each column shows:
  - Date (MM-DD format)
  - ✅ Completed count
  - ~ Similar count
  - ✗ Skipped count

**Example Day:**
```
10-22
✅ 3
~ 1
✗ 0
```
Means:
- 3 events completed
- 1 event similar adherence
- 0 events skipped

**Testing Progress Tracking:**
1. Complete 2-3 workouts/meals throughout the week
2. Navigate to `/plan/progress`
3. Should see completed count increase for those days
4. Verify counts match actual completions

**Data Calculation:**
- Backend aggregates `calendar_events` by date
- Groups by status: completed, similar, skipped, planned, modified
- Returns counts for each day in range

---

#### **8. Integration Testing**

**Full Flow Test:**

1. **Generate Program**
   - Dashboard → "Generate Your Plan"
   - Wait for completion
   - Auto-redirect to `/plan/today`

2. **Complete Today's Items**
   - Mark workout complete
   - Mark 2-3 meals complete

3. **Verify Calendar**
   - Navigate to `/plan/calendar`
   - Check today's events show "completed" status
   - Verify future events show "planned" status

4. **Verify Progress**
   - Navigate to `/plan/progress`
   - Check today's column shows completed count
   - Should match number of items you marked complete

5. **Verify Weekly Schedule**
   - Navigate to `/plan/week`
   - Check today shows completion status
   - Verify rest of week shows planned sessions/meals

6. **Verify Persistence**
   - Refresh browser
   - Navigate through all pages again
   - All completion data should persist

---

## 🔍 DEBUGGING

### Common Issues

**Issue:** Migration not run
- **Symptom:** 500 error when marking items complete
- **Error:** "column completed_at does not exist"
- **Fix:** Run migration 045 via Supabase Dashboard

**Issue:** Calendar events not appearing
- **Symptom:** Empty calendar page
- **Check:** Did program generation complete successfully?
- **Verify:** Query database:
  ```sql
  SELECT COUNT(*) FROM calendar_events WHERE user_id = 'your-user-id';
  ```
- **Expected:** Should have events (sessions + meals × 7 days × weeks)

**Issue:** Calendar status not updating
- **Symptom:** Complete items, but calendar still shows "planned"
- **Check:** Backend logs for "calendar_event_updated" log entry
- **Verify:** Query database:
  ```sql
  SELECT status FROM calendar_events WHERE ref_id = 'session-or-meal-id';
  ```
- **Expected:** Status should be "completed"

**Issue:** Progress page shows zero counts
- **Symptom:** All days show 0 completed
- **Check:** Have you marked any items complete?
- **Verify:** Calendar events exist with completed status:
  ```sql
  SELECT date, status, COUNT(*)
  FROM calendar_events
  WHERE user_id = 'your-user-id'
  GROUP BY date, status;
  ```

### Backend Logs

**Check Railway Logs:**
1. Go to Railway dashboard
2. Select `ULTIMATE_COACH_BACKEND` project
3. View logs tab
4. Search for:
   - `generate_program_request` - Program generation started
   - `program_generated` - Generation completed
   - `calendar_events_created` - Events created
   - `session_marked_complete` - Workout completed
   - `calendar_event_updated` - Calendar status updated

**Successful Generation Log:**
```
{"event": "generate_program_request", "user_id": "...", "duration_weeks": 12}
{"event": "program_generated", "program_id": "...", "sessions": 48, "meals": 252}
{"event": "calendar_events_created", "program_id": "...", "events": 300}
```

**Successful Completion Log:**
```
{"event": "mark_session_complete", "user_id": "...", "session_id": "..."}
{"event": "calendar_event_updated", "session_id": "...", "status": "completed"}
{"event": "session_marked_complete", "session_name": "Upper Body Strength"}
```

---

## ✅ SUCCESS CRITERIA

### Phase 1 Success

- [ ] Program generates without errors
- [ ] Auto-redirects to `/plan/today` after generation
- [ ] Today's page shows workout + meals with full details
- [ ] "Mark Complete" button works for workouts
- [ ] "Mark Complete" button works for meals
- [ ] Completion status persists after refresh
- [ ] Weekly schedule shows 7 days correctly
- [ ] Today highlighted with orange border in week view
- [ ] Rest days show 😴 emoji
- [ ] All navigation works (today ↔ week ↔ summary)

### Phase 2 Success

- [ ] Calendar page shows events for the week
- [ ] Events grouped by date correctly
- [ ] Completed items show green "completed" badge
- [ ] Calendar status updates when items marked complete
- [ ] Progress page shows last 7 days
- [ ] Completion counts accurate per day
- [ ] Integration: Complete item → Calendar updates → Progress reflects

---

## 🎯 WHAT'S BEEN BUILT

### Backend (Python/FastAPI)

**Phase 1:**
- Enhanced `GET /programs/today` - Full workout + meal data
- Created `GET /programs/week` - 7-day schedule
- Created `PATCH /programs/sessions/{id}/complete` - Mark workout done
- Created `PATCH /programs/meals/{id}/complete` - Mark meal done
- Migration 045 - Added `completed_at` columns

**Phase 2:**
- Created `GET /calendar/full` - Calendar events with status
- Created `GET /calendar/summary` - Adherence statistics
- Updated completion endpoints - Auto-update calendar status
- Program generation - Auto-creates calendar events

**Total Lines Added:** ~810 lines

### Frontend (Next.js/TypeScript)

**Phase 1:**
- Created `components/program/WorkoutCard.tsx` - Workout display
- Created `components/program/MealCard.tsx` - Meal display
- Created `/plan/today` page - Today's plan
- Created `/plan/week` page - Weekly schedule
- Updated `/plan` summary page - Program overview
- Updated `/dashboard` - Auto-redirect after generation

**Phase 2:**
- Frontend pages already existed:
  - `/plan/calendar` - Calendar view (now fully functional)
  - `/plan/progress` - Progress tracking (now fully functional)
  - `/plan/log` - Activity/meal hub

**Total Lines Added:** ~850 lines

---

## 🚀 NEXT STEPS

After successful testing:

1. **Run Migration 045** (if not done yet)
2. **Test all flows** using this guide
3. **Report any bugs** you find
4. **Optional Future Features:**
   - Adherence logging (attach activities to planned sessions)
   - Day overrides (modify plan for specific days)
   - Notifications (reminders for upcoming sessions)
   - Regeneration (create new program)

---

## 📊 SYSTEM STATUS

**✅ COMPLETE:**
- Phase 1: Program Display System
- Phase 2: Calendar & Progress Tracking
- Backend endpoints deployed to Railway
- Frontend pages built and deployed to Vercel
- Database schema ready (migration 036 from 2025-10-15)
- Calendar events auto-created on program generation
- Completion tracking fully integrated

**⏳ PENDING:**
- Migration 045 needs to be run by user
- Testing required to verify all features work

**🎊 READY FOR PRODUCTION TESTING!**

---

**Questions or Issues?**
Check backend logs in Railway dashboard, or inspect frontend browser console for errors.

**Last Updated:** 2025-10-22
**Version:** Phase 1 & 2 Complete
