# Test Design: Manual Meal Logging

**Version:** 2.0
**Status:** Test Plan Complete
**Last Updated:** 2025-10-12

---

## 1. Test Strategy

### Testing Pyramid

```
        E2E (10%)
       /         \
    Integration (30%)
   /               \
 Unit Tests (60%)
```

**Unit Tests:** Individual functions, components, utilities
**Integration Tests:** API endpoints with database
**E2E Tests:** Full user flows through UI

---

## 2. Backend Testing

### 2.1 Unit Tests

#### `app/services/nutrition_service.py`

**Test: `test_search_foods_basic`**
```python
async def test_search_foods_basic():
    """Should return foods matching query."""
    # Given: Database has "Chicken Breast" and "Chicken Thigh"
    # When: Search for "chicken"
    results = await nutrition_service.search_foods(query="chicken", limit=20, user_id=test_user_id)
    # Then: Returns both foods
    assert len(results) == 2
    assert any(f.name == "Chicken Breast" for f in results)
```

**Test: `test_search_foods_min_query_length`**
```python
async def test_search_foods_min_query_length():
    """Should return empty for queries <2 chars."""
    results = await nutrition_service.search_foods(query="c", limit=20, user_id=test_user_id)
    assert len(results) == 0
```

**Test: `test_search_foods_includes_custom`**
```python
async def test_search_foods_includes_custom():
    """Should return user's custom foods in search results."""
    # Given: User created custom "Grandma's Cookies"
    # When: Search for "grandma"
    results = await nutrition_service.search_foods(query="grandma", limit=20, user_id=test_user_id)
    # Then: Returns custom food
    assert len(results) == 1
    assert results[0].created_by == test_user_id
```

**Test: `test_create_custom_food_valid`**
```python
async def test_create_custom_food_valid():
    """Should create custom food with correct nutrition per 100g."""
    # Given: Valid custom food data (1 cookie = 25g, 120 cal)
    food = await nutrition_service.create_custom_food(
        user_id=test_user_id,
        name="Test Cookie",
        brand_name=None,
        serving_size=Decimal("1"),
        serving_unit="cookie",
        grams_per_serving=Decimal("25"),
        calories=Decimal("120"),
        protein_g=Decimal("8"),
        carbs_g=Decimal("12"),
        fat_g=Decimal("4"),
    )
    # Then: Nutrition converted to per-100g correctly
    assert food.calories_per_100g == Decimal("480")  # 120 * (100/25)
    assert food.protein_g_per_100g == Decimal("32")  # 8 * 4
    assert len(food.servings) == 1
    assert food.servings[0].grams_per_serving == Decimal("25")
```

**Test: `test_create_meal_calculates_totals`**
```python
async def test_create_meal_calculates_totals():
    """Should calculate meal totals from items correctly."""
    # Given: Chicken breast (174g) + Rice (158g)
    # When: Create meal with both items
    meal = await nutrition_service.create_meal(
        user_id=test_user_id,
        meal_type="lunch",
        logged_at=None,
        notes=None,
        items=[
            MealItemBase(food_id=chicken_id, serving_id=breast_serving_id, quantity=Decimal("1")),
            MealItemBase(food_id=rice_id, serving_id=cup_serving_id, quantity=Decimal("1")),
        ],
        source="manual",
    )
    # Then: Totals = Chicken (284 cal, 53g protein) + Rice (216 cal, 5g protein)
    assert meal.total_calories == Decimal("500")
    assert meal.total_protein_g == Decimal("58")
    assert len(meal.items) == 2
```

**Test: `test_create_meal_invalid_serving`**
```python
async def test_create_meal_invalid_serving():
    """Should reject meal with invalid serving_id."""
    # Given: Non-existent serving_id
    # When: Try to create meal
    # Then: Raises ValueError
    with pytest.raises(ValueError, match="Serving .* not found"):
        await nutrition_service.create_meal(
            user_id=test_user_id,
            meal_type="lunch",
            items=[MealItemBase(food_id=chicken_id, serving_id="invalid-uuid", quantity=Decimal("1"))],
        )
```

