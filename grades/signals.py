# grades/signals.py
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone

from .models import Grade, GradeAudit


@receiver(pre_save, sender=Grade)
def grade_pre_save(sender, instance: Grade, **kwargs):
    if instance.pk:
        try:
            instance._pre_save_instance = Grade.objects.get(pk=instance.pk)
        except Grade.DoesNotExist:
            instance._pre_save_instance = None
    else:
        instance._pre_save_instance = None


@receiver(post_save, sender=Grade)
def grade_post_save(sender, instance: Grade, created: bool, **kwargs):
    pre = getattr(instance, "_pre_save_instance", None)
    changed_by = getattr(instance, "_changed_by", None)

    try:
        GradeAudit.objects.create(
            grade=instance if not created else instance,
            student=instance.student,
            assessment=instance.assessment,
            learning_outcome=instance.learning_outcome,
            changed_by=changed_by,
            old_score=(pre.score_percentage if pre else None),
            new_score=instance.score_percentage,
            old_mastery=(pre.lo_mastery_score if pre else None),
            new_mastery=instance.lo_mastery_score,
            timestamp=timezone.now(),
        )
    except Exception:
        pass


@receiver(post_delete, sender=Grade)
def grade_post_delete(sender, instance: Grade, **kwargs):
    try:
        GradeAudit.objects.create(
            grade=None,
            student=instance.student,
            assessment=instance.assessment,
            learning_outcome=instance.learning_outcome,
            changed_by=None,
            old_score=instance.score_percentage,
            new_score=None,
            old_mastery=instance.lo_mastery_score,
            new_mastery=None,
            timestamp=timezone.now(),
        )
    except Exception:
        pass
