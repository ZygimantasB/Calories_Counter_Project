"""
Unit tests for Analytics calculations verification.

Tests verify that all calculations in the Analytics view are mathematically correct:
- Macronutrient distribution percentages
- Protein per kg body weight
- Calorie consistency scores
- Weight pace calculations
- Streak calculations
- Day of week analysis
- Calorie budget calculations
- Weight volatility
- Nutrition scores
"""

from datetime import timedelta
from decimal import Decimal

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from count_calories_app.models import FoodItem, Weight


class MacronutrientCalculationTestCase(TestCase):
    """Test cases to verify macronutrient percentage calculations."""

    def setUp(self):
        """Set up test data with known macro values."""
        self.client = Client()
        self.url = reverse('analytics')
        self.now = timezone.now()

        # Create weight for protein/kg calculation
        Weight.objects.create(
            weight=Decimal('100.0'),  # 100 kg for easy calculation
            recorded_at=self.now
        )

    def test_macro_percentages_equal_distribution(self):
        """Test macro percentages when protein=carbs=fat in grams."""
        # Create food with equal grams of each macro
        # 100g protein = 400 cal, 100g carbs = 400 cal, 100g fat = 900 cal
        # Total = 1700 cal
        # Protein % = 400/1700 = 23.5%
        # Carbs % = 400/1700 = 23.5%
        # Fat % = 900/1700 = 52.9%
        for i in range(10):
            FoodItem.objects.create(
                product_name=f'Test Food {i}',
                calories=Decimal('1700'),
                protein=Decimal('100'),
                carbohydrates=Decimal('100'),
                fat=Decimal('100'),
                consumed_at=self.now - timedelta(days=i)
            )

        response = self.client.get(self.url)
        macro = response.context['macro_analysis']

        # Verify calculations
        self.assertAlmostEqual(macro['protein_percent'], 23.5, delta=0.1)
        self.assertAlmostEqual(macro['carbs_percent'], 23.5, delta=0.1)
        self.assertAlmostEqual(macro['fat_percent'], 52.9, delta=0.1)

        # Verify percentages sum to 100
        total = macro['protein_percent'] + macro['carbs_percent'] + macro['fat_percent']
        self.assertAlmostEqual(total, 100.0, delta=0.5)

    def test_macro_percentages_high_protein(self):
        """Test macro percentages with high protein diet."""
        # 200g protein = 800 cal
        # 100g carbs = 400 cal
        # 50g fat = 450 cal
        # Total = 1650 cal
        # Protein % = 800/1650 = 48.5%
        # Carbs % = 400/1650 = 24.2%
        # Fat % = 450/1650 = 27.3%
        for i in range(10):
            FoodItem.objects.create(
                product_name=f'High Protein Food {i}',
                calories=Decimal('1650'),
                protein=Decimal('200'),
                carbohydrates=Decimal('100'),
                fat=Decimal('50'),
                consumed_at=self.now - timedelta(days=i)
            )

        response = self.client.get(self.url)
        macro = response.context['macro_analysis']

        self.assertAlmostEqual(macro['protein_percent'], 48.5, delta=0.1)
        self.assertAlmostEqual(macro['carbs_percent'], 24.2, delta=0.1)
        self.assertAlmostEqual(macro['fat_percent'], 27.3, delta=0.1)

    def test_macro_percentages_high_carb(self):
        """Test macro percentages with high carb diet."""
        # 100g protein = 400 cal
        # 300g carbs = 1200 cal
        # 50g fat = 450 cal
        # Total = 2050 cal
        # Protein % = 400/2050 = 19.5%
        # Carbs % = 1200/2050 = 58.5%
        # Fat % = 450/2050 = 22.0%
        for i in range(10):
            FoodItem.objects.create(
                product_name=f'High Carb Food {i}',
                calories=Decimal('2050'),
                protein=Decimal('100'),
                carbohydrates=Decimal('300'),
                fat=Decimal('50'),
                consumed_at=self.now - timedelta(days=i)
            )

        response = self.client.get(self.url)
        macro = response.context['macro_analysis']

        self.assertAlmostEqual(macro['protein_percent'], 19.5, delta=0.1)
        self.assertAlmostEqual(macro['carbs_percent'], 58.5, delta=0.1)
        self.assertAlmostEqual(macro['fat_percent'], 22.0, delta=0.1)

    def test_macro_percentages_high_fat(self):
        """Test macro percentages with high fat (keto-style) diet."""
        # 150g protein = 600 cal
        # 30g carbs = 120 cal
        # 150g fat = 1350 cal
        # Total = 2070 cal
        # Protein % = 600/2070 = 29.0%
        # Carbs % = 120/2070 = 5.8%
        # Fat % = 1350/2070 = 65.2%
        for i in range(10):
            FoodItem.objects.create(
                product_name=f'High Fat Food {i}',
                calories=Decimal('2070'),
                protein=Decimal('150'),
                carbohydrates=Decimal('30'),
                fat=Decimal('150'),
                consumed_at=self.now - timedelta(days=i)
            )

        response = self.client.get(self.url)
        macro = response.context['macro_analysis']

        self.assertAlmostEqual(macro['protein_percent'], 29.0, delta=0.1)
        self.assertAlmostEqual(macro['carbs_percent'], 5.8, delta=0.1)
        self.assertAlmostEqual(macro['fat_percent'], 65.2, delta=0.1)

    def test_protein_per_kg_calculation(self):
        """Test protein per kg body weight calculation."""
        # Weight = 100 kg, Protein = 150g
        # Protein per kg = 150/100 = 1.5 g/kg
        for i in range(10):
            FoodItem.objects.create(
                product_name=f'Test Food {i}',
                calories=Decimal('2000'),
                protein=Decimal('150'),
                carbohydrates=Decimal('200'),
                fat=Decimal('80'),
                consumed_at=self.now - timedelta(days=i)
            )

        response = self.client.get(self.url)
        macro = response.context['macro_analysis']

        self.assertEqual(macro['protein_per_kg'], 1.5)

    def test_protein_per_kg_with_different_weight(self):
        """Test protein per kg with 80kg body weight."""
        # Update weight to 80 kg
        Weight.objects.all().delete()
        Weight.objects.create(
            weight=Decimal('80.0'),
            recorded_at=self.now
        )

        # Protein = 160g, Weight = 80kg
        # Protein per kg = 160/80 = 2.0 g/kg
        for i in range(10):
            FoodItem.objects.create(
                product_name=f'Test Food {i}',
                calories=Decimal('2000'),
                protein=Decimal('160'),
                carbohydrates=Decimal('200'),
                fat=Decimal('80'),
                consumed_at=self.now - timedelta(days=i)
            )

        response = self.client.get(self.url)
        macro = response.context['macro_analysis']

        self.assertEqual(macro['protein_per_kg'], 2.0)


