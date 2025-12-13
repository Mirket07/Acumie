from django.contrib import admin
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.forms.models import BaseInlineFormSet
from .models import Course, Assessment, CourseSection, CourseMaterial


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