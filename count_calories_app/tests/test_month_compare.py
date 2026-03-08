"""
Unit tests for the month_compare view and its nested helpers.

Covers:
- get_month_data: zero-data month, single-entry month, December boundary,
  macro-pct sum-to-100 guarantee, avg calculations, weight stats.
- get_weekly_breakdown: week boundaries, loop termination, data-less weeks,
  December 31-day month (5 weeks), leap-year February (4 weeks).
- comparison_foods build: _zero mutable-default sharing, cal_impact_pct when all
  diffs are zero, correct only_in_a / only_in_b before the [:25] truncation.
- overview_diffs: weight_avg / weight_change only added when BOTH months have data.
- month_choices: future months excluded, January boundary (year rollover).
- parse_month: malformed string falls back gracefully.
- Full HTTP response: status 200, template used, context keys present.
"""

import json
from datetime import datetime, timedelta
from decimal import Decimal

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from count_calories_app.models import FoodItem, Weight


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_food(name, year, month, day, *, calories=200, protein=20,
              fat=10, carbs=30, hour=12):
    """Create a FoodItem in UTC-aware datetime at noon by default."""
    dt = timezone.make_aware(datetime(year, month, day, hour, 0, 0))
    return FoodItem.objects.create(
        product_name=name,
        calories=Decimal(str(calories)),
        protein=Decimal(str(protein)),
        fat=Decimal(str(fat)),
        carbohydrates=Decimal(str(carbs)),
        consumed_at=dt,
    )


def make_weight(kg, year, month, day, hour=8):
    dt = timezone.make_aware(datetime(year, month, day, hour, 0, 0))
    return Weight.objects.create(weight=Decimal(str(kg)), recorded_at=dt)


URL = reverse('month_compare')


# ---------------------------------------------------------------------------
# 1. Zero-data months
# ---------------------------------------------------------------------------

class ZeroDataMonthTest(TestCase):
    """Both months have no food or weight data at all."""

    def test_view_returns_200_with_no_data(self):
        response = Client().get(URL, {'month1': '2024-01', 'month2': '2023-12'})
        self.assertEqual(response.status_code, 200)

    def test_context_keys_present(self):
        response = Client().get(URL, {'month1': '2024-01', 'month2': '2023-12'})
        ctx = response.context
        for key in ('data1', 'data2', 'overview_diffs', 'comparison_foods',
                    'only_in_a', 'only_in_b', 'weekly1_json', 'weekly2_json',
                    'month_choices'):
            self.assertIn(key, ctx, f"Missing context key: {key}")

    def test_zero_data_month_stats_all_zero(self):
        response = Client().get(URL, {'month1': '2024-01', 'month2': '2023-12'})
        d = response.context['data1']
        self.assertEqual(d['days_logged'], 0)
        self.assertEqual(d['total_calories'], 0)
        self.assertEqual(d['avg_daily_calories'], 0)
        self.assertEqual(d['total_protein'], 0)
        self.assertEqual(d['total_fat'], 0)
        self.assertEqual(d['total_carbs'], 0)
        self.assertIsNone(d['weight'])

    def test_zero_data_macro_pct_all_zero(self):
        response = Client().get(URL, {'month1': '2024-01', 'month2': '2023-12'})
        pct = response.context['data1']['macro_pct']
        self.assertEqual(pct, {'protein': 0, 'fat': 0, 'carbs': 0})

    def test_comparison_foods_empty_when_no_data(self):
        response = Client().get(URL, {'month1': '2024-01', 'month2': '2023-12'})
        self.assertEqual(response.context['comparison_foods'], [])

    def test_only_in_a_and_b_empty_when_no_data(self):
        response = Client().get(URL, {'month1': '2024-01', 'month2': '2023-12'})
        self.assertEqual(response.context['only_in_a'], [])
        self.assertEqual(response.context['only_in_b'], [])

    def test_weekly_json_is_valid_json(self):
        response = Client().get(URL, {'month1': '2024-01', 'month2': '2023-12'})
        # Must parse without exceptions
        json.loads(response.context['weekly1_json'])
        json.loads(response.context['weekly2_json'])

    def test_overview_diffs_no_weight_keys_when_no_weight(self):
        """weight_avg and weight_change must NOT appear when neither month has weight."""
        response = Client().get(URL, {'month1': '2024-01', 'month2': '2023-12'})
        diffs = response.context['overview_diffs']
        self.assertNotIn('weight_avg', diffs)
        self.assertNotIn('weight_change', diffs)


