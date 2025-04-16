from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('api/nutrition-data/', views.get_nutrition_data, name='nutrition_data'),
    path('api/calories-trend/', views.get_calories_trend_data, name='calories_trend_data'),
    path('api/macros-trend/', views.get_macros_trend_data, name='macros_trend_data'),

    # Weight tracking URLs
    path('weight/', views.weight_tracker, name='weight_tracker'),
    path('api/weight-data/', views.get_weight_data, name='weight_data'),

    # Workout tracking URLs
    path('workout/', views.workout_tracker, name='workout_tracker'),
    path('workout/<int:workout_id>/', views.workout_detail, name='workout_detail'),
    path('exercise/', views.exercise_list, name='exercise_list'),
    path('api/workout-frequency/', views.get_workout_frequency_data, name='workout_frequency_data'),
    path('api/exercise-progress/', views.get_exercise_progress_data, name='exercise_progress_data'),
    path('api/exercise-progress/<int:exercise_id>/', views.get_exercise_progress_data, name='exercise_progress_data_with_id'),
]
