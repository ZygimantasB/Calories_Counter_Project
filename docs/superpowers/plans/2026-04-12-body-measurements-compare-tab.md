# Body Measurements Compare Tab Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Compare tab to the Body Measurements Tracker (both Django template and React SPA) where the user can compare any two snapshots of their measurements and see what changed.

**Architecture:** Client-side only — no new backend endpoints. React version uses already-fetched measurements prop + fetches weight from existing `/api/react/weight-items/`. Django template version receives all measurements serialized as JSON in context and fetches weight via `/api/weight-data/`. All comparison logic runs in the browser.

**Tech Stack:** React 18, Recharts, Tailwind CSS v4, Lucide icons, date-fns (React); Bootstrap 5, Chart.js, vanilla JS (Django template); Vitest + Testing Library (tests)

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `frontend/src/pages/BodyMeasurements/compareUtils.js` | **Create** | Pure functions: grouping, averaging, delta, summary computation |
| `frontend/src/pages/BodyMeasurements/CompareTab.jsx` | **Create** | Full Compare tab UI component |
| `frontend/src/pages/BodyMeasurements/index.jsx` | **Modify** | Add Compare tab nav entry + render CompareTab |
| `frontend/src/pages/BodyMeasurements/__tests__/compareUtils.test.js` | **Create** | Vitest unit tests for compareUtils |
| `count_calories_app/views.py` | **Modify** | Add `measurements_json` to context in `body_measurements_tracker` |
| `count_calories_app/templates/count_calories_app/body_measurements_tracker.html` | **Modify** | Add Compare tab nav + pane with Chart.js + vanilla JS |

> **Note on folder structure:** `BodyMeasurements.jsx` currently lives at `frontend/src/pages/BodyMeasurements.jsx`. Move it to `BodyMeasurements/index.jsx` so new files can live alongside it.

---

## Task 1: Restructure BodyMeasurements into a folder

**Files:**
- Rename: `frontend/src/pages/BodyMeasurements.jsx` → `frontend/src/pages/BodyMeasurements/index.jsx`

- [ ] **Step 1: Rename the file**

```bash
cd /mnt/samsung/Calories_Counter_Project/frontend
mkdir -p src/pages/BodyMeasurements
mv src/pages/BodyMeasurements.jsx src/pages/BodyMeasurements/index.jsx
mkdir -p src/pages/BodyMeasurements/__tests__
```

- [ ] **Step 2: Verify build still works**

Node resolves `import BodyMeasurements from './pages/BodyMeasurements'` to `index.jsx` automatically. Confirm:

```bash
npm run build 2>&1 | tail -10
```

Expected: build succeeds with no import errors.

- [ ] **Step 3: Commit**

```bash
cd /mnt/samsung/Calories_Counter_Project
git add -A
git commit -m "refactor(react): move BodyMeasurements.jsx into subfolder for Compare tab co-location"
```

---

## Task 2: Write compareUtils.js with tests (TDD)

Pure utility functions. No React, no imports from the project. These are the heart of the feature.

**Files:**
- Create: `frontend/src/pages/BodyMeasurements/__tests__/compareUtils.test.js`
- Create: `frontend/src/pages/BodyMeasurements/compareUtils.js`

### Spec for the utilities

```
MEASUREMENT_FIELDS = ['neck','chest','belly','butt','left_biceps','right_biceps',
  'left_triceps','right_triceps','left_forearm','right_forearm',
  'left_thigh','right_thigh','left_lower_leg','right_lower_leg']

getISOWeekKey(dateStr) → "2025-W17"  (ISO week number)

groupByWeek(measurements) → { "2025-W17": [entry, entry], ... }

resolveSnapshot(measurements, mode, selector, strategy):
  mode='date'   → selector is entry id (number) → returns that entry directly
  mode='week'   → selector is ISO week key "YYYY-Www"
                  strategy='latest'    → entry with max date in that week
                  strategy='average'   → averaged object across all entries in week
                  strategy='firstlast' → { first: entry, last: entry }
  mode='period' → selector is { start: ISO date string, end: ISO date string }
                  same strategy options as week mode

computeDeltas(sideA, sideB, fields) → { field: delta, ... }
  (sideB[field] - sideA[field], null if either is null)

computeSummary(deltas, weightA, weightB) →
  { weightChange, totalCmLost, totalCmGained, improved, worsened }
  totalCmLost = absolute value of sum of all negative deltas
  totalCmGained = sum of all positive deltas
  improved = count of fields where delta < 0
  worsened = count where delta > 0
```

