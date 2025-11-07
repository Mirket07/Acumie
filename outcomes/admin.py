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