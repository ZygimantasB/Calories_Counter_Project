# React SPA Feature Parity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bring the React SPA (`/app/*`) to full feature parity with the Django template frontend, adding all missing features, CRUD operations, and UI components.

**Architecture:** Each task adds one logical feature group. Backend API endpoints are added first, then React components consume them. Existing patterns (Axios client with CSRF, Recharts charts, Tailwind dark-theme cards, modal-first CRUD) are followed exactly.

**Tech Stack:** Django 5.2 (Python), React 18 + Vite, Tailwind CSS v4, Recharts, Axios, Lucide icons, Vitest + Testing Library

---

## Feature Gap Summary

### Missing from React SPA (grouped by priority)

| # | Feature | Django Page | React Status |
|---|---------|-------------|-------------|
| 1 | Calculator widget | Food Tracker | Missing entirely |
| 2 | Copy a Previous Day | Food Tracker | Missing entirely |
| 3 | Meal Templates (save/load/manage) | Food Tracker | Missing entirely |
| 4 | CSV download on all pages | Food Tracker, Weight, Top Foods | Missing entirely |
| 5 | Eating Pattern by Hour chart | Food Tracker | Missing entirely |
| 6 | Calorie/Macro trend charts on food page | Food Tracker | Missing (only on Dashboard) |
| 7 | Nutrition Overview with daily averages | Food Tracker | Partial (no multi-day averages) |
| 8 | Today's Budget progress bars | Food Tracker | Partial (exists on Dashboard but not Food page) |
| 9 | Weight edit functionality | Weight Tracker | Missing (only add/delete) |
| 10 | Weight Change Analysis (rate, trend, consistency) | Weight Tracker | Missing entirely |
| 11 | Weight Changes bar chart | Weight Tracker | Missing entirely |
| 12 | Health Metrics (BMI, category) | Weight Tracker | Missing entirely |
| 13 | Weight Projections (time to goal, goal date) | Weight Tracker | Partial (stats exist but no projection cards) |
| 14 | Weight vs Calorie Intake correlation table | Weight Tracker | Missing entirely |
| 15 | Running session edit/delete | Running Tracker | Missing (only add) |
| 16 | Running charts (distance, duration over time) | Running Tracker | Missing entirely |
| 17 | Running performance metrics | Running Tracker | Partial (basic stats only) |
| 18 | Workout CRUD (create/edit/delete sessions) | Workout Tracker | Missing (read-only) |
| 19 | Exercise library CRUD | Workout Tracker | Missing (read-only) |
| 20 | Workout table/spreadsheet | Workout Tracker | Missing entirely |
| 21 | Body Measurements dedicated React API | Body Measurements | Uses Django template endpoints |
| 22 | Month Comparison analytics | Analytics | Missing entirely |
| 23 | Yearly Trends analytics | Analytics | Missing entirely |
| 24 | Product Compare analytics | Analytics | Missing entirely |
| 25 | Multi-day date range filtering on Food page | Food Tracker | Missing (only single date nav) |
| 26 | Date range filtering on Top Foods | Top Foods | Partial (only days selector) |
| 27 | Sort controls on Top Foods | Top Foods | Missing (only tab switching) |

---

## File Structure

### New Files to Create

```
frontend/src/
├── components/
│   ├── Calculator.jsx              # Calculator widget (reusable)
│   ├── CopyPreviousDay.jsx         # Copy day's foods modal
│   ├── MealTemplates.jsx           # Meal template save/load/manage
│   ├── DateRangeFilter.jsx         # Reusable date range filter bar
│   ├── EatingPatternChart.jsx      # Hour-of-day calorie chart
│   ├── CalorieTrendChart.jsx       # Calorie intake trend (reusable)
│   ├── MacroTrendChart.jsx         # Macro trends chart (reusable)
│   ├── WeightChangeAnalysis.jsx    # Weight change rate/trend/consistency
│   ├── WeightCorrelationTable.jsx  # Weight vs calories table
│   ├── HealthMetrics.jsx           # BMI display
│   ├── WeightProjections.jsx       # Goal projections
│   └── CSVDownloadButton.jsx       # Reusable CSV export button
├── api/
│   └── mealTemplates.js            # Meal template API calls
```

### Files to Modify

