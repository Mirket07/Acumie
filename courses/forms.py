from django import forms
from decimal import Decimal
from django.forms.models import inlineformset_factory, BaseInlineFormSet
from .models import Course, Assessment
from .models import AssessmentLearningOutcome

DECIMAL_100 = Decimal("100.00")
DECIMAL_ZERO = Decimal("0.00")

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ("code", "title", "ects_credit", "instructor")
        widgets = {
            "instructor": forms.HiddenInput(),
        }

class AssessmentForm(forms.ModelForm):
    class Meta:
        model = Assessment
        fields = ("type", "weight_percentage", "name")
        widgets = {}

class AssessmentLearningOutcomeForm(forms.ModelForm):
    class Meta:
        model = AssessmentLearningOutcome
        fields = ("learning_outcome", "contribution_percentage")
        widgets = {
            'contribution_percentage': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'max': '100'})
        }

AssessmentLearningOutcomeFormSet = inlineformset_factory(
    Assessment,
    AssessmentLearningOutcome,
    form=AssessmentLearningOutcomeForm,
    extra=1,
    can_delete=True,
)

class AssessmentInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        total = Decimal("0.00")
        seen = False
        for form in self.forms:
            if getattr(form, "cleaned_data", None) is None:
                continue
            if form.cleaned_data.get("DELETE", False):
                continue
            weight = form.cleaned_data.get("weight_percentage")
            if weight in (None, ""):
                continue
            try:
                w = Decimal(str(weight))
            except Exception:
                raise forms.ValidationError("Invalid weight percentage value.")
            total += w
            seen = True

        if not seen:
            raise forms.ValidationError("You must define at least one assessment and the total weight must be 100%.")
        total = total.quantize(Decimal("0.01"))
        if total != DECIMAL_100:
            raise forms.ValidationError(f"Total weight of assessments must equal {DECIMAL_100}%. Current total: {total}%.")

AssessmentFormSet = inlineformset_factory(
    Course,
    Assessment,
    form=AssessmentForm,
    formset=AssessmentInlineFormSet,
    extra=1,
    can_delete=True,
)
