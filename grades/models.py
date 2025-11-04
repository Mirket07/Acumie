from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

from courses.models import Assessment
from outcomes.models import LearningOutcome
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

    def __str__(self):
        return (
            f"Student: {self.student.username} - "
            f"Assessment: {self.assessment.course.code}/{self.assessment.get_type_display()} - "
            f"LO: {self.learning_outcome.code}"
        )