```
frontend/src/
├── pages/
│   ├── FoodTracker.jsx             # Add calculator, copy-day, templates, date range, charts
│   ├── WeightTracker.jsx           # Add edit, analysis, BMI, projections, correlation
│   ├── RunningTracker.jsx          # Add edit/delete, charts, performance metrics
│   ├── WorkoutTracker.jsx          # Add full CRUD, exercise library management
│   ├── BodyMeasurements.jsx        # Switch to React API endpoints
│   ├── Analytics.jsx               # Add month compare, yearly trends, product compare tabs
│   └── TopFoods.jsx                # Add date range, sort controls, CSV download
├── api/
│   ├── food.js                     # Add copy-day, hourly pattern endpoints
│   ├── weight.js                   # Add edit, correlation, analysis endpoints
│   ├── running.js                  # Add edit/delete endpoints
│   ├── workout.js                  # Add CRUD endpoints
│   └── bodyMeasurements.js         # Add dedicated React API calls

count_calories_app/
├── views.py                        # Add missing API endpoints
├── urls.py                         # Register new API routes
└── tests/
    └── test_react_api_parity.py    # Tests for all new endpoints
```

---

## Tasks

### Task 1: Food Tracker — Calculator Widget

**Files:**
- Create: `frontend/src/components/Calculator.jsx`
- Modify: `frontend/src/pages/FoodTracker.jsx`
- Test: `frontend/src/components/__tests__/Calculator.test.jsx`

- [ ] **Step 1: Write Calculator component test**

```jsx
// frontend/src/components/__tests__/Calculator.test.jsx
import { render, screen, fireEvent } from '@testing-library/react';
import Calculator from '../Calculator';

describe('Calculator', () => {
  it('renders calculator buttons', () => {
    render(<Calculator onCopyValue={() => {}} />);
    expect(screen.getByText('7')).toBeInTheDocument();
    expect(screen.getByText('=')).toBeInTheDocument();
    expect(screen.getByText('C')).toBeInTheDocument();
  });

  it('calculates basic expression', () => {
    const onCopy = vi.fn();
    render(<Calculator onCopyValue={onCopy} />);
    fireEvent.click(screen.getByText('5'));
    fireEvent.click(screen.getByText('+'));
    fireEvent.click(screen.getByText('3'));
    fireEvent.click(screen.getByText('='));
    fireEvent.click(screen.getByText('Copy to Calories'));
    expect(onCopy).toHaveBeenCalledWith('calories', 8);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npx vitest run src/components/__tests__/Calculator.test.jsx`
Expected: FAIL — module not found

- [ ] **Step 3: Implement Calculator component**

Create `frontend/src/components/Calculator.jsx`:
- Display input (read-only text showing expression)
- Button grid: C, (, ), /, 7, 8, 9, *, 4, 5, 6, -, 1, 2, 3, +, 0, ., =
- Copy buttons: "Copy to Calories", Fat, Carbs, Protein
- `onCopyValue(field, value)` callback prop
- Use `eval()` safely (regex-validated numeric expression only)
- Dark theme: `bg-gray-800 border-gray-700` card styling

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npx vitest run src/components/__tests__/Calculator.test.jsx`
Expected: PASS

- [ ] **Step 5: Integrate into FoodTracker page**

In `frontend/src/pages/FoodTracker.jsx`:
- Import Calculator component
- Add collapsible Calculator section below the Add Food button area
- Wire `onCopyValue` to update the add food form fields

- [ ] **Step 6: Build and verify**

Run: `cd frontend && npm run build`
Expected: Build succeeds with no errors

- [ ] **Step 7: Commit**

```bash
git add frontend/src/components/Calculator.jsx frontend/src/components/__tests__/Calculator.test.jsx frontend/src/pages/FoodTracker.jsx
git commit -m "feat(react): add calculator widget to food tracker"
```

---

### Task 2: Food Tracker — Copy a Previous Day

**Files:**
- Create: `frontend/src/components/CopyPreviousDay.jsx`
- Modify: `frontend/src/api/food.js`
- Modify: `frontend/src/pages/FoodTracker.jsx`
- Verify: `count_calories_app/views.py` (existing copy_day_foods endpoint)

- [ ] **Step 1: Add new React API endpoint (existing `copy_day_meals` uses form-data POST, not JSON)**

The existing Django template endpoint `copy_day_meals` reads `request.POST`, not JSON body. We MUST create a new dedicated JSON endpoint.

- [ ] **Step 2: Add backend API endpoint**

In `count_calories_app/views.py`, add `api_copy_day_foods`:
```python
@require_http_methods(["POST"])
def api_copy_day_foods(request):
    data = json.loads(request.body)
    source_date_str = data.get('source_date')
    target_date_str = data.get('target_date')  # defaults to today
    # Parse dates, query FoodItems from source_date, clone to target_date
    # Return count of copied items
