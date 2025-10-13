# Phase 2: Template Matching System - Implementation Plan

**Status**: In Progress
**Started**: 2025-10-13 03:35 UTC
**Goal**: Build intelligent template matching algorithm and supporting UI

---

## 🎯 Objectives

1. **Auto-suggest templates** for manually logged activities
2. **Track match history** to improve algorithm over time
3. **Provide rich statistics** for template usage
4. **Enable template editing** with full UI
5. **Integrate templates** into activity logging workflow

---

## 🏗️ Architecture Overview

### Matching Algorithm (Scoring System)

**Total Score: 0-100 points**

| Factor | Points | Description |
|--------|--------|-------------|
| Activity Type | 40 | Exact match required (all or nothing) |
| Distance | 25 | Based on tolerance (±%) |
| Time of Day | 20 | Within time window (±hours) |
| Day of Week | 10 | Matches preferred days |
| Duration | 5 | Based on tolerance (±%) |

**Match Thresholds:**
- 90-100: Excellent match (auto-apply with notification)
- 70-89: Good match (suggest to user)
- 50-69: Fair match (show in "other suggestions")
- 0-49: Poor match (don't show)

**GPS Route Matching (Future Enhancement):**
- If template requires GPS and has route hash: +15 bonus points
- If GPS matches but not required: +5 bonus points

### Match Decision Flow

```
User logs activity
    ↓
Extract features (type, distance, duration, time, day)
    ↓
Query active templates for same activity_type
    ↓
Calculate score for each template
    ↓
Filter by min_match_score threshold
    ↓
Sort by score DESC
    ↓
Present to user (UI shows top 3)
    ↓
User accepts/rejects/ignores
    ↓
Record decision in activity_template_matches table
    ↓
Apply template if accepted (copy default_metrics, notes, etc.)
```

---

## 📋 Implementation Checklist

### Phase 2A: Backend Matching Service ✅

**File**: `app/services/template_matching_service.py` (~500 lines)

**Core Functions:**
- [ ] `calculate_match_score()` - Score a single template vs activity
  - [ ] Type matching (40 pts)
  - [ ] Distance matching (25 pts, with tolerance)
  - [ ] Time matching (20 pts, within window)
  - [ ] Day matching (10 pts, preferred days)
  - [ ] Duration matching (5 pts, with tolerance)
- [ ] `find_matching_templates()` - Find all matches for activity
  - [ ] Query templates by activity_type
  - [ ] Filter by is_active=true
  - [ ] Calculate score for each
  - [ ] Filter by min_match_score
  - [ ] Sort by score DESC
  - [ ] Return top N matches
- [ ] `apply_template_to_activity()` - Apply template to activity
  - [ ] Update activity with template_id
  - [ ] Copy default_metrics (if activity metrics empty)
  - [ ] Copy default_notes (if activity notes empty)
  - [ ] Update template use_count and last_used_at
  - [ ] Record match in activity_template_matches table
- [ ] `record_match_decision()` - Record user decision
  - [ ] Insert into activity_template_matches table
  - [ ] Track: activity_id, template_id, score, method, user_decision
  - [ ] Use for future algorithm improvements
- [ ] `get_match_suggestions()` - Get suggestions for activity
  - [ ] Calculate matches
  - [ ] Group by quality (excellent, good, fair)
  - [ ] Return with metadata for UI

**Helper Functions:**
- [ ] `_calculate_type_score()` - 40 pts if exact match
- [ ] `_calculate_distance_score()` - 25 pts max, scaled by tolerance
- [ ] `_calculate_time_score()` - 20 pts max, scaled by time window
- [ ] `_calculate_day_score()` - 10 pts if in preferred days
- [ ] `_calculate_duration_score()` - 5 pts max, scaled by tolerance
- [ ] `_extract_activity_features()` - Extract matchable features from activity

**Data Structures:**
```python
class MatchResult:
    template_id: UUID
    template_name: str
    match_score: int  # 0-100
    breakdown: MatchScoreBreakdown
    template: ActivityTemplate

class MatchScoreBreakdown:
    type_score: int  # 0 or 40
    distance_score: float  # 0-25
    time_score: float  # 0-20
    day_score: float  # 0-10
    duration_score: float  # 0-5
    total: int  # Sum rounded

class MatchSuggestion:
    excellent: List[MatchResult]  # 90-100
    good: List[MatchResult]  # 70-89
    fair: List[MatchResult]  # 50-69
```

### Phase 2B: Backend API Endpoints ✅

**File**: `app/api/v1/templates.py` (add to existing)

**New Endpoints:**
- [ ] `POST /api/v1/templates/match` - Get match suggestions
  - Body: Activity data (type, distance, duration, start_time)
  - Returns: MatchSuggestion with grouped results
- [ ] `POST /api/v1/templates/{template_id}/apply/{activity_id}` - Apply template
  - Updates activity with template_id and defaults
  - Records match decision
  - Returns: Updated activity
- [ ] `POST /api/v1/templates/match/decision` - Record match decision
  - Body: activity_id, template_id, decision (accepted/rejected/ignored)
  - Records in activity_template_matches
  - Returns: Success response

### Phase 2C: Frontend Template Stats Page ✅

**File**: `app/activities/templates/[id]/stats/page.tsx` (~400 lines)

**Sections:**
1. **Header**
   - Template name with icon
   - Back button
   - Edit button

2. **Overview Cards** (4 cards in grid)
   - Total Uses
   - Average Duration (with trend)
   - Average Distance (with trend)
   - Consistency Score (with gauge)

3. **Performance Trends** (Chart)
   - Line chart: Duration over time
   - Line chart: Distance over time (if applicable)
   - Pace trend visualization
   - Best performance highlight

4. **Recent Activities** (List)
   - Last 10 activities using this template
   - Mini activity cards with key stats
   - Link to full activity details

5. **Insights** (Smart analytics)
   - "You're getting faster! Pace improved by X% over last month"
   - "Most consistent on [days]"
   - "Best time of day: [time range]"

### Phase 2D: Frontend Template Edit Page ✅

**File**: `app/activities/templates/[id]/edit/page.tsx` (~500 lines)

**Features:**
- Reuse form components from creation page
- Pre-populate with existing template data
- Same sections: Basic Info, Metrics, Schedule, Auto-Matching, Goals
- Update API call instead of create
- Success message and redirect

**Key Differences from Create:**
- Title: "Edit Template"
- Button: "Save Changes" instead of "Create Template"
- Show last_used_at and use_count in header
- Confirmation before leaving with unsaved changes

### Phase 2E: Frontend Template Selection UI ✅

**Component**: `app/components/activities/TemplateSuggestions.tsx` (~300 lines)

**UI Design (Mobile-First):**

```
┌─────────────────────────────────────┐
│ 💡 Suggested Templates              │
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ 🏃 Morning 5K Route             │ │
│ │ Excellent match (95%)            │ │
│ │ Expected: 5.2 km • 45 min       │ │
│ │                                  │ │
│ │ [Apply Template] [Dismiss]      │ │
│ └─────────────────────────────────┘ │
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ 🚴 Evening Ride                 │ │
│ │ Good match (82%)                 │ │
│ │ Expected: 15 km • 60 min        │ │
│ │                                  │ │
│ │ [Apply Template] [Dismiss]      │ │
│ └─────────────────────────────────┘ │
│                                     │
│ Show 2 more suggestions ▼           │
└─────────────────────────────────────┘
```

**Features:**
- Show top 3 matches by default
- Expandable to show more
- Color-coded by match quality (excellent=green, good=orange, fair=gray)
- "Apply Template" button:
  - Pre-fills form with default_metrics
  - Pre-fills notes with default_notes
  - Shows success toast: "Template applied!"
- "Dismiss" button:
  - Records decision as "rejected"
  - Removes from suggestions
- Match score breakdown on hover/tap

### Phase 2F: Activity Log Integration ✅

**File**: `app/activities/log/page.tsx` (enhance existing)

**Changes:**
1. **Add Template Selection Dropdown** (above form)
   ```tsx
   <select onChange={handleTemplateSelect}>
     <option value="">No template</option>
     {templates.map(t => (
       <option key={t.id} value={t.id}>{t.template_name}</option>
     ))}
   </select>
   ```

2. **Template Auto-Fill on Selection**
   - Load template data
   - Pre-fill distance, duration, metrics
   - Pre-fill notes
   - Show "Applied template: [name]" badge
   - Allow user to override any field

3. **Smart Suggestions After Type Selection**
   - When user selects activity type
   - Fetch matching templates for that type
   - Show TemplateSuggestions component
   - Allow quick apply

4. **URL Parameter Support**
   - `/activities/log?template={id}` - Pre-select template
   - Useful when clicking "Use Template" from template list

### Phase 2G: Create Template from Activity ✅

**Component**: `app/components/activities/CreateTemplateButton.tsx` (~150 lines)

**Location**: Inside ActivityCard component (add to actions)

**Flow:**
1. User clicks "Create Template" button on activity
2. Modal opens with form:
   ```
   ┌─────────────────────────────────────┐
   │ Create Template from Activity       │
   │                                     │
   │ Template Name:                      │
   │ [Morning Run Route_____________]    │
   │                                     │
   │ ☑ Enable auto-matching              │
   │ ☐ Require GPS route match           │
   │                                     │
   │ This will create a template using:  │
   │ • Activity type: Running            │
   │ • Distance: 5.2 km                  │
   │ • Duration: 45 min                  │
   │ • Metrics and exercises             │
   │                                     │
   │ [Cancel]  [Create Template]         │
   └─────────────────────────────────────┘
   ```
3. Call `POST /api/v1/templates/from-activity/{activity_id}`
4. Show success toast with link to template
5. Link back to activity shows "Template created from this activity"

---

## 📊 Database Usage

### Tables Used

**activity_template_matches** (Match History)
```sql
SELECT
    template_id,
    COUNT(*) as total_suggestions,
    SUM(CASE WHEN user_decision = 'accepted' THEN 1 ELSE 0 END) as accepted,
    AVG(match_score) as avg_score
FROM activity_template_matches
WHERE match_method = 'auto'
GROUP BY template_id;
```

**activity_templates** (Updated Fields)
- `use_count` - Incremented when template applied
- `last_used_at` - Updated when template applied

**activities** (Updated Fields)
- `template_id` - Set when template applied
- `template_match_score` - Score of matched template
- `template_applied_at` - Timestamp when template was applied

---

## 🎨 UI/UX Design Principles

### Match Quality Colors
- **Excellent (90-100)**: Green accent `#10B981` (emerald-500)
- **Good (70-89)**: Orange accent `#F97316` (iron-orange)
- **Fair (50-69)**: Gray accent `#6B7280` (iron-gray)

### Animation & Transitions
- Template suggestion cards slide in from top (300ms ease-out)
- Apply button shows success checkmark animation
- Match score fills like a progress bar

### Mobile-First Considerations
- Template suggestions as bottom sheet on mobile
- Swipeable template cards (swipe left = dismiss, swipe right = apply)
- Large touch targets (min 44x44 px)
- Sticky "Apply Template" button on scroll

### Accessibility
- ARIA labels for all interactive elements
- Keyboard navigation support
- Screen reader friendly match score announcements
- High contrast mode support

---

## 🧪 Testing Strategy

### Unit Tests (Backend)
```python
# test_template_matching_service.py

def test_calculate_type_score_exact_match():
    # Should return 40 if types match

def test_calculate_distance_score_within_tolerance():
    # Should return max points if within ±10%

def test_calculate_time_score_outside_window():
    # Should return 0 if outside ±2 hour window

def test_find_matching_templates_filters_by_threshold():
    # Should only return matches above min_match_score
```

### Integration Tests (Frontend)
```typescript
// Template Stats Page
- Loads template data correctly
- Displays charts with real data
- Shows "No data" state when use_count = 0

// Template Edit Page
- Pre-populates form with template data
- Updates template successfully
- Shows validation errors

// Template Suggestions
- Fetches matches after activity type selection
- Applies template and pre-fills form
- Records decision when dismissed
```

### E2E User Flows
1. **Create → Use → Stats**
   - Create template
   - Use template to log activity
   - View stats showing 1 use

2. **Auto-Suggestion → Apply**
   - Start logging activity
   - See suggestion appear
   - Apply suggestion
   - Verify form pre-filled

3. **Create from Activity → Use**
   - Log activity
   - Create template from it
   - Use template for next activity

---

## 🚀 Implementation Order

### Day 1 (Backend Core)
1. ✅ Create matching service with scoring algorithm
2. ✅ Add matching endpoints to API
3. ✅ Test with curl/Postman

### Day 2 (Frontend Core)
4. ✅ Build template stats page
5. ✅ Build template edit page
6. ✅ Test navigation and data loading

### Day 3 (Integration)
7. ✅ Build template suggestions component
8. ✅ Integrate with activity log page
9. ✅ Add "Create Template from Activity" button

### Day 4 (Polish)
10. ✅ End-to-end testing
11. ✅ Bug fixes and edge cases
12. ✅ Documentation updates

---

## 📈 Success Metrics

| Metric | Target | How to Measure |
|--------|--------|----------------|
| Match accuracy | >80% | % of suggestions accepted by users |
| Suggestion relevance | >3 matches | Avg matches per activity type |
| User adoption | >50% | % of activities using templates |
| Time saved | >30 sec | Avg time to log with template vs without |

---

## 🔒 Edge Cases to Handle

1. **No templates exist** - Show empty state with CTA
2. **No matches found** - Show "No matching templates" message
3. **Template deleted after match** - Handle gracefully (show "Template no longer available")
4. **Activity without required fields** - Skip matching for incomplete activities
5. **Multiple excellent matches** - Show all, let user choose
6. **Template used once** - Stats page should handle limited data
7. **Concurrent template edits** - Optimistic locking or last-write-wins

---

## 📝 Documentation Updates

### Backend CLAUDE.md
- Add template matching service documentation
- Update file index with new service
- Add matching algorithm explanation

### Frontend CLAUDE.md
- Add new pages to file index
- Document template suggestion component
- Add screenshots of key UI elements

### API Documentation
- OpenAPI/Swagger auto-updated with new endpoints
- Add examples for matching requests/responses

---

**Status**: 🚧 Ready to implement
**Next Step**: Create `template_matching_service.py` with scoring algorithm
**Estimated Time**: 4-6 hours total
**Blockers**: None

---

**Last Updated**: 2025-10-13 03:35 UTC
**Created By**: Claude (Sonnet 4.5)
