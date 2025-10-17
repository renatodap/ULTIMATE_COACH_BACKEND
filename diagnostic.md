# Activities Not Showing - Diagnostic Checklist

## Your Supabase Data (Confirmed)
✅ 2 active activities exist:
- Activity "un": start_time = "2025-10-16 18:00:00+00", deleted_at = null
- Activity "tennis": start_time = "2025-10-16 04:16:00+00", deleted_at = null

## Step 1: Verify Railway Deployed Latest Code

**Check if Railway auto-deployed commit b32f6bb:**

1. Go to: https://railway.app
2. Select ULTIMATE_COACH_BACKEND project
3. Go to "Deployments" tab
4. Look for latest deployment - should show commit: "Add comprehensive debug logging"
5. Check status: "Active" (green)

**If not deployed:**
- Click "Deploy" button manually
- Wait 2-3 minutes for build + deploy

---

## Step 2: Call Debug Endpoint

**Option A - Browser Console (EASIEST):**

1. Open your frontend app (http://localhost:3000 or production URL)
2. Make sure you're logged in
3. Press F12 to open DevTools
4. Go to Console tab
5. Paste this code and hit Enter:

```javascript
// Replace with your actual backend URL
const backendUrl = 'http://localhost:8000' // or 'https://your-app.railway.app'

fetch(`${backendUrl}/api/v1/activities/debug`, {
  credentials: 'include',
  headers: {
    'Content-Type': 'application/json'
  }
})
.then(r => r.json())
.then(data => {
  console.log('=== DEBUG ENDPOINT RESULT ===')
  console.log('User ID:', data.current_user_id)
  console.log('Server Time:', data.server_time_now)
  console.log('Server Date:', data.server_date_today)
  console.log('Total Activities (all):', data.total_activities_all)
  console.log('Total Activities (active):', data.total_activities_active)
  console.log('\nAll Activities:')
  console.table(data.all_activities_sample)
  console.log('\nActive Activities:')
  console.table(data.active_activities_sample)
})
.catch(err => {
  console.error('Debug endpoint error:', err)
})
```

**Option B - Check Railway Logs:**

1. Go to Railway dashboard
2. Click ULTIMATE_COACH_BACKEND
3. Click "View Logs"
4. Reload your activities page in browser
5. Search logs for: "get_user_activities_debug"
6. You should see detailed logging for the query

---

## Step 3: Call Regular Activities Endpoint

In browser console:

```javascript
const backendUrl = 'http://localhost:8000' // or production URL

fetch(`${backendUrl}/api/v1/activities`, {
  credentials: 'include'
})
.then(r => r.json())
.then(data => {
  console.log('=== ACTIVITIES ENDPOINT RESULT ===')
  console.log('Total returned:', data.total)
  console.log('Activities:', data.activities)
  console.table(data.activities)
})
.catch(err => console.error('Error:', err))
```

---

## Step 4: Analyze Results

### Scenario A: Debug endpoint returns 0 activities
**Cause:** User ID mismatch
**Action:** Compare current_user_id from debug endpoint with user_id in Supabase data (38a5596a-9397-4660-8180-132c50541964)

### Scenario B: Debug returns activities but /activities returns 0
**Cause:** Date filtering bug
**Action:** Check Railway logs for "get_user_activities_debug_filters" to see calculated next_day value

### Scenario C: Both endpoints return activities but frontend shows nothing
**Cause:** Frontend rendering issue
**Action:** Check browser console for JavaScript errors

### Scenario D: API calls fail (401, 403, 500)
**Cause:** Auth or server error
**Action:** Check error message and Railway logs

---

## Quick Health Check

Run this in browser console to check everything:

```javascript
const backendUrl = 'http://localhost:8000' // CHANGE THIS

Promise.all([
  fetch(`${backendUrl}/api/v1/health`, { credentials: 'include' }),
  fetch(`${backendUrl}/api/v1/activities/debug`, { credentials: 'include' }),
  fetch(`${backendUrl}/api/v1/activities?limit=10`, { credentials: 'include' })
]).then(async ([health, debug, activities]) => {
  console.log('🏥 Health:', await health.json())
  console.log('🐛 Debug:', await debug.json())
  console.log('🏃 Activities:', await activities.json())
}).catch(err => console.error('❌ Error:', err))
```

---

## Expected Results (What Success Looks Like)

```json
{
  "current_user_id": "38a5596a-9397-4660-8180-132c50541964",
  "server_date_today": "2025-10-16",
  "total_activities_all": 3,
  "total_activities_active": 2,
  "all_activities_sample": [
    { "activity_name": "un", "deleted_at": null },
    { "activity_name": "tennis", "deleted_at": null },
    { "activity_name": "Run", "deleted_at": "2025-10-16T14:00:33.265855Z" }
  ]
}
```

And `/api/v1/activities` should return:
```json
{
  "activities": [
    { "activity_name": "un", ... },
    { "activity_name": "tennis", ... }
  ],
  "total": 2
}
```
