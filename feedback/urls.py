from django.urls import path
from . import views

app_name = 'feedback'

urlpatterns = [
    path('feed/', views.feedback_feed_view, name='feed'), 
    path('submit/', views.feedback_feed_view, name='submit'),
    path('like/<int:feedback_id>/', views.toggle_like, name='toggle_like'),
    path('comment/<int:feedback_id>/', views.add_comment, name='add_comment'),
    path('request/<int:assessment_id>/', views.request_feedback, name='request_feedback'),
]