- [ ] **Step 1: Write the failing tests**

Create `frontend/src/pages/BodyMeasurements/__tests__/compareUtils.test.js`:

```js
import { describe, it, expect } from 'vitest';
import {
  getISOWeekKey,
  groupByWeek,
  resolveSnapshot,
  computeDeltas,
  computeSummary,
  MEASUREMENT_FIELDS,
} from '../compareUtils.js';

const m1 = { id: 1, date: '2025-04-07T10:00:00', belly: 98, chest: 114, neck: null, butt: 110,
  left_biceps: 43, right_biceps: 43, left_triceps: 35, right_triceps: 35,
  left_forearm: 30, right_forearm: 30, left_thigh: 60, right_thigh: 60,
  left_lower_leg: 40, right_lower_leg: 40 };
const m2 = { id: 2, date: '2025-04-20T10:00:00', belly: 95, chest: 115.7, neck: null, butt: 108,
  left_biceps: 44.5, right_biceps: 44.5, left_triceps: 36, right_triceps: 36,
  left_forearm: 31, right_forearm: 31, left_thigh: 61, right_thigh: 61,
  left_lower_leg: 41, right_lower_leg: 41 };
const m3 = { id: 3, date: '2025-04-27T10:00:00', belly: 93, chest: 116, neck: 38, butt: 107,
  left_biceps: 45, right_biceps: 45, left_triceps: 37, right_triceps: 37,
  left_forearm: 32, right_forearm: 32, left_thigh: 62, right_thigh: 62,
  left_lower_leg: 42, right_lower_leg: 42 };

const measurements = [m3, m2, m1]; // newest first

describe('getISOWeekKey', () => {
  it('returns ISO week key for a date string', () => {
    expect(getISOWeekKey('2025-04-27T10:00:00')).toMatch(/^\d{4}-W\d{2}$/);
  });
  it('two dates in same week return the same key', () => {
    expect(getISOWeekKey('2025-04-21T00:00:00')).toBe(getISOWeekKey('2025-04-27T00:00:00'));
  });
  it('dates in different weeks return different keys', () => {
    expect(getISOWeekKey('2025-04-20T00:00:00')).not.toBe(getISOWeekKey('2025-04-27T00:00:00'));
  });
});

describe('groupByWeek', () => {
  it('groups measurements by ISO week', () => {
    const groups = groupByWeek(measurements);
    expect(Object.keys(groups).length).toBeGreaterThanOrEqual(2);
  });
});

describe('resolveSnapshot - date mode', () => {
  it('returns the entry matching the given id', () => {
    expect(resolveSnapshot(measurements, 'date', 2, 'latest')).toEqual(m2);
  });
  it('returns null for unknown id', () => {
    expect(resolveSnapshot(measurements, 'date', 999, 'latest')).toBeNull();
  });
});

describe('resolveSnapshot - week mode', () => {
  it('latest strategy returns the most recent entry in the week', () => {
    const weekKey = getISOWeekKey(m3.date);
    const result = resolveSnapshot(measurements, 'week', weekKey, 'latest');
    expect(result.id).toBe(m3.id);
  });
  it('average strategy returns averaged values', () => {
    const sameDayM = { ...m2, id: 99, date: m3.date };
    const weekKey = getISOWeekKey(m3.date);
    const result = resolveSnapshot([m3, sameDayM], 'week', weekKey, 'average');
    expect(result.belly).toBeCloseTo(94, 1);
  });
  it('firstlast strategy returns object with first and last keys', () => {
    const weekKey = getISOWeekKey(m3.date);
    const result = resolveSnapshot(measurements, 'week', weekKey, 'firstlast');
    expect(result).toHaveProperty('first');
    expect(result).toHaveProperty('last');
  });
  it('returns null for a week with no entries', () => {
    expect(resolveSnapshot(measurements, 'week', '2020-W01', 'latest')).toBeNull();
  });
});

describe('resolveSnapshot - period mode', () => {
  it('latest strategy returns last entry in range', () => {
    const result = resolveSnapshot(measurements, 'period', { start: '2025-04-01', end: '2025-04-30' }, 'latest');
    expect(result.id).toBe(m3.id);
  });
  it('returns null for an empty range', () => {
    expect(resolveSnapshot(measurements, 'period', { start: '2020-01-01', end: '2020-01-31' }, 'latest')).toBeNull();
  });
});

describe('computeDeltas', () => {
  it('computes correct deltas between two snapshots', () => {
    const deltas = computeDeltas(m1, m2, MEASUREMENT_FIELDS);
    expect(deltas.belly).toBeCloseTo(-3, 1);
    expect(deltas.chest).toBeCloseTo(1.7, 1);
  });
  it('returns null delta when either side is null', () => {
    expect(computeDeltas(m1, m2, ['neck']).neck).toBeNull();
  });
});

describe('computeSummary', () => {
  it('computes weight change and cm totals', () => {
    const deltas = computeDeltas(m1, m3, MEASUREMENT_FIELDS);
    const summary = computeSummary(deltas, 113.6, 101.82);
    expect(summary.weightChange).toBeCloseTo(-11.78, 1);
    expect(summary.totalCmLost).toBeGreaterThan(0);
    expect(summary.improved).toBeGreaterThan(0);
  });
  it('handles null weight gracefully', () => {
    const deltas = computeDeltas(m1, m2, MEASUREMENT_FIELDS);
    expect(computeSummary(deltas, null, null).weightChange).toBeNull();
  });
});
```

