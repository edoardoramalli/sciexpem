from django.db import models
from django.conf import settings

from ExperimentManager.Models import ResearchGroup

class Affiliation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, default=None, null=True)
    group = models.ForeignKey(ResearchGroup, on_delete=models.SET_NULL, default=None, null=True)