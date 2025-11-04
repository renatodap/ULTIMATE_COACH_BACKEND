# ULTIMATE_COACH_BACKEND Refactoring Plan

**Created:** 2025-11-04
**Status:** In Progress
**Estimated Completion:** 8-12 weeks

## Executive Summary

This document outlines a comprehensive refactoring of the backend to address:
- **God classes** (4 files >2,500 lines)
- **Testing gap** (85% of services untested)
- **Code duplication** (query patterns, enrichment services)
- **Tight coupling** (singleton dependencies, circular risks)
- **Architectural debt** (no DI pattern, monolithic services)

## Current State Analysis

### Critical Issues

| Issue | Severity | Impact | Files Affected |
|-------|----------|--------|----------------|
| God classes (>2,500 LOC) | CRITICAL | Maintenance, testing, debugging | 4 files |
| No tests for core services | CRITICAL | Production risk, refactoring risk | 34 services |
| Tight coupling | HIGH | Hard to mock, test, modify | All services |
| Duplicate code | MEDIUM | Maintenance burden, bug propagation | 10+ files |
| Excessive logging verbosity | LOW | Log file size, readability | 5 files |

### Health Score: 6/10

| Aspect | Score | Notes |
|--------|-------|-------|
| Architecture | 4/10 | God classes, tight coupling |
| Testing | 3/10 | 85% services untested |
| Logging | 8/10 | Excellent structlog usage |
| Error Handling | 6/10 | Inconsistent patterns |
| Code Organization | 5/10 | Duplication, coupling |
| Documentation | 7/10 | Good docstrings |
| Dependency Management | 4/10 | No DI, circular risks |

---

## Refactoring Phases (9 Total)

### Phase 1: Tool Plugin Architecture ⭐ [IN PROGRESS]

**Goal:** Extract 2,622-line `tool_service.py` into modular plugin system

**Status:** Infrastructure Complete, Tools In Progress

**Completed:**
- ✅ Created `app/services/tools/base_tool.py` - Abstract base class
- ✅ Created `app/services/tools/tool_registry.py` - Registry pattern
- ✅ Created `app/services/tools/__init__.py` - Factory function
- ✅ Extracted `UserProfileTool` - First example tool
- ✅ Extracted `DailyNutritionSummaryTool` - Second example tool
- ✅ Created comprehensive tests:
  - `tests/unit/services/tools/test_base_tool.py` - 17 tests
  - `tests/unit/services/tools/test_tool_registry.py` - 15 tests
  - `tests/unit/services/tools/test_user_profile_tool.py` - 9 tests

**Remaining:**
- ⏳ Extract 18 remaining tools:
  - `RecentMealsTool`
  - `RecentActivitiesTool`
  - `BodyMeasurementsTool`
  - `ProgressTrendTool`
  - `TrainingVolumeTool`
  - `FoodSearchTool`
  - `MealNutritionCalculatorTool`
  - `MealAdjustmentsTool`
  - `ActivityCaloriesTool`
  - `QuickMealLogTool`
  - `SemanticSearchTool`
  - `UpdateMealTool`
  - `DeleteMealTool`
  - `UpdateMealItemTool`
  - `CopyMealTool`
  - `CreateQuickMealTool`
  - `DeleteQuickMealTool`
  - `ListQuickMealsTool`
- ⏳ Update `tool_service.py` to use registry
- ⏳ Update `unified_coach_service.py` to use new tool system
- ⏳ Write tests for all extracted tools

**Effort:** 1 week
**Risk:** Medium
**Impact:** High (enables testing, reduces LOC by 60%)

**Before:**
```python
# tool_service.py - 2,622 lines
class ToolService:
    async def execute_tool(self, tool_name, params, user_id):
        if tool_name == "get_user_profile":
            return await self._get_user_profile(user_id, params)
        elif tool_name == "get_daily_nutrition_summary":
            # ...850 more lines
```

**After:**
```python
# tool_service.py - ~200 lines
class ToolService:
    def __init__(self, supabase_client, cache_service):
        self.registry = create_tool_registry(supabase_client, cache_service)

    async def execute_tool(self, tool_name, params, user_id):
        return await self.registry.execute(tool_name, user_id, params)

# app/services/tools/user_profile_tool.py - ~90 lines
class UserProfileTool(BaseTool):
    def get_definition(self): ...
    async def execute(self, user_id, params): ...
```

