from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.db.models import CheckConstraint,Q,Index



class Grade(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'is_student': True},
        related_name='grades',
        verbose_name="Student"
    )

 
    assessment = models.ForeignKey(
        'courses.Assessment',
        on_delete=models.CASCADE,
        related_name='grades',
        verbose_name="Assessment"
    )


    learning_outcome = models.ForeignKey(
        'outcomes.LearningOutcome',
        on_delete=models.CASCADE,
        related_name='grades',
        verbose_name="Learning Outcome"
    )


    score_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Score (%)",
        help_text="The raw score percentage achieved in the assessment."
    )

 
    lo_mastery_score = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="LO Mastery Score (1-5)",
        help_text="The 1-5 score indicating mastery level for this specific LO (1: Low, 5: High)."
    )

    class Meta:
        verbose_name = "Grade"
        verbose_name_plural = "Grades"
        unique_together = ('student', 'assessment', 'learning_outcome')
        permissions = [
            ("can_grade", "Can enter and modify grades"),
        ]
        indexes=[
            Index(fields=['student', 'assessment']),
        ]
        constraints=[
            CheckConstraint(check=Q(score_percentage__gte=0)& Q(score_percentage__lte=100), name='grade_score_percentage_between_0_and_100'), CheckConstraint(check=Q(lo_mastery_score__gte=1) & Q(lo_mastery_score__lte=5), name='grade_lo_mastery_between_1_and_5'),
        ]

    def __str__(self):
        student_username = getattr(self.student, "username", str(self.student))
        course_code = getattr(getattr(self.assessment, 'course', None), 'code', 'N/A')
        assessment_type = getattr(self.assessment, 'get_type_display', lambda: '')()
        lo_code = getattr(self.learning_outcome, 'code', 'N/A')
        return f"Student: {student_username} - Assessment: {course_code}/{assessment_type} - LO: {lo_code}"



class CourseGrade(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'is_student': True},
        related_name='course_grades',
        verbose_name="Student"
    )

    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.CASCADE,
        related_name='course_grades',
        verbose_name="Course"
    )

    grade = models.DecimalField( max_digits=6, decimal_places=2, null=True, blank=True, help_text="Computed course grade (0-100)")

    computed_at=models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('student', 'course')
        verbose_name = "Course Grade"
        verbose_name_plural = "Course Grades"

    def __str__(self):
        student_name = getattr(self.student, "username", str(self.student))
        course_code = getattr(self.course, 'code', 'N/A')
        return f"{student_name} - {course_code}: {self.grade}"

class GradeAudit(models.Model):
    grade = models.ForeignKey('Grade', on_delete=models.CASCADE, related_name='audits', null=True)
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    assessment = models.ForeignKey('courses.Assessment', on_delete=models.SET_NULL, null=True)
    learning_outcome = models.ForeignKey('outcomes.LearningOutcome', on_delete=models.SET_NULL, null=True)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='grade_changes')
    old_score = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    new_score = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    old_mastery = models.IntegerField(null=True, blank=True)
    new_mastery = models.IntegerField(null=True, blank=True)
    reason = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
