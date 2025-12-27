from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from courses.models import Course
from .models import Grade
from .utils import calculate_weighted_po_score


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
        courses_qs = Course.objects.filter(
            enrollments__student=user
        ).distinct().order_by("code")

    context["courses"] = courses_qs
    context["total_courses"] = courses_qs.count()

    if role == "STUDENT":
        context["is_student"] = True

        try:
            po_scores = calculate_weighted_po_score(student_id=user.id) or {}
        except Exception:
            po_scores = {}

        context["po_scores"] = po_scores
        context["average_po_score"] = (
            f"{sum(po_scores.values()) / len(po_scores):.2f}"
            if po_scores else "N/A"
        )

        if not po_scores:
            context["info_message"] = (
                "No grades or PO contribution data found to calculate Synergy Score."
            )

    if role == "INSTRUCTOR":
        context["is_instructor"] = True
        context["message"] = "Instructor dashboard features will be added here."

    if role == "DEPT_HEAD":
        context["is_dept_head"] = True
        context["message"] = "Department Head reporting features will be added here."

    return render(request, "grades/dashboard.html", context)


@login_required
def all_grades_average_view(request):
    avg_score = Grade.objects.aggregate(avg_mastery=Grade.objects.all().values("lo_mastery_score"))["avg_mastery"]
    context = {
        "average": f"{avg_score:.2f}" if avg_score is not None else "0.00"
    }
    return render(request, "grades/all_grades_average.html", context)
