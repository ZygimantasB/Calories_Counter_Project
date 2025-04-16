from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('api/nutrition-data/', views.get_nutrition_data, name='nutrition_data'),

    # Weight tracking URLs
    path('weight/', views.weight_tracker, name='weight_tracker'),
    path('api/weight-data/', views.get_weight_data, name='weight_data'),

    # Workout tracking URLs
    path('workout/', views.workout_tracker, name='workout_tracker'),
    path('workout/<int:workout_id>/', views.workout_detail, name='workout_detail'),
    path('exercise/', views.exercise_list, name='exercise_list'),
]
