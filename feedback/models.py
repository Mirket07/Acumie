from django.db import models
from django.conf import settings
from courses.models import Course, Assessment

class Feedback(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='feedback_entries',
        null=True,
        blank=True,
        verbose_name="Related Course"
    )
    feedback_text = models.TextField(
        verbose_name="Feedback Content"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Whisper Box Feedback"
        verbose_name_plural = "Whisper Box Feedbacks"
        ordering = ['-created_at']

    def __str__(self):
        course_name = self.course.code if self.course else "General"
        return f"Feedback for {course_name} ({self.created_at.strftime('%Y-%m-%d')})"

class FeedbackRequest(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='feedback_requests'
    )
    assessment = models.ForeignKey(
        Assessment, 
        on_delete=models.CASCADE, 
        related_name='feedback_requests'
    )
    request_date = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)
    instructor_response = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('student', 'assessment')
        ordering = ['-request_date']

    def __str__(self):
        full_name = f"{self.student.first_name} {self.student.last_name}"
        if not self.student.first_name:
            full_name = self.student.username
            
        return f"{full_name} requested feedback for {self.assessment.course.code} - {self.assessment.get_type_display()}"