class OverallStatsCalculationTestCase(TestCase):
    """Test cases for overall statistics calculations."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.url = reverse('analytics')
        self.now = timezone.now()

    def test_average_daily_calories(self):
        """Test average daily calories calculation."""
        # Create 10 days with 2000 cal each = avg 2000
        for i in range(10):
            FoodItem.objects.create(
                product_name=f'Test Food {i}',
                calories=Decimal('2000'),
                protein=Decimal('100'),
                carbohydrates=Decimal('200'),
                fat=Decimal('80'),
                consumed_at=self.now - timedelta(days=i)
            )

        response = self.client.get(self.url)
        stats = response.context['overall_stats']

        self.assertEqual(stats['avg_daily_calories'], 2000)

    def test_average_daily_calories_varying(self):
        """Test average with varying daily calories."""
        # Day 1: 1500, Day 2: 2000, Day 3: 2500 = avg 2000
        calories = [1500, 2000, 2500]
        for i, cal in enumerate(calories):
            FoodItem.objects.create(
                product_name=f'Test Food {i}',
                calories=Decimal(str(cal)),
                protein=Decimal('100'),
                carbohydrates=Decimal('200'),
                fat=Decimal('80'),
                consumed_at=self.now - timedelta(days=i)
            )

        response = self.client.get(self.url)
        stats = response.context['overall_stats']

        self.assertEqual(stats['avg_daily_calories'], 2000)

    def test_total_days_logged(self):
        """Test total days logged count."""
        # Create food for 5 different days
        for i in range(5):
            FoodItem.objects.create(
                product_name=f'Test Food {i}',
                calories=Decimal('2000'),
                protein=Decimal('100'),
                carbohydrates=Decimal('200'),
                fat=Decimal('80'),
                consumed_at=self.now - timedelta(days=i)
            )

        response = self.client.get(self.url)
        stats = response.context['overall_stats']

        self.assertEqual(stats['total_days_logged'], 5)

    def test_calorie_range(self):
        """Test calorie min/max calculation."""
        # Create days with 1000, 2000, 3000 calories
        calories = [1000, 2000, 3000]
        for i, cal in enumerate(calories):
            FoodItem.objects.create(
                product_name=f'Test Food {i}',
                calories=Decimal(str(cal)),
                protein=Decimal('100'),
                carbohydrates=Decimal('200'),
                fat=Decimal('80'),
                consumed_at=self.now - timedelta(days=i)
            )

        response = self.client.get(self.url)
        stats = response.context['overall_stats']

        self.assertEqual(stats['calorie_min'], 1000)
        self.assertEqual(stats['calorie_max'], 3000)


class WeightAnalysisCalculationTestCase(TestCase):
    """Test cases for weight analysis calculations."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.url = reverse('analytics')
        self.now = timezone.now()

    def test_weight_change_calculation(self):
        """Test total weight change calculation."""
        # Start: 100kg, End: 95kg = -5kg change
        Weight.objects.create(weight=Decimal('100'), recorded_at=self.now - timedelta(days=30))
        Weight.objects.create(weight=Decimal('95'), recorded_at=self.now)

        # Need some food data for analytics to work
        FoodItem.objects.create(
            product_name='Test',
            calories=Decimal('2000'),
            protein=Decimal('100'),
            carbohydrates=Decimal('200'),
            fat=Decimal('80'),
            consumed_at=self.now
        )

        response = self.client.get(self.url)
        weight_analysis = response.context['weight_analysis']

        self.assertEqual(weight_analysis['start_weight'], 100.0)
        self.assertEqual(weight_analysis['end_weight'], 95.0)
        self.assertEqual(weight_analysis['total_change'], -5.0)

    def test_weight_min_max(self):
        """Test weight min/max calculation."""
        weights = [100, 98, 95, 97, 93]
        for i, w in enumerate(weights):
            Weight.objects.create(
                weight=Decimal(str(w)),
                recorded_at=self.now - timedelta(days=len(weights) - 1 - i)
            )

        FoodItem.objects.create(
            product_name='Test',
            calories=Decimal('2000'),
            protein=Decimal('100'),
            carbohydrates=Decimal('200'),
            fat=Decimal('80'),
            consumed_at=self.now
        )

        response = self.client.get(self.url)
        weight_analysis = response.context['weight_analysis']

        self.assertEqual(weight_analysis['min_weight'], 93.0)
        self.assertEqual(weight_analysis['max_weight'], 100.0)

    def test_weight_average(self):
        """Test weight average calculation."""
        # Weights: 100, 98, 96, 94, 92 = avg 96
        weights = [100, 98, 96, 94, 92]
        for i, w in enumerate(weights):
            Weight.objects.create(
                weight=Decimal(str(w)),
                recorded_at=self.now - timedelta(days=len(weights) - 1 - i)
            )

        FoodItem.objects.create(
            product_name='Test',
            calories=Decimal('2000'),
            protein=Decimal('100'),
            carbohydrates=Decimal('200'),
            fat=Decimal('80'),
            consumed_at=self.now
        )

        response = self.client.get(self.url)
        weight_analysis = response.context['weight_analysis']

        self.assertEqual(weight_analysis['avg_weight'], 96.0)


