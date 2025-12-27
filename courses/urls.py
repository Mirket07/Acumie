from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    path('<int:course_id>/', views.course_detail_view, name='detail'),
    path('teacher/create/', views.teacher_course_create, name='teacher_course_create'),
    path('teacher/<int:course_id>/edit/', views.teacher_course_edit, name='teacher_course_edit'),
]