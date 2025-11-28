from django.contrib import admin
from .models import ProgramOutcome, LearningOutcome, LO_PO_Contribution
from django.forms.models import BaseInlineFormSet
from django.core.exceptions import ValidationError


class LOPOInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        total=0
        for form in self.forms:
            if not getattr(form,"cleaned_data",None):
                continue
            if form.cleaned_data.get("DELETE",False):
                continue
            val=form.cleaned_data.get("contribution_percentage")
            if val is None:
                continue
            try:
                total+=float(val)
            except (TypeError, ValueError):
                continue

        if total>100.0:
            raise ValidationError(
                f"Total LO → PO contribution cannot exceed 100% (current total: {total:.2f}%)."
            )

class LO_PO_ContributionInline(admin.TabularInline):
    model = LO_PO_Contribution
    formset = LOPOInlineFormSet
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