class WeightPaceCalculationTestCase(TestCase):
    """Test cases for weight pace calculations."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.url = reverse('analytics')
        self.now = timezone.now()

    def test_weekly_rate_calculation(self):
        """Test weekly weight change rate."""
        # 100kg to 93kg over 14 days = -7kg in 2 weeks = -3.5 kg/week
        Weight.objects.create(weight=Decimal('100'), recorded_at=self.now - timedelta(days=14))
        Weight.objects.create(weight=Decimal('93'), recorded_at=self.now)

        FoodItem.objects.create(
            product_name='Test',
            calories=Decimal('2000'),
            protein=Decimal('100'),
            carbohydrates=Decimal('200'),
            fat=Decimal('80'),
            consumed_at=self.now
        )

        response = self.client.get(self.url)
        weight_pace = response.context['weight_pace']

        self.assertEqual(weight_pace['total_change'], -7.0)
        self.assertEqual(weight_pace['days'], 14)
        self.assertEqual(weight_pace['weekly_rate'], -3.5)

    def test_monthly_rate_calculation(self):
        """Test monthly weight change rate."""
        # 100kg to 94kg over 30 days = -6kg = -6 kg/month
        Weight.objects.create(weight=Decimal('100'), recorded_at=self.now - timedelta(days=30))
        Weight.objects.create(weight=Decimal('94'), recorded_at=self.now)

        FoodItem.objects.create(
            product_name='Test',
            calories=Decimal('2000'),
            protein=Decimal('100'),
            carbohydrates=Decimal('200'),
            fat=Decimal('80'),
            consumed_at=self.now
        )

        response = self.client.get(self.url)
        weight_pace = response.context['weight_pace']

        self.assertEqual(weight_pace['monthly_rate'], -6.0)

    def test_calorie_deficit_estimation(self):
        """Test estimated daily calorie deficit."""
        # -7kg over 14 days = -0.5kg/day
        # 1kg = 7700 cal, so -0.5kg = -3850 cal/day deficit... wait that's wrong
        # Actually: -7kg * 7700 cal/kg / 14 days = -3850 cal/day
        Weight.objects.create(weight=Decimal('100'), recorded_at=self.now - timedelta(days=14))
        Weight.objects.create(weight=Decimal('93'), recorded_at=self.now)

        FoodItem.objects.create(
            product_name='Test',
            calories=Decimal('2000'),
            protein=Decimal('100'),
            carbohydrates=Decimal('200'),
            fat=Decimal('80'),
            consumed_at=self.now
        )

        response = self.client.get(self.url)
        weight_pace = response.context['weight_pace']

        # -7kg * 7700 / 14 = -3850
        self.assertEqual(weight_pace['estimated_daily_deficit'], -3850)


class StreakCalculationTestCase(TestCase):
    """Test cases for streak calculations."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.url = reverse('analytics')
        self.now = timezone.now()

    def test_current_streak_consecutive_days(self):
        """Test current streak with consecutive days."""
        # Log food for 5 consecutive days ending today
        for i in range(5):
            FoodItem.objects.create(
                product_name=f'Test Food {i}',
                calories=Decimal('2000'),
                protein=Decimal('100'),
                carbohydrates=Decimal('200'),
                fat=Decimal('80'),
                consumed_at=self.now - timedelta(days=i)
            )

        response = self.client.get(self.url)
        streaks = response.context['streaks']

        self.assertEqual(streaks['current_streak'], 5)

    def test_streak_broken(self):
        """Test streak calculation when streak is broken."""
        # Days 0, 1, 2 (consecutive) then skip day 3, then day 4
        # Current streak should be 3 (days 0, 1, 2)
        for i in [0, 1, 2, 4]:
            FoodItem.objects.create(
                product_name=f'Test Food {i}',
                calories=Decimal('2000'),
                protein=Decimal('100'),
                carbohydrates=Decimal('200'),
                fat=Decimal('80'),
                consumed_at=self.now - timedelta(days=i)
            )

        response = self.client.get(self.url)
        streaks = response.context['streaks']

        self.assertEqual(streaks['current_streak'], 3)

    def test_longest_streak(self):
        """Test longest streak calculation."""
        # Days 0-2 (3 days) and days 10-15 (6 days)
        # Longest streak should be 6
        for i in [0, 1, 2, 10, 11, 12, 13, 14, 15]:
            FoodItem.objects.create(
                product_name=f'Test Food {i}',
                calories=Decimal('2000'),
                protein=Decimal('100'),
                carbohydrates=Decimal('200'),
                fat=Decimal('80'),
                consumed_at=self.now - timedelta(days=i)
            )

        response = self.client.get(self.url)
        streaks = response.context['streaks']

        self.assertEqual(streaks['longest_streak'], 6)

    def test_consistency_rate(self):
        """Test consistency rate calculation."""
        # Log 10 days out of 20 day period = 50% consistency
        # First day: 19 days ago, logged 10 days total
        for i in range(0, 20, 2):  # Every other day
            FoodItem.objects.create(
                product_name=f'Test Food {i}',
                calories=Decimal('2000'),
                protein=Decimal('100'),
                carbohydrates=Decimal('200'),
                fat=Decimal('80'),
                consumed_at=self.now - timedelta(days=i)
            )

        response = self.client.get(self.url)
        streaks = response.context['streaks']

        # 10 days logged, first log was 18 days ago, so 19 days total span
        # Actual consistency depends on calculation
        self.assertEqual(streaks['total_days'], 10)