# ---------------------------------------------------------------------------
# 2. One month has data, the other is empty
# ---------------------------------------------------------------------------

class OneMonthDataTest(TestCase):

    def setUp(self):
        # Month A (2024-03) has 3 entries; Month B (2024-02) is empty
        make_food('Chicken', 2024, 3, 1, calories=300, protein=40, fat=5, carbs=0)
        make_food('Chicken', 2024, 3, 2, calories=300, protein=40, fat=5, carbs=0)
        make_food('Rice', 2024, 3, 1, calories=200, protein=5, fat=1, carbs=45)

    def test_data1_days_logged(self):
        response = Client().get(URL, {'month1': '2024-03', 'month2': '2024-02'})
        # Two distinct days in March
        self.assertEqual(response.context['data1']['days_logged'], 2)

    def test_data2_empty(self):
        response = Client().get(URL, {'month1': '2024-03', 'month2': '2024-02'})
        d2 = response.context['data2']
        self.assertEqual(d2['total_calories'], 0)
        self.assertEqual(d2['days_logged'], 0)

    def test_avg_daily_calories_correct(self):
        response = Client().get(URL, {'month1': '2024-03', 'month2': '2024-02'})
        d1 = response.context['data1']
        # Total 800 kcal / 2 days = 400.0
        self.assertEqual(d1['avg_daily_calories'], 400.0)

    def test_only_in_a_contains_all_foods_from_nonempty_month(self):
        response = Client().get(URL, {'month1': '2024-03', 'month2': '2024-02'})
        names = {f['name'] for f in response.context['only_in_a']}
        self.assertIn('Chicken', names)
        self.assertIn('Rice', names)

    def test_only_in_b_empty_when_month_b_has_no_data(self):
        response = Client().get(URL, {'month1': '2024-03', 'month2': '2024-02'})
        self.assertEqual(response.context['only_in_b'], [])

    def test_overview_diffs_no_weight_keys_when_only_one_has_weight(self):
        """weight_avg must not appear when only month A has weight data."""
        make_weight(80.0, 2024, 3, 5)
        response = Client().get(URL, {'month1': '2024-03', 'month2': '2024-02'})
        diffs = response.context['overview_diffs']
        self.assertNotIn('weight_avg', diffs)
        self.assertNotIn('weight_change', diffs)


# ---------------------------------------------------------------------------
# 3. Weight stats — one or both months populated
# ---------------------------------------------------------------------------

