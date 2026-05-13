# Trends "All Time" View — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an "All Time" view mode to `/analytics/trends/` that displays every month from the user's first `FoodItem` entry through the current month.

**Architecture:** Extend the existing `month_trends` view in `count_calories_app/views.py` with a third `mode` value (`all`) alongside the existing `last12` and `year`. The downstream aggregation, summary, and chart-JSON code already iterate over a `months_to_analyze` list and require no further changes. Add an "All Time" button to the template's mode selector and rename the page/tab label from "Yearly Trends" to "Trends".

**Tech Stack:** Django 5.2 templates, Python 3.12, Chart.js (existing), Django `TestCase`.

**Spec:** `docs/superpowers/specs/2026-05-13-trends-all-time-view-design.md`

---

## File Structure

**Modify:**
- `count_calories_app/views.py` — extend `month_trends` (around line 5440–5470) with the `all` branch.
- `count_calories_app/templates/count_calories_app/month_trends.html` — add button (line 80–91), rename title (line 4), rename tab (line 64).
- `templates/includes/navbar.html` — rename "Yearly Trends" → "Trends" on line 56.
- `count_calories_app/templates/count_calories_app/analytics.html` — rename tab on line 147.
- `count_calories_app/templates/count_calories_app/month_compare.html` — rename tab on line 106.
- `count_calories_app/templates/count_calories_app/product_compare.html` — rename tab on line 97.

**Create (append):**
- `count_calories_app/tests/test_views.py` — append a new `MonthTrendsViewTestCase` class at the end of the file.

---

## Task 1: Add backend `mode='all'` branch with TDD

**Files:**
- Modify: `count_calories_app/views.py` (function `month_trends`, lines ~5440–5470)
- Test: `count_calories_app/tests/test_views.py` (new class at end of file)

- [ ] **Step 1: Write failing tests**

Append the following class to the END of `count_calories_app/tests/test_views.py`:

```python
class MonthTrendsViewTestCase(TestCase):
    """Tests for the /analytics/trends/ page (month_trends view)."""

    def setUp(self):
        self.client = Client()
        self.url = reverse('month_trends')
        self.now = timezone.now()

    def test_default_mode_returns_200(self):
        """Default (last12) mode renders correctly."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'count_calories_app/month_trends.html')

    def test_all_mode_returns_200(self):
        """?mode=all returns 200."""
        response = self.client.get(self.url, {'mode': 'all'})
        self.assertEqual(response.status_code, 200)

    def test_all_mode_context_mode_value(self):
        """?mode=all puts 'all' in the template context so the button can highlight."""
        response = self.client.get(self.url, {'mode': 'all'})
        self.assertEqual(response.context['mode'], 'all')

    def test_all_mode_with_no_data_falls_back_to_current_month(self):
        """Empty database → All Time view shows just the current month, doesn't crash."""
        response = self.client.get(self.url, {'mode': 'all'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['monthly_data']), 1)
        self.assertEqual(response.context['monthly_data'][0]['year'], self.now.year)
        self.assertEqual(response.context['monthly_data'][0]['month'], self.now.month)

    def test_all_mode_spans_from_first_entry_to_current_month(self):
        """With entries spanning multiple months, All Time covers every month inclusive."""
        # Seed an entry 3 months ago
        three_months_ago = self.now - timedelta(days=95)
        FoodItem.objects.create(
            product_name='Old Food',
            calories=Decimal('400'),
            protein=Decimal('30'),
            carbohydrates=Decimal('40'),
            fat=Decimal('10'),
            consumed_at=three_months_ago,
        )

        response = self.client.get(self.url, {'mode': 'all'})
        monthly_data = response.context['monthly_data']

        # First entry should be the month of the seeded entry
        self.assertEqual(monthly_data[0]['year'], three_months_ago.year)
        self.assertEqual(monthly_data[0]['month'], three_months_ago.month)

        # Last entry should be the current month
        self.assertEqual(monthly_data[-1]['year'], self.now.year)
        self.assertEqual(monthly_data[-1]['month'], self.now.month)

        # The seeded month should be marked as having data
        self.assertTrue(monthly_data[0]['has_data'])

    def test_all_mode_no_month_gaps(self):
        """All Time produces a contiguous month sequence (no gaps even if some months are empty)."""
        # Seed entries in two non-adjacent months: 4 months ago and now
        four_months_ago = self.now - timedelta(days=125)
        FoodItem.objects.create(
            product_name='Old',
            calories=Decimal('500'),
            protein=Decimal('20'),
            carbohydrates=Decimal('60'),
            fat=Decimal('15'),
            consumed_at=four_months_ago,
        )
        FoodItem.objects.create(
            product_name='Now',
            calories=Decimal('600'),
            protein=Decimal('25'),
            carbohydrates=Decimal('70'),
            fat=Decimal('18'),
            consumed_at=self.now,
        )

        response = self.client.get(self.url, {'mode': 'all'})
        monthly_data = response.context['monthly_data']

        # Walk through monthly_data and verify each entry is exactly one month after the previous
        for i in range(1, len(monthly_data)):
            prev_y, prev_m = monthly_data[i - 1]['year'], monthly_data[i - 1]['month']
            cur_y, cur_m = monthly_data[i]['year'], monthly_data[i]['month']
            expected_m = prev_m + 1
            expected_y = prev_y
            if expected_m == 13:
                expected_m = 1
                expected_y += 1
            self.assertEqual(
                (cur_y, cur_m), (expected_y, expected_m),
                f"Gap detected between {(prev_y, prev_m)} and {(cur_y, cur_m)}",
            )
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python manage.py test count_calories_app.tests.test_views.MonthTrendsViewTestCase -v 2`

