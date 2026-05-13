# Trends — Add "All Time" View

**Date:** 2026-05-13
**Page affected:** `/analytics/trends/`
**Status:** Approved, ready for implementation

## Background

The Trends page (`count_calories_app/templates/count_calories_app/month_trends.html`,
view at `count_calories_app/views.py:5440`) currently offers two view modes:

- **Last 12 Months** — rolling 12-month window ending in the current month
- **A specific calendar year** — Jan–Dec of any year with logged data

Both modes display data at **monthly granularity** (one bar per month) in the
main chart and one row per month in the breakdown table.

The user wants a third option that spans the **entire logging history** — every
month from the first `FoodItem` entry up to the current month — so they are not
limited to either a 12-month window or a single year.

## Goals

1. Add an **"All Time"** button to the existing button row.
2. When selected, the chart and table show every month from the first entry
   through the current month, in chronological order, at **monthly granularity**
   (one bar / one row per month).
3. Rename the page title and navigation tab from **"Yearly Trends"** to
   **"Trends"** (since the view is no longer year-bound).

## Non-Goals

- No new chart types, granularities (daily/weekly/quarterly), or custom date
  ranges. Only the "All Time" mode is being added.
- No changes to the summary cards, chart toggles, or per-month table columns —
  they already adapt to whatever month list the view supplies.
- No new API endpoints.

## Design

### Backend (`count_calories_app/views.py`, `month_trends` view)

The view already accepts `mode` from the query string with values `last12`
(default) and `year`. Add a third value: `all`.

The view currently computes `first_entry` (first `FoodItem.consumed_at`) and
`first_year` for the available-years dropdown. Reuse this:

```python
if mode == 'all':
    # Every month from the first FoodItem up through the current month
    months_to_analyze = []
    if first_entry:
        y, m = first_entry.year, first_entry.month
        while (y, m) <= (now.year, now.month):
            months_to_analyze.append((y, m))
            m += 1
            if m == 13:
                m = 1
                y += 1
    else:
        # No entries yet — fall back to just the current month
        months_to_analyze = [(now.year, now.month)]
elif mode == 'year':
    months_to_analyze = [(selected_year, m) for m in range(1, 13)]
else:  # last12 (default)
    # ... existing rolling 12-month logic, unchanged
```

Everything downstream (per-month aggregation loop, `monthly_data`,
`mark_best_worst`, `summary`, `chart_data` JSON) is already driven by
`months_to_analyze` and requires **no further changes**.

### Frontend (`count_calories_app/templates/count_calories_app/month_trends.html`)

1. **Add the "All Time" button** inside the existing `<div class="btn-group ...">`
   block at lines 80–91, placed **before** "Last 12 Months":

   ```html
   <a href="?mode=all"
      class="btn btn-sm {% if mode == 'all' %}btn-primary{% else %}btn-outline-primary{% endif %}">
     All Time
   </a>
   ```

2. **Rename page title** at line 4: `{% block title %}Trends{% endblock %}`.

3. **Rename navigation tab label** at line 64: `Yearly Trends` → `Trends`.
   The same tab label appears in these files — update each occurrence so the
   tab name stays consistent across pages:
   - `templates/includes/navbar.html`
   - `count_calories_app/templates/count_calories_app/analytics.html`
   - `count_calories_app/templates/count_calories_app/month_compare.html`
   - `count_calories_app/templates/count_calories_app/product_compare.html`

4. **Page header** at line 48 (`<h1>Analytics & Insights</h1>`) — no change.

### Edge Cases

| Case | Behavior |
|------|----------|
| Database has no `FoodItem` entries | `months_to_analyze` falls back to `[(now.year, now.month)]` — single empty month, summary card section hides itself via `{% if summary.months_with_data %}` (already implemented). |
| First entry is in the current month | Single-month All Time view — works fine, same as the empty-database fallback. |
| Many months (e.g. 30+) | Chart.js handles arbitrary-length datasets; the breakdown table just gets longer. No performance concern at expected data volumes (one query per month, all indexed by `consumed_at`). |
| User has gaps (months with zero entries) in their history | Already handled: months with no data render as `—` cells and are excluded from best/worst highlighting via the `has_data` flag. |

## Testing

Existing tests for `month_trends` live in
`count_calories_app/tests/test_views.py`. Add tests covering:

1. `GET /analytics/trends/?mode=all` returns 200 and the template renders.
2. With multi-year seeded data (e.g. entries in 2024 and 2026), the response
   context contains `monthly_data` spanning from the earliest entry's month
   through the current month, with no gaps.
3. With no `FoodItem` rows in the database, `?mode=all` falls back to a single
   current-month entry and does not crash.
4. The "All Time" button is present in the rendered HTML and is highlighted
   (`btn-primary`) when `mode=all`.

No frontend (React) tests are affected — this page is Django-template-only.

## Files Touched

- `count_calories_app/views.py` — extend `month_trends` with the `all` branch.
- `count_calories_app/templates/count_calories_app/month_trends.html` — add
  button, rename title and tab label.
- `templates/includes/navbar.html` — rename "Yearly Trends" tab to "Trends".
- `count_calories_app/templates/count_calories_app/analytics.html` — rename tab.
- `count_calories_app/templates/count_calories_app/month_compare.html` — rename tab.
- `count_calories_app/templates/count_calories_app/product_compare.html` — rename tab.
- `count_calories_app/tests/test_views.py` — add the test cases above.
