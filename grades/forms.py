from django import forms
from django.forms import ModelForm
from .models import Grade

class GradeForm(ModelForm):
    class Meta:
        model = Grade
        fields = ['student', 'assessment', 'score_percentage']
        widgets = {
            'score_percentage': forms.NumberInput(attrs={'step': '0.01'}),
        }

GradeFormSet = forms.modelformset_factory(
    Grade,
    form=GradeForm,
    extra=1,
    can_delete=True
)