---

### Phase 2: Split Unified Coach Service ⭐ [PENDING]

**Goal:** Split 2,658-line `unified_coach_service.py` into 6 focused services

**Target Architecture:**
```
app/services/coach/
├── __init__.py                          # Factory function
├── unified_coach_router.py              # Message routing (~400 lines)
├── chat_mode_handler.py                 # Chat responses (~450 lines)
├── log_mode_handler.py                  # Log extraction (~450 lines)
├── conversation_memory_manager.py       # Memory ops (~350 lines)
├── enrichment_orchestrator.py           # Enrichment (~400 lines)
└── language_detector.py                 # Language ops (~200 lines)
```

**Benefits:**
- Single Responsibility Principle
- Each component independently testable
- Clear boundaries and interfaces
- Easier debugging and maintenance
- ~440 lines per file (vs. 2,658)

**Migration Strategy:**
1. Create service interfaces
2. Extract log_mode_handler first (most independent)
3. Extract language_detector (minimal dependencies)
4. Extract enrichment_orchestrator
5. Extract conversation_memory_manager
6. Extract chat_mode_handler
7. Create unified_coach_router to coordinate
8. Update dependencies and tests

**Effort:** 1-2 weeks
**Risk:** High (core feature)
**Impact:** Critical (+300% maintainability)

---

### Phase 3: Nutrition Service Layers [PENDING]

**Goal:** Refactor 1,527-line `nutrition_service.py` into layered architecture

**Target Architecture:**
```
app/services/nutrition/
├── __init__.py                    # Factory function
├── food_repository.py             # DB queries with fallback (~300 lines)
├── food_validator.py              # Validation logic (~200 lines)
├── food_normalizer.py             # Response formatting (~200 lines)
├── food_search_service.py         # Search orchestration (~300 lines)
└── meal_service.py                # Meal operations (~500 lines)
```

**Key Improvements:**
- Extract 80-line nested try/catch fallback logic into `food_repository.py`
- Standardize query patterns (eliminate duplication)
- Clear validation boundaries
- Easier error handling testing

**Effort:** 3-5 days
**Risk:** Medium
**Impact:** High (cleaner error handling, testability)

---

### Phase 4: Repository Pattern [PENDING]

**Goal:** Extract database access from 1,296-line `supabase_service.py`

**Target Architecture:**
```
app/repositories/
├── __init__.py
├── base_repository.py              # Abstract base (~100 lines)
├── user_repository.py              # User/profile queries (~200 lines)
├── meal_repository.py              # Meal queries (~250 lines)
├── activity_repository.py          # Activity queries (~200 lines)
├── body_metrics_repository.py      # Measurements (~150 lines)
├── program_repository.py           # Programs (~200 lines)
└── template_repository.py          # Templates (~200 lines)
```

**Benefits:**
- Clear data access patterns
- Easy to mock for testing
- Database changes isolated
- Better abstraction layer

**Effort:** 1-2 weeks
**Risk:** High (touches all database access)
**Impact:** High (enables testing, clearer boundaries)

---

### Phase 5: Comprehensive Testing [PENDING]

**Goal:** Achieve 80%+ test coverage (currently ~15%)

**Test Structure:**
```
tests/
├── unit/
│   ├── services/
│   │   ├── test_unified_coach/         # 6 test files
│   │   ├── test_tools/                 # 20 test files
│   │   ├── test_nutrition/             # 5 test files
│   │   ├── test_repositories/          # 7 test files
│   │   ├── test_auth_service.py
│   │   ├── test_activity_service.py
│   │   └── ...                         # 30+ service test files
│   └── repositories/                   # 7 test files
├── integration/
│   ├── test_coach_workflows.py
│   ├── test_database_operations.py
│   ├── test_error_scenarios.py
│   └── ...
└── fixtures/
    ├── mock_supabase.py               # Enhanced mocks
    ├── test_data_builders.py          # Test data factories
    └── ...
```

