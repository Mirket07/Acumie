from django.urls import path
from . import views
from . import views_teacher

app_name = 'grades'

urlpatterns = [
    path('dashboard/', views.grade_dashboard_view, name='dashboard'),
    path('average/all/', views.all_grades_average_view, name='all_grades_average'),
    path('teacher/course/<int:course_id>/select-assessment/', views_teacher.teacher_select_assessment, name='teacher_select_assessment'),
    path('teacher/course/<int:course_id>/grades/', views_teacher.teacher_grade_entry, name='teacher_grade_entry'),
    path('teacher/course/<int:course_id>/grades/bulk-upload/', views_teacher.teacher_grade_bulk_upload, name='teacher_grade_bulk_upload'),

]