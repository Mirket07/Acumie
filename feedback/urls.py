from django.urls import path
from . import views

app_name = 'feedback'

urlpatterns = [
    path('submit/', views.feedback_submit_view, name='submit'), 
    path('thank-you/', views.feedback_thank_you_view, name='thank_you'),
    path('request/<int:assessment_id>/', views.request_feedback, name='request_feedback'),
]