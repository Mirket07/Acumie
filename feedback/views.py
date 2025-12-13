from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
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

# --- GÜNCELLENEN KISIM BURASI ---
@login_required
def request_feedback(request, assessment_id):
    # Sadece öğrenci kontrolü
    if request.user.role != 'STUDENT':
        return JsonResponse({'status': 'error', 'message': "Only students can request feedback."}, status=403)

    assessment = get_object_or_404(Assessment, id=assessment_id)
    
    # Kayıt oluşturma (get_or_create zaten varsa oluşturmaz)
    obj, created = FeedbackRequest.objects.get_or_create(
        student=request.user, 
        assessment=assessment
    )
    
    if created:
        return JsonResponse({
            'status': 'success', 
            'message': f"Request sent for {assessment.get_type_display()}!"
        })
    else:
        return JsonResponse({
            'status': 'warning', 
            'message': "You have already requested feedback for this assessment."
        })