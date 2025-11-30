from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum, Count, Avg, Max, Min
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.core.paginator import Paginator
from .models import FoodItem, Weight, Exercise, WorkoutSession, WorkoutExercise, RunningSession, WorkoutTable, BodyMeasurement
from .forms import FoodItemForm, WeightForm, ExerciseForm, WorkoutSessionForm, WorkoutExerciseForm, RunningSessionForm, BodyMeasurementForm
import logging
import json
import google.generativeai as genai
import os
import csv
from django.conf import settings
from google.api_core.exceptions import GoogleAPICallError, PermissionDenied, Unauthenticated, InvalidArgument, FailedPrecondition

logger = logging.getLogger('count_calories_app')

def home(request):
    return render(request, 'count_calories_app/home.html')

def get_nutrition_data(request):
    time_range = request.GET.get('range', 'today')
    selected_date_str = request.GET.get('date')
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    now = timezone.now()
    start_date = now
    end_date = None

    if selected_date_str:
        try:
            from datetime import datetime
            selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
            start_date = timezone.make_aware(datetime.combine(selected_date, datetime.min.time()))
            end_date = timezone.make_aware(datetime.combine(selected_date, datetime.max.time()))
        except (ValueError, TypeError):
            selected_date_str = None

    elif start_date_str and end_date_str:
        try:
            from datetime import datetime
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

            start_date = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
            end_date = timezone.make_aware(datetime.combine(end_date, datetime.max.time()))
        except (ValueError, TypeError):
            start_date_str = None
            end_date_str = None

    else:
        if time_range == 'today':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif time_range == 'week':
            start_date = now - timedelta(days=now.weekday())
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        elif time_range == 'month':
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    if end_date:
        food_items = FoodItem.objects.filter(consumed_at__gte=start_date, consumed_at__lte=end_date)
    else:
        food_items = FoodItem.objects.filter(consumed_at__gte=start_date)

    nutrition_data = {
        'labels': ['Protein', 'Carbs', 'Fat'],
        'data': [
            float(food_items.aggregate(Sum('protein'))['protein__sum'] or 0),
            float(food_items.aggregate(Sum('carbohydrates'))['carbohydrates__sum'] or 0),
            float(food_items.aggregate(Sum('fat'))['fat__sum'] or 0)
        ]
    }

    return JsonResponse(nutrition_data)

