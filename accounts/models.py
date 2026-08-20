from django.contrib.auth.models import AbstractUser, UserManager as DjangoUserManager
from django.db import models

class UserManager(DjangoUserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("role", User.Role.ADMIN)
        return super().create_superuser(username, email, password, **extra_fields)


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = (
            "admin",
            "Administrador",
        )
        TECH = (
            "tech",
            "Técnico",
        )
        ATTENDANT = (
            "attendant",
            "Atendente",
        )

    role = models.CharField(
        "Função", max_length=20, choices=Role.choices, default=Role.TECH
    )
    phone = models.CharField("Telefone", max_length=11, null=True, blank=True)
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)
    notification_prefs = models.JSONField("Preferências", default=dict, blank=True)
    groups = models.ManyToManyField(
        "auth.Group", related_name="custom_user_groups", blank=True
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission", related_name="custom_user_permissions", blank=True
    )
    
    objects = UserManager()

    class Meta:
        ordering = ["-date_joined"]
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"

    def __str__(self):
        return f"{self.get_full_name()} ({self.role})"
