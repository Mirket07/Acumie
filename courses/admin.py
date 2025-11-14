from django.contrib import admin
from .models import Course, Assessment
from django.forms.models import BaseInlineFormSet
from django.core.exceptions import ValidationError

class AssessmentInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        total=0
        for form in self.forms:
            if not getattr(form,"cleaned_data",None):
                continue
            if form.cleaned_data.get("DELETE",False):
                continue
            weight_percentage = form.cleaned_data.get("weight_percentage")
            if weight_percentage is None:
                continue
            try:
                total +=float(weight_percentage)
            except (TypeError, ValueError):
                continue

        if total >100.0:
            raise ValidationError(
                "Total weight of assessments for this course cannot exceed 100% "
                f"(current total in formset: {total:.2f}%)."
            )

class AssessmentInline(admin.TabularInline):
    model = Assessment
    formset = AssessmentInlineFormSet
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
