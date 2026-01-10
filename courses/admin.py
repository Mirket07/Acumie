from django.contrib import admin
from .models import Course, Enrollment, Assessment, AssessmentLearningOutcome, CourseSection, CourseMaterial

class EnrollmentInline(admin.TabularInline):
    model = Enrollment
    extra = 1
    readonly_fields = ('date_enrolled',) 

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'date_enrolled')
    list_filter = ('course', 'date_enrolled')

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('code', 'title', 'instructor', 'ects_credit')
    search_fields = ('code', 'title')
    inlines = [EnrollmentInline]

admin.site.register(Assessment)
admin.site.register(AssessmentLearningOutcome)
admin.site.register(CourseSection)
admin.site.register(CourseMaterial)