# Phase 3: Frontend Integration - Implementation Plan

**Status**: In Progress
**Started**: 2025-10-13 04:05 UTC
**Goal**: Complete frontend integration for template suggestions and activity-template workflows

---

## 🎯 Objectives

1. **Template Suggestions Component** - Reusable component to show auto-matched templates
2. **Create Template from Activity** - Button in ActivityCard to create template from existing activity
3. **Activity Log Integration** - Template selection, auto-fill, and suggestion flow
4. **Matching API Client** - Frontend functions for matching endpoints

---

## 📋 Implementation Checklist

### 1. Frontend Matching API Functions ✅
**File**: `lib/api/templates.ts` (add to existing)

**New Functions**:
```typescript
// Get template match suggestions for activity data
getTemplateMatches(activityData: {
  activity_type: string
  distance_km?: number
  duration_minutes?: number
  start_time?: string
}): Promise<MatchSuggestions>

// Apply template to activity
applyTemplateToActivity(
  templateId: string,
  activityId: string,
  matchScore?: number,
  matchMethod?: 'manual' | 'auto'
): Promise<Activity>

// Record match decision
recordMatchDecision(decision: {
  activity_id: string
  template_id: string
  match_score: number
  match_method: 'manual' | 'auto'
  user_decision: 'accepted' | 'rejected' | 'ignored'
}): Promise<SuccessResponse>
```

**New Types**:
```typescript
interface MatchResult {
  template_id: string
  template_name: string
  match_score: number
  breakdown: MatchScoreBreakdown
  template: ActivityTemplate
}

interface MatchScoreBreakdown {
  type_score: number
  distance_score: number
  time_score: number
  day_score: number
  duration_score: number
  total: number
}

interface MatchSuggestions {
  excellent: MatchResult[]
  good: MatchResult[]
  fair: MatchResult[]
}
```

### 2. TemplateSuggestions Component ✅
**File**: `app/components/templates/TemplateSuggestions.tsx` (~400 lines)

**Props**:
```typescript
interface TemplateSuggestionsProps {
  activityData: {
    activity_type: string
    distance_km?: number
    duration_minutes?: number
    start_time?: string
  }
  onApplyTemplate: (templateId: string, template: ActivityTemplate) => void
  onDismiss?: (templateId: string) => void
  autoFetch?: boolean  // Auto-fetch on mount
}
```

**Features**:
- Fetches matches on mount (if autoFetch=true) or when activityData changes
- Groups by quality (Excellent, Good, Fair)
- Shows top 3 by default, expandable
- Match score visualization (progress bar 0-100)
- Score breakdown on hover/tap
- Apply button → calls onApplyTemplate callback
- Dismiss button → records 'rejected' decision + calls onDismiss
- Empty state: "No matching templates found"
- Loading state
- Error handling

**UI Design**:
```
┌─────────────────────────────────────┐
│ 💡 Suggested Templates              │
│                                     │
│ Excellent Matches (2)               │
│ ┌─────────────────────────────────┐ │
│ │ 🏃 Morning 5K Route      [95%] │ │
│ │ Expected: 5.2 km • 45 min      │ │
│ │ [Apply] [View] [Dismiss]       │ │
│ └─────────────────────────────────┘ │
│                                     │
│ Good Matches (1) ▼                  │
│ (collapsed)                         │
│                                     │
│ [Show 1 more suggestion]            │
└─────────────────────────────────────┘
```

### 3. CreateTemplateModal Component ✅
**File**: `app/components/templates/CreateTemplateModal.tsx` (~300 lines)

**Props**:
```typescript
interface CreateTemplateModalProps {
  isOpen: boolean
  onClose: () => void
  activityId: string
  activityName: string
  activityType: string
  onSuccess?: (template: ActivityTemplate) => void
}
```

**Features**:
- Modal overlay with backdrop
- Form with template_name input (required)
- Checkboxes for auto_match_enabled, require_gps_match
- Preview of what will be copied from activity
- Submit → calls createTemplateFromActivity API
- Success → shows toast + calls onSuccess callback
- Error handling with toast
- ESC key to close
- Click outside to close

**UI Design**:
```
┌─────────────────────────────────────┐
│ Create Template from Activity       │
│                                     │
│ Template Name *                     │
│ [Morning Run Route____________]    │
│                                     │
│ ☑ Enable auto-matching              │
│ ☐ Require GPS route match           │
│                                     │
│ This template will include:         │
│ • Activity type: Running            │
│ • Distance: 5.2 km                  │
│ • Duration: 45 min                  │
│ • All metrics and notes             │
│                                     │
│ [Cancel] [Create Template]          │
└─────────────────────────────────────┘
```