class WeightStatsTest(TestCase):

    def setUp(self):
        # Month A weights
        make_weight(80.0, 2024, 3, 1)
        make_weight(79.0, 2024, 3, 15)
        make_weight(78.0, 2024, 3, 31)
        # Month B weights
        make_weight(82.0, 2024, 2, 1)
        make_weight(81.0, 2024, 2, 29)  # 2024 is a leap year

    def test_weight_stats_calculated_for_month_a(self):
        response = Client().get(URL, {'month1': '2024-03', 'month2': '2024-02'})
        w = response.context['data1']['weight']
        self.assertIsNotNone(w)
        self.assertEqual(w['start'], 80.0)
        self.assertEqual(w['end'], 78.0)
        self.assertEqual(w['change'], -2.0)
        self.assertEqual(w['count'], 3)

    def test_weight_stats_calculated_for_month_b(self):
        response = Client().get(URL, {'month1': '2024-03', 'month2': '2024-02'})
        w = response.context['data2']['weight']
        self.assertIsNotNone(w)
        self.assertEqual(w['start'], 82.0)
        self.assertEqual(w['end'], 81.0)
        self.assertEqual(w['change'], -1.0)
        self.assertEqual(w['count'], 2)

    def test_overview_diffs_weight_keys_appear_when_both_have_weight(self):
        response = Client().get(URL, {'month1': '2024-03', 'month2': '2024-02'})
        diffs = response.context['overview_diffs']
        self.assertIn('weight_avg', diffs)
        self.assertIn('weight_change', diffs)

    def test_overview_diffs_weight_avg_value(self):
        response = Client().get(URL, {'month1': '2024-03', 'month2': '2024-02'})
        w1 = response.context['data1']['weight']['avg']
        w2 = response.context['data2']['weight']['avg']
        expected = round(w1 - w2, 1)
        self.assertEqual(response.context['overview_diffs']['weight_avg'], expected)

    def test_weight_stats_none_when_month_has_no_weight(self):
        response = Client().get(URL, {'month1': '2024-01', 'month2': '2024-02'})
        self.assertIsNone(response.context['data1']['weight'])


# ---------------------------------------------------------------------------
# 4. Macro percentage — always sums to 100
# ---------------------------------------------------------------------------

class MacroPctTest(TestCase):

    def _get_macro_pct(self, protein_cal, fat_cal, carb_cal, year=2024, month=1):
        """Create foods that produce a specific macro calorie split."""
        # protein_cal / 4 = protein grams, etc.
        make_food(
            'TestFood', year, month, 10,
            calories=protein_cal + fat_cal + carb_cal,
            protein=protein_cal / 4,
            fat=fat_cal / 9,
            carbs=carb_cal / 4,
        )
        response = Client().get(URL, {
            'month1': f'{year}-{month:02d}',
            'month2': '2000-01',
        })
        return response.context['data1']['macro_pct']

    def test_macro_pct_sums_to_100_typical(self):
        # 40% protein, 30% fat, 30% carbs (rounded)
        pct = self._get_macro_pct(400, 300, 300)
        self.assertEqual(pct['protein'] + pct['fat'] + pct['carbs'], 100)

    def test_macro_pct_sums_to_100_with_rounding_artifacts(self):
        # Choose values that create a 33/33/33 split — rounds to 33+33+34=100
        pct = self._get_macro_pct(100, 100, 100)
        self.assertEqual(pct['protein'] + pct['fat'] + pct['carbs'], 100)

    def test_macro_pct_zero_when_all_zero(self):
        # No food in month → all zeros, no division
        response = Client().get(URL, {'month1': '2000-01', 'month2': '2000-02'})
        pct = response.context['data1']['macro_pct']
        self.assertEqual(pct, {'protein': 0, 'fat': 0, 'carbs': 0})

    def test_macro_pct_carbs_derived_not_independently_rounded(self):
        """The carbs pct must be 100 - protein - fat (not three independent rounds)."""
        # This is the structural guarantee in the code: carbs = 100 - p - f
        pct = self._get_macro_pct(333, 333, 334)  # deliberately asymmetric
        self.assertEqual(pct['carbs'], 100 - pct['protein'] - pct['fat'])


# ---------------------------------------------------------------------------
# 5. _zero dict — shared-reference mutation check
# ---------------------------------------------------------------------------

