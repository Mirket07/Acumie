from django.db.models import F
from collections import defaultdict
from decimal import Decimal
from .models import Grade
from courses.models import Course
from outcomes.models import LO_PO_Contribution

def calculate_weighted_po_score(student_id: int):
    student_grades = Grade.objects.filter(student_id=student_id).select_related('assessment__course')
    
    if not student_grades.exists():
        return {}

    po_totals = defaultdict(Decimal)
    total_ects_impact = defaultdict(Decimal)

    all_contributions = LO_PO_Contribution.objects.select_related('program_outcome', 'learning_outcome').all()
    lo_po_map = defaultdict(list)
    for contrib in all_contributions:
        lo_po_map[contrib.learning_outcome_id].append(contrib)

    for grade in student_grades:
        assessment = grade.assessment
        course = assessment.course
        
        raw_score_ratio = grade.score_percentage / Decimal(100)
        assessment_weight = assessment.weight_percentage / Decimal(100)
        
        linked_los = assessment.learning_outcomes.all()
        
        if not linked_los:
            continue

        for lo in linked_los:
            po_contributions = lo_po_map.get(lo.id, [])
            
            for contrib in po_contributions:
                po_code = contrib.program_outcome.code
                
                contribution_val = (
                    raw_score_ratio * assessment_weight * (contrib.contribution_percentage / Decimal(100)) * course.ects_credit
                )
                
                po_totals[po_code] += contribution_val
                
                max_possible_val = (
                    Decimal(1.0) * assessment_weight * (contrib.contribution_percentage / Decimal(100)) * course.ects_credit
                )
                total_ects_impact[po_code] += max_possible_val

    final_po_scores = {}
    for po_code, earned_score in po_totals.items():
        max_score = total_ects_impact.get(po_code, Decimal(1))
        if max_score > 0:
            final_percentage = (earned_score / max_score) * 100
            final_po_scores[po_code] = round(final_percentage, 2)
        else:
            final_po_scores[po_code] = 0.0

    return final_po_scores