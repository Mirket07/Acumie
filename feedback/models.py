from django.db import models
from django.conf import settings
from courses.models import Course 

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