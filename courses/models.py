from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from outcomes.models import LearningOutcome 

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
        LearningOutcome, 
        related_name='assessments',
        verbose_name="Associated Learning Outcomes (LOs)" 
    )

    class Meta:
        verbose_name = "Assessment" 
        verbose_name_plural = "Assessments" 
        unique_together = ('course', 'type') 

    def __str__(self):
        return f"{self.course.code} - {self.get_type_display()}"
