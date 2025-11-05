from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator



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

    def __str__(self):
        student_username = getattr(self.student, "username", str(self.student))
        course_code = getattr(getattr(self.assessment, 'course', None), 'code', 'N/A')
        assessment_type = getattr(self.assessment, 'get_type_display', lambda: '')()
        lo_code = getattr(self.learning_outcome, 'code', 'N/A')
        return f"Student: {student_username} - Assessment: {course_code}/{assessment_type} - LO: {lo_code}"
