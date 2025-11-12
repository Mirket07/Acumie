from django.shortcuts import render, redirect
from django.urls import reverse
from .forms import FeedbackForm

def feedback_submit_view(request):
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(reverse('feedback:thank_you'))
    else:
        form = FeedbackForm()

    context = {
        'form': form,
        'page_title': 'Whisper Box: Anonymous Feedback'
    }
    return render(request, 'feedback/submit_feedback.html', context)

def feedback_thank_you_view(request):
    return render(request, 'feedback/thank_you.html', {'page_title': 'Thank You'})