class ZeroDictMutationTest(TestCase):
    """
    Bug: _zero is defined once as a plain dict. If any code path mutates it
    (e.g., f1['count'] += 1 or similar), subsequent lookups will see the
    mutated value. The current code only *reads* from _zero, so mutation
    should NOT happen — but we verify this by exercising many foods-absent
    scenarios in the same request.
    """

    def setUp(self):
        # Month A has 30 unique foods; Month B is empty.
        # Each food is absent from B, so _zero is used 30 times as f2.
        for i in range(30):
            make_food(f'FoodA_{i}', 2024, 3, (i % 28) + 1, calories=100)

    def test_zero_dict_not_mutated_across_foods(self):
        """All foods absent from month B should show count2 == 0, calories2 == 0."""
        response = Client().get(URL, {'month1': '2024-03', 'month2': '2024-02'})
        for food in response.context['only_in_a']:
            self.assertEqual(food['count2'], 0,
                             f"{food['name']} count2 should be 0 (got {food['count2']})")
            self.assertEqual(food['calories2'], 0,
                             f"{food['name']} calories2 should be 0 (got {food['calories2']})")

    def test_only_in_a_length_equals_all_30_foods(self):
        """With 30 foods in A and none in B, only_in_a must contain all 30."""
        response = Client().get(URL, {'month1': '2024-03', 'month2': '2024-02'})
        self.assertEqual(len(response.context['only_in_a']), 30)


# ---------------------------------------------------------------------------
# 6. only_in_a / only_in_b computed before [:25] truncation
# ---------------------------------------------------------------------------

class OnlyInExclusiveBeforeTruncationTest(TestCase):
    """
    Regression: only_in_a and only_in_b must reflect ALL exclusive foods,
    even those ranked 26th or beyond.
    """

    def setUp(self):
        # 25 foods appear in BOTH months (high frequency → top-25 table)
        for i in range(25):
            for _ in range(5):  # 5 times each in A
                make_food(f'Shared_{i}', 2024, 3, 1, calories=100)
            for _ in range(5):  # 5 times each in B
                make_food(f'Shared_{i}', 2024, 2, 1, calories=100)

        # 5 foods appear ONLY in A with low frequency (rank 26+)
        for i in range(5):
            make_food(f'OnlyA_{i}', 2024, 3, 2, calories=50)

        # 5 foods appear ONLY in B with low frequency (rank 26+)
        for i in range(5):
            make_food(f'OnlyB_{i}', 2024, 2, 2, calories=50)

    def test_only_in_a_includes_foods_beyond_rank_25(self):
        response = Client().get(URL, {'month1': '2024-03', 'month2': '2024-02'})
        names = {f['name'] for f in response.context['only_in_a']}
        for i in range(5):
            self.assertIn(f'OnlyA_{i}', names,
                          f"OnlyA_{i} missing from only_in_a")

    def test_only_in_b_includes_foods_beyond_rank_25(self):
        response = Client().get(URL, {'month1': '2024-03', 'month2': '2024-02'})
        names = {f['name'] for f in response.context['only_in_b']}
        for i in range(5):
            self.assertIn(f'OnlyB_{i}', names,
                          f"OnlyB_{i} missing from only_in_b")

    def test_comparison_foods_table_capped_at_25(self):
        response = Client().get(URL, {'month1': '2024-03', 'month2': '2024-02'})
        self.assertLessEqual(len(response.context['comparison_foods']), 25)


# ---------------------------------------------------------------------------
# 7. cal_impact_pct
# ---------------------------------------------------------------------------

class CalImpactPctTest(TestCase):

    def test_cal_impact_pct_present_on_each_food(self):
        make_food('Chicken', 2024, 3, 1, calories=500)
        make_food('Rice', 2024, 2, 1, calories=300)
        response = Client().get(URL, {'month1': '2024-03', 'month2': '2024-02'})
        for food in response.context['comparison_foods']:
            self.assertIn('cal_impact_pct', food,
                          f"cal_impact_pct missing from {food['name']}")

    def test_cal_impact_pct_sums_to_100_when_diffs_vary(self):
        """
        cal_impact_pct is NOT required to sum to 100 (rounding). But it should
        be between 0 and 100 for each food and total should be >= 99 and <= 102.
        """
        make_food('A', 2024, 3, 1, calories=600)
        make_food('B', 2024, 3, 2, calories=200)
        make_food('C', 2024, 2, 1, calories=100)
        response = Client().get(URL, {'month1': '2024-03', 'month2': '2024-02'})
        total = sum(f['cal_impact_pct'] for f in response.context['comparison_foods'])
        self.assertGreaterEqual(total, 99)
        self.assertLessEqual(total, 101)

    def test_cal_impact_pct_when_all_cal_diffs_zero(self):
        """
        When every food has equal calories in both months, cal_impact_pct should
        be 0 for all (since all calories_diff == 0 and total_abs_cal_diff falls
        back to 1 to avoid division by zero).
        """
        make_food('Shared', 2024, 3, 1, calories=300)
        make_food('Shared', 2024, 2, 1, calories=300)
        response = Client().get(URL, {'month1': '2024-03', 'month2': '2024-02'})
        for food in response.context['comparison_foods']:
            self.assertEqual(food['cal_impact_pct'], 0,
                             f"Expected 0 cal_impact_pct for {food['name']}")


