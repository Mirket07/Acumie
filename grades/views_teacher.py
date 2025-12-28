import csv
import io
from decimal import Decimal
from typing import List, Tuple
from functools import wraps

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db import transaction, DatabaseError
from django.contrib import messages
from django.urls import reverse
from django.conf import settings
from django.http import HttpResponseForbidden
from django.core.exceptions import PermissionDenied
from django.contrib.auth.views import redirect_to_login
from django.db.models import Avg

from .models import Grade
from courses.models import Course, Assessment, Enrollment
from outcomes.models import LearningOutcome
from feedback.models import FeedbackRequest


DEFAULT_MAX_UPLOAD_BYTES = getattr(settings, "GRADE_CSV_MAX_BYTES", 5 * 1024 * 1024)
ALLOWED_UPLOAD_EXTENSIONS = getattr(settings, "GRADE_CSV_ALLOWED_EXT", (".csv",))


def permission_or_staff_required(perm_codename: str):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            user = request.user
            if not user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            if user.is_superuser or user.is_staff:
                return view_func(request, *args, **kwargs)
            if user.has_perm(perm_codename) or getattr(user, "is_teacher", False):
                return view_func(request, *args, **kwargs)
            raise PermissionDenied
        return _wrapped
    return decorator


def _user_can_manage_course(user, course: Course) -> bool:
    if user.is_staff or user.is_superuser:
        return True
    return course.instructor_id == user.id


@login_required
def teacher_dashboard(request):
    user = request.user
    if not (user.is_staff or getattr(user, "role", "") == "INSTRUCTOR"):
        return HttpResponseForbidden()

    my_courses = Course.objects.all() if user.is_staff else Course.objects.filter(instructor=user)

    feedback_requests = FeedbackRequest.objects.filter(
        assessment__course__in=my_courses,
        is_resolved=False
    ).select_related('student', 'assessment').order_by('-request_date')

    return render(request, "grades/teacher/dashboard.html", {
        "my_courses": my_courses.order_by("code"),
        "feedback_requests": feedback_requests
    })


CAN_GRADE_DECORATOR = permission_or_staff_required("grades.can_grade")


@CAN_GRADE_DECORATOR
@login_required
def teacher_grade_entry(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    if not _user_can_manage_course(request.user, course):
        return HttpResponseForbidden()

    assessments = list(course.assessments.all().order_by("type"))
    students = [e.student for e in Enrollment.objects.filter(course=course).select_related("student")]

    with transaction.atomic():
        for student in students:
            for assessment in assessments:
                for lo in assessment.learning_outcomes.all():
                    Grade.objects.get_or_create(
                        student=student,
                        assessment=assessment,
                        learning_outcome=lo,
                        defaults={"score_percentage": Decimal("0.00"), "lo_mastery_score": 1}
                    )

    if request.method == "POST":
        updated = 0
        errors = []

        for student in students:
            for assessment in assessments:
                key = f"score_{student.id}_{assessment.id}"
                raw = request.POST.get(key, "").strip()
                if raw == "":
                    continue
                try:
                    val = Decimal(raw)
                    if val < 0 or val > 100:
                        raise ValueError
                except Exception:
                    errors.append(f"Invalid score for {student.username} / {assessment.get_type_display()}")
                    continue

                qs = Grade.objects.filter(student=student, assessment=assessment)
                for g in qs:
                    g.score_percentage = val
                    g.save(update_fields=["score_percentage"])
                    updated += 1

        if errors:
            for e in errors:
                messages.error(request, e)
        if updated:
            messages.success(request, "Grades updated successfully.")

        return redirect(reverse("grades:grade_entry", args=[course.id]))

    flat_scores = {}
    for student in students:
        for assessment in assessments:
            avg = Grade.objects.filter(
                student=student,
                assessment=assessment
            ).aggregate(a=Avg("score_percentage"))["a"]
            flat_scores[f"{student.id}_{assessment.id}"] = (
                Decimal(avg).quantize(Decimal("0.01")) if avg is not None else ""
            )

    return render(request, "grades/teacher/grade_entry.html", {
        "course": course,
        "students": students,
        "assessments": assessments,
        "flat_scores": flat_scores
    })


@CAN_GRADE_DECORATOR
@login_required
def teacher_grade_bulk_upload(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    if not _user_can_manage_course(request.user, course):
        return HttpResponseForbidden()

    if request.method == "POST":
        csvfile = request.FILES.get("csv_file")
        if not csvfile:
            messages.error(request, "No file uploaded.")
            return redirect(request.path)

        reader = csv.DictReader(io.StringIO(csvfile.read().decode("utf-8")))
        success = 0

        with transaction.atomic():
            for row in reader:
                student = row.get("student_username")
                lo_code = row.get("lo_code")
                score = row.get("score_percentage")
                mastery = row.get("lo_mastery_score")

                try:
                    from django.contrib.auth import get_user_model
                    User = get_user_model()
                    student = User.objects.get(username=student)
                    lo = LearningOutcome.objects.get(code=lo_code)
                    assessment = Assessment.objects.filter(course=course, learning_outcomes=lo).first()
                    Grade.objects.update_or_create(
                        student=student,
                        assessment=assessment,
                        learning_outcome=lo,
                        defaults={
                            "score_percentage": Decimal(score),
                            "lo_mastery_score": int(mastery)
                        }
                    )
                    success += 1
                except Exception:
                    continue

        messages.success(request, f"{success} grades imported.")
        return redirect(reverse("grades:grade_entry", args=[course.id]))

    return render(request, "grades/teacher/bulk_upload.html", {"course": course})