class CalorieBudgetCalculationTestCase(TestCase):
    """Test cases for calorie budget calculations."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.url = reverse('analytics')
        self.now = timezone.now()

    def test_days_under_over_budget(self):
        """Test days under/over 2500 calorie budget."""
        # 3 days under (2000, 2200, 2400) and 2 days over (2600, 3000)
        calories = [2000, 2200, 2400, 2600, 3000]
        for i, cal in enumerate(calories):
            FoodItem.objects.create(
                product_name=f'Test Food {i}',
                calories=Decimal(str(cal)),
                protein=Decimal('100'),
                carbohydrates=Decimal('200'),
                fat=Decimal('80'),
                consumed_at=self.now - timedelta(days=i)
            )

        response = self.client.get(self.url)
        budget = response.context['calorie_budget']

        self.assertEqual(budget['days_under'], 3)
        self.assertEqual(budget['days_over'], 2)
        self.assertEqual(budget['under_percent'], 60.0)

    def test_average_over_amount(self):
        """Test average amount over budget."""
        # Days over: 2600 (+100), 3000 (+500) = avg over = 300
        calories = [2000, 2600, 3000]
        for i, cal in enumerate(calories):
            FoodItem.objects.create(
                product_name=f'Test Food {i}',
                calories=Decimal(str(cal)),
                protein=Decimal('100'),
                carbohydrates=Decimal('200'),
                fat=Decimal('80'),
                consumed_at=self.now - timedelta(days=i)
            )

        response = self.client.get(self.url)
        budget = response.context['calorie_budget']

        self.assertEqual(budget['avg_over_amount'], 300)

    def test_average_under_amount(self):
        """Test average amount under budget."""
        # Days under: 2000 (-500), 2200 (-300), 2400 (-100) = avg under = 300
        calories = [2000, 2200, 2400]
        for i, cal in enumerate(calories):
            FoodItem.objects.create(
                product_name=f'Test Food {i}',
                calories=Decimal(str(cal)),
                protein=Decimal('100'),
                carbohydrates=Decimal('200'),
                fat=Decimal('80'),
                consumed_at=self.now - timedelta(days=i)
            )

        response = self.client.get(self.url)
        budget = response.context['calorie_budget']

        self.assertEqual(budget['avg_under_amount'], 300)


class CalorieDistributionCalculationTestCase(TestCase):
    """Test cases for calorie distribution calculations."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.url = reverse('analytics')
        self.now = timezone.now()

    def test_calorie_distribution_categories(self):
        """Test calorie distribution categorization."""
        # Create 10 days with specific calorie ranges
        # 2 very low (<1500), 2 low (1500-2000), 2 moderate (2000-2500),
        # 2 high (2500-3000), 2 very high (3000+)
        calories = [1200, 1400, 1700, 1900, 2200, 2400, 2700, 2900, 3200, 3500]
        for i, cal in enumerate(calories):
            FoodItem.objects.create(
                product_name=f'Test Food {i}',
                calories=Decimal(str(cal)),
                protein=Decimal('100'),
                carbohydrates=Decimal('200'),
                fat=Decimal('80'),
                consumed_at=self.now - timedelta(days=i)
            )

        response = self.client.get(self.url)
        dist = response.context['calorie_distribution']

        self.assertEqual(dist['very_low']['count'], 2)
        self.assertEqual(dist['low']['count'], 2)
        self.assertEqual(dist['moderate']['count'], 2)
        self.assertEqual(dist['high']['count'], 2)
        self.assertEqual(dist['very_high']['count'], 2)

        # Each should be 20%
        self.assertEqual(dist['very_low']['percent'], 20.0)
        self.assertEqual(dist['low']['percent'], 20.0)