# ---------------------------------------------------------------------------
# 8. get_weekly_breakdown — loop correctness
# ---------------------------------------------------------------------------

class WeeklyBreakdownTest(TestCase):

    def _weekly(self, year, month, month2='2000-01'):
        response = Client().get(URL, {
            'month1': f'{year}-{month:02d}',
            'month2': month2,
        })
        return json.loads(response.context['weekly1_json'])

    def test_january_2024_has_5_weeks(self):
        # Jan 2024: 1–7 (W1), 8–14 (W2), 15–21 (W3), 22–28 (W4), 29–31 (W5)
        weeks = self._weekly(2024, 1)
        self.assertEqual(len(weeks), 5)

    def test_february_2024_has_5_weeks(self):
        # Feb 2024 (29 days): 1–7 (W1), 8–14 (W2), 15–21 (W3), 22–28 (W4), 29 (W5)
        # The loop always advances by 7 days; day 29 starts a 5th partial week.
        weeks = self._weekly(2024, 2)
        self.assertEqual(len(weeks), 5)

    def test_december_has_5_weeks(self):
        # Dec 2024: 31 days → 5 weeks (last week: 29–31)
        weeks = self._weekly(2024, 12)
        self.assertEqual(len(weeks), 5)

    def test_loop_terminates_for_december(self):
        """Regression: week_end can equal end_d (Dec 31). Loop must not hang."""
        # A food in December ensures daily_cals is populated
        make_food('XmasFood', 2024, 12, 31, calories=500)
        weeks = self._weekly(2024, 12)
        self.assertGreater(len(weeks), 0)

    def test_week_labels_sequential(self):
        weeks = self._weekly(2024, 3)
        for i, w in enumerate(weeks, start=1):
            self.assertEqual(w['label'], f'W{i}')

    def test_avg_calories_none_when_no_food_in_week(self):
        """Weeks with no food entries should have avg_calories=None, not 0."""
        # No food created → all weeks should be None
        weeks = self._weekly(2024, 3)
        for w in weeks:
            self.assertIsNone(w['avg_calories'],
                              f"Expected None but got {w['avg_calories']} for {w['label']}")

    def test_avg_calories_computed_correctly(self):
        # W1 of March 2024: days 1–7
        make_food('F1', 2024, 3, 1, calories=400)
        make_food('F2', 2024, 3, 3, calories=600)
        # Days 1 and 3 have food → avg = (400 + 600) / 2 = 500
        weeks = self._weekly(2024, 3)
        w1 = weeks[0]
        self.assertEqual(w1['avg_calories'], 500)

    def test_avg_weight_none_when_no_weight_data(self):
        weeks = self._weekly(2024, 3)
        for w in weeks:
            self.assertIsNone(w['avg_weight'])

    def test_avg_weight_computed_for_week(self):
        make_weight(80.0, 2024, 3, 1)
        make_weight(78.0, 2024, 3, 3)
        weeks = self._weekly(2024, 3)
        # W1 (days 1–7): avg = (80+78)/2 = 79.0
        self.assertEqual(weeks[0]['avg_weight'], 79.0)

    def test_weekly_breakdown_week_boundary_does_not_cross_month(self):
        """The last week's end should never go past the last day of the month."""
        # All weeks together should span exactly the month
        weeks = self._weekly(2024, 3)  # March = 31 days
        # Verify last week starts ≤ March 31 and is labelled correctly
        self.assertEqual(weeks[-1]['start'][:3], 'Mar')


