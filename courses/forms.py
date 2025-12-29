from django import forms
from decimal import Decimal
from django.forms.models import inlineformset_factory, BaseInlineFormSet
from .models import Course, Assessment, AssessmentLearningOutcome
from outcomes.models import LearningOutcome

DECIMAL_100 = Decimal("100.00")

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
    learning_outcome = forms.ModelChoiceField(
        queryset=LearningOutcome.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    class Meta:
        model = AssessmentLearningOutcome
        fields = ("learning_outcome", "contribution_percentage")
        widgets = {
            'contribution_percentage': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01', 'min': '0', 'max': '100'})
        }

AssessmentLearningOutcomeFormSet = inlineformset_factory(
    Assessment, AssessmentLearningOutcome, form=AssessmentLearningOutcomeForm, extra=1, can_delete=True
)

class AssessmentInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        total = Decimal("0.00")
        has_assessments = False
        for form in self.forms:
            if getattr(form, "cleaned_data", None) is None or form.cleaned_data.get("DELETE", False): continue
            weight = form.cleaned_data.get("weight_percentage")
            if weight is not None:
                total += Decimal(str(weight))
                has_assessments = True
        if has_assessments and total.quantize(Decimal("0.01")) != DECIMAL_100:
            raise forms.ValidationError(f"Total weight must be 100%. Current: {total}%")

AssessmentFormSet = inlineformset_factory(
    Course, Assessment, form=AssessmentForm, formset=AssessmentInlineFormSet, extra=1, can_delete=True
)

class LearningOutcomeForm(forms.ModelForm):
    class Meta:
        model = LearningOutcome
        fields = ('title',)
        widgets = {'title': forms.TextInput(attrs={'class': 'form-control w-100'})}

LearningOutcomeFormSet = inlineformset_factory(
    Course, LearningOutcome, form=LearningOutcomeForm, extra=1, can_delete=True
)