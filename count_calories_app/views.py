# F:\Python GitHub ZygimantasB\Calories_Counter_Project\count_calories_app\views.py
from django.shortcuts import render, redirect
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum # Import Sum
from .models import FoodItem
from .forms import FoodItemForm

def home(request):
    """
    View for the main calorie counting page.
    Handles displaying the form, list of items, and totals,
    as well as processing form submissions.
    """
    time_range = request.GET.get('range', 'today') # Default to 'today'
    now = timezone.now()
    start_date = now

    # Determine the date range for filtering
    if time_range == 'today':
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif time_range == 'week':
        # Start from the beginning of the current week (assuming Monday is the first day)
        start_date = now - timedelta(days=now.weekday())
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    elif time_range == 'month':
        # Start from the beginning of the current month
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Filter food items based on the selected time range
    food_items = FoodItem.objects.filter(consumed_at__gte=start_date)

    # Calculate totals for the selected range
    # Use aggregate and Sum, handling None if no items exist
    totals = food_items.aggregate(
        total_calories=Sum('calories'),
        total_fat=Sum('fat'),
        total_carbohydrates=Sum('carbohydrates'),
        total_protein=Sum('protein')
    )

    # Replace None with 0 if the aggregation result is None
    for key, value in totals.items():
        if value is None:
            totals[key] = 0

    if request.method == 'POST':
        # Handle form submission
        form = FoodItemForm(request.POST)
        if form.is_valid():
            form.save()
            # Redirect to the same page (using GET) to prevent form resubmission
            # Keep the current time range selection
            return redirect(f"{request.path}?range={time_range}")
        # If form is invalid, it will be re-rendered with errors below
    else:
        # Handle GET request (displaying the page)
        form = FoodItemForm() # Create an empty form

    context = {
        'form': form,
        'food_items': food_items,
        'totals': totals,
        'selected_range': time_range, # Pass the selected range to the template
    }
    return render(request, 'count_calories_app/home.html', context)