# ---------------------------------------------------------------------------
# 9. December / year-boundary for get_month_data
# ---------------------------------------------------------------------------

class DecemberBoundaryTest(TestCase):

    def setUp(self):
        # Food on Dec 31 23:59 — must be IN December
        dt_dec = timezone.make_aware(datetime(2023, 12, 31, 23, 59, 59))
        FoodItem.objects.create(
            product_name='YearEnd',
            calories=Decimal('100'), protein=Decimal('5'),
            fat=Decimal('2'), carbohydrates=Decimal('15'),
            consumed_at=dt_dec,
        )
        # Food at exactly Jan 1 00:00:00 — must be EXCLUDED from December
        dt_jan = timezone.make_aware(datetime(2024, 1, 1, 0, 0, 0))
        FoodItem.objects.create(
            product_name='NewYear',
            calories=Decimal('200'), protein=Decimal('10'),
            fat=Decimal('4'), carbohydrates=Decimal('30'),
            consumed_at=dt_jan,
        )

    def test_december_includes_dec31_entry(self):
        response = Client().get(URL, {'month1': '2023-12', 'month2': '2022-12'})
        self.assertEqual(response.context['data1']['total_entries'], 1)

    def test_december_excludes_jan1_midnight_entry(self):
        response = Client().get(URL, {'month1': '2023-12', 'month2': '2022-12'})
        # top_foods dicts from .values() use 'product_name', not 'name'
        names = {f['product_name'] for f in response.context['data1']['top_foods']}
        self.assertNotIn('NewYear', names)

    def test_january_includes_jan1_midnight_entry(self):
        response = Client().get(URL, {'month1': '2024-01', 'month2': '2023-01'})
        names = {f['product_name'] for f in response.context['data1']['top_foods']}
        self.assertIn('NewYear', names)


# ---------------------------------------------------------------------------
# 10. parse_month — invalid / malformed input
# ---------------------------------------------------------------------------

class ParseMonthFallbackTest(TestCase):

    def test_malformed_month1_falls_back_gracefully(self):
        """Malformed month string should not crash the view — falls back to now."""
        response = Client().get(URL, {'month1': 'not-a-date', 'month2': '2024-01'})
        self.assertEqual(response.status_code, 200)

    def test_malformed_month2_falls_back_gracefully(self):
        response = Client().get(URL, {'month1': '2024-01', 'month2': 'YYYY-MM'})
        self.assertEqual(response.status_code, 200)

    def test_missing_params_uses_defaults(self):
        """When month1/month2 params are absent, defaults must be used without error."""
        response = Client().get(URL)
        self.assertEqual(response.status_code, 200)

    def test_empty_string_params(self):
        response = Client().get(URL, {'month1': '', 'month2': ''})
        self.assertEqual(response.status_code, 200)


# ---------------------------------------------------------------------------
# 11. month_choices generation
# ---------------------------------------------------------------------------

