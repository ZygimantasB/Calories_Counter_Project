from django.db import models
from django.utils import timezone
import json

class FoodItem(models.Model):
    """
    Represents a single food item consumed by the user.
    """
    product_name = models.CharField(max_length=200, help_text="Name of the food or drink")
    calories = models.PositiveIntegerField(default=0, help_text="Calories per serving")
    fat = models.DecimalField(max_digits=5, decimal_places=2, default=0.0, help_text="Fat content in grams")
    carbohydrates = models.DecimalField(max_digits=5, decimal_places=2, default=0.0, help_text="Carbohydrate content in grams")
    protein = models.DecimalField(max_digits=5, decimal_places=2, default=0.0, help_text="Protein content in grams")
    consumed_at = models.DateTimeField(default=timezone.now, help_text="Date and time the item was consumed")

    def __str__(self):
        """String representation of the food item."""
        return f"{self.product_name} ({self.calories} kcal) consumed at {self.consumed_at.strftime('%Y-%m-%d %H:%M')}"

    class Meta:
        ordering = ['-consumed_at'] # Show newest items first

class RunningSession(models.Model):
    """
    Represents a running session recorded by the user.
    """
    date = models.DateTimeField(default=timezone.now, help_text="Date and time of the run")
    distance = models.DecimalField(max_digits=5, decimal_places=2, help_text="Distance in kilometers")
    duration = models.DurationField(help_text="Duration of the run (HH:MM:SS)")
    notes = models.TextField(blank=True, null=True, help_text="Optional notes about this run")

    def __str__(self):
        """String representation of the running session."""
        return f"{self.distance} km on {self.date.strftime('%Y-%m-%d')}"

    class Meta:
        ordering = ['-date'] # Show newest runs first

class Weight(models.Model):
    """
    Represents a weight measurement recorded by the user.
    """
    weight = models.DecimalField(max_digits=5, decimal_places=2, help_text="Weight in kilograms")
    recorded_at = models.DateTimeField(default=timezone.now, help_text="Date and time the weight was recorded")
    notes = models.TextField(blank=True, null=True, help_text="Optional notes about this weight measurement")

    def __str__(self):
        """String representation of the weight measurement."""
        return f"{self.weight} kg on {self.recorded_at.strftime('%Y-%m-%d')}"

    class Meta:
        ordering = ['-recorded_at'] # Show newest measurements first

class Exercise(models.Model):
    """
    Represents a type of exercise that can be performed in a workout.
    """
    name = models.CharField(max_length=200, help_text="Name of the exercise")
    description = models.TextField(blank=True, null=True, help_text="Description of how to perform the exercise")
    muscle_group = models.CharField(max_length=100, blank=True, null=True, help_text="Primary muscle group targeted")

    def __str__(self):
        """String representation of the exercise."""
        return self.name

    class Meta:
        ordering = ['name'] # Order alphabetically by name

class WorkoutSession(models.Model):
    """
    Represents a workout session performed by the user.
    """
    date = models.DateTimeField(default=timezone.now, help_text="Date and time of the workout")
    name = models.CharField(max_length=200, blank=True, null=True, help_text="Optional name for this workout session")
    notes = models.TextField(blank=True, null=True, help_text="Optional notes about this workout session")

    def __str__(self):
        """String representation of the workout session."""
        if self.name:
            return f"{self.name} on {self.date.strftime('%Y-%m-%d')}"
        return f"Workout on {self.date.strftime('%Y-%m-%d')}"

    class Meta:
        ordering = ['-date'] # Show newest workouts first

class WorkoutExercise(models.Model):
    """
    Represents an exercise performed during a workout session, including sets and reps.
    """
    workout = models.ForeignKey(WorkoutSession, on_delete=models.CASCADE, related_name='exercises')
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    sets = models.PositiveIntegerField(default=1, help_text="Number of sets performed")
    reps = models.PositiveIntegerField(default=1, help_text="Number of repetitions per set")
    weight = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True, help_text="Weight used (if applicable)")
    notes = models.TextField(blank=True, null=True, help_text="Optional notes about this exercise performance")

    def __str__(self):
        """String representation of the exercise in a workout."""
        weight_str = f" with {self.weight} kg" if self.weight else ""
        return f"{self.exercise.name}: {self.sets} sets x {self.reps} reps{weight_str}"

    class Meta:
        ordering = ['id'] # Preserve the order exercises were added

class WorkoutTable(models.Model):
    """
    Represents a workout table with exercises and workout data.
    """
    name = models.CharField(max_length=200, help_text="Name of the workout table")
    created_at = models.DateTimeField(default=timezone.now, help_text="Date and time the table was created")
    # Store the table data as JSON
    table_data = models.JSONField(help_text="JSON representation of the table data")

    def __str__(self):
        """String representation of the workout table."""
        return f"{self.name} (created on {self.created_at.strftime('%Y-%m-%d')})"

    class Meta:
        ordering = ['-created_at'] # Show newest tables first
