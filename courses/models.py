from django.db import models
from django.conf import settings

class Course(models.Model):
    code = models.CharField(max_length=20)
    title = models.CharField(max_length=200)
    ects_credit = models.PositiveIntegerField(default=5)
    instructor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"{self.code} - {self.title}"

class Enrollment(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    date_enrolled = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'course')

class Assessment(models.Model):
    ASSESSMENT_TYPES = [
        ('MIDTERM', 'Midterm Exam'),
        ('FINAL', 'Final Exam'),
        ('PROJECT', 'Project'),
        ('QUIZ', 'Quiz'),
        ('ASSIGNMENT', 'Assignment'),
        ('LAB', 'Laboratory'),
        ('OTHER', 'Other'),
    ]
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assessments')
    type = models.CharField(max_length=20, choices=ASSESSMENT_TYPES)
    weight_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    name = models.CharField(max_length=100, blank=True, default='')

    def __str__(self):
        return f"{self.get_type_display()} ({self.weight_percentage}%) - {self.course.code}"

class AssessmentLearningOutcome(models.Model):
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='lo_contributions')
    learning_outcome = models.ForeignKey('outcomes.LearningOutcome', on_delete=models.CASCADE)
    contribution_percentage = models.DecimalField(max_digits=5, decimal_places=2)

class CourseSection(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="sections")
    title = models.CharField(max_length=200)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

class CourseMaterial(models.Model):
    MATERIAL_TYPES = [
        ('SLIDE', 'Slide/File'),
        ('LINK', 'Link/URL'),
        ('ANNOUNCEMENT', 'Announcement'),
    ]
    section = models.ForeignKey(CourseSection, on_delete=models.CASCADE, related_name='materials')
    title = models.CharField(max_length=200)
    type = models.CharField(max_length=20, choices=MATERIAL_TYPES, default='SLIDE')
    file = models.FileField(upload_to="course_materials/", blank=True, null=True)
    link = models.URLField(blank=True, null=True)