# F:\Python GitHub ZygimantasB\Calories_Counter_Project\count_calories_app\forms.py
from django import forms
from .models import FoodItem

class FoodItemForm(forms.ModelForm):
    """
    Form for users to input food item details.
    """
    class Meta:
        model = FoodItem
        fields = ['product_name', 'calories', 'fat', 'carbohydrates', 'protein']
        # You can customize widgets if needed, e.g., using NumberInput for numeric fields
        widgets = {
            'product_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Apple, Chicken Breast'}),
            'calories': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'fat': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.1'}),
            'carbohydrates': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.1'}),
            'protein': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.1'}),
        }
        labels = {
            'product_name': 'Product Name',
            'calories': 'Calories (kcal)',
            'fat': 'Fat (g)',
            'carbohydrates': 'Carbs (g)',
            'protein': 'Protein (g)',
        }
