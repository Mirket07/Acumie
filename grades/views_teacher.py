import csv
import io
from decimal import Decimal
from typing import List, Tuple
from functools import wraps

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.forms import modelformset_factory
from django.db import transaction, DatabaseError
from django.contrib import messages
from django.urls import reverse
from django.conf import settings
from django.http import HttpResponseForbidden
from django.core.exceptions import PermissionDenied
from django.contrib.auth.views import redirect_to_login

from .models import Grade
from courses.models import Course, Assessment, Enrollment
from outcomes.models import LearningOutcome



GradeForm = None
GradeFormSet = None
try:
    from .forms import GradeForm, GradeFormSet
except ImportError:
    GradeForm = None
    GradeFormSet = None


DEFAULT_MAX_UPLOAD_BYTES = getattr(settings, "GRADE_CSV_MAX_BYTES", 5 * 1024 * 1024)
ALLOWED_UPLOAD_EXTENSIONS = getattr(settings, "GRADE_CSV_ALLOWED_EXT", (".csv",))


@login_required
def teacher_dashboard(request):
    user = request.user
    if not (getattr(user, "role", "") == "INSTRUCTOR" or user.is_staff):
        return HttpResponseForbidden("You do not have permission to access this page.")

    my_courses = Course.objects.filter(instructor=user).order_by("code")
    total_courses = my_courses.count()

    context = {
        "my_courses": my_courses,
        "total_courses": total_courses,
    }
    return render(request, "grades/teacher/dashboard.html", context)


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
    if hasattr(course, 'instructor') and getattr(course, 'instructor') is not None:
        try:
            return course.instructor.id == user.id
        except Exception:
            return False
    return getattr(user, 'is_teacher', False)


CAN_GRADE_DECORATOR = permission_or_staff_required('grades.can_grade')


@CAN_GRADE_DECORATOR
@login_required
def teacher_select_assessment(request, course_id: int):
    course = get_object_or_404(Course, pk=course_id)
    if not _user_can_manage_course(request.user, course):
        return HttpResponseForbidden("You do not have permission to manage this course.")
    assessments = course.assessments.all().order_by('type')
    return render(request, 'grades/teacher/select_assessment.html', {
        'course': course,
        'assessments': assessments,
    })


@CAN_GRADE_DECORATOR
@login_required
def teacher_grade_entry(request, course_id: int):
    course = get_object_or_404(Course, pk=course_id)
    if not _user_can_manage_course(request.user, course):
        return HttpResponseForbidden("You do not have permission to manage this course.")
    assessment_id = request.GET.get('assessment')
    if not assessment_id:
        return redirect(reverse('grades:teacher_select_assessment', args=[course_id]))

    assessment = get_object_or_404(Assessment, pk=assessment_id, course=course)

    enrolled_qs = Enrollment.objects.filter(course=course).select_related('student')
    students = [e.student for e in enrolled_qs]

    los = list(assessment.learning_outcomes.all())

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

    qs = Grade.objects.filter(assessment=assessment, student__in=students).order_by('student__username', 'learning_outcome__code')

    grade_formset_class = GradeFormSet
    if grade_formset_class is None:
        grade_formset_class = modelformset_factory(Grade, fields=('score_percentage', 'lo_mastery_score'), extra=0)

    if request.method == 'POST':
        formset = grade_formset_class(request.POST, queryset=qs)
        if formset.is_valid():
            try:
                with transaction.atomic():
                    saved_any = False
                    for form in formset:
                        if not form.has_changed():
                            continue
                        inst = form.save(commit=False)
                        try:
                            score_val = Decimal(inst.score_percentage)
                        except Exception:
                            messages.error(request, f"Invalid score value for {inst.student}. Must be numeric 0-100.")
                            raise
                        if score_val < 0 or score_val > 100:
                            messages.error(request, f"Score out of range (0-100) for {inst.student}.")
                            raise ValueError("score out of range")

                        try:
                            mastery_val = int(inst.lo_mastery_score)
                        except Exception:
                            messages.error(request, f"Invalid mastery value for {inst.student}. Must be integer 1-5.")
                            raise
                        if mastery_val < 1 or mastery_val > 5:
                            messages.error(request, f"Mastery out of range (1-5) for {inst.student}.")
                            raise ValueError("mastery out of range")

                        inst._changed_by = request.user
                        inst.save()
                        saved_any = True
                    if saved_any:
                        messages.success(request, "Grades updated successfully.")
                    else:
                        messages.info(request, "No changes detected.")
                return redirect(f"{reverse('grades:teacher_grade_entry', args=[course_id])}?assessment={assessment.id}")
            except DatabaseError as db_err:
                messages.error(request, f"Database error saving grades: {db_err}")
            except ValueError:
                pass
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


