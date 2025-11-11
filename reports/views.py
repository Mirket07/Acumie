from django.shortcuts import render
from django.contrib.auth.decorators import user_passes_test
from .utils import get_aggregated_po_report
from accounts.models import UserRole 

def is_dept_head(user):
    return user.is_authenticated and user.role == UserRole.DEPT_HEAD

@user_passes_test(is_dept_head, login_url='/accounts/login/')
def aggregated_po_report_view(request):
    report_data = get_aggregated_po_report()
    context = {
        'report': report_data.get('data'),
        'is_available': report_data.get('report_available'),
        'message': report_data.get('message', 'PO Report is ready.'),
    }
    return render(request, 'reports/po_report.html', context)