- [ ] **Step 2: Run tests — confirm failure**

```bash
cd /mnt/samsung/Calories_Counter_Project/frontend
npm test -- --run src/pages/BodyMeasurements/__tests__/compareUtils.test.js 2>&1 | tail -10
```

Expected: FAIL — `compareUtils.js` does not exist.

- [ ] **Step 3: Implement compareUtils.js**

Create `frontend/src/pages/BodyMeasurements/compareUtils.js`:

```js
import { parseISO, getISOWeek, getISOWeekYear, isWithinInterval, startOfDay, endOfDay } from 'date-fns';

export const MEASUREMENT_FIELDS = [
  'neck', 'chest', 'belly', 'butt',
  'left_biceps', 'right_biceps', 'left_triceps', 'right_triceps',
  'left_forearm', 'right_forearm',
  'left_thigh', 'right_thigh', 'left_lower_leg', 'right_lower_leg',
];

export function getISOWeekKey(dateStr) {
  const d = parseISO(dateStr);
  const week = String(getISOWeek(d)).padStart(2, '0');
  return `${getISOWeekYear(d)}-W${week}`;
}

export function groupByWeek(measurements) {
  const groups = {};
  for (const m of measurements) {
    if (!m.date) continue;
    const key = getISOWeekKey(m.date);
    if (!groups[key]) groups[key] = [];
    groups[key].push(m);
  }
  return groups;
}

function pickLatest(entries) {
  return entries.reduce((best, e) => !best || e.date > best.date ? e : best, null);
}

function pickFirst(entries) {
  return entries.reduce((best, e) => !best || e.date < best.date ? e : best, null);
}

function computeAverage(entries) {
  if (!entries.length) return null;
  const averaged = { date: pickLatest(entries).date };
  for (const field of MEASUREMENT_FIELDS) {
    const vals = entries.map(e => e[field]).filter(v => v != null);
    averaged[field] = vals.length ? vals.reduce((a, b) => a + b, 0) / vals.length : null;
  }
  return averaged;
}

export function resolveSnapshot(measurements, mode, selector, strategy) {
  if (mode === 'date') {
    return measurements.find(m => m.id === selector) || null;
  }

  let entries = [];

  if (mode === 'week') {
    entries = measurements.filter(m => m.date && getISOWeekKey(m.date) === selector);
  }

  if (mode === 'period') {
    const { start, end } = selector;
    entries = measurements.filter(m => {
      if (!m.date) return false;
      return isWithinInterval(parseISO(m.date), {
        start: startOfDay(parseISO(start)),
        end: endOfDay(parseISO(end)),
      });
    });
  }

  if (!entries.length) return null;
  if (strategy === 'latest') return pickLatest(entries);
  if (strategy === 'average') return computeAverage(entries);
  if (strategy === 'firstlast') return { first: pickFirst(entries), last: pickLatest(entries) };
  return pickLatest(entries);
}

export function computeDeltas(sideA, sideB, fields) {
  const deltas = {};
  for (const field of fields) {
    const a = sideA?.[field] ?? null;
    const b = sideB?.[field] ?? null;
    deltas[field] = a != null && b != null ? parseFloat((b - a).toFixed(2)) : null;
  }
  return deltas;
}

export function computeSummary(deltas, weightA, weightB) {
  const values = Object.values(deltas).filter(v => v != null);
  const improved = values.filter(v => v < 0).length;
  const worsened = values.filter(v => v > 0).length;
  const totalCmLost = parseFloat(
    Math.abs(values.filter(v => v < 0).reduce((s, v) => s + v, 0)).toFixed(2)
  );
  const totalCmGained = parseFloat(
    values.filter(v => v > 0).reduce((s, v) => s + v, 0).toFixed(2)
  );
  const weightChange = weightA != null && weightB != null
    ? parseFloat((weightB - weightA).toFixed(2)) : null;
  return { weightChange, totalCmLost, totalCmGained, improved, worsened };
}
```

