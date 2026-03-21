import json
from datetime import timedelta
from decimal import Decimal
from django.test import TestCase, Client
from django.utils import timezone
from count_calories_app.models import Weight, RunningSession, FoodItem, BodyMeasurement, MealTemplate, MealTemplateItem, WorkoutSession


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


class MealTemplateAPITestCase(TestCase):
    def setUp(self):
        self.client = Client()
        # Create a food item for today so we can save it as a template
        self.food = FoodItem.objects.create(
            product_name='Chicken Breast',
            calories=Decimal('165'),
            protein=Decimal('31'),
            carbohydrates=Decimal('0'),
            fat=Decimal('3.6'),
            consumed_at=timezone.now(),
        )
        # Pre-existing template for apply/delete tests
        self.template = MealTemplate.objects.create(name='Existing Template')
        MealTemplateItem.objects.create(
            template=self.template,
            product_name='Rice',
            calories=Decimal('200'),
            protein=Decimal('4'),
            carbohydrates=Decimal('44'),
            fat=Decimal('0.5'),
        )

    def test_list_templates(self):
        response = self.client.get('/api/react/meal-templates/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('templates', data)
        self.assertEqual(len(data['templates']), 1)
        t = data['templates'][0]
        self.assertEqual(t['name'], 'Existing Template')
        self.assertEqual(t['items_count'], 1)
        self.assertAlmostEqual(t['total_calories'], 200.0)

    def test_save_today_as_template(self):
        today_str = timezone.now().strftime('%Y-%m-%d')
        response = self.client.post(
            '/api/react/meal-templates/add/',
            json.dumps({'name': 'My Saved Template', 'date': today_str}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['items_count'], 1)
        self.assertTrue(MealTemplate.objects.filter(name='My Saved Template').exists())

    def test_save_template_no_name_returns_400(self):
        response = self.client.post(
            '/api/react/meal-templates/add/',
            json.dumps({'name': ''}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)

    def test_save_template_no_food_returns_404(self):
        response = self.client.post(
            '/api/react/meal-templates/add/',
            json.dumps({'name': 'Empty Day', 'date': '2000-01-01'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 404)

    def test_apply_template_creates_food_items(self):
        count_before = FoodItem.objects.count()
        response = self.client.post(f'/api/react/meal-templates/{self.template.id}/log/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['items_logged'], 1)
        self.assertEqual(FoodItem.objects.count(), count_before + 1)

    def test_apply_nonexistent_template_returns_404(self):
        response = self.client.post('/api/react/meal-templates/99999/log/')
        self.assertEqual(response.status_code, 404)

    def test_delete_template(self):
        response = self.client.delete(f'/api/react/meal-templates/{self.template.id}/delete/')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(MealTemplate.objects.filter(id=self.template.id).exists())

    def test_delete_nonexistent_template_returns_404(self):
        response = self.client.delete('/api/react/meal-templates/99999/delete/')
        self.assertEqual(response.status_code, 404)


class WorkoutCRUDAPITestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_add_workout(self):
        response = self.client.post('/api/react/workouts/add/',
            json.dumps({'name': 'Leg Day', 'notes': 'Heavy day'}),
            content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertIn('id', data)

    def test_add_workout_default_name(self):
        response = self.client.post('/api/react/workouts/add/',
            json.dumps({}),
            content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        workout = WorkoutSession.objects.get(id=data['id'])
        self.assertEqual(workout.name, 'Workout')

    def test_update_workout_name(self):
        workout = WorkoutSession.objects.create(name='Old Name', date=timezone.now())
        response = self.client.put(
            f'/api/react/workouts/{workout.id}/update/',
            json.dumps({'name': 'New Name'}),
            content_type='application/json')
        self.assertEqual(response.status_code, 200)
        workout.refresh_from_db()
        self.assertEqual(workout.name, 'New Name')

    def test_update_workout_notes(self):
        workout = WorkoutSession.objects.create(name='Test', date=timezone.now())
        response = self.client.put(
            f'/api/react/workouts/{workout.id}/update/',
            json.dumps({'notes': 'Great session'}),
            content_type='application/json')
        self.assertEqual(response.status_code, 200)
        workout.refresh_from_db()
        self.assertEqual(workout.notes, 'Great session')

    def test_update_nonexistent_workout_returns_404(self):
        response = self.client.put(
            '/api/react/workouts/99999/update/',
            json.dumps({'name': 'X'}),
            content_type='application/json')
        self.assertEqual(response.status_code, 404)

    def test_delete_workout(self):
        workout = WorkoutSession.objects.create(name='Test', date=timezone.now())
        response = self.client.delete(f'/api/react/workouts/{workout.id}/delete/')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(WorkoutSession.objects.filter(id=workout.id).exists())

    def test_delete_nonexistent_workout_returns_404(self):
        response = self.client.delete('/api/react/workouts/99999/delete/')
        self.assertEqual(response.status_code, 404)


class ExerciseLibraryCRUDTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_add_exercise(self):
        response = self.client.post(
            '/api/react/exercises/add/',
            json.dumps({'name': 'Squats', 'muscle_group': 'Legs'}),
            content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertIn('id', data)

    def test_add_exercise_with_description(self):
        response = self.client.post(
            '/api/react/exercises/add/',
            json.dumps({'name': 'Bench Press', 'muscle_group': 'Chest', 'description': 'Flat bench press'}),
            content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])

    def test_add_exercise_no_name_returns_400(self):
        response = self.client.post(
            '/api/react/exercises/add/',
            json.dumps({'name': ''}),
            content_type='application/json')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])

    def test_add_exercise_whitespace_name_returns_400(self):
        response = self.client.post(
            '/api/react/exercises/add/',
            json.dumps({'name': '   '}),
            content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_delete_exercise(self):
        from count_calories_app.models import Exercise
        ex = Exercise.objects.create(name='Test', muscle_group='Test')
        response = self.client.delete(f'/api/react/exercises/{ex.id}/delete/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertFalse(Exercise.objects.filter(id=ex.id).exists())

    def test_delete_nonexistent_exercise_returns_404(self):
        response = self.client.delete('/api/react/exercises/99999/delete/')
        self.assertEqual(response.status_code, 404)
