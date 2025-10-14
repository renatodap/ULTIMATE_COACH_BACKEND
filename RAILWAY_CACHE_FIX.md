# Railway Dependency Cache Issue

## Problem
Railway is caching the old corrupted Anthropic SDK (from `anthropic==0.39.0` which doesn't exist).

Even after updating `requirements.txt` to `anthropic==0.34.2`, Railway's Nixpacks build cache may preserve the old installation.

## Symptoms
- Error: `'Anthropic' object has no attribute 'messages'`
- Error: `'AsyncAnthropic' object has no attribute 'messages'`
- Occurs even after requirements.txt was updated

## Solution: Force Clean Rebuild

### Option 1: Environment Variable (Recommended)
Add this environment variable in Railway dashboard:

```
NIXPACKS_NO_CACHE=1
```

Then trigger a new deployment (push a commit or use Railway's "Redeploy" button).

**After successful deployment**, remove this variable to restore cache for faster future builds.

### Option 2: Manual Redeploy
1. Go to Railway dashboard
2. Click on your service
3. Click "Settings" → "Redeploy"
4. The new deployment should use fresh dependencies

### Option 3: Clear Build Cache via CLI
```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Clear cache and redeploy
railway up --reset
```

## Verification

After redeployment, check logs for:

**✅ Success:**
```
[SDK] Anthropic version: 0.34.2
[SDK] ✅ Anthropic SDK validated successfully (v0.34.2)
anthropic_sdk_validated message="All AI features operational"
[ComplexityAnalyzer] ✅ Initialized with valid Anthropic client
[UnifiedCoach] ✅ Initialized
```

**❌ Still failing (cache not cleared):**
```
[SDK] ❌ Sync client missing 'messages' attribute
anthropic_sdk_validation_failed
```

## Root Cause

The original `requirements.txt` had:
```
anthropic==0.39.0  # This version doesn't exist!
```

Pip likely installed a corrupted/broken version, which got cached by Railway's build system.

## Permanent Fix Applied

1. **Updated SDK version**: `anthropic==0.34.2` (proven stable)
2. **Added SDK validation**: Checks at startup before initializing services
3. **Lazy initialization**: Services don't initialize until first request (after validation)
4. **Graceful fallbacks**: If SDK fails, system degrades gracefully instead of crashing

## Prevention

- Always use stable, documented SDK versions
- Verify version exists on PyPI before adding to requirements.txt
- Test in local environment before deploying
- Monitor startup logs for SDK validation messages