```

In `count_calories_app/urls.py`:
```python
path('api/react/food-items/copy-day/', views.api_copy_day_foods, name='api_copy_day_foods'),
```

- [ ] **Step 3: Write Django test for copy endpoint**

```python
# In count_calories_app/tests/test_react_api_parity.py
def test_copy_day_foods(self):
    # Create food items on a past date
    # POST to copy endpoint
    # Verify items cloned to target date
```

- [ ] **Step 4: Run Django tests**

Run: `python manage.py test count_calories_app.tests.test_react_api_parity -v 2`
Expected: PASS

- [ ] **Step 5: Add API function in food.js**

```javascript
// frontend/src/api/food.js
copyDayFoods: async (sourceDate, targetDate) => {
  const response = await apiClient.post('/api/react/food-items/copy-day/', {
    source_date: sourceDate,
    target_date: targetDate,
  });
  return response.data;
},
```

- [ ] **Step 6: Create CopyPreviousDay component**

Create `frontend/src/components/CopyPreviousDay.jsx`:
- Date picker for source date
- "Copy to Today" button
- Success/error feedback
- Card styling matching existing components

- [ ] **Step 7: Integrate into FoodTracker page**

Add CopyPreviousDay below the Quick Add section in FoodTracker.jsx.

- [ ] **Step 8: Build and commit**

```bash
cd frontend && npm run build
git add -A && git commit -m "feat(react): add copy previous day to food tracker"
```

---

### Task 3: Food Tracker — Meal Templates

**Files:**
- Create: `frontend/src/components/MealTemplates.jsx`
- Create: `frontend/src/api/mealTemplates.js`
- Modify: `frontend/src/pages/FoodTracker.jsx`
- Modify: `count_calories_app/views.py` (add API endpoints)
- Modify: `count_calories_app/urls.py`
- Test: `count_calories_app/tests/test_react_api_parity.py`

- [ ] **Step 1: Add backend API endpoints for meal templates**

Endpoints needed:
- `GET /api/react/meal-templates/` — list all templates
- `POST /api/react/meal-templates/add/` — save current day as template
- `POST /api/react/meal-templates/<id>/log/` — apply template to today
- `DELETE /api/react/meal-templates/<id>/delete/` — delete template

- [ ] **Step 2: Write Django tests for template endpoints**
- [ ] **Step 3: Run Django tests** — Expected: PASS
- [ ] **Step 4: Create mealTemplates.js API module**
- [ ] **Step 5: Create MealTemplates component**

Features:
- Text input for template name + "Save Today" button
- List of saved templates with "Apply" and "Delete" buttons
- Empty state: "No templates saved yet"

- [ ] **Step 6: Integrate into FoodTracker page**
- [ ] **Step 7: Build and commit**

---

### Task 4: Food Tracker — Date Range Filtering & Multi-Day Views

**Files:**
- Create: `frontend/src/components/DateRangeFilter.jsx`
- Modify: `frontend/src/pages/FoodTracker.jsx`
- Modify: `frontend/src/api/food.js`

- [ ] **Step 1: Create DateRangeFilter component**

Reusable component with:
- Quick filter buttons: Today, This Week, This Month, 7d, 30d, 90d, 6M, 1Y, All
- Custom date range picker (start + end date inputs + Apply button)
- `onChange({ type, days, startDate, endDate })` callback
- Active state highlighting on selected filter

- [ ] **Step 2: Update FoodTracker to support multi-day views**

Changes to FoodTracker.jsx:
- Replace simple date navigator with DateRangeFilter
- When multi-day selected: show period totals + daily averages section
- Update food list heading (e.g., "Last 7 Days" instead of date)
- Fetch food items with `days` or `start_date/end_date` params

- [ ] **Step 3: Add daily averages display**

When viewing multi-day range, show:
- Period totals: Calories, Fat, Carbs, Protein
- Daily Averages (N days): same breakdown with per-day values
- % of calories and % by weight for each macro

- [ ] **Step 4: Build and commit**

---

### Task 5: Food Tracker — Trend Charts & Eating Pattern

**Files:**
- Create: `frontend/src/components/EatingPatternChart.jsx`
- Create: `frontend/src/components/CalorieTrendChart.jsx`
- Create: `frontend/src/components/MacroTrendChart.jsx`
- Modify: `frontend/src/api/food.js` (add `getHourlyPattern` only)
- Modify: `frontend/src/pages/FoodTracker.jsx`

- [ ] **Step 1: Add hourly pattern API function to existing food.js**

NOTE: `/api/calories-trend/` and `/api/macros-trend/` are already in `food.js` as `getCaloriesTrend` and `getMacrosTrend`. Do NOT create a separate `trends.js` — only add the new hourly pattern function to `food.js`:

```javascript
// Add to frontend/src/api/food.js
getHourlyPattern: async (params) => {
  const response = await apiClient.get('/api/react/food-items/hourly/', { params });
  return response.data;
},
```

- [ ] **Step 2: Add hourly eating pattern API endpoint**

In `views.py`, add `api_hourly_eating_pattern`:
```python
@require_http_methods(["GET"])
def api_hourly_eating_pattern(request):
    # Query FoodItems, group by hour of consumed_at
    # Return {hours: [0-23], calories: [values]}
