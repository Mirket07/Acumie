import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','Acumie.settings')
import django
django.setup()
from django.contrib.auth import get_user_model
from grades.models import Grade
from courses.models import Assessment
from outcomes.models import LO_PO_Contribution, LearningOutcome
from grades.utils import calculate_weighted_po_score

User = get_user_model()
print('Grade count:', Grade.objects.count())
print('Assessment count:', Assessment.objects.count())
print('LO count:', LearningOutcome.objects.count())
print('LO_PO_Contribution count:', LO_PO_Contribution.objects.count())
student = User.objects.filter(role='STUDENT').first()
print('Sample student id:', getattr(student,'id',None))
if student:
    print('Grades for student:', Grade.objects.filter(student=student).count())
    try:
        print('calculate_weighted_po_score:', calculate_weighted_po_score(student.id))
    except Exception as e:
        import traceback
        traceback.print_exc()
        print('Exception in calculate_weighted_po_score:', e)
else:
    print('No student users found with role=STUDENT')

