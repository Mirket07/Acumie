from django.contrib import admin
from .models import ProgramOutcome, LearningOutcome, LO_PO_Contribution

class LO_PO_ContributionInline(admin.TabularInline):
    model = LO_PO_Contribution
    extra = 1 
    fields = ('program_outcome', 'contribution_percentage',)


@admin.register(LearningOutcome)
class LearningOutcomeAdmin(admin.ModelAdmin):
    list_display = ('code', 'title')
    search_fields = ('code', 'title')
    inlines = [LO_PO_ContributionInline]


@admin.register(ProgramOutcome)
class ProgramOutcomeAdmin(admin.ModelAdmin):
    list_display = ('code', 'title')
    search_fields = ('code', 'title')


from django.contrib import admin
from .models import StudentGoal, GoalLearningOutcome, LearningOutcome 
from accounts.models import UserRole 

class GoalLearningOutcomeInline(admin.TabularInline):
    model = GoalLearningOutcome
    extra = 1
    fields = ('learning_outcome', 'weight_in_goal',)


@admin.register(StudentGoal)
class StudentGoalAdmin(admin.ModelAdmin):
    list_display = (
        'student', 
        'goal_description', 
        'target_date', 
        'completion_percentage', 
        'is_completed'
    )
    list_filter = ('is_completed', 'target_date')
    search_fields = ('student__username', 'goal_description')
    

    inlines = [GoalLearningOutcomeInline]
    raw_id_fields = ('student',) 