### 4. Update ActivityCard Component ✅
**File**: `app/components/activities/ActivityCard.tsx` (modify existing)

**Changes**:
- Add "Create Template" button to actions row
- Button opens CreateTemplateModal
- Pass activity data to modal
- On success: Show toast "Template created!" with link
- If activity already has template_id, show badge "Using template: [name]"

**New Code**:
```typescript
const [showCreateModal, setShowCreateModal] = useState(false)

// In actions row
<button
  onClick={() => setShowCreateModal(true)}
  className="text-sm font-medium text-iron-white hover:text-iron-orange"
>
  Create Template
</button>

<CreateTemplateModal
  isOpen={showCreateModal}
  onClose={() => setShowCreateModal(false)}
  activityId={activity.id}
  activityName={activity.activity_name}
  activityType={activity.category}
  onSuccess={(template) => {
    toast.success(`Template "${template.template_name}" created!`)
    setShowCreateModal(false)
  }}
/>
```

### 5. Enhance Activity Log Page ✅
**File**: `app/activities/log/page.tsx` (read and enhance)

**Changes Needed**:
1. **Add Template Selection Dropdown** (top of form)
   ```typescript
   <select onChange={handleTemplateSelect}>
     <option value="">No template</option>
     {templates.map(t => (
       <option key={t.id} value={t.id}>
         {t.icon} {t.template_name}
       </option>
     ))}
   </select>
   ```

2. **Load Templates on Mount**
   ```typescript
   useEffect(() => {
     loadUserTemplates()
   }, [])
   ```

3. **Handle Template Selection**
   ```typescript
   const handleTemplateSelect = (templateId: string) => {
     const template = templates.find(t => t.id === templateId)
     if (template) {
       // Pre-fill form
       setFormData({
         ...formData,
         distance_km: template.expected_distance_m ? template.expected_distance_m / 1000 : '',
         duration_minutes: template.expected_duration_minutes || '',
         metrics: template.default_metrics || {},
         notes: template.default_notes || ''
       })
       setSelectedTemplate(template)
     }
   }
   ```

4. **Show Template Suggestions After Activity Type Selection**
   ```typescript
   {activityType && !selectedTemplate && (
     <TemplateSuggestions
       activityData={{
         activity_type: activityType,
         distance_km: formData.distance_km,
         duration_minutes: formData.duration_minutes,
         start_time: formData.start_time
       }}
       onApplyTemplate={handleApplyTemplate}
       autoFetch={true}
     />
   )}
   ```

5. **Handle URL Parameter** (pre-select template)
   ```typescript
   const searchParams = useSearchParams()
   const templateParam = searchParams.get('template')

   useEffect(() => {
     if (templateParam) {
       handleTemplateSelect(templateParam)
     }
   }, [templateParam, templates])
   ```

6. **Show Applied Template Badge**
   ```typescript
   {selectedTemplate && (
     <div className="bg-iron-orange/20 p-3 rounded-lg">
       <p className="text-sm text-iron-orange">
         Using template: {selectedTemplate.icon} {selectedTemplate.template_name}
       </p>
       <button onClick={() => setSelectedTemplate(null)}>
         Clear template
       </button>
     </div>
   )}
   ```

---

## 🎨 UI/UX Principles

### Component Reusability ✅
- TemplateSuggestions: Reusable in any context (activity log, post-log, etc.)
- CreateTemplateModal: Reusable in any component
- Both accept callbacks for flexibility

### Loading States ✅
- Skeleton loaders for suggestions
- Disabled buttons during API calls
- "Creating..." text on submit buttons

### Error Handling ✅
- Toast notifications for errors
- Inline error messages in forms
- Graceful degradation (if no matches, show empty state)

### Mobile-First ✅
- Touch-friendly buttons (min 44x44 px)
- Responsive grid layouts
- Bottom sheet modals on mobile
- Swipe gestures (future enhancement)

### Accessibility ✅
- ARIA labels on all interactive elements
- Keyboard navigation support
- Focus management in modals
- Screen reader announcements for dynamic content

---

## 🔄 User Flows

