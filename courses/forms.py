from django import forms
from decimal import Decimal
from django.forms.models import inlineformset_factory, BaseInlineFormSet
from .models import Course, Assessment, AssessmentLearningOutcome, CourseSection, CourseMaterial
from outcomes.models import LearningOutcome

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ("code", "title", "ects_credit", "instructor")
        widgets = {"instructor": forms.HiddenInput()}

class AssessmentForm(forms.ModelForm):
    class Meta:
        model = Assessment
        fields = ("type", "weight_percentage")

class AssessmentLearningOutcomeForm(forms.ModelForm):
    class Meta:
        model = AssessmentLearningOutcome
        fields = ("learning_outcome", "contribution_percentage")
        widgets = {
            'learning_outcome': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'contribution_percentage': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01'})
        }

AssessmentLearningOutcomeFormSet = inlineformset_factory(
    Assessment, AssessmentLearningOutcome, form=AssessmentLearningOutcomeForm, extra=1, can_delete=True
)

class AssessmentInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        total = Decimal("0.00")
        has_forms = False
        for form in self.forms:
            if getattr(form, "cleaned_data", None) and not form.cleaned_data.get("DELETE"):
                total += Decimal(str(form.cleaned_data.get("weight_percentage", 0)))
                has_forms = True
        if has_forms and total.quantize(Decimal("0.01")) != Decimal("100.00"):
            raise forms.ValidationError(f"Total weight must be 100%. Current: {total}%")

AssessmentFormSet = inlineformset_factory(Course, Assessment, form=AssessmentForm, formset=AssessmentInlineFormSet, extra=1, can_delete=True)
LearningOutcomeFormSet = inlineformset_factory(Course, LearningOutcome, fields=('title',), extra=1, can_delete=True)
CourseSectionFormSet = inlineformset_factory(Course, CourseSection, fields=('title', 'order'), extra=1, can_delete=True)

class CourseMaterialForm(forms.ModelForm):
    class Meta:
        model = CourseMaterial
        fields = ['title', 'type', 'file', 'link']
    
    def clean(self):
        cleaned_data = super().clean()
        m_type = cleaned_data.get("type")
        if m_type == 'SLIDE' and not cleaned_data.get("file"):
            self.add_error('file', "File is required for Slide type.")
        if m_type == 'LINK' and not cleaned_data.get("link"):
            self.add_error('link', "URL is required for Link type.")
        return cleaned_data