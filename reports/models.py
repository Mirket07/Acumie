from django.db import models
from courses.models import Course
from django.conf import settings

class Report(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reports')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='reports')
    grade = models.CharField(max_length=2)
    comments = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        student_name = getattr(self.student, "username", str(self.student))
        course_title = getattr(self.course, "title", "N/A")
        return f"{student_name} - {course_title} ({self.grade})"