- [ ] **Step 4: Run tests — confirm all pass**

```bash
cd /mnt/samsung/Calories_Counter_Project/frontend
npm test -- --run src/pages/BodyMeasurements/__tests__/compareUtils.test.js 2>&1 | tail -10
```

Expected: All tests PASS.

- [ ] **Step 5: Commit**

```bash
cd /mnt/samsung/Calories_Counter_Project
git add frontend/src/pages/BodyMeasurements/compareUtils.js \
        frontend/src/pages/BodyMeasurements/__tests__/compareUtils.test.js
git commit -m "feat(react): add compareUtils with full test coverage"
```

---

## Task 3: Build CompareTab.jsx (React)

**Files:**
- Create: `frontend/src/pages/BodyMeasurements/CompareTab.jsx`

This component receives `measurements` (all entries, newest first) as a prop. It fetches weight from the existing `weightApi` on mount. All comparison state is local.

**Component structure:**

```
CompareTab
  props: measurements[]
  state: mode, strategy, selectorA, selectorB, result, weightItems, enabled{}
  
  Sub-components (defined in same file):
    DatePicker       — <select> listing all measurement entries by date
    WeekPicker       — <select> listing ISO week keys with entry counts
    PeriodPicker     — two <input type="date"> forming a range
    SummaryCard      — 4 stat tiles: weight change, total cm lost, improved count, worsened count
    FieldFilter      — checkbox panel grouped by Core/Arms/Legs + Weight toggle
    ComparisonTable  — <table> with Side A | Side B | Change columns
    grouped BarChart — Recharts BarChart with two Bar components (sideA color vs sideB color)
    delta BarChart   — Recharts BarChart with one Bar, Cell color per sign of delta, ReferenceLine at y=0
```