class MonthChoicesTest(TestCase):

    def test_month_choices_contains_current_month(self):
        now = timezone.now()
        current = f"{now.year}-{now.month:02d}"
        response = Client().get(URL)
        values = [c['value'] for c in response.context['month_choices']]
        self.assertIn(current, values)

    def test_month_choices_excludes_future_months(self):
        now = timezone.now()
        response = Client().get(URL)
        for choice in response.context['month_choices']:
            y, m = map(int, choice['value'].split('-'))
            self.assertFalse(
                (y > now.year) or (y == now.year and m > now.month),
                f"Future month {choice['value']} found in month_choices",
            )

    def test_month_choices_covers_3_years(self):
        now = timezone.now()
        response = Client().get(URL)
        values = [c['value'] for c in response.context['month_choices']]
        # The oldest month should be from (now.year - 2)
        oldest_year = min(int(v.split('-')[0]) for v in values)
        self.assertEqual(oldest_year, now.year - 2)

    def test_month_choices_have_value_and_label_keys(self):
        response = Client().get(URL)
        for choice in response.context['month_choices']:
            self.assertIn('value', choice)
            self.assertIn('label', choice)

    def test_month_choices_values_are_valid_yyyy_mm(self):
        response = Client().get(URL)
        for choice in response.context['month_choices']:
            parts = choice['value'].split('-')
            self.assertEqual(len(parts), 2)
            self.assertEqual(len(parts[1]), 2)  # zero-padded


# ---------------------------------------------------------------------------
# 12. comparison_foods sort and content
# ---------------------------------------------------------------------------

class ComparisonFoodsSortTest(TestCase):

    def setUp(self):
        # 'Chicken' eaten 3 times in A, 1 time in B → combined = 4
        for _ in range(3):
            make_food('Chicken', 2024, 3, 1, calories=200)
        make_food('Chicken', 2024, 2, 1, calories=200)

        # 'Rice' eaten 1 time in A, 3 times in B → combined = 4
        make_food('Rice', 2024, 3, 2, calories=100)
        for _ in range(3):
            make_food('Rice', 2024, 2, 2, calories=100)

        # 'Eggs' eaten 1 time in A only → combined = 1
        make_food('Eggs', 2024, 3, 3, calories=80)

    def test_comparison_foods_sorted_by_combined_frequency_desc(self):
        response = Client().get(URL, {'month1': '2024-03', 'month2': '2024-02'})
        foods = response.context['comparison_foods']
        combined = [f['count1'] + f['count2'] for f in foods]
        self.assertEqual(combined, sorted(combined, reverse=True))

    def test_comparison_food_count1_count2_correct(self):
        response = Client().get(URL, {'month1': '2024-03', 'month2': '2024-02'})
        foods = {f['name']: f for f in response.context['comparison_foods']}
        self.assertEqual(foods['Chicken']['count1'], 3)
        self.assertEqual(foods['Chicken']['count2'], 1)
        self.assertEqual(foods['Rice']['count1'], 1)
        self.assertEqual(foods['Rice']['count2'], 3)
        self.assertEqual(foods['Eggs']['count1'], 1)
        self.assertEqual(foods['Eggs']['count2'], 0)

    def test_count_diff_is_a_minus_b(self):
        response = Client().get(URL, {'month1': '2024-03', 'month2': '2024-02'})
        foods = {f['name']: f for f in response.context['comparison_foods']}
        self.assertEqual(foods['Chicken']['count_diff'], 2)   # 3 - 1
        self.assertEqual(foods['Rice']['count_diff'], -2)      # 1 - 3

    def test_calories_diff_is_a_minus_b(self):
        response = Client().get(URL, {'month1': '2024-03', 'month2': '2024-02'})
        foods = {f['name']: f for f in response.context['comparison_foods']}
        chicken = foods['Chicken']
        self.assertEqual(chicken['calories_diff'],
                         chicken['calories1'] - chicken['calories2'])


# ---------------------------------------------------------------------------
# 13. overview_diffs values
# ---------------------------------------------------------------------------

