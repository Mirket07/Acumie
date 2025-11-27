from django.forms import ModelForm
from django.forms.models import modelformset_factory
from .models import Grade

class GradeForm(ModelForm):
    class Meta:
        model = Grade
        fields = ('student', 'assessment', 'learning_outcome', 'score_percentage', 'lo_mastery_score')

GradeFormSet = modelformset_factory(Grade, form=GradeForm, extra=0)