```

Add URL: `path('api/react/food-items/hourly/', views.api_hourly_eating_pattern, name='api_hourly_pattern')`

- [ ] **Step 3: Write Django test for hourly endpoint**
- [ ] **Step 4: Create CalorieTrendChart component**

Recharts AreaChart showing daily calorie intake over the selected period.
Uses existing `/api/calories-trend/` endpoint.

- [ ] **Step 5: Create MacroTrendChart component**

Recharts multi-line chart with protein/carbs/fat trends.
Uses existing `/api/macros-trend/` endpoint.

- [ ] **Step 6: Create EatingPatternChart component**

Recharts BarChart showing calories per hour of day (0-23).
Uses new `/api/react/food-items/hourly/` endpoint.

- [ ] **Step 7: Add all three charts to FoodTracker page**
- [ ] **Step 8: Build and commit**

---

### Task 6: Food Tracker — CSV Download

**Files:**
- Create: `frontend/src/components/CSVDownloadButton.jsx`
- Modify: `frontend/src/pages/FoodTracker.jsx`
- Modify: `frontend/src/pages/TopFoods.jsx`
- Modify: `frontend/src/pages/WeightTracker.jsx`

- [ ] **Step 1: Create CSVDownloadButton component**

```jsx
// Reusable across all pages
export default function CSVDownloadButton({ endpoint, params, label = 'Download CSV' }) {
  const handleDownload = () => {
    const searchParams = new URLSearchParams(params);
    searchParams.set('export', 'csv');
    window.location.href = `${endpoint}?${searchParams.toString()}`;
  };
  return <Button variant="outline" icon={Download} onClick={handleDownload}>{label}</Button>;
}
```

- [ ] **Step 2: Add to FoodTracker, WeightTracker, TopFoods, BodyMeasurements pages**

Note: BodyMeasurements already has `bodyMeasurements/export/csv/` endpoint wired in `bodyMeasurements.js`, but the page needs a visible download button.
- [ ] **Step 3: Build and commit**

---

### Task 7: Weight Tracker — Edit Functionality

**Files:**
- Modify: `count_calories_app/views.py` (add edit endpoint)
- Modify: `count_calories_app/urls.py`
- Modify: `frontend/src/api/weight.js`
- Modify: `frontend/src/pages/WeightTracker.jsx`
- Test: `count_calories_app/tests/test_react_api_parity.py`

- [ ] **Step 1: Add backend PUT endpoint**

```python
from django.utils.dateparse import parse_datetime