Expected: `test_default_mode_returns_200`, `test_all_mode_returns_200`, `test_all_mode_context_mode_value` PASS (the route already exists; passing `mode=all` is accepted but currently falls into the `last12` branch).

`test_all_mode_with_no_data_falls_back_to_current_month` FAILS — `monthly_data` will have 12 entries (last12 fallback), not 1.

`test_all_mode_spans_from_first_entry_to_current_month` FAILS — `monthly_data` will be 12 entries ending at current month but starting 11 months back, not at the seeded entry.

`test_all_mode_no_month_gaps` PASSES (the existing `last12` branch is also gap-free) — but it remains as a regression guard.

- [ ] **Step 3: Implement the `mode='all'` branch**

Open `count_calories_app/views.py`. Find the block at lines ~5460–5471:

```python
    # Build the list of (year, month) pairs to analyse
    if mode == 'year':
        months_to_analyze = [(selected_year, m) for m in range(1, 13)]
    else:  # last12 — rolling window ending this month
        months_to_analyze = []
        y, m = now.year, now.month
        for _ in range(12):
            months_to_analyze.insert(0, (y, m))
            m -= 1
            if m == 0:
                m = 12
                y -= 1
```

Replace it with:

```python
    # Build the list of (year, month) pairs to analyse
    if mode == 'year':
        months_to_analyze = [(selected_year, m) for m in range(1, 13)]
    elif mode == 'all':
        # Every month from the user's first FoodItem entry through the current month
        if first_entry:
            months_to_analyze = []
            y, m = first_entry.year, first_entry.month
            while (y, m) <= (now.year, now.month):
                months_to_analyze.append((y, m))
                m += 1
                if m == 13:
                    m = 1
                    y += 1
        else:
            # No entries yet — show just the current month
            months_to_analyze = [(now.year, now.month)]
    else:  # last12 — rolling window ending this month
        months_to_analyze = []
        y, m = now.year, now.month
        for _ in range(12):
            months_to_analyze.insert(0, (y, m))
            m -= 1
            if m == 0:
                m = 12
                y -= 1
```

