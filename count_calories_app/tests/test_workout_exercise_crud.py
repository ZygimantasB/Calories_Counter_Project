"""
Unit tests for workout exercise CRUD API endpoints.

Tests cover:
- Adding exercises to a workout session
- Updating exercises within a workout session
- Deleting exercises from a workout session
"""

import json
from decimal import Decimal

from django.test import TestCase, Client
from django.utils import timezone

from count_calories_app.models import Exercise, WorkoutSession, WorkoutExercise


class WorkoutExerciseCRUDTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.workout = WorkoutSession.objects.create(
            name='Test Workout',
            date=timezone.now(),
        )
        self.exercise = Exercise.objects.create(
            name='Bench Press',
            muscle_group='Chest',
        )

    # --- Add exercise tests ---

    def test_add_exercise_to_workout(self):
        response = self.client.post(
            f'/api/react/workouts/{self.workout.id}/exercises/add/',
            json.dumps({'exercise_id': self.exercise.id, 'sets': 3, 'reps': 10, 'weight': 80}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('id', data)

    def test_add_exercise_creates_db_record(self):
        self.client.post(
            f'/api/react/workouts/{self.workout.id}/exercises/add/',
            json.dumps({'exercise_id': self.exercise.id, 'sets': 3, 'reps': 10, 'weight': 80}),
            content_type='application/json',
        )
        self.assertEqual(WorkoutExercise.objects.filter(workout=self.workout).count(), 1)
        we = WorkoutExercise.objects.get(workout=self.workout)
        self.assertEqual(we.exercise, self.exercise)
        self.assertEqual(we.sets, 3)
        self.assertEqual(we.reps, 10)
        self.assertEqual(float(we.weight), 80.0)

    def test_add_exercise_without_weight(self):
        response = self.client.post(
            f'/api/react/workouts/{self.workout.id}/exercises/add/',
            json.dumps({'exercise_id': self.exercise.id, 'sets': 4, 'reps': 8}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        we = WorkoutExercise.objects.get(workout=self.workout)
        self.assertIsNone(we.weight)

    def test_add_exercise_with_notes(self):
        response = self.client.post(
            f'/api/react/workouts/{self.workout.id}/exercises/add/',
            json.dumps({'exercise_id': self.exercise.id, 'sets': 3, 'reps': 12, 'notes': 'Felt strong'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        we = WorkoutExercise.objects.get(workout=self.workout)
        self.assertEqual(we.notes, 'Felt strong')

    def test_add_exercise_to_nonexistent_workout_returns_404(self):
        response = self.client.post(
            '/api/react/workouts/99999/exercises/add/',
            json.dumps({'exercise_id': self.exercise.id, 'sets': 3, 'reps': 10}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 404)

    def test_add_exercise_with_nonexistent_exercise_returns_404(self):
        response = self.client.post(
            f'/api/react/workouts/{self.workout.id}/exercises/add/',
            json.dumps({'exercise_id': 99999, 'sets': 3, 'reps': 10}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 404)

    def test_add_exercise_only_accepts_post(self):
        response = self.client.get(
            f'/api/react/workouts/{self.workout.id}/exercises/add/',
        )
        self.assertEqual(response.status_code, 405)

    # --- Update exercise tests ---

    def test_update_exercise_sets_reps(self):
        we = WorkoutExercise.objects.create(
            workout=self.workout,
            exercise=self.exercise,
            sets=3,
            reps=10,
        )
        response = self.client.put(
            f'/api/react/workouts/{self.workout.id}/exercises/{we.id}/update/',
            json.dumps({'sets': 5, 'reps': 5}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        we.refresh_from_db()
        self.assertEqual(we.sets, 5)
        self.assertEqual(we.reps, 5)

    def test_update_exercise_weight(self):
        we = WorkoutExercise.objects.create(
            workout=self.workout,
            exercise=self.exercise,
            sets=3,
            reps=10,
        )
        response = self.client.put(
            f'/api/react/workouts/{self.workout.id}/exercises/{we.id}/update/',
            json.dumps({'weight': 100}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        we.refresh_from_db()
        self.assertEqual(float(we.weight), 100.0)

    def test_update_exercise_clear_weight(self):
        we = WorkoutExercise.objects.create(
            workout=self.workout,
            exercise=self.exercise,
            sets=3,
            reps=10,
            weight=Decimal('80.00'),
        )
        response = self.client.put(
            f'/api/react/workouts/{self.workout.id}/exercises/{we.id}/update/',
            json.dumps({'weight': None}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        we.refresh_from_db()
        self.assertIsNone(we.weight)

    def test_update_exercise_wrong_workout_returns_404(self):
        other_workout = WorkoutSession.objects.create(name='Other', date=timezone.now())
        we = WorkoutExercise.objects.create(
            workout=other_workout,
            exercise=self.exercise,
            sets=3,
            reps=10,
        )
        response = self.client.put(
            f'/api/react/workouts/{self.workout.id}/exercises/{we.id}/update/',
            json.dumps({'sets': 5}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 404)

    # --- Delete exercise tests ---

    def test_delete_exercise_from_workout(self):
        we = WorkoutExercise.objects.create(
            workout=self.workout,
            exercise=self.exercise,
            sets=3,
            reps=10,
        )
        response = self.client.delete(
            f'/api/react/workouts/{self.workout.id}/exercises/{we.id}/delete/',
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertFalse(WorkoutExercise.objects.filter(id=we.id).exists())

    def test_delete_exercise_nonexistent_returns_404(self):
        response = self.client.delete(
            f'/api/react/workouts/{self.workout.id}/exercises/99999/delete/',
        )
        self.assertEqual(response.status_code, 404)

    def test_delete_exercise_wrong_workout_returns_404(self):
        other_workout = WorkoutSession.objects.create(name='Other', date=timezone.now())
        we = WorkoutExercise.objects.create(
            workout=other_workout,
            exercise=self.exercise,
            sets=3,
            reps=10,
        )
        response = self.client.delete(
            f'/api/react/workouts/{self.workout.id}/exercises/{we.id}/delete/',
        )
        self.assertEqual(response.status_code, 404)

    def test_delete_exercise_only_accepts_delete(self):
        we = WorkoutExercise.objects.create(
            workout=self.workout,
            exercise=self.exercise,
            sets=3,
            reps=10,
        )
        response = self.client.get(
            f'/api/react/workouts/{self.workout.id}/exercises/{we.id}/delete/',
        )
        self.assertEqual(response.status_code, 405)