@require_http_methods(["PUT", "PATCH"])
def api_update_weight(request, weight_id):
    weight = get_object_or_404(Weight, id=weight_id)
    data = json.loads(request.body)
    if 'weight' in data:
        weight.weight = Decimal(str(data['weight']))
    if 'notes' in data:
        weight.notes = data['notes']
    if 'recorded_at' in data:
        weight.recorded_at = parse_datetime(data['recorded_at'])
    weight.save()
    return JsonResponse({'success': True})
```

URL: `path('api/react/weight-items/<int:weight_id>/update/', views.api_update_weight, name='api_update_weight')`

- [ ] **Step 2: Write Django test**
- [ ] **Step 3: Add API function in weight.js**
- [ ] **Step 4: Add edit modal to WeightTracker.jsx**

Same modal pattern as add, but pre-filled with existing values.
Edit button (pencil icon) on each weight entry row.

- [ ] **Step 5: Build and commit**

---

### Task 8: Weight Tracker — Analysis, BMI, Projections

**Files:**
- Create: `frontend/src/components/WeightChangeAnalysis.jsx`
- Create: `frontend/src/components/HealthMetrics.jsx`
- Create: `frontend/src/components/WeightProjections.jsx`
- Modify: `frontend/src/pages/WeightTracker.jsx`

- [ ] **Step 1: Create WeightChangeAnalysis component**

Uses stats from existing `/api/react/weight-items/` response.
Shows:
- Change Rate (kg/week) — from `stats.change_rate`
- Trend direction (Losing/Gaining/Stable) — derived from rate
- Consistency (Standard Deviation) — from `stats.consistency`
- Weight Changes bar chart (Recharts BarChart) — computed from weight entries

- [ ] **Step 2: Create HealthMetrics component**

Shows:
- BMI value — from `stats.bmi`
- BMI Category — derived from BMI value (Underweight/Normal/Overweight/Obese)
- Color-coded display

- [ ] **Step 3: Create WeightProjections component**

Shows:
- Projected weight (4 weeks) — from `stats.projected_weight`
- Time to Goal — from `stats.weeks_to_goal`
- Goal Date — from `stats.goal_date`

- [ ] **Step 4: Add all components to WeightTracker page**
- [ ] **Step 5: Build and commit**

---

### Task 9: Weight Tracker — Calorie Correlation Table

**Files:**
- Create: `frontend/src/components/WeightCorrelationTable.jsx`
- Modify: `frontend/src/api/weight.js`
- Modify: `frontend/src/pages/WeightTracker.jsx`

- [ ] **Step 1: Add API function for correlation data**

```javascript
// frontend/src/api/weight.js
getCorrelation: async (params) => {
  const response = await apiClient.get('/api/weight-calories-correlation/', { params });
  return response.data;
},
```

- [ ] **Step 2: Create WeightCorrelationTable component**

Paginated table showing:
- Period (date range)
- Weight Change (color-coded: green loss, red gain)
- Days between measurements
- Total Calories during period

Uses existing `/api/weight-calories-correlation/` endpoint.

- [ ] **Step 3: Add to WeightTracker page**
- [ ] **Step 4: Build and commit**

---

### Task 10: Running Tracker — Edit, Delete, Charts

**Files:**
- Modify: `count_calories_app/views.py` (add edit/delete endpoints)
- Modify: `count_calories_app/urls.py`
- Modify: `frontend/src/api/running.js`
- Modify: `frontend/src/pages/RunningTracker.jsx`
- Test: `count_calories_app/tests/test_react_api_parity.py`

- [ ] **Step 1: Add backend edit/delete endpoints**

```python
@require_http_methods(["PUT", "PATCH"])
def api_update_running(request, session_id):
    session = get_object_or_404(RunningSession, id=session_id)
    data = json.loads(request.body)
    # Update fields: date, distance, duration, notes
    session.save()
    return JsonResponse({'success': True})

@require_http_methods(["DELETE"])
def api_delete_running(request, session_id):
    session = get_object_or_404(RunningSession, id=session_id)
    session.delete()
    return JsonResponse({'success': True})