@CAN_GRADE_DECORATOR
@login_required
def teacher_grade_bulk_upload(request, course_id: int):
    course = get_object_or_404(Course, pk=course_id)
    if not _user_can_manage_course(request.user, course):
        return HttpResponseForbidden("You do not have permission to manage this course.")

    if request.method == 'POST':
        csvfile = request.FILES.get('csv_file')
        if not csvfile:
            messages.error(request, "No file uploaded.")
            return redirect(request.path)

        filename = csvfile.name or ""
        if not any(filename.lower().endswith(ext) for ext in ALLOWED_UPLOAD_EXTENSIONS):
            messages.error(request, f"Invalid file extension. Allowed: {', '.join(ALLOWED_UPLOAD_EXTENSIONS)}")
            return redirect(request.path)

        max_bytes = DEFAULT_MAX_UPLOAD_BYTES
        if csvfile.size and csvfile.size > max_bytes:
            messages.error(request, f"File too large. Max allowed size is {max_bytes} bytes.")
            return redirect(request.path)

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

                    from django.contrib.auth import get_user_model
                    User = get_user_model()
                    try:
                        student = User.objects.get(username=student_username)
                    except User.DoesNotExist:
                        errors.append((line_no, f"Student '{student_username}' not found"))
                        continue

                    assessment_obj = None
                    if assessment_field.isdigit():
                        assessment_obj = Assessment.objects.filter(pk=int(assessment_field), course=course).first()
                    if assessment_obj is None:
                        assessment_obj = Assessment.objects.filter(course=course).first()  # fallback heuristic

                    if assessment_obj is None:
                        errors.append((line_no, f"Assessment '{assessment_field}' not found for course"))
                        continue

                    last_assessment = assessment_obj

                    lo_obj = LearningOutcome.objects.filter(code=lo_code).first()
                    if lo_obj is None:
                        errors.append((line_no, f"Learning outcome '{lo_code}' not found"))
                        continue
                    if not assessment_obj.learning_outcomes.filter(pk=lo_obj.pk).exists():
                        errors.append((line_no, f"LO '{lo_code}' is not linked to assessment '{assessment_obj.id}'."))
                        continue

                    try:
                        score_decimal = Decimal(score_str)
                        if score_decimal < 0 or score_decimal > 100:
                            raise ValueError("score out of range")
                        mastery_int = int(mastery_str)
                        if mastery_int < 1 or mastery_int > 5:
                            raise ValueError("mastery out of range")
                    except (ArithmeticError, ValueError) as parse_err:
                        errors.append((line_no, f"Invalid numeric value: {parse_err}"))
                        continue

                    obj, created = Grade.objects.update_or_create(
                        student=student,
                        assessment=assessment_obj,
                        learning_outcome=lo_obj,
                        defaults={'score_percentage': score_decimal, 'lo_mastery_score': mastery_int}
                    )

                    try:
                        obj._changed_by = request.user
                        obj.save(update_fields=['score_percentage', 'lo_mastery_score'])
                    except Exception:
                        errors.append((line_no, "Failed to save grade after update_or_create"))
                        continue

                    success_count += 1

        except DatabaseError as db_err:
            messages.error(request, f"Database error during upload: {db_err}")
            return redirect(request.path)

        if errors:
            for ln, err in errors[:20]:
                messages.error(request, f"Line {ln}: {err}")
            messages.info(request, f"Imported {success_count} rows (some rows had errors).")
        else:
            messages.success(request, f"Successfully imported {success_count} rows.")

        if last_assessment:
            return redirect(reverse('grades:teacher_grade_entry', args=[course_id]) + f'?assessment={last_assessment.id}')
        return redirect(reverse('grades:teacher_select_assessment', args=[course_id]))

    return render(request, 'grades/teacher/bulk_upload.html', {'course': course})
