from django.urls import path
from . import views
from . import views_teacher

app_name = 'grades'

urlpatterns = [
    path('dashboard/', views.grade_dashboard_view, name='dashboard'),
]