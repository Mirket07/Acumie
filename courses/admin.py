from django.contrib import admin
from .models import Course, Assessment, CourseSection, CourseMaterial

class AssessmentInline(admin.StackedInline):
    model = Assessment
    extra = 1
    filter_horizontal = ('learning_outcomes',) 
    fields = ('type', 'weight_percentage', 'learning_outcomes',)

class CourseMaterialInline(admin.TabularInline):
    model = CourseMaterial
    extra = 1

@admin.register(CourseSection)
class CourseSectionAdmin(admin.ModelAdmin):
    list_display = ('course', 'title', 'order')
    inlines = [CourseMaterialInline]

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