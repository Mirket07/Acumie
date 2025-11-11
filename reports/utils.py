from django.db.models import Sum, DecimalField
from django.db.models.functions import Coalesce
from collections import defaultdict
from decimal import Decimal
import logging

from grades.models import Grade
from courses.models import Course, Assessment
from outcomes.models import LO_PO_Contribution
from accounts.models import CustomUser as User

logger = logging.getLogger(__name__)

def get_aggregated_po_report():
    all_grades = Grade.objects.select_related(
        'student', 
        'assessment__course', 
        'learning_outcome'
    ).all()

    if not all_grades:
        return {"report_available": False, "data": {}, "message": "No grade data available for reporting."}

    
    po_totals = defaultdict(Decimal)
    po_student_counts = defaultdict(set) 

    contributions = LO_PO_Contribution.objects.select_related('program_outcome').all()
    lo_contributions_map = defaultdict(list)
    for c in contributions:
        lo_contributions_map[c.learning_outcome_id].append(c)

    total_ects_in_system = Course.objects.aggregate(total=Coalesce(Sum('ects_credit'), Decimal(0)))['total']

    if total_ects_in_system == 0:
        return {"report_available": False, "data": {}, "message": "No ECTS credit data available."}

    for grade in all_grades:
        course = grade.assessment.course
        student = grade.student
        lo = grade.learning_outcome
        
        weighted_lo_score = grade.lo_mastery_score * (grade.assessment.weight_percentage / 100.0)

        for contrib in lo_contributions_map.get(lo.id, []):
            po_code = contrib.program_outcome.code
            
            contribution_amount = (
                weighted_lo_score * (contrib.contribution_percentage / 100.0) * course.ects_credit
            )
            po_totals[po_code] += contribution_amount
            po_student_counts[po_code].add(student.id) 

    final_po_report = {}
    normalizing_factor = total_ects_in_system * 5 
    
    for po_code, po_total_score in po_totals.items():
        if normalizing_factor > 0:
            final_score = (po_total_score / normalizing_factor) * 100.0 
        else:
            final_score = 0.0

        final_po_report[po_code] = {
            'score': round(final_score, 2),
            'student_count': len(po_student_counts[po_code])
        }

    return {"report_available": True, "data": final_po_report}