**Test: `test_create_meal_serving_food_mismatch`**
```python
async def test_create_meal_serving_food_mismatch():
    """Should reject meal when serving doesn't belong to food."""
    # Given: Rice serving_id but chicken food_id
    # When: Try to create meal
    # Then: Raises ValueError
    with pytest.raises(ValueError, match="Serving .* does not belong to food"):
        await nutrition_service.create_meal(
            user_id=test_user_id,
            meal_type="lunch",
            items=[MealItemBase(food_id=chicken_id, serving_id=rice_serving_id, quantity=Decimal("1"))],
        )
```

---

### 2.2 Integration Tests (API Endpoints)

#### `test_api/test_foods.py`

**Test: `test_search_foods_authenticated`**
```python
async def test_search_foods_authenticated(client, auth_headers):
    """Should return search results for authenticated user."""
    response = await client.get("/api/v1/foods/search?q=chicken", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "foods" in data
    assert "total" in data
```

**Test: `test_search_foods_unauthenticated`**
```python
async def test_search_foods_unauthenticated(client):
    """Should return 401 for unauthenticated request."""
    response = await client.get("/api/v1/foods/search?q=chicken")
    assert response.status_code == 401
```

**Test: `test_get_food_by_id_with_servings`**
```python
async def test_get_food_by_id_with_servings(client, auth_headers, chicken_id):
    """Should return food with servings array."""
    response = await client.get(f"/api/v1/foods/{chicken_id}", headers=auth_headers)
    assert response.status_code == 200
    food = response.json()
    assert food["id"] == str(chicken_id)
    assert "servings" in food
    assert len(food["servings"]) > 0
```

**Test: `test_create_custom_food_success`**
```python
async def test_create_custom_food_success(client, auth_headers):
    """Should create custom food and return it."""
    payload = {
        "name": "My Protein Bar",
        "brand_name": "HomeMade",
        "serving_size": 1,
        "serving_unit": "bar",
        "grams_per_serving": 60,
        "calories": 220,
        "protein_g": 20,
        "carbs_g": 22,
        "fat_g": 8,
    }
    response = await client.post("/api/v1/foods/custom", json=payload, headers=auth_headers)
    assert response.status_code == 201
    food = response.json()
    assert food["name"] == "My Protein Bar"
    assert food["is_public"] == False
    assert food["created_by"] == auth_headers["user_id"]
```

#### `test_api/test_meals.py`

**Test: `test_create_meal_success`**
```python
async def test_create_meal_success(client, auth_headers, chicken_id, breast_serving_id):
    """Should create meal and return with calculated totals."""
    payload = {
        "meal_type": "lunch",
        "logged_at": "2025-10-12T12:30:00Z",
        "notes": "Post-workout meal",
        "items": [
            {"food_id": str(chicken_id), "serving_id": str(breast_serving_id), "quantity": 1.5}
        ],
    }
    response = await client.post("/api/v1/meals", json=payload, headers=auth_headers)
    assert response.status_code == 201
    meal = response.json()
    assert meal["meal_type"] == "lunch"
    assert meal["total_calories"] > 0
    assert len(meal["items"]) == 1
    assert meal["items"][0]["quantity"] == 1.5
```

**Test: `test_create_meal_empty_items`**
```python
async def test_create_meal_empty_items(client, auth_headers):
    """Should reject meal with no items."""
    payload = {"meal_type": "lunch", "items": []}
    response = await client.post("/api/v1/meals", json=payload, headers=auth_headers)
    assert response.status_code == 400
    assert "NUTRITION_202" in response.json()["error_code"]
```

**Test: `test_list_meals_with_date_filter`**
```python
async def test_list_meals_with_date_filter(client, auth_headers):
    """Should return meals within date range."""
    response = await client.get(
        "/api/v1/meals?start_date=2025-10-01&end_date=2025-10-13",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "meals" in data
    # All meals should be within range
    for meal in data["meals"]:
        logged_at = datetime.fromisoformat(meal["logged_at"])
        assert datetime(2025, 10, 1) <= logged_at < datetime(2025, 10, 13)
```

