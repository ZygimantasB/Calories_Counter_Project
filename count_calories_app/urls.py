from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('food_tracker/', views.food_tracker, name='food_tracker'),
    path('top_foods/', views.top_foods, name='top_foods'),
    path('api/food-autocomplete/', views.food_autocomplete, name='food_autocomplete'),
    path('api/nutrition-data/', views.get_nutrition_data, name='nutrition_data'),
    path('api/gemini-nutrition/', views.get_gemini_nutrition, name='gemini_nutrition'),
    path('api/calories-trend/', views.get_calories_trend_data, name='calories_trend_data'),
    path('api/macros-trend/', views.get_macros_trend_data, name='macros_trend_data'),

    path('food/<int:food_item_id>/edit/', views.edit_food_item, name='edit_food_item'),
    path('food/<int:food_item_id>/delete/', views.delete_food_item, name='delete_food_item'),
    path('food/<int:food_item_id>/hide-from-quick-list/', views.hide_from_quick_list, name='hide_from_quick_list'),

    path('weight/', views.weight_tracker, name='weight_tracker'),
    path('weight/<int:weight_id>/edit/', views.edit_weight, name='edit_weight'),
    path('weight/<int:weight_id>/delete/', views.delete_weight, name='delete_weight'),
    path('api/weight-data/', views.get_weight_data, name='weight_data'),
    path('api/weight-calories-correlation/', views.get_weight_calories_correlation, name='weight_calories_correlation'),

    path('workout/', views.workout_tracker, name='workout_tracker'),
    path('workout/<int:workout_id>/', views.workout_detail, name='workout_detail'),
    path('workout-table/', views.workout_table, name='workout_table'),
    path('exercise/', views.exercise_list, name='exercise_list'),
    path('api/workout-frequency/', views.get_workout_frequency_data, name='workout_frequency_data'),
    path('api/exercise-progress/', views.get_exercise_progress_data, name='exercise_progress_data'),
    path('api/exercise-progress/<int:exercise_id>/', views.get_exercise_progress_data, name='exercise_progress_data_with_id'),

    path('running/', views.running_tracker, name='running_tracker'),
    path('running/<int:running_session_id>/edit/', views.edit_running_session, name='edit_running_session'),
    path('running/<int:running_session_id>/delete/', views.delete_running_session, name='delete_running_session'),
    path('api/running-data/', views.get_running_data, name='running_data'),

    path('api/workout-tables/', views.get_workout_tables, name='get_workout_tables'),
    path('api/workout-tables/save/', views.save_workout_table, name='save_workout_table'),
    path('api/workout-tables/<int:table_id>/delete/', views.delete_workout_table, name='delete_workout_table'),

    path('body-measurements/', views.body_measurements_tracker, name='body_measurements_tracker'),
    path('body-measurements/<int:measurement_id>/edit/', views.edit_body_measurement, name='edit_body_measurement'),
    path('body-measurements/<int:measurement_id>/delete/', views.delete_body_measurement, name='delete_body_measurement'),
    path('body-measurements/export/csv/', views.export_body_measurements_csv, name='export_body_measurements_csv'),
    path('api/body-measurements-data/', views.get_body_measurements_data, name='body_measurements_data'),

    path('food-tracker/copy-day/', views.copy_day_meals, name='copy_day_meals'),
    path('meal-templates/', views.meal_templates, name='meal_templates'),
    path('meal-templates/save/', views.save_meal_template, name='save_meal_template'),
    path('meal-templates/<int:template_id>/log/', views.log_meal_template, name='log_meal_template'),
    path('meal-templates/<int:template_id>/delete/', views.delete_meal_template, name='delete_meal_template'),
    path('analytics/', views.analytics, name='analytics'),
    path('analytics/month-compare/', views.month_compare, name='month_compare'),
    path('analytics/trends/', views.month_trends, name='month_trends'),
    path('analytics/product-compare/', views.product_compare, name='product_compare'),

    # Settings
    path('settings/', views.settings_view, name='settings'),
    path('settings/export/', views.export_data, name='export_data'),

    # React API endpoints
    path('api/react/dashboard/', views.api_dashboard, name='api_dashboard'),
    path('api/react/food-items/', views.api_food_items, name='api_food_items'),
    path('api/react/food-items/add/', views.api_add_food, name='api_add_food'),
    path('api/react/food-items/<int:food_id>/update/', views.api_update_food, name='api_update_food'),
    path('api/react/food-items/<int:food_id>/delete/', views.api_delete_food, name='api_delete_food'),
    path('api/react/quick-add-foods/', views.api_quick_add_foods, name='api_quick_add_foods'),
    path('api/react/search-foods/', views.api_search_all_foods, name='api_search_all_foods'),
    path('api/react/weight-items/', views.api_weight_items, name='api_weight_items'),
    path('api/react/weight-items/add/', views.api_add_weight, name='api_add_weight'),
    path('api/react/weight-items/<int:weight_id>/delete/', views.api_delete_weight, name='api_delete_weight'),
    path('api/react/running-items/', views.api_running_items, name='api_running_items'),
    path('api/react/running-items/add/', views.api_add_running, name='api_add_running'),
    path('api/react/workouts/', views.api_workouts, name='api_workouts'),
    path('api/react/exercises/', views.api_exercises, name='api_exercises'),
    path('api/react/body-measurements/', views.api_body_measurements, name='api_body_measurements'),
    path('api/react/analytics/', views.api_analytics, name='api_analytics'),
    path('api/react/top-foods/', views.api_top_foods, name='api_top_foods'),
    path('api/react/settings/', views.api_settings, name='api_settings'),
    path('api/react/settings/update/', views.api_update_settings, name='api_update_settings'),
    path('api/react/settings/fitness-goal/', views.api_update_fitness_goal, name='api_update_fitness_goal'),
]
