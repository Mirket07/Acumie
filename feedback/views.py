from typing import Set

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseNotAllowed, HttpResponseForbidden
from django.db import transaction
from django.db.models import F

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

    feedbacks = (
        Feedback.objects
        .select_related('course')
        .prefetch_related('comments')
        .order_by('-created_at')
    )

    user_likes: Set[int] = set(
        FeedbackLike.objects.filter(user=request.user).values_list('feedback_id', flat=True)
    )

    context = {
        'form': form,
        'comment_form': CommentForm(),
        'feedbacks': feedbacks,
        'user_likes': user_likes,
        'page_title': 'Whisper Box Feed',
    }
    return render(request, 'feedback/feed.html', context)


@login_required
def toggle_like(request, feedback_id):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    feedback = get_object_or_404(Feedback, id=feedback_id)

    with transaction.atomic():
        like_obj, created = FeedbackLike.objects.select_for_update().get_or_create(
            user=request.user, feedback=feedback
        )

        if not created:
            like_obj.delete()
            Feedback.objects.filter(pk=feedback.pk).update(likes_count=F('likes_count') - 1)
            feedback.refresh_from_db(fields=['likes_count'])
            liked = False
        else:
            Feedback.objects.filter(pk=feedback.pk).update(likes_count=F('likes_count') + 1)
            feedback.refresh_from_db(fields=['likes_count'])
            liked = True

    return JsonResponse({'status': 'success', 'liked': liked, 'likes_count': feedback.likes_count})


@login_required
def add_comment(request, feedback_id):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

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
    if request.method not in ('GET', 'POST'):
        return HttpResponseNotAllowed(['GET', 'POST'])

    if getattr(request.user, 'role', '') != 'STUDENT':
        return JsonResponse({'status': 'error', 'message': "Only students can request feedback."}, status=403)

    assessment = get_object_or_404(Assessment, id=assessment_id)

    obj, created = FeedbackRequest.objects.get_or_create(student=request.user, assessment=assessment)

    if created:
        return JsonResponse({'status': 'success', 'message': f"Request sent for {assessment.get_type_display()}!"})
    else:
        return JsonResponse({'status': 'warning', 'message': "You have already requested feedback."})