Note: `first_entry` is already computed a few lines above (line ~5456) — no new query is needed.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python manage.py test count_calories_app.tests.test_views.MonthTrendsViewTestCase -v 2`

Expected: All 6 tests PASS.

- [ ] **Step 5: Run the full test suite to check for regressions**

Run: `python manage.py test count_calories_app`

Expected: All tests pass (was 369; should be 375 now with the 6 new ones).

- [ ] **Step 6: Commit**

```bash
git add count_calories_app/views.py count_calories_app/tests/test_views.py
git commit -m "feat(trends): add 'all' mode to month_trends view

When mode=all, builds months_to_analyze from the first FoodItem entry
through the current month, inclusive. Falls back to the current month
only when the database is empty.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 2: Add "All Time" button + rename page title & tab on Trends page

**Files:**
- Modify: `count_calories_app/templates/count_calories_app/month_trends.html` (lines 4, 64, 80–91)

- [ ] **Step 1: Rename the page title**

In `count_calories_app/templates/count_calories_app/month_trends.html`, change line 4 from:

```django
{% block title %}Yearly Trends{% endblock %}
```

to:

```django
{% block title %}Trends{% endblock %}
```

- [ ] **Step 2: Rename the in-page tab label**

In the same file, change line 64 from:

```django
<i class="fas fa-chart-line me-1"></i>Yearly Trends
```

to:

```django
<i class="fas fa-chart-line me-1"></i>Trends
```

- [ ] **Step 3: Add the "All Time" button**

In the same file, find the button group at lines 80–91:

```django
<div class="btn-group d-block">
  <a href="?mode=last12"
     class="btn btn-sm {% if mode == 'last12' %}btn-primary{% else %}btn-outline-primary{% endif %}">
    Last 12 Months
  </a>
  {% for yr in available_years %}
  <a href="?mode=year&year={{ yr }}"
     class="btn btn-sm {% if mode == 'year' and selected_year == yr %}btn-primary{% else %}btn-outline-primary{% endif %}">
    {{ yr }}
  </a>
  {% endfor %}
</div>
```

Replace it with (note the new `<a href="?mode=all" ...>` inserted before "Last 12 Months"):

```django
<div class="btn-group d-block">
  <a href="?mode=all"
     class="btn btn-sm {% if mode == 'all' %}btn-primary{% else %}btn-outline-primary{% endif %}">
    All Time
  </a>
  <a href="?mode=last12"
     class="btn btn-sm {% if mode == 'last12' %}btn-primary{% else %}btn-outline-primary{% endif %}">
    Last 12 Months
  </a>
  {% for yr in available_years %}
  <a href="?mode=year&year={{ yr }}"
     class="btn btn-sm {% if mode == 'year' and selected_year == yr %}btn-primary{% else %}btn-outline-primary{% endif %}">
    {{ yr }}
  </a>
  {% endfor %}
</div>
```

- [ ] **Step 4: Run the existing test suite to confirm the template still renders**

Run: `python manage.py test count_calories_app.tests.test_views.MonthTrendsViewTestCase -v 2`

Expected: All 6 tests still PASS (template rendering is verified by `test_default_mode_returns_200` and `test_all_mode_returns_200`).

- [ ] **Step 5: Commit**

```bash
git add count_calories_app/templates/count_calories_app/month_trends.html
git commit -m "feat(trends): add 'All Time' button and rename page title to 'Trends'

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 3: Rename "Yearly Trends" tab label in cross-linking templates

**Files:**
- Modify: `templates/includes/navbar.html:56`
- Modify: `count_calories_app/templates/count_calories_app/analytics.html:147`
- Modify: `count_calories_app/templates/count_calories_app/month_compare.html:106`
- Modify: `count_calories_app/templates/count_calories_app/product_compare.html:97`

These are four identical edits — the same text appears in four different files, each at a known line number. Each occurrence is the in-page or navbar tab label that links to `month_trends`.

- [ ] **Step 1: Update `templates/includes/navbar.html`**

Change line 56 from:

```django
              <i class="fas fa-chart-line me-1"></i>Yearly Trends