**Priority Testing:**
1. Tool plugin system (completed ✅)
2. Unified coach services (6 components)
3. Nutrition service layers (5 components)
4. Repositories (7 repositories)
5. Integration workflows

**Effort:** 2-4 weeks
**Risk:** Low (additive)
**Impact:** Critical (production confidence)

---

### Phase 6: Error Handling Standardization [PENDING]

**Goal:** Standardize error handling across all services

**Changes:**

1. **Create Error Handler Utilities**
```python
# app/errors/handler.py
class ToolErrorHandler:
    @staticmethod
    def handle_tool_error(error: Exception) -> Dict:
        logger.error("tool_error", error=str(error), exc_info=True)
        return {"error": error.code, "message": error.message}
```

2. **Implement Retry Logic**
```python
# app/errors/retry.py
async def retry_with_exponential_backoff(
    func, max_retries=3, base_delay=2.0, exceptions=(Exception,)
):
    """Retry function with exponential backoff."""
    for attempt in range(max_retries):
        try:
            return await func()
        except exceptions as e:
            if attempt == max_retries - 1:
                raise
            delay = base_delay * (2 ** attempt)
            await asyncio.sleep(delay)
```

3. **Standardize Tool Error Responses**
- All tools return `{"error": code, "message": msg}` format
- No silent failures
- Consistent HTTP status codes

**Effort:** 2-3 days
**Risk:** Low
**Impact:** Medium (better error tracking)

---

### Phase 7: Extract Duplicate Code [PENDING]

**Goal:** Eliminate code duplication

**Changes:**

1. **Query Pattern Extraction**
```python
# app/database/query_patterns.py
class QueryPatterns:
    @staticmethod
    def meals_with_items_and_foods():
        return "*, meal_items(*, foods(name, brand_name))"

    @staticmethod
    def activities_with_metrics():
        return "*, metrics"

# Usage everywhere
result = supabase.table("meals").select(
    QueryPatterns.meals_with_items_and_foods()
).execute()
```

2. **Enrichment Service Consolidation**

Merge 3 services into strategy pattern:
- `activity_preview_enrichment_service.py` (532 lines)
- `measurement_preview_enrichment_service.py` (456 lines)
- `log_preview_enrichment_service.py` (458 lines)

**Target:**
```python
# app/services/enrichment/base_enricher.py
class PreviewEnricher(ABC):
    async def enrich(self, data: Dict) -> Tuple[Dict, List[str]]:
        pass

# app/services/enrichment/activity_enricher.py
class ActivityEnricher(PreviewEnricher):
    async def enrich(self, data: Dict):
        # Activity-specific logic

# app/services/enrichment/enrichment_service.py
class EnrichmentService:
    def __init__(self):
        self.enrichers = {
            "activity": ActivityEnricher(),
            "measurement": MeasurementEnricher(),
            "log": LogEnricher(),
        }

    async def enrich(self, data_type: str, data: Dict):
        enricher = self.enrichers[data_type]
        return await enricher.enrich(data)
```

**Effort:** 3-4 days
**Risk:** Low
**Impact:** Medium (-1,000 LOC, clearer patterns)

---

### Phase 8: Logging Improvements [PENDING]

**Goal:** Improve log quality and reduce verbosity

**Changes:**

1. **Remove Emoji Markers** (5-10% size reduction)
```python
# BEFORE
logger.info(f"[UnifiedCoach] 🧠 CHAT MODE")
logger.info(f"[UnifiedCoach] 📝 Extracting logs")
logger.info(f"[UnifiedCoach] 💾 Log {idx+1}: Saved")

# AFTER
logger.info("chat_mode_started", mode="chat")
logger.info("extracting_logs", source="user_message")
logger.info("log_saved", log_index=idx+1, log_id=log_id)
```

2. **Add Request Correlation IDs**
```python
# app/middleware/correlation_id.py
import uuid
from starlette.middleware.base import BaseHTTPMiddleware

class CorrelationIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        # Inject into structlog context
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        return response
```

3. **Standardize Log Levels**
- DEBUG: Cache hits, detailed internal state
- INFO: Business events (user_login, meal_created)
- WARNING: Recoverable errors (cache miss fallback)
- ERROR: Failures requiring attention

