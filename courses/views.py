from django.shortcuts import render, get_object_or_404
from .models import Course
from grades.models import Grade

def course_detail_view(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    sections = course.sections.prefetch_related('materials').all()
    
    student_grades = []
    if request.user.is_authenticated and request.user.role == 'STUDENT':
        student_grades = Grade.objects.filter(
            student=request.user,
            assessment__course=course
        ).select_related("assessment", "learning_outcome")

    context = {
        'course': course,
        'sections': sections,
        'student_grades': student_grades,
    }
    return render(request, 'courses/course_detail.html', context)
