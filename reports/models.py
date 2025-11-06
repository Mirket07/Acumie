from django.db import models
from django.contrib.auth.models import User
from courses.models import Course

class Report(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='reports')
    grade = models.CharField(max_length=2)
    comments = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student.username} - {self.course.name} ({self.grade})"
