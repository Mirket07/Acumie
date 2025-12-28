from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from courses.models import Assessment
from outcomes.models import LearningOutcome
from django.utils import timezone
from accounts.models import UserRole

class Grade(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': UserRole.STUDENT},
        related_name='grades',
        verbose_name="Student"
    )
    assessment = models.ForeignKey(
        Assessment,
        on_delete=models.CASCADE,
        related_name='grades',
        verbose_name="Assessment"
    )
    learning_outcome = models.ForeignKey(
        LearningOutcome,
        on_delete=models.CASCADE,
        related_name='grades',
        verbose_name="Learning Outcome",
        null=True,
        blank=True
    )
    score_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Score (%)",
        help_text="Student's score for this assessment (0-100)."
    )
    lo_mastery_score = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True,
        verbose_name="LO Mastery (1-5)"
    )

    class Meta:
        verbose_name = "Grade"
        verbose_name_plural = "Grades"
        unique_together = ('student', 'assessment', 'learning_outcome')

    def __str__(self):
        return f"{self.student.username} - {self.assessment} - {self.score_percentage}"