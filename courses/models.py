from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db.models import Sum

class Course(models.Model):
    code = models.CharField(
        max_length=15, 
        unique=True, 
        verbose_name="Course Code" 
    )
    title = models.CharField(
        max_length=255, 
        verbose_name="Course Title"
    )
    ects_credit = models.DecimalField(
        max_digits=4, 
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="ECTS Credit" 
    )

    class Meta:
        verbose_name = "Course" 
        verbose_name_plural = "Courses" 

    def __str__(self):
        return f"{self.code} - {self.title}"


# --- 2. Assessment Model ---
class Assessment(models.Model):
    ASSESSMENT_TYPES = [
        ('MIDTERM', 'Midterm'), 
        ('FINAL', 'Final'),     
        ('HOMEWORK', 'Homework'), 
        ('PROJECT', 'Project'), 
        ('QUIZ', 'Quiz'),      
        ('OTHER', 'Other'),     
    ]
    
    course = models.ForeignKey(
        Course, 
        on_delete=models.CASCADE, 
        related_name='assessments',
        verbose_name="Course" 
    )
    type = models.CharField(
        max_length=10, 
        choices=ASSESSMENT_TYPES,
        default='MIDTERM',
        verbose_name="Assessment Type" 
    )
    weight_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Weight Percentage (%)",
        help_text="The contribution percentage of this assessment to the overall course grade." 
    )
    
    learning_outcomes = models.ManyToManyField(
        "outcomes.LearningOutcome",
        related_name='assessments',
        verbose_name="Associated Learning Outcomes (LOs)" 
    )

    class Meta:
        verbose_name = "Assessment" 
        verbose_name_plural = "Assessments" 
        unique_together = ('course', 'type') 

    def __str__(self):
        return f"{self.course.code} - {self.get_type_display()}"

    @property
    def weight_fraction(self):
        return (Decimal(self.weight_percentage) / Decimal(100)) if self.weight_percentage is not None else Decimal(0)

    def clean(self):
        if not getattr(self,"course_id",None):
            return

        qs=Assessment.objects.filter(course=self.course).exclude(pk=self.pk)
        total_other=qs.aggregate(total=Sum('weight_percentage'))['total'] or 0
        total=Decimal(total_other)+Decimal(self.weight_percentage or 0)

        if total>Decimal(100):
            raise ValidationError({'weight_percentage': f"Total weight for assessments in this course would exceed 100%. Current without this: {total_other}%. With this: {total}%."})

class Enrollment(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'is_student': True},
        related_name='enrollments',
    )
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name='enrollments',
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'course')

    def __str__(self):
        return f"{self.student.username} in {self.course.title}"
