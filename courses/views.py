from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponseForbidden
from django.contrib import messages
from .forms import CourseForm, AssessmentFormSet, AssessmentLearningOutcomeFormSet, LearningOutcomeFormSet
from .models import Course
from grades.models import Grade
from outcomes.models import LearningOutcome

@login_required
def course_detail_view(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    return render(request, 'courses/course_detail.html', {
        'course': course,
        'sections': course.sections.all(),
        'participants': course.enrollments.all(),
        'learning_outcomes': LearningOutcome.objects.filter(course=course).order_by('code'),
        'student_grades': Grade.objects.filter(assessment__course=course),
        'is_instructor': (request.user.is_staff or course.instructor == request.user)
    })

@login_required
def teacher_course_create(request):
    if not (request.user.is_staff or getattr(request.user, "role", "") == "INSTRUCTOR"): return HttpResponseForbidden()
    if request.method == "POST":
        form = CourseForm(request.POST)
        formset = AssessmentFormSet(request.POST)
        lo_formset = LearningOutcomeFormSet(request.POST)
        if form.is_valid() and formset.is_valid() and lo_formset.is_valid():
            try:
                with transaction.atomic():
                    course = form.save(commit=False); course.instructor = request.user; course.save()
                    lo_formset.instance = course; lo_formset.save()
                    formset.instance = course; formset.save()
                    for i, a_form in enumerate(formset.forms):
                        if a_form.instance.pk and not a_form.cleaned_data.get('DELETE'):
                            alo_fs = AssessmentLearningOutcomeFormSet(request.POST, instance=a_form.instance, prefix=f'assessmentlearningoutcome-{i}')
                            if alo_fs.is_valid(): alo_fs.save()
                    messages.success(request, "Course created successfully.")
                    return redirect("grades:teacher_dashboard")
            except Exception as e: messages.error(request, f"Error: {e}")
    else:
        form = CourseForm(initial={'instructor': request.user}); formset = AssessmentFormSet(); lo_formset = LearningOutcomeFormSet()
    rows = [{'form': f, 'alo_fs': AssessmentLearningOutcomeFormSet(prefix=f'assessmentlearningoutcome-{i}')} for i, f in enumerate(formset.forms)]
    return render(request, "courses/teacher/course_form.html", {"form": form, "formset": formset, "lo_formset": lo_formset, "assessment_rows": rows, "is_create": True})

@login_required
def teacher_course_edit(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    if not (request.user.is_staff or course.instructor == request.user): return HttpResponseForbidden()
    if request.method == "POST":
        form = CourseForm(request.POST, instance=course); formset = AssessmentFormSet(request.POST, instance=course); lo_formset = LearningOutcomeFormSet(request.POST, instance=course)
        if form.is_valid() and formset.is_valid() and lo_formset.is_valid():
            try:
                with transaction.atomic():
                    form.save(); lo_formset.save(); formset.save()
                    for i, a_form in enumerate(formset.forms):
                        if a_form.instance.pk:
                            alo_fs = AssessmentLearningOutcomeFormSet(request.POST, instance=a_form.instance, prefix=f'assessmentlearningoutcome-{i}')
                            if alo_fs.is_valid(): alo_fs.save()
                    messages.success(request, "Course updated.")
                    return redirect("grades:teacher_dashboard")
            except Exception as e: messages.error(request, f"Error: {e}")
    else:
        form = CourseForm(instance=course); formset = AssessmentFormSet(instance=course); lo_formset = LearningOutcomeFormSet(instance=course)
    rows = [{'form': f, 'alo_fs': AssessmentLearningOutcomeFormSet(instance=f.instance if f.instance.pk else None, prefix=f'assessmentlearningoutcome-{i}')} for i, f in enumerate(formset.forms)]
    return render(request, "courses/teacher/course_form.html", {"form": form, "formset": formset, "lo_formset": lo_formset, "assessment_rows": rows, "is_create": False, "course": course})