**handleCompare logic:**
1. Call `resolveSnapshot(measurements, mode, selectorA, strategy)` → snapA
2. Call `resolveSnapshot(measurements, mode, selectorB, strategy)` → snapB
3. For `firstlast` strategy: use `snapA.last` as Side A and `snapB.last` as Side B — this compares *where each period ended*, not progress within a period. The `.first` property is available for context but is not used in the comparison values.
4. Call `computeDeltas(resolvedA, resolvedB, MEASUREMENT_FIELDS)` → deltas
5. Find nearest weight entries by matching the `date` substring (YYYY-MM-DD) of each resolved entry against `weightItems`
6. Call `computeSummary(deltas, weightA, weightB)` → summary
7. Store all into `result` state — triggers re-render

**Import list for CompareTab.jsx:**
```js
import { useState, useEffect, useMemo } from 'react';
import { format, parseISO, startOfISOWeek, endOfISOWeek } from 'date-fns';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend, ReferenceLine, Cell } from 'recharts';
import { GitCompare, Loader2 } from 'lucide-react';
import { Card, Button } from '../../components/ui';
import { weightApi } from '../../api';
import { MEASUREMENT_FIELDS, getISOWeekKey, groupByWeek,
  resolveSnapshot, computeDeltas, computeSummary } from './compareUtils.js';
```

- [ ] **Step 1: Implement CompareTab.jsx** following the structure above. Keep all sub-components in the same file. The component should:
  - Fetch weight items on mount (`weightApi.getWeightItems()`)
  - Show a "need 2+ measurements" empty state if `measurements.length < 2`
  - Only show the strategy row when mode is not `date`
  - Show the appropriate picker pair based on mode
  - Disable the Compare button when either selector is empty
  - After comparison, show: SummaryCard, FieldFilter, ComparisonTable, grouped BarChart, delta BarChart in sequence

- [ ] **Step 2: Verify build**

```bash
cd /mnt/samsung/Calories_Counter_Project/frontend
npm run build 2>&1 | tail -15
```

Expected: succeeds with no errors.

- [ ] **Step 3: Commit**

```bash
cd /mnt/samsung/Calories_Counter_Project
git add frontend/src/pages/BodyMeasurements/CompareTab.jsx
git commit -m "feat(react): add CompareTab component"
```

---

## Task 4: Wire Compare tab into BodyMeasurements/index.jsx

**Files:**
- Modify: `frontend/src/pages/BodyMeasurements/index.jsx`

- [ ] **Step 1: Add GitCompare to lucide-react import** (top of file, add `GitCompare` to the existing import)

- [ ] **Step 2: Add CompareTab import** after existing page imports:

```js
import CompareTab from './CompareTab.jsx';
```

- [ ] **Step 3: Add Compare to the tab nav array** (find the tabs array around line 448):

```js
{ id: 'compare', label: 'Compare', icon: GitCompare },
```

Add after the existing `{ id: 'add', label: 'Add New', icon: Plus }` entry.

- [ ] **Step 4: Add Compare tab panel** after the existing `{activeTab === 'add' && ...}` block:

```jsx
{activeTab === 'compare' && (
  <CompareTab measurements={measurements} />
)}
```

- [ ] **Step 5: Build and smoke-test**

```bash
cd /mnt/samsung/Calories_Counter_Project/frontend && npm run build 2>&1 | tail -10
```

Navigate to `http://localhost:8000/app/body-measurements/` → Click **Compare** tab → verify mode switcher, pickers, and results all render correctly.

- [ ] **Step 6: Commit**

```bash
cd /mnt/samsung/Calories_Counter_Project
git add frontend/src/pages/BodyMeasurements/index.jsx
git commit -m "feat(react): wire Compare tab into BodyMeasurements page"
```