```

to:

```django
              <i class="fas fa-chart-line me-1"></i>Trends
```

- [ ] **Step 2: Update `count_calories_app/templates/count_calories_app/analytics.html`**

Change line 147 from:

```django
            <i class="fas fa-chart-line me-1"></i>Yearly Trends
```

to:

```django
            <i class="fas fa-chart-line me-1"></i>Trends
```

- [ ] **Step 3: Update `count_calories_app/templates/count_calories_app/month_compare.html`**

Change line 106 from:

```django
            <i class="fas fa-chart-line me-1"></i>Yearly Trends
```

to:

```django
            <i class="fas fa-chart-line me-1"></i>Trends
```

- [ ] **Step 4: Update `count_calories_app/templates/count_calories_app/product_compare.html`**

Change line 97 from:

```django
            <i class="fas fa-chart-line me-1"></i>Yearly Trends
```

to:

```django
            <i class="fas fa-chart-line me-1"></i>Trends
```

- [ ] **Step 5: Verify no stale "Yearly Trends" strings remain**

Run: `grep -rn "Yearly Trends" count_calories_app/ templates/`

Expected: NO output (no matches).

- [ ] **Step 6: Run the full test suite once more**

Run: `python manage.py test count_calories_app`

Expected: All tests pass.

- [ ] **Step 7: Commit**

```bash
git add templates/includes/navbar.html \
        count_calories_app/templates/count_calories_app/analytics.html \
        count_calories_app/templates/count_calories_app/month_compare.html \
        count_calories_app/templates/count_calories_app/product_compare.html
git commit -m "feat(trends): rename 'Yearly Trends' tab label to 'Trends'

Updates the cross-page nav tabs in analytics, month_compare, product_compare,
and the global navbar dropdown to match the new page title.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 4: Manual verification in the browser

This is a UI change — verify it actually works by clicking the new button.

- [ ] **Step 1: Start the dev server**

Run: `python manage.py runserver 8005` (the user accesses on port 8005)

- [ ] **Step 2: Open the Trends page**

Visit: `http://127.0.0.1:8005/analytics/trends/`

Verify:
- Page title in the browser tab says **"Trends"** (not "Yearly Trends").
- The in-page tab labeled **"Trends"** is highlighted (active).
- A new **"All Time"** button appears at the start of the mode selector, before "Last 12 Months".

- [ ] **Step 3: Click "All Time"**

Verify:
- The URL becomes `http://127.0.0.1:8005/analytics/trends/?mode=all`.
- The "All Time" button is now highlighted in solid blue (`btn-primary`).
- The chart and the breakdown table show every month from the user's first logged entry through the current month, in chronological order. Months with no entries appear as "—" rows.
- Summary cards (Days Logged, Total Calories, Total Protein, Most Consistent Month) reflect the all-time totals.

- [ ] **Step 4: Cross-page tab name check**

Visit each of:
- `http://127.0.0.1:8005/analytics/`
- `http://127.0.0.1:8005/analytics/month-compare/` (or whichever URL `month_compare` resolves to)
- `http://127.0.0.1:8005/analytics/product-compare/`

Verify each has a tab labeled **"Trends"** (not "Yearly Trends") that links back to the trends page.

- [ ] **Step 5: Verify the navbar dropdown**

Open the global top navigation (look for the analytics dropdown). Verify the dropdown item under the analytics group is labeled **"Trends"** and links to `/analytics/trends/`.

- [ ] **Step 6: Regression check on existing modes**

Click "Last 12 Months" → verify the page still works exactly as before. Click any year button (e.g. "2026") → verify it still works.

---

## Done

All tasks complete. The Trends page now offers three view modes: All Time, Last 12 Months, and any specific year — and the page/tab name reflects that it's no longer just yearly.
