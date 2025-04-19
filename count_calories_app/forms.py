# F:\Python GitHub ZygimantasB\Calories_Counter_Project\count_calories_app\forms.py
from django import forms
from .models import FoodItem, Weight, Exercise, WorkoutSession, WorkoutExercise, RunningSession

class FoodItemForm(forms.ModelForm):
    """
    Form for users to input food item details.
    """
    class Meta:
        model = FoodItem
        fields = ['product_name', 'calories', 'fat', 'carbohydrates', 'protein', 'consumed_at']
        # You can customize widgets if needed, e.g., using NumberInput for numeric fields
        widgets = {
            'product_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Apple, Chicken Breast'}),
            'calories': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'fat': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'carbohydrates': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'protein': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'consumed_at': forms.HiddenInput(),
        }
        labels = {
            'product_name': 'Product Name',
            'calories': 'Calories (kcal)',
            'fat': 'Fat (g)',
            'carbohydrates': 'Carbs (g)',
            'protein': 'Protein (g)',
            'consumed_at': 'Consumed At',
        }

class WeightForm(forms.ModelForm):
    """
    Form for users to input weight measurements.
    """
    class Meta:
        model = Weight
        fields = ['weight', 'recorded_at', 'notes']
        widgets = {
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.1'}),
            'recorded_at': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Optional notes about this weight measurement'}),
        }
        labels = {
            'weight': 'Weight (kg)',
            'recorded_at': 'Date and Time',
            'notes': 'Notes',
        }

class ExerciseForm(forms.ModelForm):
    """
    Form for users to input exercise details.
    """
    class Meta:
        model = Exercise
        fields = ['name', 'muscle_group', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Bench Press, Squats'}),
            'muscle_group': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Chest, Legs'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Optional description of how to perform the exercise'}),
        }
        labels = {
            'name': 'Exercise Name',
            'muscle_group': 'Muscle Group',
            'description': 'Description',
        }

class WorkoutSessionForm(forms.ModelForm):
    """
    Form for users to create workout sessions.
    """
    class Meta:
        model = WorkoutSession
        fields = ['name', 'date', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Morning Workout, Leg Day'}),
            'date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Optional notes about this workout session'}),
        }
        labels = {
            'name': 'Workout Name',
            'date': 'Date and Time',
            'notes': 'Notes',
        }

class WorkoutExerciseForm(forms.ModelForm):
    """
    Form for users to add exercises to a workout session.
    """
    class Meta:
        model = WorkoutExercise
        fields = ['exercise', 'sets', 'reps', 'weight', 'notes']
        widgets = {
            'exercise': forms.Select(attrs={'class': 'form-control'}),
            'sets': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'value': '1'}),
            'reps': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'value': '1'}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.5'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Optional notes about this exercise'}),
        }
        labels = {
            'exercise': 'Exercise',
            'sets': 'Sets',
            'reps': 'Reps',
            'weight': 'Weight (kg)',
            'notes': 'Notes',
        }

class RunningSessionForm(forms.ModelForm):
    """
    Form for users to input running session details.
    """
    class Meta:
        model = RunningSession
        fields = ['date', 'distance', 'duration', 'notes']
        widgets = {
            'date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'distance': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'duration': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time', 'step': '1'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Optional notes about this run'}),
        }
        labels = {
            'date': 'Date and Time',
            'distance': 'Distance (km)',
            'duration': 'Duration (HH:MM:SS)',
            'notes': 'Notes',
        }