```

- [ ] **Step 2: Write Django tests**
- [ ] **Step 3: Update running.js API module**
- [ ] **Step 4: Add edit modal and delete confirmation to RunningTracker**
- [ ] **Step 5: Add running charts**

Two Recharts charts:
- Distance over time (AreaChart)
- Duration over time (AreaChart)
Using data from existing `/api/react/running-items/` response.

- [ ] **Step 6: Add performance metrics section**

Cards for:
- Pace Improvement (%)
- Fastest Pace (min/km)
- Longest Run (km)
- Avg Weekly/Monthly Distance

- [ ] **Step 7: Build and commit**

---

### Task 11a: Workout Tracker — Session CRUD

**Files:**
- Modify: `count_calories_app/views.py` (add session CRUD endpoints)
- Modify: `count_calories_app/urls.py`
- Modify: `frontend/src/api/workout.js`
- Modify: `frontend/src/pages/WorkoutTracker.jsx`
- Test: `count_calories_app/tests/test_react_api_parity.py`

- [ ] **Step 1: Add backend session CRUD endpoints**

Endpoints:
- `POST /api/react/workouts/add/` — create workout session
- `PUT /api/react/workouts/<id>/update/` — update workout
- `DELETE /api/react/workouts/<id>/delete/` — delete workout

- [ ] **Step 2: Write Django tests for session CRUD**
- [ ] **Step 3: Update workout.js API module with add/update/delete**
- [ ] **Step 4: Add "Start Workout" modal with form**

Fields: Workout Name, Date/Time, Notes.
Add edit and delete buttons to existing workout cards.

- [ ] **Step 5: Build and commit**

---

### Task 11b: Workout Tracker — Exercise CRUD within Sessions

**Depends on:** Task 11a

**Files:**
- Modify: `count_calories_app/views.py` (add exercise-in-workout endpoints)
- Modify: `count_calories_app/urls.py`
- Modify: `frontend/src/api/workout.js`
- Modify: `frontend/src/pages/WorkoutTracker.jsx`
- Test: `count_calories_app/tests/test_react_api_parity.py`

- [ ] **Step 1: Add backend exercise-within-workout endpoints**

Endpoints:
- `POST /api/react/workouts/<id>/exercises/add/` — add exercise to workout
- `PUT /api/react/workouts/<id>/exercises/<eid>/update/` — update exercise
- `DELETE /api/react/workouts/<id>/exercises/<eid>/delete/` — delete exercise

- [ ] **Step 2: Write Django tests**
- [ ] **Step 3: Update workout.js API module**
- [ ] **Step 4: Add expandable workout detail view**

Expandable workout card showing:
- List of exercises with sets/reps/weight
- "Add Exercise" button with exercise picker from library
- Edit/delete per exercise

- [ ] **Step 5: Build and commit**

---

### Task 11c: Workout Tracker — Exercise Library Management

**Files:**
- Modify: `count_calories_app/views.py` (add exercise library CRUD)
- Modify: `count_calories_app/urls.py`
- Modify: `frontend/src/api/workout.js`
- Modify: `frontend/src/pages/WorkoutTracker.jsx`
- Test: `count_calories_app/tests/test_react_api_parity.py`

- [ ] **Step 1: Add backend exercise library endpoints**

Endpoints:
- `POST /api/react/exercises/add/` — add to exercise library
- `DELETE /api/react/exercises/<id>/delete/` — delete from library

- [ ] **Step 2: Write Django tests**
- [ ] **Step 3: Update workout.js API module**
- [ ] **Step 4: Add exercise library management section**

Section to add new exercises (name, muscle group, description).
Delete button on each exercise in the library grid.

- [ ] **Step 5: Build and commit**

---

### Task 11d: Workout Tracker — Workout Table/Spreadsheet

**Depends on:** Task 11a

**Files:**
- Modify: `count_calories_app/views.py` (add workout table API endpoints)
- Modify: `count_calories_app/urls.py`
- Modify: `frontend/src/api/workout.js`
- Modify: `frontend/src/pages/WorkoutTracker.jsx`
- Test: `count_calories_app/tests/test_react_api_parity.py`

- [ ] **Step 1: Add backend workout table endpoints**

Endpoints (matching existing Django template routes):
- `GET /api/react/workout-tables/` — list saved tables
- `POST /api/react/workout-tables/add/` — save workout table
- `DELETE /api/react/workout-tables/<id>/delete/` — delete table

- [ ] **Step 2: Write Django tests**
- [ ] **Step 3: Update workout.js with table API functions**
- [ ] **Step 4: Add workout table UI**

Spreadsheet-style grid:
- Table name input
- Editable grid with Exercise rows and Workout columns
- "Add Workout" column button, "Add Exercise" row button
- Per-exercise delete and "View Progress" icons
- Save/Load/Delete table actions
- List of saved tables below

- [ ] **Step 5: Build and commit**

---

### Task 12: Body Measurements — Dedicated React API

**Files:**
- Modify: `count_calories_app/views.py` (add CRUD endpoints)
- Modify: `count_calories_app/urls.py`
- Modify: `frontend/src/api/bodyMeasurements.js`
- Modify: `frontend/src/pages/BodyMeasurements.jsx`
- Test: `count_calories_app/tests/test_react_api_parity.py`

- [ ] **Step 1: Add backend CRUD endpoints**

```python
@require_http_methods(["POST"])
def api_add_body_measurement(request):
    data = json.loads(request.body)
    measurement = BodyMeasurement.objects.create(
        recorded_at=parse_datetime(data.get('recorded_at', timezone.now().isoformat())),
        neck=data.get('neck'), chest=data.get('chest'), belly=data.get('belly'),
        # ... all 14 measurement fields
        notes=data.get('notes', ''),
    )
    return JsonResponse({'success': True, 'id': measurement.id})

