# Frontend Integration Guide

Complete guide to integrate the adaptive program system into `ULTIMATE_COACH_FRONTEND`.

---

## Overview

This integration adds:
- **Program Dashboard** - Daily plan view with workouts and meals
- **Workout Tracking** - Exercise-by-exercise completion
- **Progress Dashboard** - Weight trends and adherence metrics
- **Grocery List** - Auto-generated shopping list
- **Program Onboarding** - First-time setup flow

**Integration time**: ~2 hours
**Lines of code changed in existing frontend**: ~15 lines
**New screens**: 5
**New components**: 10

---

## File Structure

```
ULTIMATE_COACH_FRONTEND/
├── src/
│   ├── types/
│   │   └── program.ts                   ← COPY FROM integration/frontend/src/types/
│   ├── services/
│   │   └── programApi.ts                ← COPY FROM integration/frontend/src/services/
│   ├── hooks/
│   │   └── useProgramData.ts            ← COPY FROM integration/frontend/src/hooks/
│   ├── screens/
│   │   ├── ProgramDashboardScreen.tsx   ← COPY FROM integration/frontend/src/screens/
│   │   ├── WorkoutScreen.tsx
│   │   ├── ProgressScreen.tsx
│   │   ├── GroceryListScreen.tsx
│   │   └── ProgramOnboardingScreen.tsx
│   └── components/
│       ├── MacroTargetsCard.tsx         ← COPY FROM integration/frontend/src/components/
│       ├── WorkoutCard.tsx
│       ├── MealsCard.tsx
│       ├── ProgressCard.tsx
│       ├── QuickActionsBar.tsx
│       ├── ExerciseCard.tsx
│       ├── SetRow.tsx
│       ├── ProgressBar.tsx
│       ├── AdjustmentCard.tsx
│       └── WeightChart.tsx
├── package.json                         ← ADD dependencies
└── App.tsx                              ← MODIFY navigation (5 lines)
```

---

## Installation Steps

### Step 1: Copy Files

```bash
# From ultimate_ai_consultation directory
cd integration/frontend

# Copy types
cp src/types/program.ts /path/to/ULTIMATE_COACH_FRONTEND/src/types/

# Copy services
cp src/services/programApi.ts /path/to/ULTIMATE_COACH_FRONTEND/src/services/

# Copy hooks
cp src/hooks/useProgramData.ts /path/to/ULTIMATE_COACH_FRONTEND/src/hooks/

# Copy screens
cp -r src/screens/* /path/to/ULTIMATE_COACH_FRONTEND/src/screens/

# Copy components
cp -r src/components/* /path/to/ULTIMATE_COACH_FRONTEND/src/components/
```

### Step 2: Install Dependencies

```bash
cd /path/to/ULTIMATE_COACH_FRONTEND

# Install required packages
npm install axios react-native-chart-kit react-native-svg

# or with yarn
yarn add axios react-native-chart-kit react-native-svg
```

**Required packages:**
- `axios` - HTTP client for API calls
- `react-native-chart-kit` - Chart library for weight trends
- `react-native-svg` - Required by chart-kit

### Step 3: Environment Configuration

Add to `.env`:

```bash
REACT_APP_API_BASE_URL=http://localhost:8000
```

For production:
```bash
REACT_APP_API_BASE_URL=https://your-backend-api.com
```

---

## Navigation Integration

### Option 1: React Navigation (Recommended)

If using React Navigation, add routes to your navigator:

**File:** `src/navigation/AppNavigator.tsx`

```tsx
import ProgramDashboardScreen from '../screens/ProgramDashboardScreen';
import WorkoutScreen from '../screens/WorkoutScreen';
import ProgressScreen from '../screens/ProgressScreen';
import GroceryListScreen from '../screens/GroceryListScreen';
import ProgramOnboardingScreen from '../screens/ProgramOnboardingScreen';

// Add to your Stack Navigator
<Stack.Screen
  name="ProgramDashboard"
  component={ProgramDashboardScreen}
  options={{ title: "My Program" }}
/>
<Stack.Screen
  name="Workout"
  component={WorkoutScreen}
  options={{ title: "Workout" }}
/>
<Stack.Screen
  name="Progress"
  component={ProgressScreen}
  options={{ title: "Progress" }}
/>
<Stack.Screen
  name="GroceryList"
  component={GroceryListScreen}
  options={{ title: "Shopping List" }}
/>
<Stack.Screen
  name="ProgramOnboarding"
  component={ProgramOnboardingScreen}
  options={{ title: "Generate Program", headerShown: false }}
/>
```

