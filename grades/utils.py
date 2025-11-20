from django.db.models import F
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from .models import Grade
from courses.models import Course
from outcomes.models import LO_PO_Contribution



DECIMAL_100=Decimal(100)
DECIMAL_ZERO=Decimal(0)
DECIMAL_ONE=Decimal(1)
DECIMAL_FIVE=Decimal(5)

def _to_decimal(value):
    if value is None:
        return DECIMAL_ZERO
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))

def calculate_weighted_po_score(student_id: int, course_id: int = None) -> dict:
    grades_queryset = Grade.objects.filter(student_id=student_id)
    
    if course_id:
        grades_queryset = grades_queryset.filter(assessment__course_id=course_id)
        
    if not grades_queryset.exists():
        return {}

    weighted_lo_scores =  (
        grades_queryset.annotate(weighted_score=F('lo_mastery_score')*(F('assessment__weight_percentage')/DECIMAL_100))
        .values(
            'learning_outcome_id',
            'assessment__course__id',
            'assessment__course__ects_credit',
            'weighted_score',
        )
        .order_by()
    )

    po_totals = defaultdict(Decimal)
    total_ects = DECIMAL_ZERO

    lo_ids = set([item['learning_outcome_id'] for item in weighted_lo_scores])

    contributions = LO_PO_Contribution.objects.filter(learning_outcome_id__in=lo_ids).select_related('program_outcome')

    lo_contributions = defaultdict(list)
    for c in contributions:
        lo_contributions[c.learning_outcome_id].append(c)

    processed_courses = set()

    for item in weighted_lo_scores:
        lo_id = item['learning_outcome_id']
        weighted_lo_score = _to_decimal(item['weighted_score'])
        ects_credit = _to_decimal(item['assessment__course__ects_credit'])
        course_pk=item['assessment__course__id']

        if not course_id and course_pk not in processed_courses:
            total_ects += ects_credit
            processed_courses.add(course_pk)

        for contrib in lo_contributions.get(lo_id,[]):
            contrib_frac=_to_decimal(contrib.contribution_percentage)/DECIMAL_100
            contribution_amount = weighted_lo_score * contrib_frac * ects_credit
            po_totals[contrib.program_outcome.code] += contribution_amount

    if course_id:
        divisor_ects = _to_decimal(Course.objects.get(id=course_id).ects_credit)
    else:
        divisor_ects = total_ects

    if divisor_ects > DECIMAL_ZERO:
        normalizing_factor = divisor_ects * DECIMAL_FIVE
    else:
        normalizing_factor = DECIMAL_ONE

    final_po_scores = {}

    for po_code, po_total_score in po_totals.items():
        if normalizing_factor > DECIMAL_ZERO:
            raw = (po_total_score / normalizing_factor) * DECIMAL_100
        else:
            raw = DECIMAL_ZERO
        quantized = raw.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        final_po_scores[po_code] = float(quantized)

    return final_po_scores

def quantize(val: Decimal) -> Decimal:
    return Decimal(val).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

def calculate_lo_scores(student, course: Course, treat_missing_as_zero: bool = True) -> dict:

    result: dict = {}
    assessments = list(course.assessments.all())
    los = set()
    for a in assessments:
        for lo in a.learning_outcomes.all():
            los.add(lo)

    for lo in los:
        total = Decimal("0.00")
        weight_sum = Decimal("0.00")
        for assessment in assessments:
            if not assessment.learning_outcomes.filter(pk=lo.pk).exists():
                continue
            weight_frac = (Decimal(assessment.weight_percentage) / Decimal(100)) if assessment.weight_percentage is not None else Decimal("0.00")
            g = Grade.objects.filter(student=student, assessment=assessment, learning_outcome=lo).first()
            if g is None:
                if treat_missing_as_zero:
                    grade_val = Decimal("0.00")
                else:
                    continue
            else:
                grade_val = Decimal(str(g.score_percentage))
            total += grade_val * weight_frac
            weight_sum += weight_frac

        if weight_sum == Decimal("0.00"):
            lo_score = Decimal("0.00")
        else:
            lo_score = (total / weight_sum)
        result[lo] = quantize(lo_score)
    return result
