# Testing Structure - Modern Full-Stack 2025 Standards

> **Philosophy**: Quality over coverage, behavioral validation, intelligent automation
> **Test Pyramid**: 60% Unit | 30% Integration | 10% E2E
> **Framework**: pytest + httpx + factory-boy + pytest-asyncio

---

## 📁 Directory Structure

```
tests/
├── unit/                          # 60% - Fast, isolated tests
│   ├── services/                  # Business logic tests
│   │   ├── test_auth_service.py
│   │   ├── test_activity_service.py
│   │   ├── test_nutrition_service.py
│   │   └── test_consultation_ai_service.py
│   ├── utils/                     # Utility function tests
│   │   ├── test_calorie_calculator.py
│   │   ├── test_macro_calculator.py
│   │   └── test_validators.py
│   └── models/                    # Pydantic model validation tests
│       ├── test_auth_models.py
│       ├── test_activity_models.py
│       └── test_onboarding_models.py
│
├── integration/                   # 30% - Service interactions
│   ├── api/                       # API endpoint tests
│   │   ├── test_auth_api.py
│   │   ├── test_activities_api.py
│   │   ├── test_meals_api.py
│   │   └── test_consultation_api.py
│   ├── database/                  # Real database tests
│   │   ├── test_user_crud.py
│   │   ├── test_activity_crud.py
│   │   └── test_rls_policies.py
│   └── workflows/                 # End-to-end business workflows
│       ├── test_real_workflows.py      # Complete user journeys
│       ├── test_onboarding_flow.py
│       └── test_program_generation.py
│
├── e2e/                           # 10% - Critical user paths only
│   ├── test_signup_to_dashboard.py
│   ├── test_consultation_to_program.py
│   └── test_activity_logging_flow.py
│
├── contract/                      # API contract testing (future)
│   ├── test_auth_contracts.py
│   └── test_activity_contracts.py
│
├── performance/                   # Load & stress tests
│   ├── test_api_load.py
│   └── test_database_performance.py
│
├── fixtures/                      # Reusable test data
│   ├── users.py
│   ├── activities.py
│   └── meals.py
│
├── factories/                     # Test data generation
│   ├── user_factory.py
│   ├── activity_factory.py
│   └── meal_factory.py
│
├── conftest.py                    # Global pytest fixtures
├── pytest.ini                     # Pytest configuration
└── README.md                      # This file
```

---

## 🎯 Testing Philosophy (2025 Standards)

### **Modern Test Pyramid**

```
        /\
       /  \      E2E (10%)
      /____\     - Critical user journeys only
     /      \    - Real browser, real database
    / Integr \   Integration (30%)
   /  -ation  \  - API contract testing
  /____________\ - Real database with isolation
 /              \
/      Unit      \ Unit (60%)
\________________/ - Fast, isolated, deterministic
```

### **Key Principles**

1. **Quality Over Coverage**
   - Don't chase 100% line coverage
   - Test business value, not implementation details
   - Focus on critical paths and edge cases

2. **Behavioral Validation**
   - Test what the system does, not how it does it
   - Verify user workflows, not internal mechanics
   - Prefer black-box testing

3. **Minimal Mocking**
   - Use real database for integration tests
   - Mock only external dependencies (3rd party APIs)
   - Prefer test isolation over mocks

4. **Fast Feedback**
   - Unit tests run in < 1 second
   - Integration tests run in < 10 seconds
   - E2E tests run in < 60 seconds

---

## 🔧 Test Categories Explained

### **Unit Tests (60% of suite)**

**Purpose**: Fast, isolated tests of pure business logic

**Characteristics**:
- No database, no HTTP, no external dependencies
- Test single functions/methods in isolation
- Run in milliseconds
- Deterministic (same input = same output)

**Example**:
```python
# tests/unit/utils/test_calorie_calculator.py
def test_calculate_tdee_for_male_athlete():
    """Test total daily energy expenditure calculation"""
    tdee = calculate_tdee(
        weight_kg=80,
        height_cm=180,
        age=28,
        biological_sex="male",
        activity_level="very_active"
    )
    assert 3000 <= tdee <= 3500  # Reasonable range
```

**What to Test**:
- ✅ Utility functions (calculators, validators, formatters)
- ✅ Business logic in service methods
- ✅ Pydantic model validation
- ✅ Edge cases and error handling
- ❌ Database queries (integration test)
- ❌ HTTP requests (integration test)

---

