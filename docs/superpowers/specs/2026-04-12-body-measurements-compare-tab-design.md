# Body Measurements Compare Tab — Design Spec

**Date:** 2026-04-12

## Summary

Add a **Compare** tab to the Body Measurements Tracker on both the Django template frontend and the React SPA. The tab lets the user pick two snapshots of their body measurements and see a detailed comparison: what improved, what got worse, and by how much.

## User Requirements

1. **Compare modes** — a mode switcher with three options:
   - **Date vs Date**: pick any two individual measurement entries
   - **Week vs Week**: pick two calendar weeks (Mon–Sun)
   - **Period vs Period**: pick two custom date ranges

2. **Multi-entry strategy toggle** (for Week and Period modes): Latest / Average / First vs Last

3. **Results display** (in order top to bottom):
   - **Summary card**: weight change, total cm lost/gained, count of measurements improved vs worsened
   - **Measurement filter**: checkbox panel grouped by Core / Arms / Legs, plus a Weight toggle
   - **Side-by-side table**: one row per measurement, columns = Side A value | Side B value | Change (+/- cm, color-coded)
   - **Grouped bar chart**: two bars per measurement (Side A vs Side B)
   - **Delta chart**: one bar per measurement showing net change only (green = smaller, red = bigger)

4. **Both frontends**: Django template version (Bootstrap 5 + Chart.js) and React version (Tailwind v4 + Recharts)

## Architecture

### React SPA

**No new backend endpoints.** All data already available:
- Measurements: existing `/api/react/body-measurements/` (fetched by parent `BodyMeasurements.jsx`, passed as prop)
- Weight: existing `/api/react/weight-items/` (fetched by `CompareTab` on mount)

**New files:**
- `frontend/src/pages/BodyMeasurements/CompareTab.jsx` — main Compare tab component
- `frontend/src/pages/BodyMeasurements/compareUtils.js` — pure comparison logic (grouping, averaging, delta computation)

**Modified files:**
- `frontend/src/pages/BodyMeasurements.jsx` — add `compare` tab, render `<CompareTab measurements={measurements} />`

**Data flow:**
```
BodyMeasurements.jsx
  measurements[] (prop) ──────────────────────────┐
                                                   ▼
                                           CompareTab.jsx
                                             ├── weightItems[] (fetched on mount)
                                             ├── compareMode: date | week | period
                                             ├── strategy: latest | average | firstlast
                                             ├── sideA selector + sideB selector
                                             ├── enabledFields[] (checkbox state)
                                             ├── computeComparison() → {sideA, sideB, deltas, summary}
                                             └── renders:
                                                   SummaryCard
                                                   FieldFilter
                                                   ComparisonTable
                                                   BarChart (grouped)
                                                   BarChart (delta)
```

### Django Template

**No new views or URLs.** The existing `body_measurements_tracker.html` view already passes all measurements in context. Weight data is fetched via `fetch('/api/weight-data/')` in-page JS.

**Modified files:**
- `count_calories_app/templates/count_calories_app/body_measurements_tracker.html` — add Compare tab nav item and tab pane with vanilla JS + Chart.js

## Comparison Logic (`compareUtils.js` / inline JS)

```
resolveSnapshot(measurements, mode, selector, strategy):
  date mode:    find entry by date id
  week mode:    filter entries in ISO week, apply strategy
  period mode:  filter entries in [start, end], apply strategy

strategies:
  latest:     take entry with max date
  average:    mean of all numeric fields
  firstlast:  {first: min-date entry, last: max-date entry} → delta within period

computeDeltas(sideA, sideB):
  for each field: delta = sideB[field] - sideA[field]

computeSummary(deltas, weightDelta):
  totalCmLost = sum of negative deltas (circumference fields)
  improved = count of fields where delta < 0
  worsened = count of fields where delta > 0
```

## UI Layout (Compare Tab)

```
┌─────────────────────────────────────────────────────────┐
│  Mode: [Date vs Date] [Week vs Week] [Period vs Period]  │
│  Strategy: [Latest ▾]  (hidden in Date mode)            │
├────────────────────────┬────────────────────────────────┤
│  Side A picker         │  Side B picker                  │
│  (date / week / range) │  (date / week / range)         │
├─────────────────────────────────────────────────────────┤
│  [Compare] button                                        │
├─────────────────────────────────────────────────────────┤
│  SUMMARY CARD                                            │
│  Weight: -11.8 kg | Total lost: -24.5 cm | 9↓ 5↑        │
├─────────────────────────────────────────────────────────┤
│  FIELD FILTER  ☑ Weight  Core: ☑☑☑☑  Arms: ☑☑☑  Legs: ☑☑│
├─────────────────────────────────────────────────────────┤
│  COMPARISON TABLE                                        │
│  Field       │ Side A  │ Side B  │ Change               │
│  Belly       │ 98.0 cm │ 93.0 cm │ -5.0 ▼ (green)       │
│  Chest       │ 114 cm  │ 116 cm  │ +2.0 ▲ (red)         │
├─────────────────────────────────────────────────────────┤
│  BAR CHART (grouped — Side A vs Side B per measurement)  │
├─────────────────────────────────────────────────────────┤
│  DELTA CHART (net change per measurement, +/- bars)      │
└─────────────────────────────────────────────────────────┘
```

## Error / Edge Cases

- If no measurements exist for a selected date/week/period: show "No data for this selection"
- If a field is null on one side: show "—" in table, exclude from charts
- If only one measurement exists total: disable Week and Period modes, show informational message
- Weight: if no weight entries exist in range, show "—" for weight row

## Testing

- Django: existing test suite covers view/model layer — no new backend = no new Django tests needed
- React: Vitest unit tests for `compareUtils.js` (grouping, averaging, delta, summary logic)