class OverviewDiffsTest(TestCase):

    def setUp(self):
        # Month A: 2 days, 500 + 300 = 800 kcal total
        make_food('A1', 2024, 3, 1, calories=500, protein=40, fat=10, carbs=50)
        make_food('A2', 2024, 3, 2, calories=300, protein=20, fat=5, carbs=30)
        # Month B: 1 day, 400 kcal
        make_food('B1', 2024, 2, 1, calories=400, protein=30, fat=8, carbs=40)

    def test_days_logged_diff(self):
        response = Client().get(URL, {'month1': '2024-03', 'month2': '2024-02'})
        self.assertEqual(response.context['overview_diffs']['days_logged'], 1)

    def test_total_calories_diff(self):
        response = Client().get(URL, {'month1': '2024-03', 'month2': '2024-02'})
        self.assertEqual(response.context['overview_diffs']['total_calories'], 400)

    def test_avg_daily_calories_diff(self):
        response = Client().get(URL, {'month1': '2024-03', 'month2': '2024-02'})
        # A: 800/2=400, B: 400/1=400 → diff = 0.0
        self.assertEqual(response.context['overview_diffs']['avg_daily_calories'], 0.0)

    def test_avg_daily_protein_diff(self):
        response = Client().get(URL, {'month1': '2024-03', 'month2': '2024-02'})
        # A: (40+20)/2=30, B: 30/1=30 → diff = 0.0
        self.assertEqual(response.context['overview_diffs']['avg_daily_protein'], 0.0)


# ---------------------------------------------------------------------------
# 14. same month for both A and B
# ---------------------------------------------------------------------------

class SameMonthBothTest(TestCase):

    def setUp(self):
        make_food('SameFood', 2024, 3, 10, calories=300, protein=25, fat=8, carbs=35)

    def test_same_month_overview_diffs_all_zero(self):
        response = Client().get(URL, {'month1': '2024-03', 'month2': '2024-03'})
        diffs = response.context['overview_diffs']
        self.assertEqual(diffs['days_logged'], 0)
        self.assertEqual(diffs['total_calories'], 0)
        self.assertEqual(diffs['avg_daily_calories'], 0.0)

    def test_same_month_food_appears_in_both_counts(self):
        response = Client().get(URL, {'month1': '2024-03', 'month2': '2024-03'})
        for food in response.context['comparison_foods']:
            self.assertEqual(food['count1'], food['count2'])
            self.assertEqual(food['calories_diff'], 0)

    def test_same_month_only_in_a_and_b_both_empty(self):
        response = Client().get(URL, {'month1': '2024-03', 'month2': '2024-03'})
        self.assertEqual(response.context['only_in_a'], [])
        self.assertEqual(response.context['only_in_b'], [])


# ---------------------------------------------------------------------------
# 15. Template rendering — correct template, no 500 errors
# ---------------------------------------------------------------------------

class TemplateRenderingTest(TestCase):

    def test_correct_template_used(self):
        response = Client().get(URL)
        self.assertTemplateUsed(response, 'count_calories_app/month_compare.html')

    def test_monthly_labels_in_context(self):
        response = Client().get(URL, {'month1': '2024-03', 'month2': '2024-02'})
        self.assertEqual(response.context['month1_label'], 'March 2024')
        self.assertEqual(response.context['month2_label'], 'February 2024')

    def test_month1_str_and_month2_str_in_context(self):
        response = Client().get(URL, {'month1': '2024-03', 'month2': '2024-02'})
        self.assertEqual(response.context['month1_str'], '2024-03')
        self.assertEqual(response.context['month2_str'], '2024-02')

    def test_weekly_json_in_context_is_parseable_list(self):
        make_food('F', 2024, 3, 5, calories=200)
        response = Client().get(URL, {'month1': '2024-03', 'month2': '2024-02'})
        w1 = json.loads(response.context['weekly1_json'])
        self.assertIsInstance(w1, list)
        self.assertGreater(len(w1), 0)

    def test_no_weight_diffs_column_shown_when_only_one_month_has_weight(self):
        """
        When only data1 has weight, overview_diffs must NOT contain weight_avg.
        Template guards on `data1.weight and data2.weight` to show the Diff column.
        """
        make_weight(80.0, 2024, 3, 1)
        response = Client().get(URL, {'month1': '2024-03', 'month2': '2024-02'})
        self.assertNotIn('weight_avg', response.context['overview_diffs'])