**Effort:** 1-2 days
**Risk:** Low
**Impact:** Low (better debugging, cleaner logs)

---

### Phase 9: Documentation & Architecture [PENDING]

**Goal:** Document new architecture and design decisions

**Deliverables:**

1. **Architecture Diagrams**
   - System overview
   - Service dependency graph
   - Repository pattern diagram
   - Tool plugin architecture
   - Request flow diagrams

2. **Design Pattern Documentation**
   - Repository pattern usage
   - Plugin architecture (tools)
   - Service layer pattern
   - Dependency injection
   - Error handling patterns

3. **Update CLAUDE.md**
   - New file structure
   - Tool plugin system guide
   - Coach service architecture
   - Nutrition service layers
   - Repository pattern usage
   - Testing guidelines

4. **Architecture Decision Records (ADRs)**
   - ADR-001: Tool Plugin Architecture
   - ADR-002: Coach Service Split
   - ADR-003: Repository Pattern
   - ADR-004: Error Handling Strategy
   - ADR-005: Testing Strategy

**Effort:** 2-3 days
**Risk:** Low
**Impact:** Medium (knowledge transfer, onboarding)

---

## Timeline & Milestones

### Sprint 1: Foundation (Weeks 1-4)
- [x] Phase 1: Tool Plugin Infrastructure (Week 1)
- [ ] Phase 1: Extract all 20 tools (Week 1-2)
- [ ] Phase 5: Core test infrastructure (Week 3)
- [ ] Phase 6: Error handling utilities (Week 4)

**Deliverable:** Working tool plugin system with tests

### Sprint 2: Core Services (Weeks 5-8)
- [ ] Phase 2: Split Coach Service (Weeks 5-6)
- [ ] Phase 3: Nutrition Layers (Week 7)
- [ ] Phase 5: Service tests (Week 8)

**Deliverable:** Modular coach and nutrition services with tests

### Sprint 3: Infrastructure (Weeks 9-12)
- [ ] Phase 4: Repository Pattern (Weeks 9-10)
- [ ] Phase 7: Duplicate Code (Week 11)
- [ ] Phase 8: Logging (Week 11)
- [ ] Phase 9: Documentation (Week 12)
- [ ] Phase 5: Final tests (Week 12)

**Deliverable:** Complete refactored backend with documentation

---

## Success Metrics

### Before Refactoring
- **Largest File:** 2,658 lines
- **Test Coverage:** ~15%
- **Untested Services:** 34 (85%)
- **Code Duplication:** High (query patterns repeated 5+ times)
- **Average Service Size:** 450 lines
- **God Classes:** 4

### After Refactoring (Target)
- **Largest File:** <600 lines
- **Test Coverage:** >80%
- **Untested Services:** 0 (100% covered)
- **Code Duplication:** Low (centralized patterns)
- **Average Service Size:** <300 lines
- **God Classes:** 0

### Quality Improvements
- **Testability:** +300% (all services testable)
- **Maintainability:** +250% (smaller, focused files)
- **Debuggability:** +200% (clearer boundaries, better logging)
- **Code Reuse:** +150% (centralized patterns)
- **Onboarding Time:** -50% (better structure, documentation)

---

## Risk Management

### High-Risk Changes
| Change | Risk | Mitigation |
|--------|------|------------|
| Split coach service | Production bugs | Comprehensive tests, gradual rollout |
| Repository pattern | Data access breaks | Thorough integration tests |
| Tool extraction | Tool execution fails | Keep old code path, feature flag |

### Rollback Strategy
- Keep original files as `.backup` until tests pass
- Feature flags for new vs. old code paths
- Gradual migration per service
- Comprehensive integration tests before deployment

---

## Next Steps

1. **Complete Phase 1:** Extract remaining 18 tools
2. **Begin Phase 2:** Design coach service split
3. **Continuous Testing:** Write tests as services are extracted
4. **Document Decisions:** Create ADRs for major changes

---

## Notes

- All changes maintain backward compatibility at API level
- Internal refactoring only - external APIs unchanged
- Tests written concurrently with refactoring
- Each phase is independently deployable
- Progressive enhancement approach (no big bang)

---

**Last Updated:** 2025-11-04
**Next Review:** After Sprint 1 completion
