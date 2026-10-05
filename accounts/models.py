from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    can_evaluate = models.BooleanField('Toegang tot Leerlingenevaluaties', default=False)
    can_export = models.BooleanField('Excel-export van eigen evaluaties', default=True)
    view_all_teachers = models.BooleanField('Inhoud van alle leerkrachten bekijken', default=True)
    visible_teachers = models.ManyToManyField('self', symmetrical=False, blank=True,
        related_name='authorized_viewers', verbose_name='Inhoud van deze leerkrachten bekijken')
    ui_colors = models.JSONField(default=dict, blank=True)
    goal_defaults = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = 'leerkracht / beheerder'
        verbose_name_plural = 'leerkrachten en beheerders'

class LoginThrottle(models.Model):
    key = models.CharField(max_length=64, unique=True)
    failures = models.PositiveIntegerField(default=0)
    window_started = models.DateTimeField()
