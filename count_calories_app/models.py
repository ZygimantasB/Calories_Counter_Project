from django.db import models
from django.utils import timezone

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
