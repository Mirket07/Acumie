from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('po-summary/', views.aggregated_po_report_view, name='po_summary'),
]