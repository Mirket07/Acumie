from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    path('<int:course_id>/', views.course_detail_view, name='detail'),
    path('teacher/course/create/', views.teacher_course_create, name='teacher_course_create'),
    path('teacher/course/<int:course_id>/edit/', views.teacher_course_edit, name='teacher_course_edit'),
    path('teacher/course/<int:course_id>/add-material/', views.teacher_add_material, name='teacher_add_material'),
]
