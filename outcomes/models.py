from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

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
        ProgramOutcome,
        through='LO_PO_Contribution', 
        related_name='learning_outcomes'
    )

    class Meta:
        verbose_name = "Learning Outcome (LO)"
        verbose_name_plural = "Learning Outcomes (LOs)"

    def __str__(self):
        return f"{self.code} - {self.title}"

class LO_PO_Contribution(models.Model):
    learning_outcome = models.ForeignKey(
        LearningOutcome, 
        on_delete=models.CASCADE,
        verbose_name="Learning Outcome(LO)"
    )
    program_outcome = models.ForeignKey(
        ProgramOutcome, 
        on_delete=models.CASCADE,
        verbose_name="Program Outcome (PO)"
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
