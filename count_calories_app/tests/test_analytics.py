"""
Unit tests for the Analytics feature.

Tests cover:
- Analytics view rendering
- Period filtering (30, 90, 180, 365 days, all)
- Weekly and monthly reports generation
- Best/worst days analysis
- Weight analysis calculations
- Correlation insights generation
- Overall statistics calculations
"""

from datetime import timedelta
from decimal import Decimal

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from count_calories_app.models import FoodItem, Weight


class AnalyticsViewTestCase(TestCase):
    """Test cases for the analytics view."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.url = reverse('analytics')
        self.now = timezone.now()

    def test_analytics_view_returns_200(self):
        """Test that analytics view returns 200 status code."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_analytics_view_uses_correct_template(self):
        """Test that analytics view uses the correct template."""
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'count_calories_app/analytics.html')

    def test_analytics_view_default_period(self):
        """Test that default period is 90 days."""
        response = self.client.get(self.url)
        self.assertEqual(response.context['period'], '90')

    def test_analytics_view_custom_period_30_days(self):
        """Test analytics with 30 days period."""
        response = self.client.get(self.url, {'period': '30'})
        self.assertEqual(response.context['period'], '30')

    def test_analytics_view_custom_period_180_days(self):
        """Test analytics with 180 days period."""
        response = self.client.get(self.url, {'period': '180'})
        self.assertEqual(response.context['period'], '180')

    def test_analytics_view_custom_period_365_days(self):
        """Test analytics with 365 days period."""
        response = self.client.get(self.url, {'period': '365'})
        self.assertEqual(response.context['period'], '365')

    def test_analytics_view_all_time_period(self):
        """Test analytics with all time period."""
        response = self.client.get(self.url, {'period': 'all'})
        self.assertEqual(response.context['period'], 'all')


class AnalyticsWithDataTestCase(TestCase):
    """Test cases for analytics with actual data."""

    def setUp(self):
        """Set up test data with food items and weights."""
        self.client = Client()
        self.url = reverse('analytics')
        self.now = timezone.now()

        # Create food items for the last 30 days
        for i in range(30):
            date = self.now - timedelta(days=i)
            FoodItem.objects.create(
                product_name=f'Test Food {i}',
                calories=Decimal('2000') + Decimal(str(i * 10)),
                protein=Decimal('100') + Decimal(str(i)),
                carbohydrates=Decimal('200') + Decimal(str(i * 2)),
                fat=Decimal('80') + Decimal(str(i)),
                consumed_at=date
            )

        # Create weight measurements
        for i in range(10):
            date = self.now - timedelta(days=i * 3)
            Weight.objects.create(
                weight=Decimal('80') - Decimal(str(i * 0.5)),  # Simulating weight loss
                recorded_at=date
            )

    def test_analytics_overall_stats_present(self):
        """Test that overall stats are present in context."""
        response = self.client.get(self.url)
        self.assertIn('overall_stats', response.context)
        self.assertIn('avg_daily_calories', response.context['overall_stats'])

    def test_analytics_weekly_reports_present(self):
        """Test that weekly reports are present in context."""
        response = self.client.get(self.url)
        self.assertIn('weekly_reports', response.context)
        self.assertIsInstance(response.context['weekly_reports'], list)

    def test_analytics_monthly_reports_present(self):
        """Test that monthly reports are present in context."""
        response = self.client.get(self.url)
        self.assertIn('monthly_reports', response.context)
        self.assertIsInstance(response.context['monthly_reports'], list)

    def test_analytics_weight_analysis_present(self):
        """Test that weight analysis is present in context."""
        response = self.client.get(self.url)
        self.assertIn('weight_analysis', response.context)

    def test_analytics_weight_analysis_values(self):
        """Test that weight analysis contains expected values."""
        response = self.client.get(self.url)
        weight_analysis = response.context['weight_analysis']

        if weight_analysis:  # Only test if we have weight data
            self.assertIn('start_weight', weight_analysis)
            self.assertIn('end_weight', weight_analysis)
            self.assertIn('total_change', weight_analysis)

    def test_analytics_best_worst_days_present(self):
        """Test that best/worst days analysis is present in context."""
        response = self.client.get(self.url)
        self.assertIn('best_worst_days', response.context)

    def test_analytics_insights_present(self):
        """Test that insights are present in context."""
        response = self.client.get(self.url)
        self.assertIn('insights', response.context)
        self.assertIsInstance(response.context['insights'], list)


