from decimal import Decimal
from collections import defaultdict
from .models import Grade
from outcomes.models import LO_PO_Contribution

def get_4_scale_point(score):
    if score >= 90: return Decimal("4.00")
    if score >= 85: return Decimal("3.50")
    if score >= 80: return Decimal("3.00")
    if score >= 75: return Decimal("2.50")
    if score >= 70: return Decimal("2.00")
    if score >= 65: return Decimal("1.50")
    if score >= 60: return Decimal("1.00")
    if score >= 50: return Decimal("0.50")
    return Decimal("0.00")

def calculate_course_grade(student, course):
    assessments = course.assessments.all()
    total_grade = Decimal("0.00")
    for assessment in assessments:
        weight = Decimal(str(assessment.weight_percentage)) / Decimal("100.00")
        grade_obj = Grade.objects.filter(student=student, assessment=assessment).first()
        score = Decimal(str(grade_obj.score_percentage)) if grade_obj else Decimal("0.00")
        total_grade += (score * weight)
    return total_grade

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
        for lo in linked_los:
            po_contributions = lo_po_map.get(lo.id, [])
            for contrib in po_contributions:
                po_code = contrib.program_outcome.code
                val = (raw_score_ratio * assessment_weight * (contrib.contribution_percentage / Decimal(100)) * course.ects_credit)
                po_totals[po_code] += val
                max_val = (Decimal(1.0) * assessment_weight * (contrib.contribution_percentage / Decimal(100)) * course.ects_credit)
                total_ects_impact[po_code] += max_val
    final_po_scores = {}
    for po_code, earned_score in po_totals.items():
        max_score = total_ects_impact.get(po_code, Decimal(1))
        final_po_scores[po_code] = round((earned_score / max_score) * 100, 2) if max_score > 0 else 0.0
    return final_po_scores