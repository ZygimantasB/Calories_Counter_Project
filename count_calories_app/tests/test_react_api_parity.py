import json
from datetime import timedelta
from decimal import Decimal
from django.test import TestCase, Client
from django.utils import timezone
from count_calories_app.models import Weight, RunningSession, FoodItem, BodyMeasurement


class WeightEditAPITestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.weight = Weight.objects.create(
            weight=Decimal('80.0'),
            recorded_at=timezone.now(),
            notes='Original note'
        )

    def test_update_weight_value(self):
        response = self.client.put(
            f'/api/react/weight-items/{self.weight.id}/update/',
            json.dumps({'weight': 82.5}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.weight.refresh_from_db()
        self.assertEqual(float(self.weight.weight), 82.5)

    def test_update_weight_notes(self):
        response = self.client.put(
            f'/api/react/weight-items/{self.weight.id}/update/',
            json.dumps({'notes': 'Updated note'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.weight.refresh_from_db()
        self.assertEqual(self.weight.notes, 'Updated note')

    def test_update_nonexistent_weight_returns_404(self):
        response = self.client.put(
            '/api/react/weight-items/99999/update/',
            json.dumps({'weight': 80}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 404)


class RunningEditDeleteAPITestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.session = RunningSession.objects.create(
            date=timezone.now(),
            distance=Decimal('5.0'),
            duration=timedelta(minutes=30),
            notes='Test run'
        )

    def test_update_running_distance(self):
        response = self.client.put(
            f'/api/react/running-items/{self.session.id}/update/',
            json.dumps({'distance': 8.5}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.session.refresh_from_db()
        self.assertEqual(float(self.session.distance), 8.5)

    def test_delete_running_session(self):
        response = self.client.delete(f'/api/react/running-items/{self.session.id}/delete/')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(RunningSession.objects.filter(id=self.session.id).exists())

    def test_delete_nonexistent_running_returns_404(self):
        response = self.client.delete('/api/react/running-items/99999/delete/')
        self.assertEqual(response.status_code, 404)


class CopyDayFoodsAPITestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.yesterday = timezone.now() - timedelta(days=1)
        FoodItem.objects.create(product_name='Test Food', calories=Decimal('500'), protein=Decimal('30'), carbohydrates=Decimal('50'), fat=Decimal('20'), consumed_at=self.yesterday)

    def test_copy_day_creates_items(self):
        yesterday_str = self.yesterday.strftime('%Y-%m-%d')
        response = self.client.post('/api/react/food-items/copy-day/', json.dumps({'source_date': yesterday_str}), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['copied_count'], 1)

    def test_copy_day_no_items_returns_404(self):
        response = self.client.post('/api/react/food-items/copy-day/', json.dumps({'source_date': '2020-01-01'}), content_type='application/json')
        self.assertEqual(response.status_code, 404)


class BodyMeasurementAPITestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.measurement = BodyMeasurement.objects.create(
            date=timezone.now(),
            chest=Decimal('100.0'),
            belly=Decimal('85.0'),
        )

    def test_add_measurement(self):
        response = self.client.post('/api/react/body-measurements/add/',
            json.dumps({'chest': 101.0, 'belly': 84.0}),
            content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])

    def test_update_measurement(self):
        response = self.client.put(
            f'/api/react/body-measurements/{self.measurement.id}/update/',
            json.dumps({'chest': 99.0}),
            content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.measurement.refresh_from_db()
        self.assertEqual(float(self.measurement.chest), 99.0)

    def test_delete_measurement(self):
        response = self.client.delete(f'/api/react/body-measurements/{self.measurement.id}/delete/')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(BodyMeasurement.objects.filter(id=self.measurement.id).exists())