---

## Task 5: Add measurements_json to Django view context

**Files:**
- Modify: `count_calories_app/views.py` — `body_measurements_tracker` function (around line 2133)

- [ ] **Step 1: Add JSON serialization to the view**

In `body_measurements_tracker`, before the `return render(...)` call, add the following. Note: `json` is already imported at the top of `views.py` — use it directly, do not add another import:

```python
measurements_json = json.dumps([
    {
        'id': m.id,
        'date': m.date.isoformat() if m.date else None,
        'neck': float(m.neck) if m.neck else None,
        'chest': float(m.chest) if m.chest else None,
        'belly': float(m.belly) if m.belly else None,
        'butt': float(m.butt) if m.butt else None,
        'left_biceps': float(m.left_biceps) if m.left_biceps else None,
        'right_biceps': float(m.right_biceps) if m.right_biceps else None,
        'left_triceps': float(m.left_triceps) if m.left_triceps else None,
        'right_triceps': float(m.right_triceps) if m.right_triceps else None,
        'left_forearm': float(m.left_forearm) if m.left_forearm else None,
        'right_forearm': float(m.right_forearm) if m.right_forearm else None,
        'left_thigh': float(m.left_thigh) if m.left_thigh else None,
        'right_thigh': float(m.right_thigh) if m.right_thigh else None,
        'left_lower_leg': float(m.left_lower_leg) if m.left_lower_leg else None,
        'right_lower_leg': float(m.right_lower_leg) if m.right_lower_leg else None,
    }
    for m in measurements
])
```

Add `'measurements_json': measurements_json` to the context dict passed to `render()`.

- [ ] **Step 2: Run Django tests**

```bash
cd /mnt/samsung/Calories_Counter_Project
source .venv/bin/activate
python manage.py test count_calories_app.tests.test_views -v 1 2>&1 | tail -10
```

Expected: All existing tests pass.

- [ ] **Step 3: Commit**

```bash
git add count_calories_app/views.py
git commit -m "feat(django): expose measurements_json in body_measurements_tracker context"
```

---

## Task 6: Add Compare tab to Django template

**Files:**
- Modify: `count_calories_app/templates/count_calories_app/body_measurements_tracker.html`

The template uses Bootstrap 5 tabs + Chart.js. All dynamic content must be built using DOM methods (createElement, textContent, appendChild) — never string-concatenated HTML set via property assignment.

- [ ] **Step 1: Add Compare tab nav item**

Find the `</ul>` closing the tab nav (after line 143). Insert before it:

```html
      <li class="nav-item" role="presentation">
        <button class="nav-link" id="compare-tab" data-bs-toggle="tab"
          data-bs-target="#compare" type="button" role="tab"
          aria-controls="compare" aria-selected="false">
          <i class="fas fa-exchange-alt me-2"></i>Compare
        </button>
      </li>
```

- [ ] **Step 2: Add Compare tab pane HTML**

Find the closing `</div>` of the `tab-content` div (after the Add New pane ends, around line 1270). Insert the Compare pane before it:

```html
      <!-- Compare Tab -->
      <div class="tab-pane fade" id="compare" role="tabpanel" aria-labelledby="compare-tab">
        <div class="card mb-4">
          <div class="card-header text-white">
            <h2 class="h4 mb-0"><i class="fas fa-exchange-alt me-2"></i>Compare Measurements</h2>
          </div>
          <div class="card-body">

            <!-- Mode -->
            <div class="mb-3">
              <div class="btn-group" role="group">
                <input type="radio" class="btn-check" name="compareMode" id="modeDate" value="date" autocomplete="off" checked>
                <label class="btn btn-outline-success" for="modeDate">Date vs Date</label>
                <input type="radio" class="btn-check" name="compareMode" id="modeWeek" value="week" autocomplete="off">
                <label class="btn btn-outline-success" for="modeWeek">Week vs Week</label>
                <input type="radio" class="btn-check" name="compareMode" id="modePeriod" value="period" autocomplete="off">
                <label class="btn btn-outline-success" for="modePeriod">Period vs Period</label>
              </div>
            </div>

            <!-- Strategy (hidden in date mode) -->
            <div class="mb-3" id="strategyRow" style="display:none">
              <span class="form-label text-muted small me-2">Strategy:</span>
              <div class="btn-group btn-group-sm" role="group">
                <input type="radio" class="btn-check" name="compareStrategy" id="stratLatest" value="latest" autocomplete="off" checked>
                <label class="btn btn-outline-secondary" for="stratLatest">Latest entry</label>
                <input type="radio" class="btn-check" name="compareStrategy" id="stratAverage" value="average" autocomplete="off">
                <label class="btn btn-outline-secondary" for="stratAverage">Average</label>
                <input type="radio" class="btn-check" name="compareStrategy" id="stratFirstLast" value="firstlast" autocomplete="off">
                <label class="btn btn-outline-secondary" for="stratFirstLast">First vs Last</label>
              </div>
            </div>

            <!-- Date selectors -->
            <div id="dateSelectors" class="row mb-3">
              <div class="col-md-5">
                <label class="form-label small text-muted">Side A</label>
                <select class="form-select" id="sideADate"></select>
              </div>
              <div class="col-md-5">
                <label class="form-label small text-muted">Side B</label>
                <select class="form-select" id="sideBDate"></select>
              </div>
            </div>

            <!-- Week selectors -->
            <div id="weekSelectors" class="row mb-3" style="display:none">
              <div class="col-md-5">
                <label class="form-label small text-muted">Side A (Week)</label>
                <select class="form-select" id="sideAWeek"></select>
              </div>
              <div class="col-md-5">
                <label class="form-label small text-muted">Side B (Week)</label>
                <select class="form-select" id="sideBWeek"></select>
              </div>
            </div>

            <!-- Period selectors -->
            <div id="periodSelectors" class="row mb-3" style="display:none">
              <div class="col-md-5">
                <label class="form-label small text-muted">Period A</label>
                <div class="d-flex gap-2 align-items-center">
                  <input type="date" class="form-control" id="periodAStart">
                  <span>to</span>
                  <input type="date" class="form-control" id="periodAEnd">
                </div>
              </div>
              <div class="col-md-5">
                <label class="form-label small text-muted">Period B</label>
                <div class="d-flex gap-2 align-items-center">
                  <input type="date" class="form-control" id="periodBStart">
                  <span>to</span>
                  <input type="date" class="form-control" id="periodBEnd">
                </div>
              </div>
            </div>

            <button class="btn btn-success mb-4" id="compareBtn">
              <i class="fas fa-exchange-alt me-2"></i>Compare
            </button>

            <!-- Results (hidden until comparison runs) -->
            <div id="compareResults" style="display:none">
              <div class="row mb-4" id="compareSummaryRow"></div>

              <!-- Field filter checkboxes built by JS -->
              <div class="card mb-3 p-3" id="compareFieldFilter"></div>

              <!-- Comparison table -->
              <div class="card mb-4">
                <div class="card-body p-0">
                  <table class="table table-hover mb-0">
                    <thead class="table-dark">
                      <tr>
                        <th>Measurement</th>
                        <th class="text-end" id="colLabelA">Side A</th>
                        <th class="text-end" id="colLabelB">Side B</th>
                        <th class="text-end">Change</th>
                      </tr>
                    </thead>
                    <tbody id="compareTableBody"></tbody>
                  </table>
                </div>
              </div>

              <!-- Bar chart -->
              <div class="card mb-4">
                <div class="card-header"><h5 class="mb-0">Side-by-Side Bar Chart</h5></div>
                <div class="card-body" style="height:360px">
                  <canvas id="compareBarCanvas"></canvas>
                </div>
              </div>

              <!-- Delta chart -->
              <div class="card mb-4">
                <div class="card-header"><h5 class="mb-0">Delta Chart (Net Change)</h5></div>
                <div class="card-body" style="height:360px">
                  <canvas id="compareDeltaCanvas"></canvas>
                </div>
              </div>
            </div>

          </div>
        </div>
      </div>
      <!-- End Compare Tab -->
```