### **Integration Tests (30% of suite)**

**Purpose**: Verify service interactions and data flows

**Characteristics**:
- Use real database (with cleanup)
- Test API endpoints with real HTTP
- Test database queries with real SQL
- Run in seconds

**Example**:
```python
# tests/integration/api/test_activities_api.py
@pytest.mark.asyncio
async def test_log_activity_workflow(authenticated_client):
    """Test complete activity logging flow: create -> fetch -> verify"""
    # Create activity
    response = await authenticated_client.post("/api/v1/activities", json={
        "category": "cardio_steady_state",
        "activity_name": "Morning Run",
        "start_time": datetime.now().isoformat(),
        "duration_minutes": 45,
        "calories_burned": 285,
        "intensity_mets": 8.5
    })
    assert response.status_code == 201
    activity_id = response.json()["id"]

    # Fetch activity
    response = await authenticated_client.get(f"/api/v1/activities/{activity_id}")
    assert response.status_code == 200
    assert response.json()["activity_name"] == "Morning Run"

    # Verify in daily summary
    response = await authenticated_client.get("/api/v1/activities/summary")
    assert response.json()["total_calories"] >= 285
```

**What to Test**:
- ✅ API endpoint functionality
- ✅ Database CRUD operations
- ✅ Service-to-service communication
- ✅ Authentication flows
- ✅ RLS policy enforcement
- ❌ Full user journeys (E2E test)
- ❌ UI interactions (frontend test)

---

### **E2E Tests (10% of suite)**

**Purpose**: Validate critical business workflows end-to-end

**Characteristics**:
- Test complete user journeys
- Real database, real HTTP, real browser (if UI)
- Slowest tests (run last)
- Critical paths only

**Example**:
```python
# tests/e2e/test_signup_to_dashboard.py
@pytest.mark.e2e
async def test_new_user_complete_journey():
    """Test: Signup -> Onboarding -> Log Activity -> View Dashboard"""
    # Signup
    user = await signup_new_user()
    assert user.id is not None

    # Complete onboarding
    await complete_onboarding(user, goal="lose_weight")

    # Log activity
    activity = await log_activity(user, category="cardio", calories=300)
    assert activity.id is not None

    # View dashboard
    dashboard = await get_dashboard(user)
    assert dashboard["today"]["calories_burned"] == 300
```

**What to Test**:
- ✅ Signup → Onboarding → First action
- ✅ Consultation → Program generation → Calendar view
- ✅ Activity logging → Progress tracking → Goal achievement
- ❌ Every possible user action (too slow)
- ❌ Edge cases (unit/integration tests)

---

## 🏃 Running Tests

### **Run All Tests**
```bash
pytest
```

### **Run by Category**
```bash
# Unit tests only (fast)
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# E2E tests only (slow)
pytest tests/e2e/ -m e2e
```

### **Run by Pattern**
```bash
# All activity tests
pytest -k "activity"

# All API tests
pytest tests/integration/api/

# Specific test file
pytest tests/unit/services/test_auth_service.py
```

### **Run with Coverage**
```bash
# All tests with coverage report
pytest --cov=app --cov-report=html

# Exclude integration tests from coverage (2025 best practice)
pytest tests/unit/ --cov=app --cov-report=html
```

### **Run in Parallel**
```bash
# Parallel execution (faster)
pytest -n auto

# Parallel with specific worker count
pytest -n 4
```

### **Run with Verbosity**
```bash
# Verbose output
pytest -v

# Very verbose (show print statements)
pytest -vv -s
```

---

## 🔨 Test Utilities

### **Fixtures** (`fixtures/`)

Reusable test data that's complex to create:

```python
# tests/fixtures/users.py
@pytest.fixture
def sample_user():
    """Returns a complete user profile for testing"""
    return {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "email": "testuser@example.com",
        "full_name": "Test User",
        "onboarding_completed": True
    }
```

### **Factories** (`factories/`)

Dynamic test data generation using factory-boy:

```python
# tests/factories/activity_factory.py
import factory
from datetime import datetime

class ActivityFactory(factory.Factory):
    class Meta:
        model = dict

    category = "cardio_steady_state"
    activity_name = factory.Faker("sentence", nb_words=3)
    start_time = factory.LazyFunction(datetime.now)
    duration_minutes = factory.Faker("random_int", min=10, max=120)
    calories_burned = factory.Faker("random_int", min=100, max=800)
    intensity_mets = factory.Faker("pyfloat", min_value=3.0, max_value=15.0)
```