### Option 2: Expo Router

If using Expo Router, create files:

```
app/
├── program/
│   ├── index.tsx        → ProgramDashboardScreen
│   ├── workout.tsx      → WorkoutScreen
│   ├── progress.tsx     → ProgressScreen
│   ├── grocery.tsx      → GroceryListScreen
│   └── onboarding.tsx   → ProgramOnboardingScreen
```

---

## User Flow Integration

### 1. After Consultation Completes

When `ConsultationAIService` finishes, navigate to onboarding:

```tsx
// In your consultation completion handler
const handleConsultationComplete = (consultationData) => {
  navigation.navigate('ProgramOnboarding', {
    userId: currentUser.id,
    consultationData: consultationData,
  });
};
```

### 2. Home Screen Quick Access

Add program shortcut to home screen:

```tsx
// In HomeScreen.tsx
import { useHasActivePlan } from '../hooks/useProgramData';

const { hasActivePlan, loading } = useHasActivePlan(userId);

{hasActivePlan && (
  <TouchableOpacity onPress={() => navigation.navigate('ProgramDashboard')}>
    <Text>View My Program</Text>
  </TouchableOpacity>
)}
```

### 3. Bottom Tab Navigation

Add program tab to bottom navigation:

```tsx
// In TabNavigator.tsx
<Tab.Screen
  name="Program"
  component={ProgramDashboardScreen}
  options={{
    tabBarIcon: ({ color, size }) => (
      <Icon name="fitness" size={size} color={color} />
    ),
  }}
/>
```

---

## Authentication

The API service expects an auth token in localStorage:

```tsx
// Make sure your auth system stores token
localStorage.setItem('auth_token', token);

// Or modify programApi.ts to use your auth method:
// AsyncStorage, SecureStore, etc.
```

---

## Styling Customization

All components use inline StyleSheet. To match your app's theme:

### Option 1: Theme Provider (Recommended)

Wrap app in theme provider and update colors:

```tsx
// theme.ts
export const theme = {
  colors: {
    primary: '#1976d2',
    success: '#4caf50',
    warning: '#ff9800',
    error: '#f44336',
  },
};

// Then replace hardcoded colors in components:
// '#1976d2' → theme.colors.primary
```

### Option 2: Global Styles

Create `src/styles/program.ts` with shared styles:

```tsx
export const cardStyle = {
  backgroundColor: '#fff',
  borderRadius: 12,
  padding: 16,
  margin: 16,
};
```

---

## Testing

### Manual Testing Flow

1. **Generate Program**:
   - Complete consultation
   - Navigate to onboarding
   - Tap "Generate My Program"
   - Should see dashboard

2. **View Today's Plan**:
   - Open Program Dashboard
   - Should see macro targets
   - Should see today's workout (or rest day)
   - Should see today's meals

3. **Complete Workout**:
   - Tap "View Workout"
   - Mark exercises complete
   - Tap "Workout Complete"

4. **Check Progress**:
   - Navigate to Progress screen
   - Should see weight chart
   - Should see adherence metrics

5. **View Grocery List**:
   - Navigate to Grocery List
   - Check items off as you shop

---

## API Integration

All API calls are handled by `programApi.ts`. No changes needed to existing code.

**Available methods:**
```tsx
import ProgramAPI from '../services/programApi';

// Generate program
await ProgramAPI.generateProgram({ user_id, consultation_data });

// Get today's plan
const todayPlan = await ProgramAPI.getTodayPlan(userId);

// Get progress
const progress = await ProgramAPI.getProgress(userId, 14);

// Trigger reassessment
await ProgramAPI.triggerReassessment({ user_id: userId, force: false });
```

---

## Hooks Usage

React hooks make data fetching easy:

