"""Utility: detect assessments with no linked LOs and (optionally) create AssessmentLearningOutcome entries.

Usage:
  py scripts/link_assessments_to_los.py [--apply]

Without --apply the script performs a dry-run and prints what it would do.
With --apply it will create ALO records and print summary.
"""
import os
import sys
from decimal import Decimal, ROUND_DOWN

# Ensure project root is on sys.path when this script is executed from scripts/
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(THIS_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Acumie.settings')
import django
django.setup()

from courses.models import Assessment, AssessmentLearningOutcome


def run(apply=False):
    to_create = []
    for a in Assessment.objects.all():
        existing = AssessmentLearningOutcome.objects.filter(assessment=a).count()
        if existing > 0:
            continue
        # Prefer direct ALO links if present; otherwise fall back to the course's LOs
        los = list(a.learning_outcomes.all())
        if not los:
            # fallback to course-level learning outcomes (useful when through table is empty)
            los = list(getattr(a, 'course').learning_outcomes.all()) if getattr(a, 'course', None) else []
            if los:
                print(f"Assessment {a.id} ({a}) has no direct linked LOs; will use course-level LOs")
            else:
                print(f"Assessment {a.id} ({a}) has no linked LOs (course also has none) -> SKIP")
                continue
        n = len(los)
        # even distribution
        base = (Decimal('100.00') / Decimal(n)).quantize(Decimal('0.01'), rounding=ROUND_DOWN)
        percents = [base] * n
        # adjust last to make sum 100.00
        total = sum(percents)
        diff = Decimal('100.00') - total
        percents[-1] = (percents[-1] + diff).quantize(Decimal('0.01'))
        for lo, p in zip(los, percents):
            to_create.append((a.id, lo.id, p))
    if not to_create:
        print('No ALO records need to be created.')
        return
    print('Dry-run: Will create the following AssessmentLearningOutcome records:')
    for a_id, lo_id, p in to_create:
        print(f'  Assessment {a_id} -> LO {lo_id} : {p}%')
    if apply:
        created = 0
        for a_id, lo_id, p in to_create:
            a = Assessment.objects.get(id=a_id)
            lo = a.learning_outcomes.model.objects.get(id=lo_id) if False else None
            # get lo object directly via the course's learning outcomes queryset
            lo = None
            # try direct ALO relation first
            for l in a.learning_outcomes.all():
                if l.id == lo_id:
                    lo = l
                    break
            # fallback to course-level LOs
            if lo is None and getattr(a, 'course', None):
                for l in a.course.learning_outcomes.all():
                    if l.id == lo_id:
                        lo = l
                        break
            if lo is None:
                print(f'  WARN: LO {lo_id} not found for assessment {a_id}, skipping')
                continue
            AssessmentLearningOutcome.objects.create(assessment=a, learning_outcome=lo, contribution_percentage=p)
            created += 1
        print(f'Created {created} AssessmentLearningOutcome records.')


if __name__ == '__main__':
    apply_flag = False
    if len(sys.argv) > 1 and sys.argv[1] == '--apply':
        apply_flag = True
    run(apply=apply_flag)
