from django.contrib.auth.models import AbstractUser
from django.db import models

class UserRole(models.TextChoices):
    STUDENT = 'STUDENT', 'Öğrenci'
    INSTRUCTOR = 'INSTRUCTOR', 'Eğitmen'
    DEPT_HEAD = 'DEPT_HEAD', 'Departman Başkanı'
    ADMIN = 'ADMIN', 'Yönetici'

class CustomUser(AbstractUser):
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.STUDENT,
        verbose_name="Kullanıcı Rolü"
    )

    class Meta:
        verbose_name = "Kullanıcı"
        verbose_name_plural = "Kullanıcılar"

    def __str__(self):
        display_name = self.email if self.email else self.username
        return f"{display_name} ({self.get_role_display()})"

    @property
    def is_student(self) -> bool:
        return self.role == UserRole.STUDENT

    @property
    def is_teacher(self) -> bool:
        return self.role == UserRole.INSTRUCTOR