@require_http_methods(["PUT", "PATCH"])
def api_update_body_measurement(request, measurement_id):
    # Update measurement fields

@require_http_methods(["DELETE"])
def api_delete_body_measurement(request, measurement_id):
    # Delete measurement
```

- [ ] **Step 2: Write Django tests**
- [ ] **Step 3: Update bodyMeasurements.js to use React API endpoints**

Replace Django template endpoint calls with:
```javascript
add: async (data) => apiClient.post('/api/react/body-measurements/add/', data),
update: async (id, data) => apiClient.put(`/api/react/body-measurements/${id}/update/`, data),
delete: async (id) => apiClient.delete(`/api/react/body-measurements/${id}/delete/`),
```

- [ ] **Step 4: Update BodyMeasurements.jsx to use new API calls**
- [ ] **Step 5: Build and commit**

---

### Task 13: Analytics — Month Comparison

**Files:**
- Modify: `count_calories_app/views.py` (add API endpoint)
- Modify: `count_calories_app/urls.py`
- Modify: `frontend/src/api/analytics.js`
- Modify: `frontend/src/pages/Analytics.jsx`

- [ ] **Step 1: Add backend API endpoint**

```python
@require_http_methods(["GET"])
def api_month_compare(request):
    month_a = request.GET.get('month_a')  # Format: "2026-01"
    month_b = request.GET.get('month_b')  # Format: "2026-02"
    # Return comparison data: overview, macros, weight, unique foods, top foods
```

URL: `path('api/react/analytics/month-compare/', views.api_month_compare, name='api_month_compare')`

- [ ] **Step 2: Write Django test**
- [ ] **Step 3: Add API function in analytics.js**
- [ ] **Step 4: Add Month Comparison tab to Analytics page**

Tab navigation: Overview | Month Compare | Yearly Trends | Product Compare

Month Compare tab features:
- Two month dropdown selectors + Compare button
- Overview comparison cards (6 metrics side-by-side)
- Macro breakdown bars
- Weight comparison table
- Unique foods lists (Only in A, Only in B)
- Top foods comparison table

- [ ] **Step 5: Build and commit**

---

### Task 14: Analytics — Yearly Trends

**Files:**
- Modify: `count_calories_app/views.py` (add API endpoint)
- Modify: `count_calories_app/urls.py`
- Modify: `frontend/src/api/analytics.js`
- Modify: `frontend/src/pages/Analytics.jsx`

- [ ] **Step 1: Add backend API endpoint**

```python
@require_http_methods(["GET"])
def api_yearly_trends(request):
    year = request.GET.get('year')  # or 'last12'
    # Return monthly breakdown: days_logged, consistency, avg macros, weight delta, top food