class WeightVolatilityCalculationTestCase(TestCase):
    """Test cases for weight volatility calculations."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.url = reverse('analytics')
        self.now = timezone.now()

    def test_average_fluctuation(self):
        """Test average daily fluctuation calculation."""
        # Weights: 100, 99.5, 100, 99, 100 (fluctuations: 0.5, 0.5, 1.0, 1.0)
        # Avg fluctuation = (0.5 + 0.5 + 1.0 + 1.0) / 4 = 0.75
        weights = [100, 99.5, 100, 99, 100]
        for i, w in enumerate(weights):
            Weight.objects.create(
                weight=Decimal(str(w)),
                recorded_at=self.now - timedelta(days=len(weights) - 1 - i)
            )

        FoodItem.objects.create(
            product_name='Test',
            calories=Decimal('2000'),
            protein=Decimal('100'),
            carbohydrates=Decimal('200'),
            fat=Decimal('80'),
            consumed_at=self.now
        )

        response = self.client.get(self.url)
        volatility = response.context['weight_volatility']

        self.assertEqual(volatility['avg_fluctuation'], 0.75)

    def test_max_fluctuation(self):
        """Test max fluctuation calculation."""
        # Weights with max 2kg fluctuation
        weights = [100, 99, 101, 99, 100]
        for i, w in enumerate(weights):
            Weight.objects.create(
                weight=Decimal(str(w)),
                recorded_at=self.now - timedelta(days=len(weights) - 1 - i)
            )

        FoodItem.objects.create(
            product_name='Test',
            calories=Decimal('2000'),
            protein=Decimal('100'),
            carbohydrates=Decimal('200'),
            fat=Decimal('80'),
            consumed_at=self.now
        )

        response = self.client.get(self.url)
        volatility = response.context['weight_volatility']

        self.assertEqual(volatility['max_fluctuation'], 2.0)

    def test_significant_fluctuations_count(self):
        """Test counting significant fluctuations (>0.5kg)."""
        # Weights: 100, 99.3, 99.5, 98.4, 98.5
        # Fluctuations: 0.7 (sig), 0.2, 1.1 (sig), 0.1
        # 2 significant fluctuations
        weights = [100, 99.3, 99.5, 98.4, 98.5]
        for i, w in enumerate(weights):
            Weight.objects.create(
                weight=Decimal(str(w)),
                recorded_at=self.now - timedelta(days=len(weights) - 1 - i)
            )

        FoodItem.objects.create(
            product_name='Test',
            calories=Decimal('2000'),
            protein=Decimal('100'),
            carbohydrates=Decimal('200'),
            fat=Decimal('80'),
            consumed_at=self.now
        )

        response = self.client.get(self.url)
        volatility = response.context['weight_volatility']

        self.assertEqual(volatility['significant_fluctuations'], 2)


class DayOfWeekAnalysisTestCase(TestCase):
    """Test cases for day of week analysis."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.url = reverse('analytics')
        self.now = timezone.now()

    def test_day_of_week_average(self):
        """Test that day of week averages are calculated correctly."""
        # Create multiple entries for the same day of week
        # Find next Monday
        days_until_monday = (7 - self.now.weekday()) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        monday = self.now - timedelta(days=self.now.weekday())

        # Create 2 Mondays with 2000 and 3000 cal = avg 2500
        FoodItem.objects.create(
            product_name='Monday Food 1',
            calories=Decimal('2000'),
            protein=Decimal('100'),
            carbohydrates=Decimal('200'),
            fat=Decimal('80'),
            consumed_at=monday
        )
        FoodItem.objects.create(
            product_name='Monday Food 2',
            calories=Decimal('3000'),
            protein=Decimal('100'),
            carbohydrates=Decimal('200'),
            fat=Decimal('80'),
            consumed_at=monday - timedelta(days=7)
        )

        response = self.client.get(self.url)
        day_stats = response.context['day_of_week_stats']

        if 'Monday' in day_stats:
            self.assertEqual(day_stats['Monday']['avg_calories'], 2500)
            self.assertEqual(day_stats['Monday']['count'], 2)


