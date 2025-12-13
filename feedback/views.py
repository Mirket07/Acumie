from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import FeedbackForm
from .models import FeedbackRequest
from courses.models import Assessment

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

@login_required
def request_feedback(request, assessment_id):
    if request.user.role != 'STUDENT':
        messages.error(request, "Only students can request feedback.")
        return redirect('grades:dashboard')

    assessment = get_object_or_404(Assessment, id=assessment_id)
    
    existing_request = FeedbackRequest.objects.filter(
        student=request.user, 
        assessment=assessment
    ).exists()
    
    if existing_request:
        messages.warning(request, "You have already requested feedback for this assessment.")
    else:
        FeedbackRequest.objects.create(student=request.user, assessment=assessment)
        messages.success(request, f"Feedback requested for {assessment.type} successfully!")
    
    return redirect('courses:detail', course_id=assessment.course.id)