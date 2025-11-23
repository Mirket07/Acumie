from django.shortcuts import render, get_object_or_404
from django.db.models import Avg
from django.contrib.auth.decorators import login_required
from .models import Grade
from courses.models import Course, Enrollment
from .utils import calculate_weighted_po_score , calculate_lo_scores
from decimal import Decimal
from typing import Any,Dict
import logging
from django.db import DatabaseError

logger = logging.getLogger(__name__)

@login_required
def grade_dashboard_view(request):
    user = request.user
    role = getattr(user, "role", "").upper() if hasattr(user, "role") else (
        "STUDENT" if getattr(user, "is_student", False) else
        "INSTRUCTOR" if getattr(user, "is_teacher", False) else ""
    )

    context: Dict[str, Any] = {
        'user_name': user.get_full_name() or user.username,
        'user_role': role,
    }

    if role == 'STUDENT':
        if callable(calculate_weighted_po_score):
            try:
                po_scores = calculate_weighted_po_score(student_id=user.id) or {}
            except (TypeError, ValueError) as e:
                logger.warning("calculate_weighted_po_score returned invalid data for user %s: %s", user.id, e)
                po_scores = {}
            except DatabaseError as e:
                logger.exception("DB error while calculating PO scores for user %s: %s", user.id, e)
                po_scores = {}
        else:
            logger.warning("calculate_weighted_po_score is not available")
            po_scores = {}

        context['po_scores'] = po_scores
        context['average_po_score'] = f"{(sum(po_scores.values()) / len(po_scores)):.2f}" if po_scores else "N/A"
        context['is_student'] = True

        try:
            total_courses = Course.objects.count()
        except DatabaseError as e:
            logger.exception("DB error counting courses: %s", e)
            total_courses = 0
        context['total_courses'] = total_courses

    elif role == 'INSTRUCTOR':
        context['is_instructor'] = True
        context['message'] = "Instructor dashboard features will be added here."
    elif role == 'DEPT_HEAD':
        context['is_dept_head'] = True
        context['message'] = "Department Head reporting features will be added here."


    courses = []
    if request.user.is_staff or request.user.is_superuser:
        try:
            courses = list(Course.objects.all())
        except Exception:
            courses = []
    else:
        try:
            enrollments = Enrollment.objects.filter(student=user).select_related('course')
            courses = [e.course for e in enrollments]
        except Exception:
            try:
                courses = list(Course.objects.filter(enrollments__student=user).distinct())
            except Exception:
                courses = []
    context['courses'] = courses

    course_id = request.GET.get('course')
    if course_id:
        selected_course = get_object_or_404(Course, pk=course_id)
        context['selected_course'] = selected_course

        rows = []
        course_total = Decimal("0.00")
        for assessment in selected_course.assessments.all().order_by('type'):
            avg_score = Decimal("0.00")
            try:
                lo_qs = Grade.objects.filter(student=user, assessment=assessment)
                if lo_qs.exists():
                    avg_raw = lo_qs.aggregate(avg=Avg('score_percentage'))['avg'] or 0
                    avg_score = Decimal(avg_raw)
            except DatabaseError as e:
                logger.exception("DB error aggregating grades for user %s assessment %s: %s", user.id, assessment.id, e)
                avg_score = Decimal("0.00")
            except (TypeError, ValueError) as e:
                logger.warning("Unexpected grade values for user %s assessment %s: %s", user.id, assessment.id, e)
                avg_score = Decimal("0.00")

            weight_frac = (Decimal(assessment.weight_percentage) / Decimal(
                100)) if assessment.weight_percentage is not None else Decimal("0.00")
            contribution = (avg_score * weight_frac).quantize(Decimal("0.01"))
            course_total += contribution

            rows.append({
                'assessment': assessment,
                'avg': avg_score.quantize(Decimal("0.01")),
                'weight_percent': float(assessment.weight_percentage or 0),
                'contribution': contribution,
            })

        if callable(calculate_lo_scores):
            try:
                lo_scores = calculate_lo_scores(user, selected_course, treat_missing_as_zero=True)
            except (TypeError, ValueError) as e:
                logger.warning("calculate_lo_scores returned bad data for user %s course %s: %s", user.id,
                               selected_course.id, e)
                lo_scores = {}
            except DatabaseError as e:
                logger.exception("DB error in calculate_lo_scores for user %s course %s: %s", user.id,
                                 selected_course.id, e)
                lo_scores = {}
        else:
            logger.warning("calculate_lo_scores is not callable")
            lo_scores = {}

        context.update({
            'rows': rows,
            'course_total': course_total.quantize(Decimal("0.01")),
            'lo_scores': lo_scores,
        })

    return render(request, 'grades/dashboard.html', context)


def all_grades_average_view(request):
    avg_score = Grade.objects.aggregate(
        avg_mastery=Avg('lo_mastery_score')
    )['avg_mastery']
    
    context = {
        'average': f"{avg_score:.2f}" if avg_score is not None else "0.00"
    }

    return render(request, 'grades/all_grades_average.html', context)