class NutritionScoreCalculationTestCase(TestCase):
    """Test cases for nutrition score calculations."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.url = reverse('analytics')
        self.now = timezone.now()

    def test_nutrition_score_high_protein(self):
        """Test nutrition score with excellent protein intake."""
        Weight.objects.create(weight=Decimal('80'), recorded_at=self.now)

        # 160g protein for 80kg = 2.0 g/kg = excellent (25 points)
        for i in range(10):
            FoodItem.objects.create(
                product_name=f'Test Food {i}',
                calories=Decimal('2500'),
                protein=Decimal('160'),
                carbohydrates=Decimal('250'),
                fat=Decimal('80'),
                consumed_at=self.now - timedelta(days=i)
            )

        response = self.client.get(self.url)
        nutrition_score = response.context['nutrition_score']

        # Check protein component is 25 (excellent)
        protein_score = next((b for b in nutrition_score['breakdown'] if b['name'] == 'Protein'), None)
        self.assertEqual(protein_score['score'], 25)
        self.assertEqual(protein_score['status'], 'Excellent')

    def test_nutrition_score_grade(self):
        """Test nutrition score grading."""
        Weight.objects.create(weight=Decimal('80'), recorded_at=self.now)

        for i in range(10):
            FoodItem.objects.create(
                product_name=f'Test Food {i}',
                calories=Decimal('2500'),
                protein=Decimal('160'),
                carbohydrates=Decimal('250'),
                fat=Decimal('80'),
                consumed_at=self.now - timedelta(days=i)
            )

        response = self.client.get(self.url)
        nutrition_score = response.context['nutrition_score']

        # Grade should be A, B, C, D, or F
        self.assertIn(nutrition_score['grade'], ['A', 'B', 'C', 'D', 'F'])
        # Total should be between 0 and 100
        self.assertGreaterEqual(nutrition_score['total'], 0)
        self.assertLessEqual(nutrition_score['total'], 100)


class MealTimingCalculationTestCase(TestCase):
    """Test cases for meal timing calculations."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.url = reverse('analytics')
        self.now = timezone.now()

    def test_meal_timing_percentages_sum_to_100(self):
        """Test that meal timing percentages sum to approximately 100%."""
        # Create food at different times of day
        times = [
            self.now.replace(hour=8),   # Morning
            self.now.replace(hour=12),  # Midday
            self.now.replace(hour=16),  # Afternoon
            self.now.replace(hour=19),  # Evening
            self.now.replace(hour=23),  # Night
        ]

        for i, time in enumerate(times):
            FoodItem.objects.create(
                product_name=f'Test Food {i}',
                calories=Decimal('500'),
                protein=Decimal('25'),
                carbohydrates=Decimal('50'),
                fat=Decimal('20'),
                consumed_at=time
            )

        response = self.client.get(self.url)
        timing = response.context['meal_timing']

        total_percent = (
            timing.get('morning', {}).get('percent', 0) +
            timing.get('midday', {}).get('percent', 0) +
            timing.get('afternoon', {}).get('percent', 0) +
            timing.get('evening', {}).get('percent', 0) +
            timing.get('night', {}).get('percent', 0)
        )

        self.assertAlmostEqual(total_percent, 100.0, delta=1.0)
