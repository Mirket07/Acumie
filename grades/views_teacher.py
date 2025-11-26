# grades/views_teacher.py
import csv
import io
from decimal import Decimal
from typing import List, Tuple

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import user_passes_test, login_required
from django.forms import modelformset_factory
from django.db import transaction, DatabaseError
from django.contrib import messages
from django.urls import reverse

from .models import Grade
from courses.models import Course, Assessment, Enrollment
from outcomes.models import LearningOutcome

# --- define names on all code paths for static analysis ---
GradeForm = None
GradeFormSet = None
try:
    # import into these names directly (no temporary aliases)
    from .forms import GradeForm, GradeFormSet
except ImportError:
    GradeForm = None
    GradeFormSet = None


def teacher_required(user) -> bool:
    """Return True for active users flagged as teacher or staff."""
    return user.is_active and (getattr(user, "is_teacher", False) or user.is_staff)


teacher_decorator = user_passes_test(teacher_required)


@teacher_decorator
@login_required
def teacher_select_assessment(request, course_id: int):
    course = get_object_or_404(Course, pk=course_id)
    assessments = course.assessments.all().order_by('type')
    return render(request, 'grades/teacher/select_assessment.html', {
        'course': course,
        'assessments': assessments,
    })


@teacher_decorator
@login_required
def teacher_grade_entry(request, course_id: int):
    course = get_object_or_404(Course, pk=course_id)
    assessment_id = request.GET.get('assessment')
    if not assessment_id:
        return redirect(reverse('grades:teacher_select_assessment', args=[course_id]))

    assessment = get_object_or_404(Assessment, pk=assessment_id, course=course)

    # Get enrolled students
    enrolled_qs = Enrollment.objects.filter(course=course).select_related('student')
    students = [e.student for e in enrolled_qs]

    # LOs related to this assessment
    los = list(assessment.learning_outcomes.all())

    # Pre-create missing Grade rows (student x assessment x lo)
    created_count = 0
    try:
        with transaction.atomic():
            for student in students:
                for lo in los:
                    _, created = Grade.objects.get_or_create(
                        student=student,
                        assessment=assessment,
                        learning_outcome=lo,
                        defaults={'score_percentage': Decimal('0.00'), 'lo_mastery_score': 1}
                    )
                    if created:
                        created_count += 1
    except DatabaseError as db_err:
        messages.error(request, f"Database error preparing grade rows: {db_err}")
        created_count = 0

    # Queryset for the formset
    qs = Grade.objects.filter(assessment=assessment, student__in=students).order_by('student__username', 'learning_outcome__code')

    # Determine which GradeFormSet to use
    grade_formset_class = GradeFormSet
    if grade_formset_class is None:
        # fallback: only edit score_percentage and lo_mastery_score
        grade_formset_class = modelformset_factory(Grade, fields=('score_percentage', 'lo_mastery_score'), extra=0)

    if request.method == 'POST':
        formset = grade_formset_class(request.POST, queryset=qs)
        if formset.is_valid():
            try:
                with transaction.atomic():
                    formset.save()
                messages.success(request, "Grades saved successfully.")
                return redirect(f"{reverse('grades:teacher_grade_entry', args=[course_id])}?assessment={assessment.id}")
            except DatabaseError as db_err:
                messages.error(request, f"Database error saving grades: {db_err}")
        else:
            messages.error(request, "There are validation errors. Please fix them and submit again.")
    else:
        formset = grade_formset_class(queryset=qs)

    return render(request, 'grades/teacher/grade_entry.html', {
        'course': course,
        'assessment': assessment,
        'formset': formset,
        'students': students,
        'los': los,
        'created_count': created_count,
    })


@teacher_decorator
@login_required
def teacher_grade_bulk_upload(request, course_id: int):
    course = get_object_or_404(Course, pk=course_id)

    if request.method == 'POST':
        csvfile = request.FILES.get('csv_file')
        if not csvfile:
            messages.error(request, "No file uploaded.")
            return redirect(request.path)

        # Try UTF-8, fall back to latin-1 if necessary
        try:
            data = csvfile.read().decode('utf-8')
        except UnicodeDecodeError:
            try:
                data = csvfile.read().decode('latin-1')
            except Exception as decode_err:
                messages.error(request, f"Could not decode uploaded file: {decode_err}")
                return redirect(request.path)

        reader = csv.DictReader(io.StringIO(data))
        errors: List[Tuple[int, str]] = []
        success_count = 0
        last_assessment = None

        try:
            with transaction.atomic():
                for line_no, row in enumerate(reader, start=2):
                    student_username = (row.get('student_username') or row.get('username') or '').strip()
                    assessment_field = (row.get('assessment_id') or row.get('assessment_code') or row.get('assessment') or '').strip()
                    lo_code = (row.get('lo_code') or row.get('learning_outcome') or row.get('lo') or '').strip()
                    score_str = (row.get('score_percentage') or row.get('score') or '').strip()
                    mastery_str = (row.get('lo_mastery_score') or row.get('mastery') or '').strip()

                    if not (student_username and assessment_field and lo_code and score_str and mastery_str):
                        errors.append((line_no, "Missing required column(s)"))
                        continue

                    # find student
                    from django.contrib.auth import get_user_model
                    User = get_user_model()
                    try:
                        student = User.objects.get(username=student_username)
                    except User.DoesNotExist:
                        errors.append((line_no, f"Student '{student_username}' not found"))
                        continue

                    # find assessment (prefer id)
                    assessment_obj = None
                    if assessment_field.isdigit():
                        assessment_obj = Assessment.objects.filter(pk=int(assessment_field), course=course).first()
                    if assessment_obj is None:
                        assessment_obj = Assessment.objects.filter(course=course).first()  # fallback heuristic

                    if assessment_obj is None:
                        errors.append((line_no, f"Assessment '{assessment_field}' not found for course"))
                        continue

                    last_assessment = assessment_obj

                    # find LO
                    lo_obj = LearningOutcome.objects.filter(code=lo_code).first()
                    if lo_obj is None:
                        errors.append((line_no, f"Learning outcome '{lo_code}' not found"))
                        continue

                    # parse numeric values
                    try:
                        score_decimal = Decimal(score_str)
                        mastery_int = int(mastery_str)
                    except (ArithmeticError, ValueError) as parse_err:
                        errors.append((line_no, f"Invalid numeric value: {parse_err}"))
                        continue

                    # update or create grade row
                    Grade.objects.update_or_create(
                        student=student,
                        assessment=assessment_obj,
                        learning_outcome=lo_obj,
                        defaults={'score_percentage': score_decimal, 'lo_mastery_score': mastery_int}
                    )
                    success_count += 1

        except DatabaseError as db_err:
            messages.error(request, f"Database error during upload: {db_err}")
            return redirect(request.path)

        # Show results to user
        if errors:
            for ln, err in errors[:20]:
                messages.error(request, f"Line {ln}: {err}")
            messages.info(request, f"Imported {success_count} rows (some rows had errors).")
        else:
            messages.success(request, f"Successfully imported {success_count} rows.")

        # Redirect to grade entry for the last processed assessment if available
        if last_assessment:
            return redirect(reverse('grades:teacher_grade_entry', args=[course_id]) + f'?assessment={last_assessment.id}')
        return redirect(reverse('grades:teacher_select_assessment', args=[course_id]))

    # GET: show upload form
    return render(request, 'grades/teacher/bulk_upload.html', {'course': course})