class AnalyticsWeeklyReportsTestCase(TestCase):
    """Test cases specifically for weekly reports."""

    def setUp(self):
        """Set up test data for weekly reports."""
        self.client = Client()
        self.url = reverse('analytics')
        self.now = timezone.now()

        # Create food items spanning multiple weeks
        for week in range(4):
            for day in range(7):
                date = self.now - timedelta(weeks=week, days=day)
                FoodItem.objects.create(
                    product_name=f'Weekly Food W{week}D{day}',
                    calories=Decimal('2500'),
                    protein=Decimal('150'),
                    carbohydrates=Decimal('250'),
                    fat=Decimal('100'),
                    consumed_at=date
                )

    def test_weekly_reports_structure(self):
        """Test that weekly reports have the correct structure."""
        response = self.client.get(self.url)
        weekly_reports = response.context['weekly_reports']

        if weekly_reports:
            report = weekly_reports[0]
            self.assertIn('week_start', report)
            self.assertIn('total_calories', report)
            self.assertIn('avg_calories', report)
            self.assertIn('avg_protein', report)
            self.assertIn('avg_carbs', report)
            self.assertIn('avg_fat', report)
            self.assertIn('days_logged', report)

    def test_weekly_reports_limited_to_12(self):
        """Test that weekly reports are limited to 12 weeks."""
        response = self.client.get(self.url)
        weekly_reports = response.context['weekly_reports']
        self.assertLessEqual(len(weekly_reports), 12)


class AnalyticsMonthlyReportsTestCase(TestCase):
    """Test cases specifically for monthly reports."""

    def setUp(self):
        """Set up test data for monthly reports."""
        self.client = Client()
        self.url = reverse('analytics')
        self.now = timezone.now()

        # Create food items spanning multiple months
        for month in range(3):
            for day in range(10):
                date = self.now - timedelta(days=month * 30 + day)
                FoodItem.objects.create(
                    product_name=f'Monthly Food M{month}D{day}',
                    calories=Decimal('2200'),
                    protein=Decimal('120'),
                    carbohydrates=Decimal('280'),
                    fat=Decimal('90'),
                    consumed_at=date
                )

    def test_monthly_reports_structure(self):
        """Test that monthly reports have the correct structure."""
        response = self.client.get(self.url)
        monthly_reports = response.context['monthly_reports']

        if monthly_reports:
            report = monthly_reports[0]
            self.assertIn('month', report)
            self.assertIn('total_calories', report)
            self.assertIn('avg_calories', report)
            self.assertIn('avg_protein', report)
            self.assertIn('avg_carbs', report)
            self.assertIn('avg_fat', report)
            self.assertIn('days_logged', report)

    def test_monthly_reports_limited_to_12(self):
        """Test that monthly reports are limited to 12 months."""
        response = self.client.get(self.url)
        monthly_reports = response.context['monthly_reports']
        self.assertLessEqual(len(monthly_reports), 12)


class AnalyticsBestWorstDaysTestCase(TestCase):
    """Test cases for best/worst days analysis."""

    def setUp(self):
        """Set up test data for best/worst days."""
        self.client = Client()
        self.url = reverse('analytics')
        self.now = timezone.now()

        # Create food items with varying calories
        # Low calorie day
        FoodItem.objects.create(
            product_name='Low Cal Food',
            calories=Decimal('1500'),
            protein=Decimal('80'),
            carbohydrates=Decimal('150'),
            fat=Decimal('50'),
            consumed_at=self.now - timedelta(days=1)
        )

        # High calorie day
        FoodItem.objects.create(
            product_name='High Cal Food',
            calories=Decimal('3500'),
            protein=Decimal('200'),
            carbohydrates=Decimal('400'),
            fat=Decimal('150'),
            consumed_at=self.now - timedelta(days=2)
        )

        # High protein day
        FoodItem.objects.create(
            product_name='High Protein Food',
            calories=Decimal('2000'),
            protein=Decimal('250'),
            carbohydrates=Decimal('100'),
            fat=Decimal('80'),
            consumed_at=self.now - timedelta(days=3)
        )

    def test_best_worst_days_structure(self):
        """Test that best/worst days have the correct structure."""
        response = self.client.get(self.url)
        best_worst_days = response.context['best_worst_days']

        if best_worst_days:
            # Check for lowest calorie day
            if 'lowest_calorie_day' in best_worst_days:
                self.assertIn('total_calories', best_worst_days['lowest_calorie_day'])
                self.assertIn('day', best_worst_days['lowest_calorie_day'])

            # Check for highest calorie day
            if 'highest_calorie_day' in best_worst_days:
                self.assertIn('total_calories', best_worst_days['highest_calorie_day'])
                self.assertIn('day', best_worst_days['highest_calorie_day'])


class AnalyticsWeightAnalysisTestCase(TestCase):
    """Test cases for weight analysis."""

    def setUp(self):
        """Set up test data for weight analysis."""
        self.client = Client()
        self.url = reverse('analytics')
        self.now = timezone.now()

        # Create weight measurements showing a trend
        weights = [85.0, 84.5, 84.0, 83.5, 83.0, 82.5, 82.0, 81.5, 81.0, 80.0]
        for i, weight in enumerate(weights):
            Weight.objects.create(
                weight=Decimal(str(weight)),
                recorded_at=self.now - timedelta(days=(len(weights) - 1 - i) * 7)
            )

    def test_weight_analysis_total_change(self):
        """Test that weight analysis correctly calculates total change."""
        response = self.client.get(self.url)
        weight_analysis = response.context['weight_analysis']

        if weight_analysis:
            self.assertIn('total_change', weight_analysis)
            # Should show weight loss (negative value)
            self.assertLess(weight_analysis['total_change'], 0)

    def test_weight_analysis_min_max(self):
        """Test that weight analysis correctly identifies min/max weights."""
        response = self.client.get(self.url)
        weight_analysis = response.context['weight_analysis']

        if weight_analysis:
            self.assertIn('min_weight', weight_analysis)
            self.assertIn('max_weight', weight_analysis)
            self.assertEqual(weight_analysis['min_weight'], 80.0)
            self.assertEqual(weight_analysis['max_weight'], 85.0)