```tsx
import { useTodayPlan, useProgress } from '../hooks/useProgramData';

function MyComponent({ userId }) {
  const { data, loading, error, refetch } = useTodayPlan(userId);

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorMessage message={error} />;

  return <View>{/* Use data here */}</View>;
}
```

---

## Troubleshooting

### Issue: "Cannot find module 'axios'"

**Fix:**
```bash
npm install axios
# or
yarn add axios
```

### Issue: "Network request failed"

**Cause:** Backend not running or wrong URL

**Fix:**
```bash
# Check .env
REACT_APP_API_BASE_URL=http://localhost:8000

# Verify backend is running
curl http://localhost:8000/api/v1/programs/{user_id}/active
```

### Issue: Charts not rendering

**Cause:** Missing `react-native-svg`

**Fix:**
```bash
npm install react-native-svg
npx pod-install  # iOS only
```

### Issue: "No active plan found"

**Cause:** User hasn't generated program yet

**Fix:** Navigate to `ProgramOnboarding` screen first

---

## Screen Descriptions

### ProgramDashboardScreen
- **Purpose**: Main hub for daily plan
- **Shows**: Macro targets, today's workout, today's meals, 7-day progress
- **Actions**: View workout, log meal, log weight, chat with coach

### WorkoutScreen
- **Purpose**: Display workout with exercise-by-exercise tracking
- **Shows**: Exercise list with sets/reps/weight, rest timers
- **Actions**: Mark exercises complete, finish workout

### ProgressScreen
- **Purpose**: View progress over time
- **Shows**: Weight chart, adherence metrics, recent adjustments
- **Actions**: Switch time period (7/14/30 days)

### GroceryListScreen
- **Purpose**: Shopping list for meal plan
- **Shows**: Categorized food items with quantities
- **Actions**: Check off items as purchased

### ProgramOnboardingScreen
- **Purpose**: First-time program generation
- **Shows**: Program features overview
- **Actions**: Trigger program generation

---

## Component Props Reference

### MacroTargetsCard
```tsx
<MacroTargetsCard macros={MacroTargets} />
```

### WorkoutCard
```tsx
<WorkoutCard
  workout={WorkoutSession}
  onPress={() => void}
/>
```

### MealsCard
```tsx
<MealsCard
  meals={Meal[]}
  onPress={() => void}
/>
```

### ProgressCard
```tsx
<ProgressCard
  progress={ProgressResponse}
  onPress={() => void}
/>
```

### QuickActionsBar
```tsx
<QuickActionsBar
  onLogMeal={() => void}
  onLogWeight={() => void}
  onViewGroceryList={() => void}
  onChatWithCoach={() => void}
/>
```

---

## Performance Optimization

### Data Caching

Add caching to reduce API calls:

```tsx
// Create src/services/programCache.ts
const cache = new Map();

export const getCachedData = (key) => {
  const cached = cache.get(key);
  if (cached && Date.now() - cached.timestamp < 300000) { // 5 min
    return cached.data;
  }
  return null;
};

export const setCachedData = (key, data) => {
  cache.set(key, { data, timestamp: Date.now() });
};
```

### Lazy Loading

Use React.lazy for screens:

```tsx
const ProgramDashboard = React.lazy(() => import('./screens/ProgramDashboardScreen'));
```

---

## Next Steps

1. **Customize Styling** - Match your app's theme
2. **Add Animations** - Use `react-native-reanimated` for smooth transitions
3. **Add Haptics** - Vibrate on workout completion
4. **Add Notifications** - Remind users of workouts
5. **Add Social Features** - Share progress with friends

---

## Support

- **Documentation**: See backend `INTEGRATION.md`
- **Examples**: All screens are fully functional examples
- **Issues**: Check types and API responses

---

## Summary

**Files copied**: 18 (1 types, 1 service, 1 hooks, 5 screens, 10 components)
**Files modified**: 2 (navigation, env)
**Dependencies added**: 3
**Total integration time**: ~2 hours

The frontend is now fully integrated and ready to:
- Display personalized programs
- Track workouts and meals
- Show progress over time
- Generate grocery lists
- Handle bi-weekly adjustments