- [ ] **Step 3: Add Compare JS block**

At the very bottom of the `<script>` block (before `</script>`), add the Compare tab JavaScript. The JS must follow these security rules:
- Parse `measurements_json` from context using `JSON.parse('{{ measurements_json|escapejs }}')`
- Build all DOM content (summary cards, table rows, filter checkboxes) using `document.createElement` + `node.textContent` — **never build HTML strings for assignment**
- Chart labels and data use numeric values only, no user-controlled strings in chart config

The JS implements the same logic as `compareUtils.js` in vanilla JS:
- `getISOWeekKey(dateStr)` using pure Date math (no date-fns available)
- `groupByWeek(measurements)`
- `resolveSnapshot(mode, selector, strategy)` — same branching as the React version
- `computeDeltas(sideA, sideB)` — same as React version
- `findWeightNear(snap)` — matches snap date substring against fetched weight items
- `renderSummary(summary)` — creates 4 stat cards using createElement, sets textContent for all values
- `renderTable(sideA, sideB, deltas, enabledFields, showWeight)` — creates `<tr>`/`<td>` nodes via createElement, sets textContent for cell values
- `renderFieldFilter()` — creates checkbox inputs + labels via createElement
- `renderCharts(sideA, sideB, deltas, labelA, labelB, fields)` — creates Chart.js bar and delta charts using canvas elements already present in HTML

**Weight fetch:** On Compare tab shown (via `shown.bs.tab`), fetch `{% url "weight_data" %}` and store the result.

**Mode switching:** `input[name="compareMode"]` change event shows/hides the appropriate selector divs and the strategy row.

**Compare button click:** Reads selectors, calls resolveSnapshot for each side, computes deltas and summary, then calls render functions in sequence, sets `compareResults` display to block.

**Field filter changes:** Re-render just the table and charts without re-running the comparison.

- [ ] **Step 4: Verify weight URL name**

```bash
grep -n "weight_data\|weight-data" /mnt/samsung/Calories_Counter_Project/count_calories_app/urls.py | head -5
```

Use the correct name in the `{% url %}` tag in the JS fetch call.

- [ ] **Step 5: Smoke-test the Django template**

Navigate to `http://localhost:8000/body-measurements/` → Compare tab → select two dates → click Compare. Verify summary cards, table, and both charts appear.

- [ ] **Step 6: Commit**

```bash
cd /mnt/samsung/Calories_Counter_Project
git add count_calories_app/templates/count_calories_app/body_measurements_tracker.html
git commit -m "feat(django-template): add Compare tab to body measurements tracker"
```

---

## Task 7: Full test suite and final verification

- [ ] **Step 1: Django tests**

```bash
cd /mnt/samsung/Calories_Counter_Project
source .venv/bin/activate
python manage.py test count_calories_app -v 1 2>&1 | tail -10
```

Expected: `OK`

- [ ] **Step 2: React tests**

```bash
cd /mnt/samsung/Calories_Counter_Project/frontend
npm test -- --run 2>&1 | tail -15
```

Expected: All tests pass including compareUtils suite.

- [ ] **Step 3: Production build**

```bash
npm run build 2>&1 | tail -10
```

Expected: Build succeeds.

- [ ] **Step 4: Final commit if anything remains uncommitted**

```bash
cd /mnt/samsung/Calories_Counter_Project
git status
git add -A && git commit -m "chore: finalize Compare tab implementation" || echo "nothing to commit"
```