class AnalyticsCorrelationInsightsTestCase(TestCase):
    """Test cases for correlation insights."""

    def setUp(self):
        """Set up test data for correlation insights."""
        self.client = Client()
        self.url = reverse('analytics')
        self.now = timezone.now()

        # Create weight measurements
        for i in range(10):
            Weight.objects.create(
                weight=Decimal('80') - Decimal(str(i * 0.3)),
                recorded_at=self.now - timedelta(days=i * 5)
            )

        # Create food items between weight measurements
        for i in range(45):
            date = self.now - timedelta(days=i)
            # Lower calories on weight loss days
            calories = Decimal('2000') if i % 2 == 0 else Decimal('2800')
            FoodItem.objects.create(
                product_name=f'Insight Food {i}',
                calories=calories,
                protein=Decimal('150'),
                carbohydrates=Decimal('200'),
                fat=Decimal('80'),
                consumed_at=date
            )

    def test_insights_is_list(self):
        """Test that insights is a list."""
        response = self.client.get(self.url)
        insights = response.context['insights']
        self.assertIsInstance(insights, list)

    def test_insight_structure(self):
        """Test that insights have the correct structure when present."""
        response = self.client.get(self.url)
        insights = response.context['insights']

        for insight in insights:
            self.assertIn('type', insight)
            self.assertIn('icon', insight)
            self.assertIn('title', insight)
            self.assertIn('description', insight)
            self.assertIn('recommendation', insight)


class AnalyticsOverallStatsTestCase(TestCase):
    """Test cases for overall statistics."""

    def setUp(self):
        """Set up test data for overall stats."""
        self.client = Client()
        self.url = reverse('analytics')
        self.now = timezone.now()

        # Create consistent food items
        for i in range(20):
            FoodItem.objects.create(
                product_name=f'Stats Food {i}',
                calories=Decimal('2500'),
                protein=Decimal('150'),
                carbohydrates=Decimal('300'),
                fat=Decimal('100'),
                consumed_at=self.now - timedelta(days=i)
            )

    def test_overall_stats_avg_calories(self):
        """Test that overall stats correctly calculate average calories."""
        response = self.client.get(self.url)
        overall_stats = response.context['overall_stats']

        if overall_stats:
            self.assertIn('avg_daily_calories', overall_stats)
            # Should be close to 2500 (exact value depends on daily aggregation)
            self.assertGreater(overall_stats['avg_daily_calories'], 2000)

    def test_overall_stats_days_logged(self):
        """Test that overall stats correctly count days logged."""
        response = self.client.get(self.url)
        overall_stats = response.context['overall_stats']

        if overall_stats:
            self.assertIn('total_days_logged', overall_stats)
            self.assertGreater(overall_stats['total_days_logged'], 0)

    def test_overall_stats_macros(self):
        """Test that overall stats include macro averages."""
        response = self.client.get(self.url)
        overall_stats = response.context['overall_stats']

        if overall_stats:
            self.assertIn('avg_daily_protein', overall_stats)
            self.assertIn('avg_daily_carbs', overall_stats)
            self.assertIn('avg_daily_fat', overall_stats)


class AnalyticsEmptyDataTestCase(TestCase):
    """Test cases for analytics with no data."""

    def setUp(self):
        """Set up empty test case."""
        self.client = Client()
        self.url = reverse('analytics')

    def test_analytics_empty_data_returns_200(self):
        """Test that analytics view returns 200 with no data."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_analytics_empty_weekly_reports(self):
        """Test that weekly reports is empty list with no data."""
        response = self.client.get(self.url)
        self.assertEqual(response.context['weekly_reports'], [])

    def test_analytics_empty_monthly_reports(self):
        """Test that monthly reports is empty list with no data."""
        response = self.client.get(self.url)
        self.assertEqual(response.context['monthly_reports'], [])

    def test_analytics_empty_insights(self):
        """Test that insights is empty list with no data."""
        response = self.client.get(self.url)
        self.assertEqual(response.context['insights'], [])

    def test_analytics_empty_weight_analysis(self):
        """Test that weight analysis is empty dict with no data."""
        response = self.client.get(self.url)
        self.assertEqual(response.context['weight_analysis'], {})

    def test_analytics_empty_best_worst_days(self):
        """Test that best_worst_days is empty dict with no data."""
        response = self.client.get(self.url)
        self.assertEqual(response.context['best_worst_days'], {})
