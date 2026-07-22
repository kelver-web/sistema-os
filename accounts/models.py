from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Administrador',
        TECH = 'tech', 'Técnico',
        ATTENDANT = 'attendant', 'Atendente'
        
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.TECH)
    phone = models.CharField(max_length=11, null=True, blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    notification_prefs = models.JSONField(default=dict, blank=True)
    groups = models.ManyToManyField('auth.Group', related_name='custom_user_groups', blank=True)
    user_permissions = models.ManyToManyField('auth.Permission', related_name='custom_user_permissions', blank=True)
    
    class Meta:
        ordering = ['-date_joined']

    def __str__(self):
        return f'{self.get_full_name()} ({self.role})'