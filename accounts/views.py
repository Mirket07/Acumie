from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.urls import reverse

@login_required
def post_login_redirect(request):
    user = request.user
    role = getattr(user, "role", "").upper()

    if role == "INSTRUCTOR":
        return redirect(reverse("grades:teacher_dashboard"))

    if role == "DEPT_HEAD":
        try:
            return redirect(reverse("reports:aggregated_po_report"))
        except Exception:
            pass

    if user.is_staff or user.is_superuser:
        return redirect(reverse("admin:index"))

    return redirect(reverse("grades:dashboard"))

