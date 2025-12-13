from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Course
from grades.models import Grade
# Yeni eklenen import
from feedback.models import FeedbackRequest

@login_required
def course_detail_view(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    sections = course.sections.prefetch_related('materials').all()
    
    # Bu değişkeni template'e göndereceğiz
    requested_assessment_ids = []

    if request.user.role == 'STUDENT':
        student_grades = Grade.objects.filter(
            student=request.user,
            assessment__course=course
        ).select_related('assessment')
        is_instructor = False
        
        # Öğrencinin bu derste daha önce feedback istediği sınavların ID'lerini çekiyoruz
        requested_assessment_ids = list(FeedbackRequest.objects.filter(
            student=request.user,
            assessment__course=course
        ).values_list('assessment_id', flat=True))
        
    elif request.user.role == 'INSTRUCTOR':
        student_grades = Grade.objects.filter(
            assessment__course=course
        ).select_related('assessment', 'student').order_by('student__first_name')
        is_instructor = True
        
    else:
        student_grades = []
        is_instructor = False

    context = {
        'course': course,
        'sections': sections,
        'student_grades': student_grades,
        'is_instructor': is_instructor,
        'requested_assessment_ids': requested_assessment_ids, # Context'e ekledik
    }
    
    return render(request, 'courses/course_detail.html', context)