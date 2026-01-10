from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponseForbidden
from django.contrib import messages
from django.urls import reverse
from .forms import (
    CourseForm, AssessmentFormSet, AssessmentLearningOutcomeFormSet, 
    LearningOutcomeFormSet, CourseSectionFormSet, CourseMaterialForm
)
from .models import Course, CourseSection
from outcomes.models import LearningOutcome
from grades.models import Grade

@login_required
def course_detail_view(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    sections = course.sections.prefetch_related('materials').all()
    learning_outcomes = LearningOutcome.objects.filter(course=course).order_by('code')
    is_instructor = (request.user.is_staff or course.instructor == request.user)
    
    if is_instructor:
        student_grades = Grade.objects.filter(assessment__course=course).select_related('assessment', 'student')
    else:
        student_grades = Grade.objects.filter(student=request.user, assessment__course=course).select_related('assessment')

    return render(request, 'courses/course_detail.html', {
        'course': course, 'sections': sections, 'learning_outcomes': learning_outcomes,
        'student_grades': student_grades, 'is_instructor': is_instructor, 'participants': course.enrollments.all(),
    })

@login_required
def teacher_course_edit(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    if not (request.user.is_staff or course.instructor == request.user): return HttpResponseForbidden()
    
    if request.method == "POST":
        form = CourseForm(request.POST, instance=course)
        formset = AssessmentFormSet(request.POST, instance=course, prefix='assessments')
        lo_formset = LearningOutcomeFormSet(request.POST, instance=course, prefix='outcomes')
        
        if form.is_valid() and formset.is_valid() and lo_formset.is_valid():
            with transaction.atomic():
                form.save()
                lo_formset.save()
                assessments = formset.save()

                for i, a_form in enumerate(formset.forms):
                    if a_form.instance.pk and not a_form.cleaned_data.get('DELETE'):
                        alo_fs = AssessmentLearningOutcomeFormSet(
                            request.POST, 
                            instance=a_form.instance, 
                            prefix=f'alo-{i}' 
                        )
                        if alo_fs.is_valid():
                            alo_fs.save()
                            
                messages.success(request, "Saved successfully.")
                return redirect("grades:teacher_dashboard")
    else:
        form = CourseForm(instance=course)
        formset = AssessmentFormSet(instance=course, prefix='assessments')
        lo_formset = LearningOutcomeFormSet(instance=course, prefix='outcomes')

    rows = []
    for i, f in enumerate(formset.forms):
        instance = f.instance if f.instance.pk else None
        alo_fs = AssessmentLearningOutcomeFormSet(instance=instance, prefix=f'alo-{i}')
        rows.append({'form': f, 'alo_fs': alo_fs})

    return render(request, "courses/teacher/course_form.html", {
        "form": form, 
        "formset": formset, 
        "lo_formset": lo_formset, 
        "assessment_rows": rows, 
        "is_create": False, 
        "course": course
    })

@login_required
def teacher_course_create(request):
    if not (request.user.is_staff or getattr(request.user, "role", "") == "INSTRUCTOR"): return HttpResponseForbidden()
    
    if request.method == "POST":
        form = CourseForm(request.POST)
        formset = AssessmentFormSet(request.POST, prefix='assessments')
        lo_formset = LearningOutcomeFormSet(request.POST, prefix='outcomes')
        
        if form.is_valid() and formset.is_valid() and lo_formset.is_valid():
            with transaction.atomic():
                course = form.save(commit=False)
                course.instructor = request.user
                course.save()
                
                lo_formset.instance = course
                lo_formset.save()
                
                formset.instance = course
                formset.save()
                return redirect("courses:teacher_course_edit", course_id=course.id)
    else:
        form = CourseForm(initial={'instructor': request.user})
        formset = AssessmentFormSet(prefix='assessments')
        lo_formset = LearningOutcomeFormSet(prefix='outcomes')

    rows = [{'form': f, 'alo_fs': None} for f in formset.forms]
    
    return render(request, "courses/teacher/course_form.html", {
        "form": form, 
        "formset": formset, 
        "lo_formset": lo_formset, 
        "assessment_rows": rows, 
        "is_create": True
    })

@login_required
def teacher_manage_content(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    if request.method == "POST":
        formset = CourseSectionFormSet(request.POST, instance=course)
        if formset.is_valid(): formset.save(); return redirect(reverse('courses:teacher_manage_content', args=[course.id]))
    else: formset = CourseSectionFormSet(instance=course)
    return render(request, "courses/teacher/add_material.html", {"course": course, "formset": formset})

@login_required
def add_course_material(request, section_id):
    section = get_object_or_404(CourseSection, id=section_id)
    if request.method == "POST":
        form = CourseMaterialForm(request.POST, request.FILES)
        if form.is_valid():
            material = form.save(commit=False); material.section = section; material.save()
            return redirect("courses:detail", section.course.id)
    else: form = CourseMaterialForm()
    return render(request, "courses/teacher/material_form.html", {"form": form, "section": section})