from django.db.models import Sum, F, DecimalField
from django.db.models.functions import Coalesce
from collections import defaultdict
from decimal import Decimal

from .models import Grade
from courses.models import Course, Assessment
from outcomes.models import LO_PO_Contribution


def calculate_weighted_po_score(student_id: int, course_id: int = None) -> dict:
    grades_queryset = Grade.objects.filter(student_id=student_id)
    
    if course_id:
        grades_queryset = grades_queryset.filter(assessment__course_id=course_id)
        
    if not grades_queryset.exists():
        return {}

    weighted_lo_scores = grades_queryset.annotate(
        weighted_score=F('lo_mastery_score') * (F('assessment__weight_percentage') / 100.0)
    ).values(
        'learning_outcome_id',
        'assessment__course__ects_credit',
        'weighted_score'
    ).order_by()  # Gruplama yapmamak için order_by'ı temizle

    po_totals = defaultdict(Decimal)
    total_ects = Decimal(0)

    lo_ids = weighted_lo_scores.values_list('learning_outcome_id', flat=True).distinct()
    contributions = LO_PO_Contribution.objects.filter(
        learning_outcome_id__in=lo_ids
    ).select_related('program_outcome')

    lo_contributions = defaultdict(list)
    for c in contributions:
        lo_contributions[c.learning_outcome_id].append(c)

    processed_courses = set()

    for item in weighted_lo_scores:
        lo_id = item['learning_outcome_id']
        weighted_lo_score = item['weighted_score']
        ects_credit = item['assessment__course__ects_credit']

        if not course_id and item['assessment__course__id'] not in processed_courses:
            total_ects += ects_credit
            processed_courses.add(item['assessment__course__id'])

        for contrib in lo_contributions[lo_id]:
            po = contrib.program_outcome
            contribution_amount = (
                weighted_lo_score * (contrib.contribution_percentage / 100.0) * ects_credit
            )
            po_totals[po.code] += contribution_amount

    final_po_scores = {}

    divisor_ects = (
        total_ects if not course_id else Course.objects.get(id=course_id).ects_credit
    )

    normalizing_factor = Decimal(divisor_ects * 5) if divisor_ects > 0 else Decimal(1)

    for po_code, po_total_score in po_totals.items():
        final_score = (
            (po_total_score / normalizing_factor) * 100.0 if normalizing_factor > 0 else 0.0
        )
        final_po_scores[po_code] = round(final_score, 2)

    return final_po_scores
