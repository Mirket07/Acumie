from django.contrib import admin
from .models import Grade


class CourseFilter(admin.SimpleListFilter):
    """
    Grade modelini, ait olduğu Ders'e göre filtrelemek için özel filtre.
    """
    title = 'Course'
    parameter_name = 'course'

    def lookups(self, request, model_admin):
        from courses.models import Course
        courses = Course.objects.all().order_by('code')
        return [(c.id, c.code) for c in courses]

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.filter(assessment__course__id=value)
        return queryset



@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = (
        'student_username', 
        'course_code', 
        'assessment_type', 
        'lo_code', 
        'score_percentage', 
        'lo_mastery_score'
    )
    
    list_filter = (
        CourseFilter, 
        'assessment__type', 
        'learning_outcome__code',
    )
    
    
    search_fields = (
        'student__username', 
        'student__first_name', 
        'student__last_name', 
        'assessment__course__code',
        'learning_outcome__code',
    )
    
    fieldsets = (
        (None, {'fields': ('student', 'assessment', 'learning_outcome')}),
        ('Scores', {'fields': ('score_percentage', 'lo_mastery_score')}),
    )

    raw_id_fields = ('student', 'assessment', 'learning_outcome')
    list_per_page = 50
    ordering = ('student__username',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('student', 'assessment__course', 'learning_outcome')

    @admin.display(description='Student')
    def student_username(self, obj):
        return getattr(obj.student, 'username', str(obj.student))

    @admin.display(description='Course Code')
    def course_code(self, obj):
        course=getattr(obj.assessment, 'course', None)
        return getattr(course, 'code', 'N/A')

    @admin.display(description='Assessment Type')
    def assessment_type(self, obj):
        return obj.assessment.get_type_display() if obj.assessment else ''

    @admin.display(description='LO Code')
    def lo_code(self, obj):
        return getattr(obj.learning_outcome, 'code', 'N/A')