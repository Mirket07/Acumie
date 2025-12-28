import csv
import io
from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.forms import modelformset_factory
from django.db import transaction
from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponseForbidden
from feedback.models import FeedbackRequest
from .models import Grade
from courses.models import Course, Assessment, Enrollment

@login_required
def teacher_dashboard(request):
    user = request.user
    if not (user.is_staff or getattr(user, "role", "") == "INSTRUCTOR"):
        return HttpResponseForbidden("Access Denied")
    my_courses = Course.objects.all().order_by("code") if user.is_staff else Course.objects.filter(instructor=user).order_by("code")
    return render(request, "grades/teacher/dashboard.html", {"my_courses": my_courses, "total_courses": my_courses.count()})

@login_required
def teacher_select_assessment(request, course_id: int):
    course = get_object_or_404(Course, pk=course_id)
    assessments = course.assessments.all().order_by('type')
    return render(request, 'grades/teacher/select_assessment.html', {'course': course, 'assessments': assessments})

@login_required
def teacher_grade_entry(request, course_id: int):
    course = get_object_or_404(Course, pk=course_id)
    assessment_id = request.GET.get('assessment')
    if not assessment_id:
        return redirect(reverse('grades:teacher_select_assessment', args=[course_id]))
    assessment = get_object_or_404(Assessment, pk=assessment_id, course=course)
    students = [e.student for e in Enrollment.objects.filter(course=course).select_related('student')]
    with transaction.atomic():
        for s in students:
            Grade.objects.get_or_create(student=s, assessment=assessment, defaults={'score_percentage': Decimal('0.00')})
    qs = Grade.objects.filter(assessment=assessment, student__in=students).order_by('student__username')
    GradeFormSet = modelformset_factory(Grade, fields=('score_percentage',), extra=0)
    if request.method == 'POST':
        formset = GradeFormSet(request.POST, queryset=qs)
        if formset.is_valid():
            formset.save()
            messages.success(request, "Grades updated.")
            return redirect(f"{reverse('grades:teacher_grade_entry', args=[course_id])}?assessment={assessment.id}")
    else:
        formset = GradeFormSet(queryset=qs)
    return render(request, 'grades/teacher/grade_entry.html', {'course': course, 'assessment': assessment, 'formset': formset})

@login_required
def teacher_grade_bulk_upload(request, course_id: int):
    course = get_object_or_404(Course, pk=course_id)
    if request.method == 'POST':
        csv_file = request.FILES.get('csv_file')
        if csv_file:
            try:
                data = csv_file.read().decode('utf-8')
                reader = csv.DictReader(io.StringIO(data))
                with transaction.atomic():
                    for row in reader:
                        from django.contrib.auth import get_user_model
                        student = get_user_model().objects.get(username=row['username'])
                        assessment = Assessment.objects.get(pk=row['assessment_id'], course=course)
                        Grade.objects.update_or_create(student=student, assessment=assessment, defaults={'score_percentage': Decimal(row['score'])})
                messages.success(request, "Bulk upload successful.")
            except Exception as e:
                messages.error(request, f"Error: {e}")
    return render(request, 'grades/teacher/bulk_upload.html', {'course': course})