**Test: `test_delete_meal_success`**
```python
async def test_delete_meal_success(client, auth_headers, meal_id):
    """Should delete meal and return 204."""
    response = await client.delete(f"/api/v1/meals/{meal_id}", headers=auth_headers)
    assert response.status_code == 204
    # Verify deleted
    get_response = await client.get(f"/api/v1/meals/{meal_id}", headers=auth_headers)
    assert get_response.status_code == 404
```

**Test: `test_delete_meal_not_owned`**
```python
async def test_delete_meal_not_owned(client, auth_headers, other_user_meal_id):
    """Should return 404 when trying to delete another user's meal."""
    response = await client.delete(f"/api/v1/meals/{other_user_meal_id}", headers=auth_headers)
    assert response.status_code == 404
```

**Test: `test_get_nutrition_stats`**
```python
async def test_get_nutrition_stats(client, auth_headers):
    """Should return daily nutrition summary."""
    response = await client.get("/api/v1/nutrition/stats?date=2025-10-12", headers=auth_headers)
    assert response.status_code == 200
    stats = response.json()
    assert "calories_consumed" in stats
    assert "protein_consumed" in stats
    assert "calories_goal" in stats
    assert "meals_count" in stats
    assert "meals_by_type" in stats
```

---

## 3. Frontend Testing

### 3.1 Component Tests

#### `FoodSearchBar.test.tsx`

**Test: `renders search input`**
```typescript
it('renders search input with placeholder', () => {
  render(<FoodSearchBar onSelect={vi.fn()} />)
  expect(screen.getByPlaceholderText(/search foods/i)).toBeInTheDocument()
})
```

**Test: `debounces search input`**
```typescript
it('debounces search input by 300ms', async () => {
  const mockSearch = vi.fn()
  vi.useFakeTimers()

  render(<FoodSearchBar onSelect={vi.fn()} onSearch={mockSearch} />)
  const input = screen.getByPlaceholderText(/search foods/i)

  fireEvent.change(input, { target: { value: 'chicken' } })
  expect(mockSearch).not.toHaveBeenCalled()

  vi.advanceTimersByTime(300)
  expect(mockSearch).toHaveBeenCalledWith('chicken')

  vi.useRealTimers()
})
```

**Test: `displays search results`**
```typescript
it('displays search results when typing', async () => {
  const mockResults = [
    { id: '1', name: 'Chicken Breast', brand_name: null, servings: [] },
    { id: '2', name: 'Chicken Thigh', brand_name: null, servings: [] },
  ]

  // Mock API
  server.use(
    rest.get('/api/v1/foods/search', (req, res, ctx) => {
      return res(ctx.json({ foods: mockResults, total: 2 }))
    })
  )

  render(<FoodSearchBar onSelect={vi.fn()} />)
  const input = screen.getByPlaceholderText(/search foods/i)

  fireEvent.change(input, { target: { value: 'chicken' } })

  await waitFor(() => {
    expect(screen.getByText('Chicken Breast')).toBeInTheDocument()
    expect(screen.getByText('Chicken Thigh')).toBeInTheDocument()
  })
})
```

#### `MealTotalsCard.test.tsx`

**Test: `displays nutrition totals`**
```typescript
it('displays calculated nutrition totals', () => {
  const items = [
    { calories: 284, protein_g: 53, carbs_g: 0, fat_g: 6 },
    { calories: 216, protein_g: 5, carbs_g: 45, fat_g: 2 },
  ]

  render(<MealTotalsCard items={items} />)

  expect(screen.getByText('500')).toBeInTheDocument() // calories
  expect(screen.getByText('58g')).toBeInTheDocument() // protein
  expect(screen.getByText('45g')).toBeInTheDocument() // carbs
  expect(screen.getByText('8g')).toBeInTheDocument() // fat
})
```

#### `AddFoodModal.test.tsx`

