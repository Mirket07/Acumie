import csv
import io
from decimal import Decimal
from functools import wraps

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.contrib import messages
from django.urls import reverse
from django.conf import settings
from django.http import HttpResponseForbidden
from django.core.exceptions import PermissionDenied
from django.contrib.auth.views import redirect_to_login
from django.db.models import Avg
from django.forms import modelformset_factory

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
            if user.has_perm(perm_codename) or getattr(user, "role", "") == "INSTRUCTOR":
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
    ).select_related("student", "assessment").order_by("-request_date")

    return render(request, "grades/teacher/dashboard.html", {
        "my_courses": my_courses.order_by("code"),
        "feedback_requests": feedback_requests,
        "total_courses": my_courses.count(),
    })


CAN_GRADE_DECORATOR = permission_or_staff_required("grades.can_grade")


@CAN_GRADE_DECORATOR
@login_required
def teacher_grade_entry(request, course_id):
    """
    Grid-based grade entry: rows = students, columns = assessments.
    Editable inputs named score_{student.id}_{assessment.id}
    """
    course = get_object_or_404(Course, pk=course_id)
    if not _user_can_manage_course(request.user, course):
        return HttpResponseForbidden()

    assessments = list(course.assessments.all().order_by("type"))
    students = [e.student for e in Enrollment.objects.filter(course=course).select_related("student")]

    # Ensure grade rows exist (one grade per student x assessment)
    with transaction.atomic():
        for student in students:
            for assessment in assessments:
                Grade.objects.get_or_create(
                    student=student,
                    assessment=assessment,
                    defaults={"score_percentage": Decimal("0.00")}
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

                Grade.objects.filter(student=student, assessment=assessment).update(score_percentage=val)
                updated += 1

        for e in errors:
            messages.error(request, e)
        if updated:
            messages.success(request, "Grades updated successfully.")
        else:
            if not errors:
                messages.info(request, "No changes detected.")

        return redirect(reverse("grades:teacher_grade_entry", args=[course.id]))

    # Build flat_scores dict for pre-filling inputs
    flat_scores = {}
    qs = Grade.objects.filter(assessment__course=course)
    for g in qs:
        flat_scores[f"{g.student_id}_{g.assessment_id}"] = g.score_percentage

    return render(request, "grades/teacher/grade_entry.html", {
        "course": course,
        "students": students,
        "assessments": assessments,
        "flat_scores": flat_scores,
    })


@login_required
def teacher_select_assessment(request, course_id: int):
    course = get_object_or_404(Course, pk=course_id)
    if not _user_can_manage_course(request.user, course):
        return HttpResponseForbidden()
    assessments = course.assessments.all().order_by("type")
    return render(request, "grades/teacher/select_assessment.html", {
        "course": course,
        "assessments": assessments,
    })


@login_required
def teacher_grade_entry_single(request, course_id: int):
    """
    Single-assessment grade entry (formset). URL expects ?assessment=<id>
    Kept as an optional flow for teachers who prefer per-assessment editing.
    """
    course = get_object_or_404(Course, pk=course_id)
    if not _user_can_manage_course(request.user, course):
        return HttpResponseForbidden()

    assessment_id = request.GET.get("assessment")
    if not assessment_id:
        return redirect(reverse("grades:teacher_select_assessment", args=[course_id]))

    assessment = get_object_or_404(Assessment, pk=assessment_id, course=course)
    students = [e.student for e in Enrollment.objects.filter(course=course).select_related("student")]

    with transaction.atomic():
        for s in students:
            Grade.objects.get_or_create(
                student=s,
                assessment=assessment,
                defaults={"score_percentage": Decimal("0.00")}
            )

    qs = Grade.objects.filter(assessment=assessment, student__in=students).order_by("student__username")
    GradeFormSet = modelformset_factory(Grade, fields=("score_percentage",), extra=0)

    if request.method == "POST":
        formset = GradeFormSet(request.POST, queryset=qs)
        if formset.is_valid():
            formset.save()
            messages.success(request, "Grades updated.")
            return redirect(f"{reverse('grades:teacher_grade_entry_single', args=[course_id])}?assessment={assessment.id}")
        else:
            messages.error(request, "There are validation errors. Please fix them and submit again.")
    else:
        formset = GradeFormSet(queryset=qs)

    return render(request, "grades/teacher/grade_entry_single.html", {
        "course": course,
        "assessment": assessment,
        "formset": formset,
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

        filename = getattr(csvfile, "name", "")
        if not any(filename.lower().endswith(ext) for ext in ALLOWED_UPLOAD_EXTENSIONS):
            messages.error(request, f"Invalid file extension. Allowed: {', '.join(ALLOWED_UPLOAD_EXTENSIONS)}")
            return redirect(request.path)

        try:
            data = csvfile.read().decode("utf-8")
        except Exception:
            messages.error(request, "Could not read the uploaded CSV file.")
            return redirect(request.path)

        reader = csv.DictReader(io.StringIO(data))
        success = 0
        with transaction.atomic():
            for row in reader:
                try:
                    username = (row.get("username") or row.get("student_username") or "").strip()
                    assessment_id = (row.get("assessment_id") or "").strip()
                    score_str = (row.get("score") or row.get("score_percentage") or "").strip()
                    if not (username and assessment_id and score_str):
                        continue
                    from django.contrib.auth import get_user_model
                    User = get_user_model()
                    student = User.objects.get(username=username)
                    assessment = Assessment.objects.get(pk=int(assessment_id), course=course)
                    Grade.objects.update_or_create(
                        student=student,
                        assessment=assessment,
                        defaults={"score_percentage": Decimal(score_str)},
                    )
                    success += 1
                except Exception:
                    continue

        messages.success(request, f"{success} grades imported.")
        return redirect(reverse("grades:teacher_grade_entry", args=[course.id]))

    return render(request, "grades/teacher/bulk_upload.html", {"course": course})
