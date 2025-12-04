from django.shortcuts import render, get_object_or_404
from .models import Course

def course_detail_view(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    sections = course.sections.prefetch_related('materials').all()
    
    context = {
        'course': course,
        'sections': sections,
        'assessments': course.assessments.all() 
    }
    return render(request, 'courses/course_detail.html', context)