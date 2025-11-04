from django.shortcuts import render
from django.db.models import Avg
from django.contrib.auth.decorators import login_required
from .models import Grade
# İleride Synergy Analyzer'ı buraya dahil edeceğiz
# from .utils import calculate_weighted_po_score 

@login_required
def grade_dashboard_view(request):
    """
    Öğrenci veya Eğitmen için not ve başarı gösterge tablosu.
    Şimdilik, basit bir LO Mastery Score ortalaması gösterir.
    """
    user = request.user
    context = {}

    if user.is_authenticated:

        student_grades = Grade.objects.filter(student=user)

        avg_mastery_result = student_grades.aggregate(
            avg_mastery=Avg('lo_mastery_score')
        )

        avg_mastery = avg_mastery_result.get('avg_mastery') if avg_mastery_result.get('avg_mastery') is not None else 0.0

        context['user_is_student'] = user.role == 'STUDENT'
        context['user_name'] = user.get_full_name() or user.username
        context['average_lo_mastery'] = f"{avg_mastery:.2f}"


    return render(request, 'grades/dashboard.html', context)


# Basit bir deneme görünümünü tutmaya devam edelim (Test amaçlı)
def all_grades_average_view(request):
    """
    Tüm veritabanındaki LO Mastery Score ortalamasını hesaplar.
    """
    avg_score = Grade.objects.aggregate(
        avg_mastery=Avg('lo_mastery_score')
    )['avg_mastery']
    
    context = {
        'average': f"{avg_score:.2f}" if avg_score is not None else "0.00"
    }

    return render(request, 'grades/all_grades_average.html', context)
