from django import forms
from .models import Feedback, FeedbackComment

class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['course', 'feedback_text']
        widgets = {
            'feedback_text': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Share your thoughts anonymously...', 'class': 'form-control'}),
            'course': forms.Select(attrs={'class': 'form-select'}),
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = FeedbackComment
        fields = ['comment_text']
        widgets = {
            'comment_text': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Reply anonymously...', 'class': 'form-control'}),
        }