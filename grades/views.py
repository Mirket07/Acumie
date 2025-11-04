from django.shortcuts import render
from django.db.models import Avg
from .models import Grade  

def average_view(request):
    
    avg_score = Grade.objects.aggregate(Avg('score'))['score__avg']

    
    return render(request, 'average.html', {'average': avg_score})

#python