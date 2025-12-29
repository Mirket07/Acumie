import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','Acumie.settings')
import django
django.setup()
from django.contrib.auth import get_user_model
from grades.models import Grade
from courses.models import Assessment
from courses.models import AssessmentLearningOutcome
from outcomes.models import LO_PO_Contribution, LearningOutcome
from grades.utils import calculate_weighted_po_score
from decimal import Decimal

User = get_user_model()
student = User.objects.filter(role='STUDENT').first()
print('Sample student id:', getattr(student,'id',None))

print('\nAssessments and their LOs:')
for a in Assessment.objects.all():
    los = list(a.learning_outcomes.all())
    print(f'Assessment {a.id} ({a}): weight={a.weight_percentage}, LOs={[ (l.id, str(l)) for l in los ]}')
    alo_qs = AssessmentLearningOutcome.objects.filter(assessment=a)
    for alo in alo_qs:
        print('  ALO:', alo.learning_outcome_id, alo.contribution_percentage)

print('\nLO -> PO contributions:')
for lo in LearningOutcome.objects.all():
    contributions = LO_PO_Contribution.objects.filter(learning_outcome=lo)
    print(f'LO {lo.id} ({lo}): contributions={[ (c.program_outcome.code, c.contribution_percentage) for c in contributions ]}')

if student:
    print('\nStudent Grades:')
    for g in Grade.objects.filter(student=student):
        print(f'Grade id:{g.id} assessment:{g.assessment_id} score:{g.score_percentage}')
    print('\ncalculate_weighted_po_score output:')
    print(calculate_weighted_po_score(student.id))
else:
    print('No student found')

