from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from courses.models import Course
from .utils import calculate_weighted_po_score

@login_required
def grade_dashboard_view(request):
    user = request.user
    context = {}

    context['user_name'] = user.get_full_name() or user.username
    context['user_role'] = user.role

    courses_list = Course.objects.all()
    context['courses'] = courses_list

    if user.role == 'STUDENT':
        context['is_student'] = True
        
        po_scores = calculate_weighted_po_score(student_id=user.id)
        context['po_scores'] = po_scores
        
        if po_scores:
            avg_po_score = sum(po_scores.values()) / len(po_scores)
            context['average_po_score'] = f"{avg_po_score:.2f}"
        else:
            context['average_po_score'] = "N/A"
            
        context['total_courses'] = courses_list.count()

    elif user.role == 'INSTRUCTOR':
        context['is_instructor'] = True
        context['message'] = "Instructor dashboard features will be added here."
        
    elif user.role == 'DEPT_HEAD':
        context['is_dept_head'] = True
        context['message'] = "Department Head reporting features will be added here."

    if user.role == 'STUDENT' and not context.get('po_scores'):
         context['info_message'] = "No grades or PO contribution data found to calculate Synergy Score."

    return render(request, 'grades/dashboard.html', context)