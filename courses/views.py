from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import FieldDoesNotExist
from django.shortcuts import redirect
from django.db import transaction
from django.http import HttpResponseForbidden
from .forms import CourseForm, AssessmentFormSet, AssessmentLearningOutcomeFormSet
from .models import Course
from grades.models import Grade
from feedback.models import FeedbackRequest
from outcomes.models import LearningOutcome

@login_required
def course_detail_view(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    sections = course.sections.prefetch_related('materials').all()
    
    participants = course.enrollments.select_related('student').all()

    learning_outcomes = (
        LearningOutcome.objects
        .filter(assessments__course=course)
        .distinct()
        .order_by('code')
    )

    requested_assessment_ids = []
    teacher_feedback_requests = []
    student_grades = []

    user = request.user

    try:
        Grade._meta.get_field('learning_outcome')
        has_learning_outcome = True
    except FieldDoesNotExist:
        has_learning_outcome = False

    if getattr(user, "role", "") == 'STUDENT':
        qs = Grade.objects.filter(
            student=user,
            assessment__course=course
        ).select_related('assessment', 'student')

        if has_learning_outcome:
            qs = qs.prefetch_related('learning_outcome').order_by('assessment__type', 'learning_outcome__code')
        else:
            qs = qs.order_by('assessment__type')

        student_grades = qs

        requested_assessment_ids = list(
            FeedbackRequest.objects
            .filter(student=user, assessment__course=course)
            .values_list('assessment_id', flat=True)
            .distinct()
        )
        is_instructor = False

    elif getattr(user, "role", "") == 'INSTRUCTOR' or user.is_staff:
        qs = Grade.objects.filter(assessment__course=course).select_related('assessment', 'student')

        if has_learning_outcome:
            qs = qs.prefetch_related('learning_outcome').order_by('student__first_name', 'assessment__type', 'learning_outcome__code')
        else:
            qs = qs.order_by('student__first_name', 'assessment__type')

        student_grades = qs
        is_instructor = True

        teacher_feedback_requests = (
            FeedbackRequest.objects
            .select_related('student', 'assessment', 'assessment__course')
            .filter(assessment__course=course, is_resolved=False)
            .order_by('-request_date')
        )
    else:
        student_grades = []
        is_instructor = False


    context = {
        'course': course,
        'sections': sections,
        'student_grades': student_grades,
        'is_instructor': is_instructor,
        'requested_assessment_ids': requested_assessment_ids,
        'learning_outcomes': learning_outcomes,
        'participants': participants, 
        'teacher_feedback_requests': teacher_feedback_requests, 
    }

    return render(request, 'courses/course_detail.html', context)


@login_required
def teacher_course_create(request):
    user = request.user
    if not (user.is_staff or getattr(user, "role", "") == "INSTRUCTOR"):
        return HttpResponseForbidden("You are not allowed to create courses.")

    if request.method == "POST":
        form = CourseForm(request.POST)
        formset = AssessmentFormSet(request.POST)
        assessment_rows = []
        if form.is_valid() and formset.is_valid():
            # Build and validate ALO formsets for each assessment form index
            valid = True
            for i, aform in enumerate(formset.forms):
                prefix = f'assessmentlearningoutcome-{i}'
                alo_fs = AssessmentLearningOutcomeFormSet(request.POST, prefix=prefix)
                assessment_rows.append({'form': aform, 'alo_fs': alo_fs})
                if not alo_fs.is_valid():
                    valid = False
            if valid:
                try:
                    with transaction.atomic():
                        course = form.save(commit=False)
                        if not user.is_staff:
                            course.instructor = user
                        else:
                            if not course.instructor:
                                course.instructor = user
                        course.save()
                        formset.instance = course
                        assessments = formset.save()
                        # Save ALOs; map created assessments by order
                        for idx, row in enumerate(assessment_rows):
                            aform = row['form']
                            alo_fs = row['alo_fs']
                            assessment_instance = aform.instance if (aform.instance and aform.instance.pk) else (assessments[idx] if idx < len(assessments) else None)
                            if assessment_instance:
                                alo_fs.instance = assessment_instance
                                alo_fs.save()
                        return redirect("grades:teacher_dashboard")
                except Exception as e:
                    form.add_error(None, f"Error saving course: {e}")
    else:
        form = CourseForm()
        formset = AssessmentFormSet()
        assessment_rows = []
        for i, aform in enumerate(formset.forms):
            prefix = f'assessmentlearningoutcome-{i}'
            assessment_rows.append({'form': aform, 'alo_fs': AssessmentLearningOutcomeFormSet(prefix=prefix)})

    return render(request, "courses/teacher/course_form.html", {
        "form": form,
        "formset": formset,
        "assessment_rows": assessment_rows,
        "is_create": True,
    })


@login_required
def teacher_course_edit(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    user = request.user
    if not (user.is_staff or (course.instructor and course.instructor.id == user.id) or getattr(user, "role", "") == "INSTRUCTOR" and course.instructor is None):
        return HttpResponseForbidden("You are not allowed to edit this course.")

    if request.method == "POST":
        form = CourseForm(request.POST, instance=course)
        formset = AssessmentFormSet(request.POST, instance=course)
        assessment_rows = []
        if form.is_valid() and formset.is_valid():
            valid = True
            for i, aform in enumerate(formset.forms):
                prefix = f'assessmentlearningoutcome-{i}'
                obj_pk = aform.instance.pk if aform.instance and aform.instance.pk else None
                alo_fs = AssessmentLearningOutcomeFormSet(request.POST, instance=(aform.instance if obj_pk else None), prefix=prefix)
                assessment_rows.append({'form': aform, 'alo_fs': alo_fs})
                if not alo_fs.is_valid():
                    valid = False
            if valid:
                try:
                    with transaction.atomic():
                        course = form.save(commit=False)
                        if not user.is_staff:
                            course.instructor = user
                        course.save()
                        formset.instance = course
                        assessments = formset.save()
                        for idx, row in enumerate(assessment_rows):
                            aform = row['form']
                            alo_fs = row['alo_fs']
                            assessment_instance = aform.instance if (aform.instance and aform.instance.pk) else (assessments[idx] if idx < len(assessments) else None)
                            if assessment_instance:
                                alo_fs.instance = assessment_instance
                                alo_fs.save()
                        return redirect("grades:teacher_dashboard")
                except Exception as e:
                    form.add_error(None, f"Error saving course: {e}")
    else:
        form = CourseForm(instance=course)
        formset = AssessmentFormSet(instance=course)
        assessment_rows = []
        for i, aform in enumerate(formset.forms):
            prefix = f'assessmentlearningoutcome-{i}'
            if aform.instance and aform.instance.pk:
                assessment_rows.append({'form': aform, 'alo_fs': AssessmentLearningOutcomeFormSet(instance=aform.instance, prefix=prefix)})
            else:
                assessment_rows.append({'form': aform, 'alo_fs': AssessmentLearningOutcomeFormSet(prefix=prefix)})

    return render(request, "courses/teacher/course_form.html", {
        "form": form,
        "formset": formset,
        "assessment_rows": assessment_rows,
        "is_create": False,
        "course": course,
    })


# Removed teacher_add_material and teacher_upload_material per user request
