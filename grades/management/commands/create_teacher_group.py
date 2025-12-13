from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from grades.models import Grade

class Command(BaseCommand):
    help = "Create 'Teachers' group and assign the 'can_grade' permission."

    def handle(self, *args, **options):
        group, created = Group.objects.get_or_create(name="Teachers")
        ct = ContentType.objects.get_for_model(Grade)
        perm, perm_created = Permission.objects.get_or_create(
            codename="can_grade",
            content_type=ct,
            defaults={"name": "Can enter and modify grades"}
        )
        group.permissions.add(perm)
        self.stdout.write(self.style.SUCCESS(
            f"Group 'Teachers' ready (created={created}). Permission 'can_grade' assigned (perm_created={perm_created})."
        ))
