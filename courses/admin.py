from django.contrib import admin
from .models import Course, Assessment

class AssessmentInline(admin.TabularInline):
    model = Assessment
    extra = 1
    filter_horizontal = ('learning_outcomes',)
    fields = ('type', 'weight_percentage', 'learning_outcomes',)

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('code', 'title', 'ects_credit')
    search_fields = ('code', 'title')
    inlines = [AssessmentInline]

@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ('course', 'type', 'weight_percentage')
    list_filter = ('course', 'type')
    filter_horizontal = ('learning_outcomes',)