Usage:
```python
activity = ActivityFactory.create()  # Random valid activity
activity = ActivityFactory.create(calories_burned=500)  # Override specific field
activities = ActivityFactory.create_batch(10)  # Create 10 activities
```

---

## 📊 Coverage Guidelines (2025 Standards)

### **Coverage Targets**

| Category | Target | Why |
|----------|--------|-----|
| **Unit Tests** | 80-90% | High coverage for business logic |
| **Integration Tests** | N/A | Don't measure coverage (behavioral tests) |
| **E2E Tests** | N/A | Critical paths only, not comprehensive |

### **What NOT to Test**

❌ **Don't test**:
- Trivial getters/setters
- Third-party library code
- Pydantic model definitions (already validated)
- Database migrations (run in CI, verified manually)
- Configuration files

✅ **DO test**:
- Business logic
- Complex calculations
- Error handling
- Edge cases
- Critical user workflows

---

## 🚀 CI/CD Integration

### **GitHub Actions Workflow**

```yaml
# .github/workflows/test.yml
name: Test Suite

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run unit tests
        run: pytest tests/unit/ --cov=app --cov-report=xml

  integration-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
    steps:
      - uses: actions/checkout@v3
      - name: Run integration tests
        run: pytest tests/integration/

  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run E2E tests
        run: pytest tests/e2e/ -m e2e
```

---

## 🔍 Best Practices

### **Test Naming Convention**

```python
# ✅ GOOD - Descriptive, behavior-focused
def test_calculate_tdee_for_sedentary_female_returns_lower_value():
    pass

def test_signup_with_existing_email_returns_400_error():
    pass

# ❌ BAD - Vague, implementation-focused
def test_tdee():
    pass

def test_signup_function():
    pass
```

### **Arrange-Act-Assert Pattern**

```python
def test_activity_summary_aggregates_calories_correctly():
    # Arrange - Set up test data
    user_id = "test-user-123"
    activities = [
        ActivityFactory.create(user_id=user_id, calories_burned=200),
        ActivityFactory.create(user_id=user_id, calories_burned=300),
    ]

    # Act - Perform the action
    summary = get_daily_summary(user_id)

    # Assert - Verify the result
    assert summary["total_calories"] == 500
```

### **Test Isolation**

```python
# ✅ GOOD - Each test is independent
@pytest.fixture(autouse=True)
async def cleanup_database():
    yield
    await database.execute("DELETE FROM activities WHERE user_id LIKE 'test-%'")

# ❌ BAD - Tests depend on each other
def test_create_activity():
    activity = create_activity(...)
    global activity_id
    activity_id = activity.id

def test_update_activity():
    update_activity(activity_id, ...)  # Depends on previous test
```

---

## 📚 Additional Resources

### **Tools & Libraries**

- **pytest**: https://docs.pytest.org/
- **httpx**: https://www.python-httpx.org/
- **factory-boy**: https://factoryboy.readthedocs.io/
- **pytest-asyncio**: https://pytest-asyncio.readthedocs.io/
- **pytest-cov**: https://pytest-cov.readthedocs.io/

### **Modern Testing Guides**

- Modern Test Pyramid: https://fullscale.io/blog/modern-test-pyramid-guide/
- Full-Stack Testing 2025: https://talent500.com/blog/fullstack-app-testing-unit-integration-e2e-2025/
- API Testing Best Practices: https://www.browserstack.com/guide/api-testing-best-practices

---

## 🎯 Current Status

### **Test Coverage (As of 2025-10-16)**

| Category | Files | Status |
|----------|-------|--------|
| **Unit Tests** | 7 files | ✅ Basic coverage |
| **Integration Tests** | 7 files | ✅ API + workflows |
| **E2E Tests** | 0 files | ⚠️ TODO |
| **Contract Tests** | 0 files | ⚠️ Future |
| **Performance Tests** | 0 files | ⚠️ Future |

### **Priority Tasks**

1. ✅ Organize test structure (DONE)
2. ⚠️ Move existing tests to appropriate folders
3. ⚠️ Create test factories for common entities
4. ⚠️ Add E2E tests for critical workflows
5. ⚠️ Configure parallel test execution
6. ⚠️ Add performance/load tests

---

**Last Updated**: 2025-10-16
**Testing Framework**: pytest 8.0+
**Python Version**: 3.12+
**Follows**: Modern Full-Stack Testing Standards 2025
