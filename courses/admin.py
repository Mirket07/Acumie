from django.contrib import admin, messages
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.forms.models import BaseInlineFormSet
from django.urls import path, reverse
from django.shortcuts import render, redirect
from django.db import transaction
import csv, io

from .models import Course, Assessment, CourseSection, CourseMaterial, Enrollment, AssessmentLearningOutcome


class AssessmentInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        total = Decimal('0.00')
        found_any = False

        for form in self.forms:
            if not getattr(form, "cleaned_data", None):
                continue
            if form.cleaned_data.get('DELETE', False):
                continue

            weight = form.cleaned_data.get('weight_percentage')
            if weight is None:
                continue

            try:
                total += Decimal(str(weight))
            except Exception:
                continue
            found_any = True

        total = total.quantize(Decimal('0.01'))

        if found_any and total != Decimal('100.00'):
            raise ValidationError(
                f"Total weight of assessments for this course must be exactly 100.00%. "
                f"Current total in this formset: {total}%."
            )


class AssessmentInline(admin.StackedInline):
    model = Assessment
    formset = AssessmentInlineFormSet
    extra = 1
    fields = ('name', 'type', 'weight_percentage')  # do NOT include learning_outcomes here


class CourseMaterialInline(admin.TabularInline):
    model = CourseMaterial
    extra = 1


class EnrollmentInline(admin.TabularInline):
    model = Enrollment
    extra = 0
    raw_id_fields = ('student',)
    fields = ('student', 'enrolled_at',)
    readonly_fields = ('enrolled_at',)


class AssessmentLearningOutcomeInline(admin.TabularInline):
    model = AssessmentLearningOutcome
    extra = 0
    fields = ('learning_outcome', 'contribution_percentage')


@admin.register(CourseSection)
class CourseSectionAdmin(admin.ModelAdmin):
    list_display = ('course', 'title', 'order')
    inlines = [CourseMaterialInline]


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ('course', 'type', 'name', 'weight_percentage')
    list_filter = ('course', 'type')
    inlines = [AssessmentLearningOutcomeInline]
    # don't use filter_horizontal or inlines for learning_outcomes if the M2M uses a manual through model


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'enrolled_at')
    search_fields = ('student__username', 'student__first_name', 'student__last_name', 'course__code')
    list_filter = ('course',)
    raw_id_fields = ('student',)
    actions = ('remove_selected_enrollments',)

    def remove_selected_enrollments(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f"Deleted {count} enrollment(s).", level=messages.SUCCESS)
    remove_selected_enrollments.short_description = "Remove selected enrollments"

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('bulk-enroll/', self.admin_site.admin_view(self.bulk_enroll_view), name='courses_enrollment_bulk_enroll'),
        ]
        return my_urls + urls

    def bulk_enroll_view(self, request):
        if request.method == 'POST':
            csvfile = request.FILES.get('csv_file')
            if not csvfile:
                self.message_user(request, "No file uploaded.", level=messages.ERROR)
                return redirect(reverse('admin:courses_enrollment_changelist'))

            try:
                content = csvfile.read().decode('utf-8')
            except Exception:
                try:
                    content = csvfile.read().decode('latin-1')
                except Exception as e:
                    self.message_user(request, f"Could not decode file: {e}", level=messages.ERROR)
                    return redirect(reverse('admin:courses_enrollment_changelist'))

            reader = csv.DictReader(io.StringIO(content))
            created = 0
            errors = []
            from django.contrib.auth import get_user_model
            User = get_user_model()

            with transaction.atomic():
                for i, row in enumerate(reader, start=2):
                    username = (row.get('username') or row.get('student_username') or '').strip()
                    email = (row.get('email') or '').strip()
                    course_code = (row.get('course_code') or row.get('course') or '').strip()
                    if not (course_code and (username or email)):
                        errors.append(f"Line {i}: missing required columns (username/email and course_code).")
                        continue
                    try:
                        user_q = User.objects.filter(username=username) if username else User.objects.filter(email=email)
                        student = user_q.first()
                        if not student:
                            errors.append(f"Line {i}: student not found ({username or email}).")
                            continue
                        course = Course.objects.filter(code=course_code).first()
                        if not course:
                            errors.append(f"Line {i}: course not found ({course_code}).")
                            continue
                        Enrollment.objects.get_or_create(student=student, course=course)
                        created += 1
                    except Exception as e:
                        errors.append(f"Line {i}: unexpected error: {e}")
                        continue

            if created:
                self.message_user(request, f"Created/ensured {created} enrollment(s).", level=messages.SUCCESS)
            if errors:
                for e in errors[:20]:
                    self.message_user(request, e, level=messages.WARNING)
            return redirect(reverse('admin:courses_enrollment_changelist'))

        context = dict(
            self.admin_site.each_context(request),
            opts=self.model._meta,
        )
        return render(request, 'admin/courses/enrollment/bulk_enroll.html', context)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('code', 'title', 'ects_credit', 'instructor')
    search_fields = ('code', 'title')
    inlines = [AssessmentInline, EnrollmentInline]
