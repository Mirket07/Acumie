from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Grade
from courses.models import AssessmentLearningOutcome
from outcomes.models import LO_PO_Contribution, StudentProgramOutcomeScore

@receiver([post_save, post_delete], sender=Grade)
def recalculate_synergy_scores(sender, instance, **kwargs):
    """
    Bir not girildiğinde veya silindiğinde, o öğrencinin tüm PO skorlarını
    tekrar hesaplar ve outcomes tablosuna kaydeder.
    """
    student = instance.student
    print(f"--- 🔄 Sinyal Tetiklendi: {student.username} için Synergy Score Hesaplanıyor... ---")

    all_grades = Grade.objects.filter(student=student)

    po_totals = {} 

    for grade in all_grades:
        if not grade.score_percentage:
            continue

        score_val = float(grade.score_percentage)
        assessment = grade.assessment
        
        alo_links = AssessmentLearningOutcome.objects.filter(assessment=assessment)
        
        for alo in alo_links:
            lo = alo.learning_outcome
            
 
            contribution = (score_val * float(assessment.weight_percentage) * float(alo.contribution_percentage)) / 10000
            
   
            po_links = LO_PO_Contribution.objects.filter(learning_outcome=lo)
            
            for link in po_links:
                po = link.program_outcome

                factor = float(link.contribution_percentage) / 100.0
                
                final_point = contribution * factor
                
                if po not in po_totals:
                    po_totals[po] = 0.0
                po_totals[po] += final_point

    for po, total_score in po_totals.items():
        StudentProgramOutcomeScore.objects.update_or_create(
            student=student,
            program_outcome=po,
            defaults={'score': total_score}
        )
        print(f"   ✅ KAYDEDİLDİ: {po.code} -> {total_score:.2f}")

    print("--- Hesaplama Tamamlandı ---")