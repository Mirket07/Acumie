from django import forms
from .models import Feedback

class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['course', 'feedback_text']
        widgets = {
            'feedback_text': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Enter your anonymous feedback here...'}),
            'course': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'course': 'Select Course (Optional)',
            'feedback_text': 'Your Feedback',
        }