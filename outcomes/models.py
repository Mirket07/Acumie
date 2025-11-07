from django.core.exceptions import ValidationError
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from django.db.models import Sum

class ProgramOutcome(models.Model):
    code = models.CharField(
        max_length=10, 
        unique=True, 
        verbose_name="PO Code"
    )
    title = models.CharField(
        max_length=255, 
        verbose_name="Title"
    )
    description = models.TextField(
        blank=True, 
        verbose_name="Explanation"
    )

    class Meta:
        verbose_name = "Program Outcome (PO)"
        verbose_name_plural = "Program Outcomes (POs)"

    def __str__(self):
        return f"{self.code} - {self.title}"

class LearningOutcome(models.Model):
    code = models.CharField(
        max_length=10, 
        unique=True, 
        verbose_name="LO Code"
    )
    title = models.CharField(
        max_length=255, 
        verbose_name="Title"
    )
    description = models.TextField(
        blank=True, 
        verbose_name="Explanation"
    )
    
    program_outcomes = models.ManyToManyField(
        'ProgramOutcome',
        through='LO_PO_Contribution', 
        related_name='learning_outcomes'
    )

    class Meta:
        verbose_name = "Learning Outcome (LO)"
        verbose_name_plural = "Learning Outcomes (LOs)"
        ordering = ("code",)

    def __str__(self):
        return f"{self.code} - {self.title}"

    def total_po_contribution(self):
        total=self.lo_po_contributions.aggregate(total=Sum('contribution_percentage'))['total']
        return Decimal(total or 0)

    def check_po_contribution(self):
        return self.total_po_contribution()<= Decimal('100.00')

class LO_PO_Contribution(models.Model):
    learning_outcome = models.ForeignKey(
        LearningOutcome, 
        on_delete=models.CASCADE,
        verbose_name="Learning Outcome(LO)",
        related_name='lo_po_contributions'
    )
    program_outcome = models.ForeignKey(
        'ProgramOutcome',
        on_delete=models.CASCADE,
        verbose_name="Program Outcome (PO)",
        related_name='lo_po_contributions'
    )
    contribution_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Contribution Percentage (%)",
        help_text="Enter the percentage contribution this LO makes to this PO (0-100)."
    )

    class Meta:
        verbose_name = "LO-PO Contribution"
        verbose_name_plural = "LO-PO Contributions"
        unique_together = ('learning_outcome', 'program_outcome') 

    def __str__(self):
        return (
            f"{self.learning_outcome.code} -> {self.program_outcome.code}: "
            f"%{self.contribution_percentage}"
        )

    def clean(self):
        qs=LO_PO_Contribution.objects.filter(learning_outcome=self.learning_outcome).exclude(pk=self.pk)
        total_other=qs.aggregate(total=Sum('contribution_percentage'))['total'] or Decimal('0')
        total=Decimal(total_other) + Decimal(self.contribution_percentage or 0)

        if total>Decimal('100.00'):
            raise ValidationError({
                'contribution_percentage': (
                    f"Total contribution for {self.learning_outcome.code} would exceed 100%. "
                    f"Current other total: {total_other}%. With this: {total}%."
                )
            })

        super().clean()



from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

class StudentGoal(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='goals',
        verbose_name="Student"
    )
    goal_description = models.CharField(
        max_length=255,
        verbose_name="Goal Description"
    )
    target_date = models.DateField(
        verbose_name="Target Date"
    )
    
    completion_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal(0.00),
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Completion (%)"
    )
    is_completed = models.BooleanField(
        default=False,
        verbose_name="Completed"
    )
    
    class Meta:
        verbose_name = "Student Goal"
        verbose_name_plural = "Student Goals"
        ordering = ['target_date']

    def __str__(self):
        return f"{self.student.username}'s Goal: {self.goal_description}"


class GoalLearningOutcome(models.Model):
    goal = models.ForeignKey(
        StudentGoal, 
        on_delete=models.CASCADE,
        related_name='linked_outcomes',
        verbose_name="Goal"
    )
    learning_outcome = models.ForeignKey(
        LearningOutcome, 
        on_delete=models.CASCADE,
        verbose_name="Learning Outcome (LO)"
    )

    weight_in_goal = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Weight in Goal (%)",
        help_text="The percentage of this goal focused on this specific LO."
    )

    class Meta:
        verbose_name = "Goal LO Link"
        verbose_name_plural = "Goal LO Links"
        unique_together = ('goal', 'learning_outcome')

    def __str__(self):
        return f"{self.goal.goal_description} focuses on {self.learning_outcome.code}"