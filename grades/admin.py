from django.contrib import admin
from .models import Grade
from courses.models import Course

class CourseFilter(admin.SimpleListFilter):
    title = 'Course'
    parameter_name = 'course'

    def lookups(self, request, model_admin):
        courses = Course.objects.all()
        return [(c.id, c.code) for c in courses]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(assessment__course__id=self.value())

@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = (
        'student_username', 
        'course_code', 
        'assessment_type', 
        'score_percentage'
    )
    
    list_filter = (
        CourseFilter,
        'assessment__type', 
    )
    
    search_fields = (
        'student__username', 
        'student__first_name', 
        'student__last_name', 
        'assessment__course__code',
    )
    
    fieldsets = (
        (None, {'fields': ('student', 'assessment', 'score_percentage')}),
    )

    @admin.display(description='Student')
    def student_username(self, obj):
        return obj.student.username

    @admin.display(description='Course Code')
    def course_code(self, obj):
        return obj.assessment.course.code

    @admin.display(description='Assessment Type')
    def assessment_type(self, obj):
        return obj.assessment.get_type_display()