### Flow 1: Create Template from Activity
```
User logs activity
  ↓
Clicks "Create Template" button
  ↓
Modal opens with activity data
  ↓
User enters template name
  ↓
Clicks "Create Template"
  ↓
API call to POST /templates/from-activity/{id}
  ↓
Success toast: "Template created!"
  ↓
Link to view template
```

### Flow 2: Use Template to Log Activity
```
User clicks "Use Template" from templates list
  ↓
Navigates to /activities/log?template={id}
  ↓
Template pre-selected in dropdown
  ↓
Form pre-filled with template defaults
  ↓
User adjusts values (optional)
  ↓
Submits activity
  ↓
Activity created with template_id
```

### Flow 3: Auto-Suggestions During Logging
```
User navigates to /activities/log
  ↓
Selects activity type
  ↓
TemplateSuggestions component appears
  ↓
Shows matched templates
  ↓
User clicks "Apply" on suggestion
  ↓
Form pre-fills with template
  ↓
Match recorded as 'accepted'
  ↓
User submits activity
```

### Flow 4: Dismiss Suggestion
```
User sees suggestion
  ↓
Clicks "Dismiss"
  ↓
API call to POST /templates/match/decision (decision='rejected')
  ↓
Suggestion removed from UI
  ↓
User continues logging manually
```

---

## 📝 Architecture Decisions

### 1. Callback Pattern
**Decision**: Use callbacks (onApplyTemplate, onDismiss, onSuccess)
**Reason**: Maximum flexibility, component doesn't need to know parent state
**Example**:
```typescript
<TemplateSuggestions
  activityData={data}
  onApplyTemplate={(templateId, template) => {
    // Parent decides what to do
    preFillForm(template)
    setSelectedTemplate(template)
  }}
/>
```

### 2. Controlled Components
**Decision**: Form state managed by parent (activity log page)
**Reason**: Single source of truth, easier to debug
**Example**:
```typescript
// Parent manages all form state
const [formData, setFormData] = useState({...})

// Child components receive values and onChange callbacks
<input
  value={formData.distance_km}
  onChange={e => setFormData({...formData, distance_km: e.target.value})}
/>
```

### 3. Modal Portal
**Decision**: Use React Portal for modals
**Reason**: Avoid z-index issues, proper accessibility
**Example**:
```typescript
import { createPortal } from 'react-dom'

return createPortal(
  <div className="modal-overlay">
    {/* Modal content */}
  </div>,
  document.body
)
```

### 4. Toast Notifications
**Decision**: Use toast library (react-hot-toast or similar)
**Reason**: Consistent UX, accessible, mobile-friendly
**Example**:
```typescript
import toast from 'react-hot-toast'

toast.success('Template created!')
toast.error('Failed to create template')
```

### 5. Optimistic UI
**Decision**: Don't use optimistic updates for this phase
**Reason**: Keep it simple, show loading states instead
**Future**: Can add optimistic updates for better perceived performance

---

## 🧪 Testing Strategy

### Manual Testing Checklist
- [ ] Create template from activity works
- [ ] Template suggestions appear after selecting activity type
- [ ] Apply template pre-fills form correctly
- [ ] Dismiss suggestion removes it from UI
- [ ] URL parameter ?template={id} pre-selects template
- [ ] Clear template button works
- [ ] Modal closes on ESC key
- [ ] Modal closes on backdrop click
- [ ] Form validation works
- [ ] Error handling shows proper messages
- [ ] Loading states display correctly
- [ ] Mobile responsive layouts work
- [ ] Keyboard navigation works

### Edge Cases to Handle
- [ ] No templates exist (show empty state)
- [ ] No matches found (show "No matches" message)
- [ ] API errors (show error toast)
- [ ] Activity type changes after template selected (clear template)
- [ ] Template deleted while form open (handle gracefully)
- [ ] Slow network (show loading states)

---

## 📊 Success Metrics

| Metric | Target | How to Measure |
|--------|--------|----------------|
| Component reusability | 100% | TemplateSuggestions used in multiple places |
| Zero typos | 100% | Code review + linting |
| No console errors | 0 | Browser console check |
| TypeScript strict | 100% | No `any` types (except where necessary) |
| Functional on first try | 100% | Manual testing |

---

**Status**: 🚧 Ready to implement
**Next Step**: Add matching API functions to frontend
**Estimated Time**: 2-3 hours
**Blockers**: None

---

**Last Updated**: 2025-10-13 04:05 UTC
**Created By**: Claude (Sonnet 4.5)
