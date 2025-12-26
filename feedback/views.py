from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Count, Prefetch
from .models import Feedback, FeedbackLike, FeedbackComment, FeedbackRequest
from .forms import FeedbackForm, CommentForm
from courses.models import Assessment

@login_required
def feedback_feed_view(request):
    if request.method == 'POST' and 'submit_feedback' in request.POST:
        form = FeedbackForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('feedback:feed')
    else:
        form = FeedbackForm()

    feedbacks = Feedback.objects.select_related('course').prefetch_related(
        'comments'
    ).order_by('-created_at')

    user_likes = set(FeedbackLike.objects.filter(user=request.user).values_list('feedback_id', flat=True))

    context = {
        'form': form,
        'comment_form': CommentForm(),
        'feedbacks': feedbacks,
        'user_likes': user_likes,
        'page_title': 'Whisper Box Feed'
    }
    return render(request, 'feedback/feed.html', context)

@login_required
def toggle_like(request, feedback_id):
    if request.method == 'POST':
        feedback = get_object_or_404(Feedback, id=feedback_id)
        like_obj, created = FeedbackLike.objects.get_or_create(user=request.user, feedback=feedback)
        
        if not created:
            like_obj.delete()
            liked = False
            feedback.likes_count = max(0, feedback.likes_count - 1)
        else:
            liked = True
            feedback.likes_count += 1
        
        feedback.save()
        
        return JsonResponse({'status': 'success', 'liked': liked, 'likes_count': feedback.likes_count})
    
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def add_comment(request, feedback_id):
    if request.method == 'POST':
        feedback = get_object_or_404(Feedback, id=feedback_id)
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.feedback = feedback
            comment.user = request.user
            comment.save()
    return redirect('feedback:feed')

@login_required
def request_feedback(request, assessment_id):
    if request.user.role != 'STUDENT':
        return JsonResponse({'status': 'error', 'message': "Only students can request feedback."}, status=403)

    assessment = get_object_or_404(Assessment, id=assessment_id)
    obj, created = FeedbackRequest.objects.get_or_create(student=request.user, assessment=assessment)
    
    if created:
        return JsonResponse({'status': 'success', 'message': f"Request sent for {assessment.get_type_display()}!"})
    else:
        return JsonResponse({'status': 'warning', 'message': "You have already requested feedback."})