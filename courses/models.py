from django.contrib.auth.models import User
from django.db import models
from django.conf import settings
from accounts.models import UserRole


class Course(models.Model):
    code=models.CharField(max_length=20)
    name=models.CharField(max_length=200)
    credits=models.DecimalField(max_digits=4,decimal_places=2)

class Enrollment(models.Model):
    student=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,limit_choices_to={'role':UserRole.STUDENT})
    course=models.ForeignKey(Course,on_delete=models.CASCADE)