def get_gemini_nutrition(request):
    """
    API endpoint to get nutritional information from Gemini AI
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method allowed'}, status=405)

    try:
        data = json.loads(request.body)
        food_name = data.get('food_name', '').strip()

        if not food_name:
            return JsonResponse({'error': 'Food name is required'}, status=400)

        api_key = getattr(settings, 'GEMINI_API_KEY', None)
        if not api_key:
            logger.error("Gemini API key is not configured on the server")
            return JsonResponse({'error': 'Gemini API key is not configured on the server'}, status=500)
        genai.configure(api_key=api_key)

        model = genai.GenerativeModel('gemini-2.5-flash')

        prompt = f"""
        You are a nutrition expert. Analyze this food description: "{food_name}"
        
        IMPORTANT: Calculate nutritional values for the EXACT quantity mentioned in the description, not per 100g.
        
        If the description contains:
        - A specific quantity (like "150g", "2 pieces", "1 cup"), calculate for that exact amount
        - Multiple foods or a complex meal, sum up the nutrition from all components
        - Lithuanian or foreign language food names, identify the foods and provide accurate values
        - No specific quantity, assume a typical serving size for that food
        
        For complex meals like "italiÅ¡kas kapotos viÅ¡tienos maltinukas, Å¡vieÅ¾iÅ¾ darÅ¾oviÅ³ salotos, virtas bulguras (iLunch)", 
        break it down into components:
        - Italian chicken cutlet/meatballs
        - Fresh vegetable salad  
        - Cooked bulgur
        And sum the nutritional values of all components for a typical meal portion.
        
        Return ONLY this JSON format with no additional text:
        {{
            "product_name": "{food_name}",
            "calories": <total_calories_for_specified_amount>,
            "fat": <total_fat_grams_for_specified_amount>,
            "carbohydrates": <total_carbs_grams_for_specified_amount>,
            "protein": <total_protein_grams_for_specified_amount>
        }}
        
        Rules:
        - All values must be numbers (not strings)
        - Calculate for the ACTUAL quantity/serving mentioned, not per 100g
        - For complex meals, sum all components
        - If quantity is unclear, use realistic serving sizes
        - Fat, carbs, protein in grams; calories in kcal
        - Be accurate with Lithuanian food translations
        """

        try:
            response = model.generate_content(prompt)
        except (Unauthenticated, PermissionDenied) as e:
            logger.error(f"Gemini authentication error: {e}")
            return JsonResponse({'error': 'Invalid or unauthorized Gemini API key. Please check your API key configuration.', 'code': 'invalid_api_key'}, status=401)
        except GoogleAPICallError as e:
            # Check if it's an API key validation error (400 status)
            error_message = str(e)
            if "API_KEY_INVALID" in error_message or "API key not valid" in error_message:
                logger.error(f"Invalid Gemini API key: {e}")
                return JsonResponse({
                    'error': 'Invalid Gemini API key. Please obtain a valid API key from https://aistudio.google.com/app/apikey and update it in your .env file.',
                    'code': 'invalid_api_key'
                }, status=401)
            else:
                logger.error(f"Gemini API error: {e}")
                return JsonResponse({'error': 'Gemini service error. Please try again later.', 'code': 'gemini_api_error'}, status=502)
        except (InvalidArgument, FailedPrecondition) as e:
            logger.error(f"Gemini API error: {e}")
            return JsonResponse({'error': 'Gemini service error. Please try again later.', 'code': 'gemini_api_error'}, status=502)

        response_text = response.text.strip()

        try:
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]

            nutrition_data = json.loads(response_text.strip())

            required_fields = ['product_name', 'calories', 'fat', 'carbohydrates', 'protein']
            for field in required_fields:
                if field not in nutrition_data:
                    raise ValueError(f"Missing field: {field}")

            for field in ['calories', 'fat', 'carbohydrates', 'protein']:
                nutrition_data[field] = float(nutrition_data[field])

            return JsonResponse({
                'success': True,
                'data': nutrition_data
            })

        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Error parsing Gemini response: {e}, Response: {response_text}")
            return JsonResponse({
                'error': 'Failed to parse nutritional information from AI response'
            }, status=500)

    except Exception as e:
        logger.error(f"Error getting nutrition from Gemini: {e}")
        return JsonResponse({
            'error': 'Failed to get nutritional information'
        }, status=500)

def food_tracker(request):
    time_range = request.GET.get('range', 'today')
    selected_date_str = request.GET.get('date')
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    now = timezone.now()
    start_date = now
    end_date = None
    selected_date = None
    date_range_selected = False
    show_averages = False

    if start_date_str and end_date_str:
        try:
            from datetime import datetime
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

            start_date = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
            end_date = timezone.make_aware(datetime.combine(end_date, datetime.max.time()))

            time_range = 'date_range'
            date_range_selected = True
            show_averages = True
        except (ValueError, TypeError):
            start_date_str = None
            end_date_str = None

    elif selected_date_str:
        try:
            from datetime import datetime
            selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()

            today_date = now.date()
            if selected_date == today_date:
                start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = start_date.replace(hour=23, minute=59, second=59, microsecond=999999)
                time_range = 'today_specific'
            else:
                start_date = timezone.make_aware(datetime.combine(selected_date, datetime.min.time()))
                end_date = timezone.make_aware(datetime.combine(selected_date, datetime.max.time()))
                time_range = 'specific_date'
        except (ValueError, TypeError):
            selected_date = None

    if not selected_date and not date_range_selected:
        if time_range == 'today':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        elif time_range == 'week':
            start_date = now - timedelta(days=now.weekday())
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)
            show_averages = True
        elif time_range == 'month':
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)
            show_averages = True

    from django.db.models.functions import TruncDate

    if end_date:
        if time_range == 'specific_date' or time_range == 'today_specific' or time_range == 'today':
            if selected_date:
                if hasattr(selected_date, 'date'):
                    date_to_filter = selected_date.date()
                else:
                    date_to_filter = selected_date
            else:
                date_to_filter = now.date()

            food_items = FoodItem.objects.annotate(
                consumed_date=TruncDate('consumed_at')
            ).filter(consumed_date=date_to_filter)
        else:
            food_items = FoodItem.objects.filter(consumed_at__gte=start_date, consumed_at__lte=end_date)
    else:
        food_items = FoodItem.objects.filter(consumed_at__gte=start_date)

    # CSV export for Food Tracker (respects current filters)
    export = request.GET.get('export')
    if export == 'csv':
        # Build filename based on selected filters
        def _date_label():
            try:
                if start_date_str and end_date_str:
                    return f"{start_date_str}_to_{end_date_str}"
                if selected_date_str:
                    return str(selected_date_str)
                return time_range
            except Exception:
                return time_range
        filename = f"food_items_{_date_label()}.csv"
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        writer = csv.writer(response)
        writer.writerow(['Consumed At', 'Product Name', 'Calories', 'Fat (g)', 'Carbs (g)', 'Protein (g)'])
        for fi in food_items.order_by('consumed_at').iterator():
            writer.writerow([
                fi.consumed_at.strftime('%Y-%m-%d %H:%M:%S') if fi.consumed_at else '',
                fi.product_name,
                float(fi.calories or 0),
                float(fi.fat or 0),
                float(fi.carbohydrates or 0),
                float(fi.protein or 0),
            ])
        return response

    from django.db.models import Max
    product_names = FoodItem.objects.filter(
        hide_from_quick_list=False
    ).values('product_name').annotate(
        latest=Max('consumed_at')
    ).order_by('-latest')

    quick_add_items = []
    for item in product_names:
        food = FoodItem.objects.filter(
            product_name=item['product_name'],
            consumed_at=item['latest'],
            hide_from_quick_list=False
        ).first()
        if food:
            quick_add_items.append(food)

    totals = food_items.aggregate(
        total_calories=Sum('calories'),
        total_fat=Sum('fat'),
        total_carbohydrates=Sum('carbohydrates'),
        total_protein=Sum('protein')
    )

    for key, value in totals.items():
        if value is None:
            totals[key] = 0

    total_macros = totals['total_fat'] + totals['total_carbohydrates'] + totals['total_protein']
    if total_macros > 0:
        totals['fat_percentage'] = round((totals['total_fat'] / total_macros) * 100, 1)
        totals['carbs_percentage'] = round((totals['total_carbohydrates'] / total_macros) * 100, 1)
        totals['protein_percentage'] = round((totals['total_protein'] / total_macros) * 100, 1)
    else:
        totals['fat_percentage'] = 0
        totals['carbs_percentage'] = 0
        totals['protein_percentage'] = 0

    averages = {}
    if show_averages and food_items.exists():
        from datetime import datetime
        end_date_obj = end_date.date() if hasattr(end_date, 'date') else end_date
        start_date_obj = start_date.date() if hasattr(start_date, 'date') else start_date
        days_in_range = (end_date_obj - start_date_obj).days + 1

        if days_in_range > 0:
            averages = {
                'avg_calories': round(totals['total_calories'] / days_in_range, 1),
                'avg_fat': round(totals['total_fat'] / days_in_range, 1),
                'avg_carbohydrates': round(totals['total_carbohydrates'] / days_in_range, 1),
                'avg_protein': round(totals['total_protein'] / days_in_range, 1),
                'days_in_range': days_in_range
            }

            avg_total_macros = averages['avg_fat'] + averages['avg_carbohydrates'] + averages['avg_protein']
            if avg_total_macros > 0:
                averages['fat_percentage'] = round((averages['avg_fat'] / avg_total_macros) * 100, 1)
                averages['carbs_percentage'] = round((averages['avg_carbohydrates'] / avg_total_macros) * 100, 1)
                averages['protein_percentage'] = round((averages['avg_protein'] / avg_total_macros) * 100, 1)
            else:
                averages['fat_percentage'] = 0
                averages['carbs_percentage'] = 0
                averages['protein_percentage'] = 0

    if request.method == 'POST':
        logger.info(f"Processing food item form submission: {request.POST}")

        post_data = request.POST.copy()

        if selected_date:
            initial_datetime = timezone.make_aware(datetime.combine(selected_date, datetime.min.time()))
            post_data['consumed_at'] = initial_datetime
            logger.info(f"Setting consumed_at to selected date: {initial_datetime}")
        elif selected_date_str:
            try:
                selected_date_from_str = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
                initial_datetime = timezone.make_aware(datetime.combine(selected_date_from_str, datetime.min.time()))
                post_data['consumed_at'] = initial_datetime
                logger.info(f"Setting consumed_at to date from URL parameter: {initial_datetime}")
            except (ValueError, TypeError):
                logger.warning(f"Could not parse date string: {selected_date_str}")

        form = FoodItemForm(post_data)
        if form.is_valid():
            try:
                food_item = form.save()
                logger.info(f"Food item saved successfully: {food_item.id} - {food_item.product_name}")
                messages.success(request, f"Food item '{food_item.product_name}' added successfully!")
                if selected_date:
                    return redirect(f"/food_tracker/?date={selected_date.strftime('%Y-%m-%d')}")
                elif selected_date_str:
                    return redirect(f"/food_tracker/?date={selected_date_str}")
                else:
                    return redirect(f"/food_tracker/?range={time_range}")
            except Exception as e:
                logger.error(f"Error saving food item: {str(e)}")
                messages.error(request, f"Error saving food item: {str(e)}")
        else:
            logger.warning(f"Invalid food item form: {form.errors}")
            messages.warning(request, "Please correct the errors in the form.")
    else:
        if selected_date:
            initial_datetime = timezone.make_aware(datetime.combine(selected_date, datetime.min.time()))
            form = FoodItemForm(initial={'consumed_at': initial_datetime})
        elif selected_date_str:
            try:
                selected_date_from_str = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
                initial_datetime = timezone.make_aware(datetime.combine(selected_date_from_str, datetime.min.time()))
                form = FoodItemForm(initial={'consumed_at': initial_datetime})
            except (ValueError, TypeError):
                logger.warning(f"Could not parse date string: {selected_date_str}")
                form = FoodItemForm() # Create an empty form if date parsing fails
        else:
            form = FoodItemForm() # Create an empty form

    page_number = request.GET.get('page', 1)
    sort_by = request.GET.get('sort', 'count')  # Default sort by count
    sort_order = request.GET.get('order', 'desc')  # Default descending order

    if end_date:
        if time_range == 'specific_date' or time_range == 'today_specific' or time_range == 'today':
            if selected_date:
                if hasattr(selected_date, 'date'):
                    date_to_filter = selected_date.date()
                else:
                    date_to_filter = selected_date
            else:
                date_to_filter = now.date()

            top_foods_queryset = FoodItem.objects.annotate(
                consumed_date=TruncDate('consumed_at')
            ).filter(consumed_date=date_to_filter)
        else:
            top_foods_queryset = FoodItem.objects.filter(consumed_at__gte=start_date, consumed_at__lte=end_date)
    else:
        top_foods_queryset = FoodItem.objects.filter(consumed_at__gte=start_date)

    top_foods_data = top_foods_queryset.values('product_name').annotate(
        count=Count('id'),
        total_calories=Sum('calories'),
        avg_calories=Avg('calories'),
        total_fat=Sum('fat'),
        total_carbs=Sum('carbohydrates'),
        total_protein=Sum('protein'),
        latest_consumed=Max('consumed_at')
    )

    if sort_by == 'count':
        if sort_order == 'desc':
            top_foods_data = top_foods_data.order_by('-count', '-latest_consumed')
        else:
            top_foods_data = top_foods_data.order_by('count', '-latest_consumed')
    elif sort_by == 'name':
        if sort_order == 'desc':
            top_foods_data = top_foods_data.order_by('-product_name')
        else:
            top_foods_data = top_foods_data.order_by('product_name')
    elif sort_by == 'calories':
        if sort_order == 'desc':
            top_foods_data = top_foods_data.order_by('-total_calories', '-count')
        else:
            top_foods_data = top_foods_data.order_by('total_calories', '-count')
    elif sort_by == 'latest':
        if sort_order == 'desc':
            top_foods_data = top_foods_data.order_by('-latest_consumed')
        else:
            top_foods_data = top_foods_data.order_by('latest_consumed')
    else:
        top_foods_data = top_foods_data.order_by('-count', '-latest_consumed')

    paginator = Paginator(top_foods_data, 10)  # Show 10 items per page
    try:
        top_foods_page = paginator.page(page_number)
    except:
        top_foods_page = paginator.page(1)

    context = {
        'form': form,
        'food_items': food_items,
        'recent_items': quick_add_items,  # Using quick_add_items but keeping the template variable name for compatibility
        'totals': totals,
        'selected_range': time_range, # Pass the selected range to the template
        'selected_date': selected_date, # Pass the selected date to the template
        'show_averages': show_averages, # Whether to show averages section
        'averages': averages if show_averages else {}, # Pass the averages to the template
        'start_date_str': start_date_str, # Pass the start date string to the template
        'end_date_str': end_date_str, # Pass the end date string to the template
        'top_foods_page': top_foods_page,  # Paginated top foods data
        'current_sort': sort_by,  # Current sort field
        'current_order': sort_order,  # Current sort order
    }
    return render(request, 'count_calories_app/food_tracker.html', context)

def top_foods(request):
    """
    View for displaying top foods eaten with pagination, date filtering, and sorting.
    """
    time_range = request.GET.get('range', 'today')
    selected_date_str = request.GET.get('date')
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    page_number = request.GET.get('page', 1)
    sort_by = request.GET.get('sort', 'count')  # Default sort by count
    sort_order = request.GET.get('order', 'desc')  # Default descending order
    export = request.GET.get('export')  # If 'csv', return CSV

    now = timezone.now()
    start_date = now
    end_date = None
    selected_date = None
    date_range_selected = False

    if start_date_str and end_date_str:
        try:
            from datetime import datetime
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

            start_date = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
            end_date = timezone.make_aware(datetime.combine(end_date, datetime.max.time()))

            time_range = 'date_range'
            date_range_selected = True
        except (ValueError, TypeError):
            start_date_str = None
            end_date_str = None

    elif selected_date_str:
        try:
            from datetime import datetime
            selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()

            today_date = now.date()
            if selected_date == today_date:
                start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = start_date.replace(hour=23, minute=59, second=59, microsecond=999999)
                time_range = 'today_specific'
            else:
                start_date = timezone.make_aware(datetime.combine(selected_date, datetime.min.time()))
                end_date = timezone.make_aware(datetime.combine(selected_date, datetime.max.time()))
                time_range = 'specific_date'
        except (ValueError, TypeError):
            selected_date = None

    if not selected_date and not date_range_selected:
        if time_range == 'today':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        elif time_range == 'week':
            start_date = now - timedelta(days=now.weekday())
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        elif time_range == 'month':
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)

    from django.db.models.functions import TruncDate

    if end_date:
        if time_range == 'specific_date' or time_range == 'today_specific' or time_range == 'today':
            if selected_date:
                if hasattr(selected_date, 'date'):
                    date_to_filter = selected_date.date()
                else:
                    date_to_filter = selected_date
            else:
                date_to_filter = now.date()

            top_foods_queryset = FoodItem.objects.annotate(
                consumed_date=TruncDate('consumed_at')
            ).filter(consumed_date=date_to_filter)
        else:
            top_foods_queryset = FoodItem.objects.filter(consumed_at__gte=start_date, consumed_at__lte=end_date)
    else:
        top_foods_queryset = FoodItem.objects.filter(consumed_at__gte=start_date)

    top_foods_data = top_foods_queryset.values('product_name').annotate(
        count=Count('id'),
        total_calories=Sum('calories'),
        avg_calories=Avg('calories'),
        total_fat=Sum('fat'),
        total_carbs=Sum('carbohydrates'),
        total_protein=Sum('protein'),
        latest_consumed=Max('consumed_at')
    )

    if sort_by == 'count':
        if sort_order == 'desc':
            top_foods_data = top_foods_data.order_by('-count', '-latest_consumed')
        else:
            top_foods_data = top_foods_data.order_by('count', '-latest_consumed')
    elif sort_by == 'name':
        if sort_order == 'desc':
            top_foods_data = top_foods_data.order_by('-product_name')
        else:
            top_foods_data = top_foods_data.order_by('product_name')
    elif sort_by == 'calories':
        if sort_order == 'desc':
            top_foods_data = top_foods_data.order_by('-total_calories', '-count')
        else:
            top_foods_data = top_foods_data.order_by('total_calories', '-count')
    elif sort_by == 'latest':
        if sort_order == 'desc':
            top_foods_data = top_foods_data.order_by('-latest_consumed')
        else:
            top_foods_data = top_foods_data.order_by('latest_consumed')
    else:
        top_foods_data = top_foods_data.order_by('-count', '-latest_consumed')

    # CSV export (fast, respects current filters and sorting)
    if export == 'csv':
        # Build filename based on selected filters
        def _date_label():
            try:
                if start_date_str and end_date_str:
                    return f"{start_date_str}_to_{end_date_str}"
                if selected_date_str:
                    return str(selected_date_str)
                return time_range
            except Exception:
                return time_range
        filename = f"top_foods_{_date_label()}.csv"
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        writer = csv.writer(response)
        writer.writerow(['Product Name', 'Times Eaten', 'Total Calories', 'Average Calories', 'Total Fat (g)', 'Total Carbs (g)', 'Total Protein (g)', 'Latest Consumed'])
        for item in top_foods_data.iterator():
            writer.writerow([
                item['product_name'],
                item['count'],
                float(item['total_calories'] or 0),
                float(item['avg_calories'] or 0),
                float(item['total_fat'] or 0),
                float(item['total_carbs'] or 0),
                float(item['total_protein'] or 0),
                item['latest_consumed'].strftime('%Y-%m-%d %H:%M:%S') if item['latest_consumed'] else ''
            ])
        return response

    paginator = Paginator(top_foods_data, 10)  # Show 10 items per page
    try:
        top_foods_page = paginator.page(page_number)
    except:
        top_foods_page = paginator.page(1)

    context = {
        'top_foods_page': top_foods_page,
        'selected_range': time_range,
        'selected_date': selected_date,
        'start_date_str': start_date_str,
        'end_date_str': end_date_str,
        'current_sort': sort_by,
        'current_order': sort_order,
    }

    return render(request, 'count_calories_app/top_foods.html', context)

def get_calories_trend_data(request):
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    food_items = FoodItem.objects.filter(
        consumed_at__gte=start_date,
        consumed_at__lte=end_date
    ).order_by('consumed_at')
    from django.db.models.functions import TruncDate
    daily_calories = food_items.annotate(
        day=TruncDate('consumed_at')
    ).values('day').annotate(
        total_calories=Sum('calories')
    ).order_by('day')

    calories_data = {
        'labels': [item['day'].strftime('%Y-%m-%d') for item in daily_calories],
        'data': [float(item['total_calories']) for item in daily_calories]
    }

    return JsonResponse(calories_data)

def get_macros_trend_data(request):
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    food_items = FoodItem.objects.filter(
        consumed_at__gte=start_date,
        consumed_at__lte=end_date
    ).order_by('consumed_at')
    from django.db.models.functions import TruncDate
    daily_macros = food_items.annotate(
        day=TruncDate('consumed_at')
    ).values('day').annotate(
        total_protein=Sum('protein'),
        total_carbs=Sum('carbohydrates'),
        total_fat=Sum('fat')
    ).order_by('day')

    macros_data = {
        'labels': [item['day'].strftime('%Y-%m-%d') for item in daily_macros],
        'protein': [float(item['total_protein']) for item in daily_macros],
        'carbs': [float(item['total_carbs']) for item in daily_macros],
        'fat': [float(item['total_fat']) for item in daily_macros]
    }

    return JsonResponse(macros_data)

def get_weight_data(request):
    # Get date range from request parameters
    days_param = request.GET.get('days')
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    end_date = timezone.now()

    if start_date_str and end_date_str:
        # Custom date range
        try:
            from datetime import datetime
            start_date = timezone.make_aware(datetime.strptime(start_date_str, '%Y-%m-%d'))
            end_date = timezone.make_aware(datetime.strptime(end_date_str, '%Y-%m-%d').replace(hour=23, minute=59, second=59))
        except ValueError:
            start_date = end_date - timedelta(days=90)
    elif days_param:
        # Preset days (90, 180, 365, or 'all')
        if days_param == 'all':
            start_date = None  # No start date filter
        else:
            try:
                days = int(days_param)
                start_date = end_date - timedelta(days=days)
            except ValueError:
                start_date = end_date - timedelta(days=90)
    else:
        # Default: last 90 days
        start_date = end_date - timedelta(days=90)

    # Build query
    if start_date:
        weights = Weight.objects.filter(recorded_at__gte=start_date, recorded_at__lte=end_date).order_by('recorded_at')
    else:
        weights = Weight.objects.filter(recorded_at__lte=end_date).order_by('recorded_at')

    weight_data = {
        'labels': [w.recorded_at.strftime('%Y-%m-%d') for w in weights],
        'data': [float(w.weight) for w in weights]
    }
    if weights.exists():
        stats = weights.aggregate(
            avg_weight=Avg('weight'),
            max_weight=Max('weight'),
            min_weight=Min('weight'),
            latest_weight=Max('recorded_at')
        )
        latest_weight = weights.filter(recorded_at=stats['latest_weight']).first()

        weight_data['stats'] = {
            'avg': float(stats['avg_weight']),
            'max': float(stats['max_weight']),
            'min': float(stats['min_weight']),
            'latest': float(latest_weight.weight) if latest_weight else 0
        }
        if len(weights) >= 2:
            oldest_weight = weights.first()
            newest_weight = weights.last()
            time_diff = (newest_weight.recorded_at - oldest_weight.recorded_at).total_seconds() / (60 * 60 * 24 * 7)
            if time_diff > 0:
                weight_change = newest_weight.weight - oldest_weight.weight
                weight_change_rate = float(weight_change) / time_diff
                weight_data['stats']['change_rate'] = float(weight_change_rate)
            else:
                weight_data['stats']['change_rate'] = 0
        else:
            weight_data['stats']['change_rate'] = 0

        height_in_meters = 1.75  # Default height
        latest_weight_value = float(latest_weight.weight) if latest_weight else 0
        if latest_weight_value > 0:
            bmi = latest_weight_value / (height_in_meters * height_in_meters)
            weight_data['stats']['bmi'] = round(bmi, 1)
        else:
            weight_data['stats']['bmi'] = 0

        if len(weights) >= 3:
            import numpy as np
            weight_values = [float(w.weight) for w in weights]
            weight_data['stats']['consistency'] = round(float(np.std(weight_values)), 2)
        else:
            weight_data['stats']['consistency'] = 0

        if weight_data['stats']['change_rate'] != 0:
            projected_weight = latest_weight_value + (weight_data['stats']['change_rate'] * 4)
            weight_data['stats']['projected_weight'] = round(projected_weight, 1)
        else:
            weight_data['stats']['projected_weight'] = latest_weight_value

        weight_goal = 70.0  # Default goal weight
        if latest_weight_value > weight_goal and weight_data['stats']['change_rate'] < 0:
            weeks_to_goal = (latest_weight_value - weight_goal) / abs(weight_data['stats']['change_rate'])
            weight_data['stats']['weeks_to_goal'] = round(weeks_to_goal, 1)

            import datetime
            goal_date = latest_weight.recorded_at + datetime.timedelta(weeks=weeks_to_goal)
            weight_data['stats']['goal_date'] = goal_date.strftime('%Y-%m-%d')
        else:
            weight_data['stats']['weeks_to_goal'] = 0
            weight_data['stats']['goal_date'] = 'N/A'
    else:
        weight_data['stats'] = {
            'avg': 0,
            'max': 0,
            'min': 0,
            'latest': 0,
            'change_rate': 0,
            'bmi': 0,
            'consistency': 0,
            'projected_weight': 0,
            'weeks_to_goal': 0,
            'goal_date': 'N/A'
        }

    return JsonResponse(weight_data)

def get_weight_calories_correlation(request):
    weights = Weight.objects.all().order_by('recorded_at')

    correlation_data = []
    if len(weights) >= 2:
        for i in range(1, len(weights)):
            current_weight = weights[i]
            previous_weight = weights[i-1]
            weight_change = float(current_weight.weight) - float(previous_weight.weight)
            from datetime import datetime, time
            prev_date = previous_weight.recorded_at.date()
            prev_datetime = timezone.make_aware(datetime.combine(prev_date, time.min))
            curr_date = current_weight.recorded_at.date()
            curr_datetime = timezone.make_aware(datetime.combine(curr_date, time.max))
            food_items = FoodItem.objects.filter(
                consumed_at__gte=prev_datetime,
                consumed_at__lte=curr_datetime
            )
            total_calories_result = food_items.aggregate(Sum('calories'))['calories__sum'] or 0
            total_calories = float(total_calories_result)
            days_between = (current_weight.recorded_at - previous_weight.recorded_at).days
            if days_between == 0:
                days_between = 1
            daily_avg_calories = float(total_calories) / days_between
            correlation_data.append({
                'start_date': previous_weight.recorded_at.strftime('%Y-%m-%d'),
                'end_date': current_weight.recorded_at.strftime('%Y-%m-%d'),
                'start_weight': float(previous_weight.weight),
                'end_weight': float(current_weight.weight),
                'weight_change': round(weight_change, 2),
                'days_between': days_between,
                'total_calories': float(total_calories),
                'daily_avg_calories': round(daily_avg_calories, 1),
            })

    correlation_data.reverse()
    page = request.GET.get('page', 1)
    try:
        page = int(page)
    except ValueError:
        page = 1
    items_per_page = 10
    start_idx = (page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    page_data = correlation_data[start_idx:end_idx]
    total_pages = (len(correlation_data) + items_per_page - 1) // items_per_page

    return JsonResponse({
        'correlation_data': page_data,
        'pagination': {
            'current_page': page,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_prev': page > 1
        }
    })

def weight_tracker(request):
    export = request.GET.get('export')
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    days_param = request.GET.get('days')

    # Default to the last 90 days
    end_date = timezone.now()
    current_days = days_param if days_param else '90'

    # Calculate start_date based on days parameter
    if days_param == 'all':
        start_date = None
    elif days_param:
        try:
            days = int(days_param)
            start_date = end_date - timedelta(days=days)
        except ValueError:
            start_date = end_date - timedelta(days=90)
            current_days = '90'
    else:
        start_date = end_date - timedelta(days=90)

    # Base queryset for the page and default CSV export
    if start_date:
        weights_query = Weight.objects.filter(recorded_at__gte=start_date).order_by('-recorded_at')
    else:
        weights_query = Weight.objects.all().order_by('-recorded_at')

    # Handle CSV export
    if export == 'csv':
        # If a date range is provided for the export, use it
        if start_date_str and end_date_str:
            try:
                from datetime import datetime, time
                from django.utils.timezone import make_aware

                start_date_csv = make_aware(datetime.combine(datetime.strptime(start_date_str, '%Y-%m-%d').date(), time.min))
                end_date_csv = make_aware(datetime.combine(datetime.strptime(end_date_str, '%Y-%m-%d').date(), time.max))
                # Use a different queryset for the ranged export
                export_query = Weight.objects.filter(recorded_at__gte=start_date_csv, recorded_at__lte=end_date_csv).order_by('recorded_at')
                filename_label = f"{start_date_str}_to_{end_date_str}"
            except (ValueError, TypeError):
                # Fallback to the default 90-day export if dates are invalid
                export_query = weights_query.order_by('recorded_at')
                filename_label = 'last_90_days'
        else:
            # Default CSV export is the last 90 days
            export_query = weights_query.order_by('recorded_at')
            filename_label = 'last_90_days'

        filename = f"weights_{filename_label}.csv"
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        writer = csv.writer(response)
        writer.writerow(['Recorded At', 'Weight (kg)', 'Notes'])
        for recorded_at, weight, notes in export_query.values_list('recorded_at', 'weight', 'notes').iterator():
            writer.writerow([
                recorded_at.strftime('%Y-%m-%d %H:%M:%S') if recorded_at else '',
                float(weight) if weight is not None else '',
                notes or ''
            ])
        return response

    # Pagination for the main page view (last 90 days)
    paginator = Paginator(weights_query, 10)
    page_number = request.GET.get('page')
    weights = paginator.get_page(page_number)

    if request.method == 'POST':
        logger.info(f"Processing weight form submission: {request.POST}")
        form = WeightForm(request.POST)
        if form.is_valid():
            try:
                weight = form.save()
                logger.info(f"Weight measurement saved successfully: {weight.id} - {weight.weight} kg")
                messages.success(request, f"Weight measurement of {weight.weight} kg added successfully!")
                return redirect('weight_tracker')
            except Exception as e:
                logger.error(f"Error saving weight measurement: {str(e)}")
                messages.error(request, f"Error saving weight measurement: {str(e)}")
        else:
            logger.warning(f"Invalid weight form: {form.errors}")
            messages.warning(request, "Please correct the errors in the form.")
    else:
        form = WeightForm(initial={'recorded_at': timezone.now()})

    context = {
        'form': form,
        'weights': weights,
        'current_days': current_days,
    }
    return render(request, 'count_calories_app/weight_tracker.html', context)

def workout_tracker(request):
    workouts = WorkoutSession.objects.all().order_by('-date')

    if request.method == 'POST':
        form = WorkoutSessionForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('workout_tracker')
    else:
        form = WorkoutSessionForm(initial={'date': timezone.now()})

    context = {
        'form': form,
        'workouts': workouts,
    }
    return render(request, 'count_calories_app/workout_tracker.html', context)

def exercise_list(request):
    exercises = Exercise.objects.all().order_by('name')

    if request.method == 'POST':
        form = ExerciseForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('exercise_list')
    else:
        form = ExerciseForm()

    context = {
        'form': form,
        'exercises': exercises,
    }
    return render(request, 'count_calories_app/exercise_list.html', context)

def get_workout_frequency_data(request):
    end_date = timezone.now()
    start_date = end_date - timedelta(days=90)

    workouts = WorkoutSession.objects.filter(
        date__gte=start_date,
        date__lte=end_date
    ).order_by('date')

    from django.db.models.functions import TruncDate
    daily_workouts = workouts.annotate(
        day=TruncDate('date')
    ).values('day').annotate(
        count=Count('id')
    ).order_by('day')

    workout_data = {
        'labels': [item['day'].strftime('%Y-%m-%d') for item in daily_workouts],
        'data': [item['count'] for item in daily_workouts]
    }

    return JsonResponse(workout_data)

def get_exercise_progress_data(request, exercise_id=None):
    """
    API endpoint to get progress data for a specific exercise
    """
    if exercise_id is None:
        exercise_id = request.GET.get('exercise_id')

    if not exercise_id:
        return JsonResponse({'error': 'No exercise ID provided'}, status=400)

    exercise = get_object_or_404(Exercise, id=exercise_id)

    workout_exercises = WorkoutExercise.objects.filter(
        exercise_id=exercise_id
    ).order_by('workout__date')

    progress_data = {
        'exercise_name': exercise.name,
        'labels': [we.workout.date.strftime('%Y-%m-%d') for we in workout_exercises],
        'weight': [float(we.weight) if we.weight else 0 for we in workout_exercises],
        'sets': [we.sets for we in workout_exercises],
        'reps': [we.reps for we in workout_exercises],
        'volume': [float(we.weight) * we.sets * we.reps if we.weight else 0 for we in workout_exercises]
    }

    return JsonResponse(progress_data)

def edit_food_item(request, food_item_id):
    """
    View for editing a food item.
    """
    food_item = get_object_or_404(FoodItem, id=food_item_id)

    if request.method == 'POST':
        form = FoodItemForm(request.POST, instance=food_item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Food item updated successfully!')
            return redirect('food_tracker')
    else:
        form = FoodItemForm(instance=food_item)

    context = {
        'form': form,
        'food_item': food_item,
        'edit_mode': True,
    }
    return render(request, 'count_calories_app/edit_food_item.html', context)

def delete_food_item(request, food_item_id):
    """
    View for deleting a food item.
    """
    food_item = get_object_or_404(FoodItem, id=food_item_id)

    if request.method == 'POST':
        food_item.delete()
        messages.success(request, 'Food item deleted successfully!')
        return redirect('food_tracker')

    context = {
        'food_item': food_item,
    }
    return render(request, 'count_calories_app/delete_food_item.html', context)

def edit_weight(request, weight_id):
    """
    View for editing a weight measurement.
    """
    weight = get_object_or_404(Weight, id=weight_id)

    if request.method == 'POST':
        form = WeightForm(request.POST, instance=weight)
        if form.is_valid():
            form.save()
            messages.success(request, 'Weight measurement updated successfully!')
            return redirect('weight_tracker')
    else:
        form = WeightForm(instance=weight)

    context = {
        'form': form,
        'weight': weight,
        'edit_mode': True,
    }
    return render(request, 'count_calories_app/edit_weight.html', context)

def delete_weight(request, weight_id):
    """
    View for deleting a weight measurement.
    """
    weight = get_object_or_404(Weight, id=weight_id)

    if request.method == 'POST':
        weight.delete()
        messages.success(request, 'Weight measurement deleted successfully!')
        return redirect('weight_tracker')

    context = {
        'weight': weight,
    }
    return render(request, 'count_calories_app/delete_weight.html', context)

def workout_table(request):
    """
    View for the Excel-like workout table interface.
    Allows users to create and manage workout tables with exercises and workout data.
    """
    workout_tables = WorkoutTable.objects.all().order_by('-created_at')

    context = {
        'workout_tables': workout_tables,
    }
    return render(request, 'count_calories_app/workout_table.html', context)

def save_workout_table(request):
    """
    API endpoint to save a workout table.
    """
    if request.method == 'POST':
        try:
            logger.info(f"Processing workout table save request")
            data = json.loads(request.body)

            table_id = data.get('id')
            table_name = data.get('name', 'Workout Table')
            table_data = data.get('data', {})

            if table_id:
                try:
                    table = WorkoutTable.objects.get(id=table_id)
                    table.name = table_name
                    table.table_data = table_data
                    table.save()
                    logger.info(f"Workout table updated successfully: {table.id} - {table.name}")
                    return JsonResponse({'success': True, 'message': 'Workout table updated successfully', 'id': table.id})
                except WorkoutTable.DoesNotExist:
                    logger.error(f"Workout table not found: {table_id}")
                    return JsonResponse({'success': False, 'message': 'Workout table not found'}, status=404)
            else:
                table = WorkoutTable.objects.create(
                    name=table_name,
                    table_data=table_data
                )
                logger.info(f"Workout table created successfully: {table.id} - {table.name}")
                return JsonResponse({'success': True, 'message': 'Workout table created successfully', 'id': table.id})

        except Exception as e:
            logger.error(f"Error saving workout table: {str(e)}")
            return JsonResponse({'success': False, 'message': f"Error saving workout table: {str(e)}"}, status=500)

    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)

def get_workout_tables(request):
    """
    API endpoint to get all workout tables.
    """
    try:
        workout_tables = WorkoutTable.objects.all().order_by('-created_at')
        tables_data = []

        for table in workout_tables:
            logger.info(f"Raw table_data for table {table.id}: {table.table_data}")

            table_data = table.table_data

            if isinstance(table_data, str):
                try:
                    table_data = json.loads(table_data)
                    logger.info(f"Successfully parsed table_data as JSON for table {table.id}")
                except json.JSONDecodeError:
                    logger.error(f"Error parsing table_data as JSON for table {table.id}")
                    pass

            if isinstance(table_data, dict) and 'workouts' in table_data and 'exercises' in table_data:
                logger.info(f"Table {table.id} has proper structure with workouts and exercises")
            else:
                logger.warning(f"Table {table.id} data structure might be incorrect: {table_data}")
                if isinstance(table_data, str):
                    try:
                        table_data = json.loads(table_data)
                        logger.info(f"Fixed double-encoded JSON for table {table.id}")
                    except json.JSONDecodeError:
                        logger.error(f"Failed to fix double-encoded JSON for table {table.id}")

                if not isinstance(table_data, dict) or 'workouts' not in table_data or 'exercises' not in table_data:
                    logger.warning(f"Creating default structure for table {table.id}")
                    table_data = {
                        'workouts': [],
                        'exercises': []
                    }

            tables_data.append({
                'id': table.id,
                'name': table.name,
                'date': table.created_at.strftime('%m/%d/%Y'),
                'data': table_data
            })

        logger.info(f"Returning {len(tables_data)} tables")
        return JsonResponse({'success': True, 'tables': tables_data})
    except Exception as e:
        logger.error(f"Error getting workout tables: {str(e)}")
        return JsonResponse({'success': False, 'message': f"Error getting workout tables: {str(e)}"}, status=500)

def delete_workout_table(request, table_id):
    """
    API endpoint to delete a workout table.
    """
    if request.method == 'DELETE':
        try:
            table = WorkoutTable.objects.get(id=table_id)
            table.delete()
            logger.info(f"Workout table deleted successfully: {table_id}")
            return JsonResponse({'success': True, 'message': 'Workout table deleted successfully'})
        except WorkoutTable.DoesNotExist:
            logger.error(f"Workout table not found: {table_id}")
            return JsonResponse({'success': False, 'message': 'Workout table not found'}, status=404)
        except Exception as e:
            logger.error(f"Error deleting workout table: {str(e)}")
            return JsonResponse({'success': False, 'message': f"Error deleting workout table: {str(e)}"}, status=500)

    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)

def workout_detail(request, workout_id):
    """
    View for a specific workout session.
    Displays details of the workout and a form to add exercises to it.
    """
    workout = get_object_or_404(WorkoutSession, id=workout_id)

    workout_exercises = WorkoutExercise.objects.filter(workout=workout).order_by('id')

    if request.method == 'POST':
        form = WorkoutExerciseForm(request.POST)
        if form.is_valid():
            workout_exercise = form.save(commit=False)
            workout_exercise.workout = workout
            workout_exercise.save()
            return redirect('workout_detail', workout_id=workout_id)
    else:
        form = WorkoutExerciseForm()  # Create an empty form

    context = {
        'workout': workout,
        'workout_exercises': workout_exercises,
        'form': form,
    }
    return render(request, 'count_calories_app/workout_detail.html', context)

def running_tracker(request):
    """
    View for the running tracking page.
    Handles displaying the form, list of running sessions, and charts,
    as well as processing form submissions.
    """
    min_distance = request.GET.get('min_distance', 3)
    try:
        min_distance = float(min_distance)
    except ValueError:
        min_distance = 3

    running_sessions = RunningSession.objects.filter(distance__gte=min_distance).order_by('-date')

    running_sessions_with_speed = []
    highest_speed_session = None
    lowest_speed_session = None
    highest_speed = 0
    lowest_speed = float('inf')

    for session in running_sessions:
        session_data = {
            'session': session,
            'speed': 0  # Default value
        }

        duration_seconds = session.duration.total_seconds()
        if duration_seconds > 0:  # Avoid division by zero
            hours = duration_seconds / 3600  # Convert seconds to hours
            speed = float(session.distance) / hours
            session_data['speed'] = round(speed, 1)  # Round to 1 decimal place

            if speed > highest_speed:
                highest_speed = speed
                highest_speed_session = session_data
            if speed < lowest_speed:
                lowest_speed = speed
                lowest_speed_session = session_data

        running_sessions_with_speed.append(session_data)

    if request.method == 'POST':
        logger.info(f"Processing running session form submission: {request.POST}")
        form = RunningSessionForm(request.POST)
        if form.is_valid():
            try:
                running_session = form.save()
                logger.info(f"Running session saved successfully: {running_session.id} - {running_session.distance} km")
                messages.success(request, f"Running session of {running_session.distance} km added successfully!")
                return redirect('running_tracker')
            except Exception as e:
                logger.error(f"Error saving running session: {str(e)}")
                messages.error(request, f"Error saving running session: {str(e)}")
        else:
            logger.warning(f"Invalid running session form: {form.errors}")
            messages.warning(request, "Please correct the errors in the form.")
    else:
        form = RunningSessionForm(initial={'date': timezone.now()})  # Create an empty form with current date/time

    context = {
        'form': form,
        'running_sessions': running_sessions_with_speed,
        'highest_speed_session': highest_speed_session,
        'lowest_speed_session': lowest_speed_session,
        'min_distance': min_distance,
    }
    return render(request, 'count_calories_app/running_tracker.html', context)

def edit_running_session(request, running_session_id):
    """
    View for editing a running session.
    """
    running_session = get_object_or_404(RunningSession, id=running_session_id)

    if request.method == 'POST':
        form = RunningSessionForm(request.POST, instance=running_session)
        if form.is_valid():
            form.save()
            messages.success(request, 'Running session updated successfully!')
            return redirect('running_tracker')
    else:
        form = RunningSessionForm(instance=running_session)

    context = {
        'form': form,
        'running_session': running_session,
        'edit_mode': True,
    }
    return render(request, 'count_calories_app/edit_running_session.html', context)

def delete_running_session(request, running_session_id):
    """
    View for deleting a running session.
    """
    running_session = get_object_or_404(RunningSession, id=running_session_id)

    if request.method == 'POST':
        running_session.delete()
        messages.success(request, 'Running session deleted successfully!')
        return redirect('running_tracker')

    context = {
        'running_session': running_session,
    }
    return render(request, 'count_calories_app/delete_running_session.html', context)

def hide_from_quick_list(request, food_item_id):
    """
    View for hiding a food item from the quick list.
    """
    food_item = get_object_or_404(FoodItem, id=food_item_id)

    food_item.hide_from_quick_list = True
    food_item.save()

    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if is_ajax:
        return JsonResponse({
            'success': True,
            'message': f"'{food_item.product_name}' has been hidden from the quick list."
        })
    else:
        messages.success(request, f"'{food_item.product_name}' has been hidden from the quick list.")

        return redirect('food_tracker')

def get_running_data(request):
    """
    API endpoint to get running data for charts
    """
    end_date = timezone.now()
    start_date = end_date - timedelta(days=90)

    min_distance = request.GET.get('min_distance', 3)
    try:
        min_distance = float(min_distance)
    except ValueError:
        min_distance = 3

    running_sessions = RunningSession.objects.filter(
        date__gte=start_date,
        date__lte=end_date,
        distance__gte=min_distance
    ).order_by('date')

    stats = {
        'total_distance': 0,
        'total_sessions': 0,
        'avg_distance': 0,
        'avg_duration': 0,
        'avg_speed': 0,  # Average speed in km/h
        'avg_pace': 0,   # Average pace in min/km
        'total_calories': 0,  # Estimated total calories burned
        'weekly_distance': 0,  # Average weekly distance
        'monthly_distance': 0,  # Average monthly distance
        'pace_improvement': 0,  # Pace improvement over time (%)
        'longest_run': 0,  # Longest run distance
        'fastest_pace': 0,  # Fastest pace (min/km)
    }

    labels = []
    distances = []
    durations = []
    paces = []  # Pace in min/km
    speeds = []  # Speed in km/h
    calories = []  # Estimated calories burned

    weekly_distances = {}
    monthly_distances = {}

    first_pace = None
    last_pace = None

    fastest_pace_value = float('inf')
    longest_run_distance = 0

    for session in running_sessions:
        labels.append(session.date.strftime('%Y-%m-%d'))
        distances.append(float(session.distance))

        duration_minutes = session.duration.total_seconds() / 60
        durations.append(duration_minutes)

        if float(session.distance) > 0:
            pace = duration_minutes / float(session.distance)
            paces.append(pace)

            if first_pace is None:
                first_pace = pace
            last_pace = pace

            if pace < fastest_pace_value:
                fastest_pace_value = pace
        else:
            paces.append(0)

        if duration_minutes > 0:
            speed = float(session.distance) / (duration_minutes / 60)
            speeds.append(speed)
        else:
            speeds.append(0)

        calorie_estimate = float(session.distance) * 60
        calories.append(calorie_estimate)

        if float(session.distance) > longest_run_distance:
            longest_run_distance = float(session.distance)

        week_key = session.date.strftime('%Y-%W')
        if week_key not in weekly_distances:
            weekly_distances[week_key] = 0
        weekly_distances[week_key] += float(session.distance)

        month_key = session.date.strftime('%Y-%m')
        if month_key not in monthly_distances:
            monthly_distances[month_key] = 0
        monthly_distances[month_key] += float(session.distance)

    if running_sessions:
        stats['total_distance'] = sum(distances)
        stats['total_sessions'] = len(running_sessions)
        stats['avg_distance'] = stats['total_distance'] / stats['total_sessions']
        total_duration_minutes = sum(durations)
        stats['avg_duration'] = total_duration_minutes / stats['total_sessions']

        total_duration_hours = total_duration_minutes / 60
        if total_duration_hours > 0:  # Avoid division by zero
            stats['avg_speed'] = stats['total_distance'] / total_duration_hours

        if stats['total_distance'] > 0:
            stats['avg_pace'] = total_duration_minutes / stats['total_distance']

        stats['total_calories'] = sum(calories)

        if weekly_distances:
            stats['weekly_distance'] = sum(weekly_distances.values()) / len(weekly_distances)

        if monthly_distances:
            stats['monthly_distance'] = sum(monthly_distances.values()) / len(monthly_distances)

        if first_pace is not None and last_pace is not None and first_pace > 0:
            improvement_percentage = ((last_pace - first_pace) / first_pace) * 100
            stats['pace_improvement'] = -improvement_percentage  # Invert so positive means improvement

        stats['longest_run'] = longest_run_distance
        stats['fastest_pace'] = fastest_pace_value if fastest_pace_value != float('inf') else 0

    running_data = {
        'labels': labels,
        'distances': distances,
        'durations': durations,
        'paces': paces,
        'speeds': speeds,
        'calories': calories,
        'stats': stats
    }

    return JsonResponse(running_data)

def body_measurements_tracker(request):
    """
    View for the body measurements tracker page.
    """
    try:
        measurements = BodyMeasurement.objects.all().order_by('-date')

        if request.method == 'POST':
            form = BodyMeasurementForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Body measurements added successfully!')
                return redirect('body_measurements_tracker')
        else:
            form = BodyMeasurementForm(initial={'date': timezone.now()})

        weights = Weight.objects.all()

        measurements_with_arrows = []
        for i, measurement in enumerate(measurements):
            measurement_data = {
                'measurement': measurement,
                'arrows': {},
                'weight': None
            }

            measurement_date = measurement.date.date() if hasattr(measurement.date, 'date') else measurement.date
            matching_weight = weights.filter(recorded_at__date=measurement_date).first()
            if matching_weight:
                measurement_data['weight'] = matching_weight.weight

            if i < len(measurements) - 1:
                next_measurement = measurements[i + 1]

                for field in ['neck', 'chest', 'belly', 'left_biceps', 'right_biceps',
                              'left_triceps', 'right_triceps', 'left_forearm', 'right_forearm',
                              'left_thigh', 'right_thigh', 'left_lower_leg', 'right_lower_leg', 'butt']:
                    current_value = getattr(measurement, field)
                    next_value = getattr(next_measurement, field)

                    if current_value is not None and next_value is not None:
                        if current_value > next_value:
                            measurement_data['arrows'][field] = 'up'
                        elif current_value < next_value:
                            measurement_data['arrows'][field] = 'down'
                        else:
                            measurement_data['arrows'][field] = 'equal'

            if i < len(measurements) - 1 and measurement_data['weight'] is not None:
                next_measurement_date = measurements[i + 1].date.date() if hasattr(measurements[i + 1].date, 'date') else measurements[i + 1].date
                next_matching_weight = weights.filter(recorded_at__date=next_measurement_date).first()
                if next_matching_weight:
                    if measurement_data['weight'] > next_matching_weight.weight:
                        measurement_data['arrows']['weight'] = 'up'
                    elif measurement_data['weight'] < next_matching_weight.weight:
                        measurement_data['arrows']['weight'] = 'down'
                    else:
                        measurement_data['arrows']['weight'] = 'equal'

            measurements_with_arrows.append(measurement_data)

        from django.core.paginator import Paginator
        paginator = Paginator(measurements_with_arrows, 10)  # Show 10 measurements per page

        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        table_view = request.GET.get('table_view', 'false')

        return render(request, 'count_calories_app/body_measurements_tracker.html', {
            'form': form,
            'measurements_with_arrows': measurements_with_arrows,  # Keep the full list for charts
            'page_obj': page_obj,  # Add paginated measurements
            'page_title': 'Body Measurements Tracker',
            'table_view': table_view,  # Pass table view state to template
        })
    except Exception as e:
        logger.error(f"Error in body_measurements_tracker: {str(e)}")
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect('home')

def edit_body_measurement(request, measurement_id):
    """
    View for editing an existing body measurement.
    """
    try:
        measurement = get_object_or_404(BodyMeasurement, id=measurement_id)

        if request.method == 'POST':
            form = BodyMeasurementForm(request.POST, instance=measurement)
            if form.is_valid():
                form.save()
                messages.success(request, 'Body measurements updated successfully!')
                return redirect('body_measurements_tracker')
        else:
            form = BodyMeasurementForm(instance=measurement)

        return render(request, 'count_calories_app/edit_body_measurement.html', {
            'form': form,
            'measurement': measurement,
            'page_title': 'Edit Body Measurements',
        })
    except Exception as e:
        logger.error(f"Error in edit_body_measurement: {str(e)}")
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect('body_measurements_tracker')

def delete_body_measurement(request, measurement_id):
    """
    View for deleting a body measurement.
    """
    try:
        measurement = get_object_or_404(BodyMeasurement, id=measurement_id)

        if request.method == 'POST':
            measurement.delete()
            messages.success(request, 'Body measurements deleted successfully!')
            return redirect('body_measurements_tracker')

        return render(request, 'count_calories_app/delete_body_measurement.html', {
            'measurement': measurement,
            'page_title': 'Delete Body Measurements',
        })
    except Exception as e:
        logger.error(f"Error in delete_body_measurement: {str(e)}")
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect('body_measurements_tracker')

def get_body_measurements_data(request):
    """
    API endpoint to get body measurements data for charts.
    """
    try:
        measurements = BodyMeasurement.objects.all().order_by('date')

        if not measurements.exists():
            return JsonResponse({
                'dates': [],
                'weight': [],
                'neck': [],
                'chest': [],
                'belly': [],
                'left_biceps': [],
                'right_biceps': [],
                'left_triceps': [],
                'right_triceps': [],
                'left_forearm': [],
                'right_forearm': [],
                'left_thigh': [],
                'right_thigh': [],
                'left_lower_leg': [],
                'right_lower_leg': [],
                'butt': [],
            })

        weights = Weight.objects.all()

        dates = [m.date.strftime('%Y-%m-%d') for m in measurements]
        neck_data = [float(m.neck) if m.neck else None for m in measurements]
        chest_data = [float(m.chest) if m.chest else None for m in measurements]
        belly_data = [float(m.belly) if m.belly else None for m in measurements]
        left_biceps_data = [float(m.left_biceps) if m.left_biceps else None for m in measurements]
        right_biceps_data = [float(m.right_biceps) if m.right_biceps else None for m in measurements]
        left_triceps_data = [float(m.left_triceps) if m.left_triceps else None for m in measurements]
        right_triceps_data = [float(m.right_triceps) if m.right_triceps else None for m in measurements]
        left_forearm_data = [float(m.left_forearm) if m.left_forearm else None for m in measurements]
        right_forearm_data = [float(m.right_forearm) if m.right_forearm else None for m in measurements]
        left_thigh_data = [float(m.left_thigh) if m.left_thigh else None for m in measurements]
        right_thigh_data = [float(m.right_thigh) if m.right_thigh else None for m in measurements]
        left_lower_leg_data = [float(m.left_lower_leg) if m.left_lower_leg else None for m in measurements]
        right_lower_leg_data = [float(m.right_lower_leg) if m.right_lower_leg else None for m in measurements]
        butt_data = [float(m.butt) if m.butt else None for m in measurements]

        weight_data = []
        for m in measurements:
            measurement_date = m.date.date() if hasattr(m.date, 'date') else m.date
            matching_weight = weights.filter(recorded_at__date=measurement_date).first()
            if matching_weight:
                weight_data.append(float(matching_weight.weight))
            else:
                weight_data.append(None)

        return JsonResponse({
            'dates': dates,
            'weight': weight_data,
            'neck': neck_data,
            'chest': chest_data,
            'belly': belly_data,
            'left_biceps': left_biceps_data,
            'right_biceps': right_biceps_data,
            'left_triceps': left_triceps_data,
            'right_triceps': right_triceps_data,
            'left_forearm': left_forearm_data,
            'right_forearm': right_forearm_data,
            'left_thigh': left_thigh_data,
            'right_thigh': right_thigh_data,
            'left_lower_leg': left_lower_leg_data,
            'right_lower_leg': right_lower_leg_data,
            'butt': butt_data,
        })
    except Exception as e:
        logger.error(f"Error in get_body_measurements_data: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)



def export_body_measurements_csv(request):
    """
    Export all body measurements as CSV with a matched weight column by date.
    """
    try:
        measurements = BodyMeasurement.objects.all().order_by('-date')
        weights = Weight.objects.all()

        response = HttpResponse(content_type='text/csv')
        filename = timezone.now().strftime('body_measurements_%Y-%m-%d.csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        writer = csv.writer(response)
        header = [
            'Date', 'Weight (kg)', 'Neck (cm)', 'Chest (cm)', 'Belly/Waist (cm)',
            'Left Biceps (cm)', 'Right Biceps (cm)', 'Left Triceps (cm)', 'Right Triceps (cm)',
            'Left Forearm (cm)', 'Right Forearm (cm)', 'Left Thigh (cm)', 'Right Thigh (cm)',
            'Left Lower Leg (cm)', 'Right Lower Leg (cm)', 'Butt/Glutes (cm)', 'Notes'
        ]
        writer.writerow(header)

        for m in measurements:
            measurement_date = m.date.date() if hasattr(m.date, 'date') else m.date
            matching_weight = weights.filter(recorded_at__date=measurement_date).first()
            weight_value = float(matching_weight.weight) if (matching_weight and matching_weight.weight is not None) else ''

            row = [
                m.date.strftime('%Y-%m-%d'),
                weight_value,
                float(m.neck) if m.neck is not None else '',
                float(m.chest) if m.chest is not None else '',
                float(m.belly) if m.belly is not None else '',
                float(m.left_biceps) if m.left_biceps is not None else '',
                float(m.right_biceps) if m.right_biceps is not None else '',
                float(m.left_triceps) if m.left_triceps is not None else '',
                float(m.right_triceps) if m.right_triceps is not None else '',
                float(m.left_forearm) if m.left_forearm is not None else '',
                float(m.right_forearm) if m.right_forearm is not None else '',
                float(m.left_thigh) if m.left_thigh is not None else '',
                float(m.right_thigh) if m.right_thigh is not None else '',
                float(m.left_lower_leg) if m.left_lower_leg is not None else '',
                float(m.right_lower_leg) if m.right_lower_leg is not None else '',
                float(m.butt) if m.butt is not None else '',
                (m.notes or '').replace('\r', ' ').replace('\n', ' ').strip()
            ]
            writer.writerow(row)

        return response
    except Exception as e:
        logger.error(f"Error exporting body measurements CSV: {str(e)}")
        messages.error(request, f"An error occurred while exporting CSV: {str(e)}")
        return redirect('body_measurements_tracker')