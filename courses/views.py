@login_required
def course_detail_view(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    sections = course.sections.prefetch_related('materials').all()
    
    participants = course.enrollments.select_related('student').all()

    learning_outcomes = (
        LearningOutcome.objects
        .filter(assessments__course=course)
        .distinct()
        .order_by('code')
    )

    requested_assessment_ids = []
    teacher_feedback_requests = []
    student_grades = []

    user = request.user

    try:
        Grade._meta.get_field('learning_outcome')
        has_learning_outcome = True
    except FieldDoesNotExist:
        has_learning_outcome = False

    if getattr(user, "role", "") == 'STUDENT':
        qs = Grade.objects.filter(
            student=user,
            assessment__course=course
        ).select_related('assessment', 'student')

        if has_learning_outcome:
            qs = qs.prefetch_related('learning_outcome').order_by('assessment__type', 'learning_outcome__code')
        else:
            qs = qs.order_by('assessment__type')

        student_grades = qs

        requested_assessment_ids = list(
            FeedbackRequest.objects
            .filter(student=user, assessment__course=course)
            .values_list('assessment_id', flat=True)
            .distinct()
        )
        is_instructor = False

    elif getattr(user, "role", "") == 'INSTRUCTOR' or user.is_staff:
        qs = Grade.objects.filter(assessment__course=course).select_related('assessment', 'student')

        if has_learning_outcome:
            qs = qs.prefetch_related('learning_outcome').order_by('student__first_name', 'assessment__type', 'learning_outcome__code')
        else:
            qs = qs.order_by('student__first_name', 'assessment__type')

        student_grades = qs
        is_instructor = True

        teacher_feedback_requests = (
            FeedbackRequest.objects
            .select_related('student', 'assessment', 'assessment__course')
            .filter(assessment__course=course, is_resolved=False)
            .order_by('-request_date')
        )
    else:
        student_grades = []
        is_instructor = False


    context = {
        'course': course,
        'sections': sections,
        'student_grades': student_grades,
        'is_instructor': is_instructor,
        'requested_assessment_ids': requested_assessment_ids,
        'learning_outcomes': learning_outcomes,
        'participants': participants, 
        'teacher_feedback_requests': teacher_feedback_requests, 
    }

    return render(request, 'courses/course_detail.html', context)
