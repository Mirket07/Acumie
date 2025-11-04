from django.urls import path
from . import views

app_name = 'grades'

urlpatterns = [
    path('dashboard/', views.grade_dashboard_view, name='dashboard'),
    path('average/all/', views.all_grades_average_view, name='all_grades_average'),
]