```

URL: `path('api/react/analytics/yearly-trends/', views.api_yearly_trends, name='api_yearly_trends')`

- [ ] **Step 2: Write Django test**
- [ ] **Step 3: Add API function**
- [ ] **Step 4: Add Yearly Trends tab to Analytics page**

Features:
- Year selector (Last 12 Months, 2026, 2025, etc.)
- Summary cards (Days Logged, Total Calories, Total Protein, Most Consistent Month)
- Monthly Trends chart (Recharts bar+line chart)
- Month-by-month breakdown table

- [ ] **Step 5: Build and commit**

---

### Task 15: Analytics — Product Compare

**Files:**
- Modify: `frontend/src/api/analytics.js`
- Modify: `frontend/src/pages/Analytics.jsx`

- [ ] **Step 1: Add API function**

Uses existing `/api/react/search-foods/` to search products, then compares their nutrition data.

- [ ] **Step 2: Add Product Compare tab to Analytics page**

Features:
- 2-3 product search inputs with autocomplete
- Compare button
- Side-by-side nutrition comparison cards
- Bar chart comparing macros

- [ ] **Step 3: Build and commit**

---

### Task 16: Top Foods — Date Range & Sort Controls

**Files:**
- Modify: `frontend/src/pages/TopFoods.jsx`

- [ ] **Step 1: Add DateRangeFilter to Top Foods page**

Replace simple time range selector with full DateRangeFilter component (from Task 4).

- [ ] **Step 2: Add sort controls**

Sort buttons: Count, Name, Calories, Protein, Fat, Carbs.
Clicking toggles ascending/descending.
Pass `sort` param to API.

- [ ] **Step 3: Add summary statistics cards**

6 stat cards: Unique Foods, Times Eaten, Total Calories, Total Fat, Total Carbs, Total Protein.

- [ ] **Step 4: Build and commit**

---

### Task 18: Run All Tests & Final Build

**Files:**
- Test: All test files

- [ ] **Step 1: Run all Django tests**

Run: `python manage.py test count_calories_app -v 2`
Expected: All tests pass

- [ ] **Step 2: Run all React tests**

Run: `cd frontend && npx vitest run`
Expected: All tests pass

- [ ] **Step 3: Production build**

Run: `cd frontend && npm run build`
Expected: Build succeeds

- [ ] **Step 4: Playwright verification**

Use Playwright MCP to navigate through all React pages and verify features work.

- [ ] **Step 5: Final commit**

```bash
git add -A && git commit -m "feat(react): complete feature parity with Django template frontend"
```

---

## Execution Notes

### Dependencies
- Task 5 depends on Task 4 (charts need date range state from DateRangeFilter)
- Task 16 depends on Task 4 (reuses DateRangeFilter component)
- Tasks 11b, 11d depend on Task 11a (session CRUD must exist first)
- Tasks 13, 14, 15 all modify Analytics.jsx — must be sequential, NOT parallel

### Recommended execution order

**Phase 1 — Backend APIs (can be parallelized, workers append to views.py/urls.py):**
- Task 2 backend (copy day endpoint)
- Task 3 backend (meal template endpoints)
- Task 5 backend (hourly pattern endpoint)
- Task 7 backend (weight edit endpoint)
- Task 10 backend (running edit/delete endpoints)
- Tasks 11a-11d backend (workout CRUD endpoints)
- Task 12 backend (body measurements CRUD endpoints)
- Task 13 backend (month compare endpoint)
- Task 14 backend (yearly trends endpoint)

**Phase 2 — React frontend (sequential within groups):**
- Group A: Tasks 1 → 4 → 5 → 2 → 3 → 6 (Food Tracker, sequential — Task 4 before 5)
- Group B: Tasks 7 → 8 → 9 (Weight Tracker, sequential)
- Group C: Task 10 (Running, independent)
- Group D: Tasks 11a → 11b → 11c → 11d (Workout, sequential)
- Group E: Task 12 (Body Measurements, independent)
- Group F: Tasks 13 → 14 → 15 (Analytics tabs, MUST be sequential — all modify Analytics.jsx)
- Group G: Task 16 (Top Foods, depends on Task 4 completing first)

Groups B, C, D, E can run in parallel with each other.
Groups F and G must wait for Phase 1 and Task 4 to complete.

**Phase 3 — Final:**
- Task 17: Run all tests, build, Playwright verification

### Note on views.py/urls.py conflicts
When parallelizing backend work, each worker should append new view functions to the END of views.py and add URL entries at the end of the url list. This avoids merge conflicts.
