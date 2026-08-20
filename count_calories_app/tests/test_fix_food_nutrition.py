"""Tests for the fix_food_nutrition management command.

The command repairs food rows that share a product_name but carry divergent
(and sometimes impossible) nutrition -- e.g. 'Bananas (1)' logged at 15g
protein. It rewrites values in place; it never deletes rows.
"""

import json
from datetime import timedelta
from decimal import Decimal
from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.utils import timezone

from count_calories_app.models import FoodItem


class FixFoodNutritionCommandTestCase(TestCase):
    def setUp(self):
        now = timezone.now()
        for i in range(3):
            FoodItem.objects.create(
                product_name='Bananas (1)', calories=Decimal('168.5'),
                protein=Decimal('15'), fat=Decimal('0.5'), carbohydrates=Decimal('26'),
                consumed_at=now - timedelta(days=10 + i),
            )
        FoodItem.objects.create(
            product_name='Bananas (1)', calories=Decimal('101.1'),
            protein=Decimal('0.3'), fat=Decimal('0.3'), carbohydrates=Decimal('24.3'),
            consumed_at=now - timedelta(days=2),
        )
        FoodItem.objects.create(
            product_name='Oatmeal', calories=Decimal('268'),
            protein=Decimal('11'), fat=Decimal('5.6'), carbohydrates=Decimal('43'),
            consumed_at=now - timedelta(days=1),
        )

    def _run(self, *args, **kwargs):
        out = StringIO()
        call_command('fix_food_nutrition', *args, stdout=out, **kwargs)
        return out.getvalue()

    def test_normalizes_every_row_with_the_given_name(self):
        self._run('--name', 'Bananas (1)', '--calories', '105',
                  '--protein', '1.3', '--fat', '0.4', '--carbs', '27')
        rows = FoodItem.objects.filter(product_name='Bananas (1)')
        self.assertEqual(rows.count(), 4, 'rows must be updated, never deleted')
        for row in rows:
            self.assertEqual(float(row.calories), 105.0)
            self.assertEqual(float(row.protein), 1.3)
            self.assertEqual(float(row.fat), 0.4)
            self.assertEqual(float(row.carbohydrates), 27.0)

    def test_leaves_other_foods_untouched(self):
        self._run('--name', 'Bananas (1)', '--calories', '105',
                  '--protein', '1.3', '--fat', '0.4', '--carbs', '27')
        oats = FoodItem.objects.get(product_name='Oatmeal')
        self.assertEqual(float(oats.calories), 268.0)
        self.assertEqual(float(oats.protein), 11.0)

    def test_dry_run_changes_nothing(self):
        output = self._run('--name', 'Bananas (1)', '--calories', '105',
                           '--protein', '1.3', '--fat', '0.4', '--carbs', '27',
                           '--dry-run')
        self.assertIn('4', output)
        unchanged = FoodItem.objects.filter(
            product_name='Bananas (1)', calories=Decimal('168.5')
        ).count()
        self.assertEqual(unchanged, 3)

    def test_unknown_name_is_an_error(self):
        with self.assertRaises(CommandError):
            self._run('--name', 'Nonexistent Food', '--calories', '1',
                      '--protein', '1', '--fat', '1', '--carbs', '1')

    def test_list_conflicts_reports_divergent_names_only(self):
        output = self._run('--list-conflicts')
        self.assertIn('Bananas (1)', output)
        self.assertNotIn('Oatmeal', output)

    def test_list_conflicts_json_reports_each_variant(self):
        payload = json.loads(self._run('--list-conflicts', '--json'))
        names = {entry['product_name']: entry for entry in payload}
        self.assertIn('Bananas (1)', names)
        self.assertEqual(len(names['Bananas (1)']['variants']), 2)
        self.assertEqual(names['Bananas (1)']['total_rows'], 4)


class FixRoundingDriftTestCase(TestCase):
    """--fix-rounding-drift restores precision lost to quick-add's display rounding.

    Quick-add used to round its payload (calories to a whole number, macros to
    one decimal) and the UI saved that rounded value back, so 24.6 kcal / 0.54g
    entries spawned a 25 kcal / 0.5g twin. Those twins differ only by the
    rounding step, so collapsing them onto the precise variant is safe.

    Genuinely different values (a re-lookup that returned different nutrition)
    must be left alone -- the command cannot know which one is right.
    """

    def setUp(self):
        now = timezone.now()
        # Rounding twins: precise original (3 rows) + rounded copy (2 rows).
        for _ in range(3):
            FoodItem.objects.create(
                product_name='morkos 60 g.', calories=Decimal('24.6'),
                protein=Decimal('0.54'), fat=Decimal('0.12'),
                carbohydrates=Decimal('5.76'), consumed_at=now,
            )
        for _ in range(2):
            FoodItem.objects.create(
                product_name='morkos 60 g.', calories=Decimal('25'),
                protein=Decimal('0.5'), fat=Decimal('0.1'),
                carbohydrates=Decimal('5.8'), consumed_at=now,
            )
        # A genuine disagreement -- two different lookups, not a rounding twin.
        FoodItem.objects.create(
            product_name='Spanguoles 50 g.', calories=Decimal('205.2'),
            protein=Decimal('0.5'), fat=Decimal('0.8'),
            carbohydrates=Decimal('49'), consumed_at=now,
        )
        FoodItem.objects.create(
            product_name='Spanguoles 50 g.', calories=Decimal('173'),
            protein=Decimal('1'), fat=Decimal('1'),
            carbohydrates=Decimal('40'), consumed_at=now,
        )

    def _run(self, *args):
        out = StringIO()
        call_command('fix_food_nutrition', *args, stdout=out)
        return out.getvalue()

    def test_collapses_rounding_twins_onto_the_precise_variant(self):
        self._run('--fix-rounding-drift')
        rows = FoodItem.objects.filter(product_name='morkos 60 g.')
        self.assertEqual(rows.count(), 5)
        for row in rows:
            self.assertEqual(float(row.calories), 24.6)
            self.assertEqual(float(row.protein), 0.54)
            self.assertEqual(float(row.fat), 0.12)
            self.assertEqual(float(row.carbohydrates), 5.76)

    def test_leaves_genuinely_different_values_alone(self):
        self._run('--fix-rounding-drift')
        values = sorted(
            float(r.calories)
            for r in FoodItem.objects.filter(product_name='Spanguoles 50 g.')
        )
        self.assertEqual(values, [173.0, 205.2])

    def test_reports_names_it_could_not_resolve(self):
        output = self._run('--fix-rounding-drift')
        self.assertIn('Spanguoles 50 g.', output)
        self.assertIn('manual', output.lower())

    def test_dry_run_writes_nothing(self):
        self._run('--fix-rounding-drift', '--dry-run')
        still_rounded = FoodItem.objects.filter(
            product_name='morkos 60 g.', calories=Decimal('25')
        ).count()
        self.assertEqual(still_rounded, 2)