**Test: `shows serving options`**
```typescript
it('shows serving size options for food', () => {
  const food = {
    id: '1',
    name: 'Chicken Breast',
    servings: [
      { id: '1', serving_unit: 'breast', serving_label: 'medium', grams_per_serving: 174 },
      { id: '2', serving_unit: 'oz', grams_per_serving: 28 },
      { id: '3', serving_unit: 'g', grams_per_serving: 100 },
    ],
  }

  render(<AddFoodModal food={food} onAdd={vi.fn()} onClose={vi.fn()} />)

  expect(screen.getByText(/medium breast/i)).toBeInTheDocument()
  expect(screen.getByText(/1 oz/i)).toBeInTheDocument()
  expect(screen.getByText(/100 g/i)).toBeInTheDocument()
})
```

**Test: `calculates nutrition preview`**
```typescript
it('calculates nutrition preview when quantity changes', () => {
  const food = {
    calories_per_100g: 165,
    protein_g_per_100g: 31,
    servings: [{ grams_per_serving: 174, serving_unit: 'breast' }],
  }

  render(<AddFoodModal food={food} onAdd={vi.fn()} onClose={vi.fn()} />)

  // Change quantity to 2
  const quantityInput = screen.getByLabelText(/quantity/i)
  fireEvent.change(quantityInput, { target: { value: '2' } })

  // 2 breasts * 174g = 348g = 3.48x nutrition
  await waitFor(() => {
    expect(screen.getByText(/574/)).toBeInTheDocument() // calories
    expect(screen.getByText(/108/)).toBeInTheDocument() // protein
  })
})
```

---

### 3.2 Integration Tests

#### `meal-logging-flow.test.tsx`

**Test: `complete meal logging flow`**
```typescript
it('allows user to log a complete meal', async () => {
  const user = userEvent.setup()

  // Mock APIs
  server.use(
    rest.get('/api/v1/foods/search', (req, res, ctx) => {
      return res(ctx.json({ foods: mockFoods, total: 1 }))
    }),
    rest.post('/api/v1/meals', (req, res, ctx) => {
      return res(ctx.json(mockMeal))
    })
  )

  render(<NutritionPage />, { wrapper: AppProviders })

  // Click "Log Meal"
  await user.click(screen.getByRole('button', { name: /log meal/i }))

  // Select meal type
  await user.click(screen.getByLabelText(/breakfast/i))

  // Search for food
  const searchInput = screen.getByPlaceholderText(/search foods/i)
  await user.type(searchInput, 'chicken breast')

  // Select food from results
  await waitFor(() => screen.getByText('Grilled Chicken Breast'))
  await user.click(screen.getByText('Grilled Chicken Breast'))

  // Select serving size
  await user.click(screen.getByText(/medium breast/i))

  // Adjust quantity
  const quantityInput = screen.getByLabelText(/quantity/i)
  await user.clear(quantityInput)
  await user.type(quantityInput, '1.5')

  // Add to meal
  await user.click(screen.getByRole('button', { name: /add to meal/i }))

  // Verify food appears in meal
  expect(screen.getByText(/grilled chicken/i)).toBeInTheDocument()
  expect(screen.getByText(/1.5/)).toBeInTheDocument()

  // Log meal
  await user.click(screen.getByRole('button', { name: /log meal/i }))

  // Verify success
  await waitFor(() => {
    expect(screen.getByText(/meal logged/i)).toBeInTheDocument()
  })
})
```

---

### 3.3 E2E Tests (Playwright)

#### `meal-logging.spec.ts`

