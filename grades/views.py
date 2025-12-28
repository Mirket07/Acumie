from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Avg
from decimal import Decimal
from courses.models import Course
from .models import Grade
from .utils import calculate_weighted_po_score, calculate_course_grade

@login_required
def grade_dashboard_view(request):
    user = request.user
    role = getattr(user, "role", "").upper() if hasattr(user, "role") else ""
    context = {
        "user_name": user.get_full_name() or user.username,
        "user_role": role,
    }
    if user.is_staff or user.is_superuser:
        courses_qs = Course.objects.all().order_by("code")
    elif role == "INSTRUCTOR":
        courses_qs = Course.objects.filter(instructor=user).order_by("code")
    else:
        courses_qs = Course.objects.filter(enrollments__student=user).distinct().order_by("code")
    context["courses"] = courses_qs
    context["total_courses"] = courses_qs.count()
    if role == "STUDENT":
        context["is_student"] = True
        course_results = []
        total_weighted_points = Decimal("0.00")
        total_ects = Decimal("0.00")
        for course in courses_qs:
            course_final_score = calculate_course_grade(user, course)
            course_results.append({'code': course.code, 'title': course.title, 'ects': course.ects_credit, 'score': course_final_score})
            total_weighted_points += (course_final_score * Decimal(str(course.ects_credit)))
            total_ects += Decimal(str(course.ects_credit))
        context["course_results"] = course_results
        context["overall_gpa"] = (total_weighted_points / total_ects) if total_ects > 0 else 0
        try:
            po_scores = calculate_weighted_po_score(student_id=user.id) or {}
        except Exception:
            po_scores = {}
        context["po_scores"] = po_scores
        context["average_po_score"] = (f"{sum(po_scores.values()) / len(po_scores):.2f}" if po_scores else "N/A")
    return render(request, "grades/dashboard.html", context)

@login_required
def all_grades_average_view(request):
    avg_score = Grade.objects.aggregate(avg_score=Avg('score_percentage'))['avg_score']
    context = {"average": f"{avg_score:.2f}" if avg_score is not None else "0.00"}
    return render(request, "grades/all_grades_average.html", context)