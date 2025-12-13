from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    path('<int:course_id>/', views.course_detail_view, name='detail'),
]