**Test: `user can log breakfast with multiple foods`**
```typescript
test('user can log breakfast with multiple foods', async ({ page }) => {
  await page.goto('/nutrition')

  // Log in
  await page.fill('[name="email"]', 'test@example.com')
  await page.fill('[name="password"]', 'password')
  await page.click('button[type="submit"]')

  // Navigate to meal logging
  await page.click('text=Log Meal')

  // Select breakfast
  await page.click('label:has-text("Breakfast")')

  // Add chicken
  await page.fill('[placeholder="Search foods..."]', 'chicken breast')
  await page.click('text=Grilled Chicken Breast')
  await page.selectOption('select[name="serving"]', { label: 'medium breast' })
  await page.fill('[name="quantity"]', '1')
  await page.click('button:has-text("Add to Meal")')

  // Add rice
  await page.fill('[placeholder="Search foods..."]', 'brown rice')
  await page.click('text=Brown Rice, Cooked')
  await page.selectOption('select[name="serving"]', { label: '1 cup' })
  await page.fill('[name="quantity"]', '1')
  await page.click('button:has-text("Add to Meal")')

  // Verify totals
  await expect(page.locator('text=/500.*cal/i')).toBeVisible()

  // Save meal
  await page.click('button:has-text("Log Meal")')

  // Verify success
  await expect(page.locator('text=/breakfast logged/i')).toBeVisible()

  // Verify appears in history
  await expect(page.locator('text=Grilled Chicken Breast')).toBeVisible()
})
```

---

## 4. Accessibility Testing

### Automated Tests (axe-core)

```typescript
// __tests__/a11y/meal-logging.a11y.test.tsx
import { render } from '@testing-library/react'
import { axe, toHaveNoViolations } from 'jest-axe'

expect.extend(toHaveNoViolations)

it('LogMealModal has no accessibility violations', async () => {
  const { container } = render(<LogMealModal isOpen={true} onClose={vi.fn()} />)
  const results = await axe(container)
  expect(results).toHaveNoViolations()
})

it('FoodSearchBar has no accessibility violations', async () => {
  const { container } = render(<FoodSearchBar onSelect={vi.fn()} />)
  const results = await axe(container)
  expect(results).toHaveNoViolations()
})
```

### Manual Tests (Screen Reader)

- [ ] Can navigate entire meal logging flow with keyboard only
- [ ] Screen reader announces search results
- [ ] Screen reader announces nutrition totals
- [ ] Screen reader announces validation errors
- [ ] Focus traps work in modals
- [ ] Focus returns to trigger after modal closes

---

## 5. Performance Testing

### Load Tests

```python
# tests/load/test_meal_logging_load.py
from locust import HttpUser, task, between

class MealLoggingUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def search_foods(self):
        self.client.get("/api/v1/foods/search?q=chicken", headers=self.headers)

    @task(1)
    def create_meal(self):
        payload = {
            "meal_type": "lunch",
            "items": [{"food_id": self.food_id, "serving_id": self.serving_id, "quantity": 1}]
        }
        self.client.post("/api/v1/meals", json=payload, headers=self.headers)
```

**Performance Targets:**
- Search: p95 < 500ms, p99 < 1s
- Create meal: p95 < 1s, p99 < 2s
- List meals: p95 < 800ms, p99 < 1.5s

---

## 6. Test Coverage Requirements

- **Overall:** ≥80%
- **Critical paths:** 100%
  - Food search
  - Meal creation
  - Nutrition calculation
  - Data validation

---

## 7. Test Execution Plan

### CI/CD Pipeline

```yaml
# .github/workflows/test.yml
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      # Backend tests
      - name: Run Python tests
        run: |
          pytest tests/ --cov=app --cov-report=xml

      # Frontend tests
      - name: Run TypeScript tests
        run: |
          npm test -- --coverage

      # E2E tests
      - name: Run Playwright tests
        run: |
          npx playwright test

      # Upload coverage
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

### Pre-commit Hooks

```bash
# .pre-commit-config.yaml
- repo: local
  hooks:
    - id: pytest
      name: pytest
      entry: pytest tests/unit/
      language: system
      pass_filenames: false
```

---

## Summary

✅ **Unit tests** cover all business logic
✅ **Integration tests** cover all API endpoints
✅ **Component tests** cover all UI components
✅ **E2E tests** cover critical user flows
✅ **Accessibility tests** ensure WCAG AA compliance
✅ **Performance tests** validate response times

**Total estimated tests:** ~120 (60 unit, 30 integration, 20 component, 5 E2E, 5 accessibility)

**Est. time to implement:** 12-16 hours (with backend + frontend)
