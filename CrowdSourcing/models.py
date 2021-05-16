from django.db import models
from django.contrib.postgres.fields import ArrayField
from ExperimentManager.exceptions import *
import ExperimentManager.Models.Tool as Tool
from django.conf import settings
import os


class Participant(models.Model):  # TODO Fuel list
    name = models.CharField(max_length=100, unique=True)
    done = ArrayField(models.DecimalField(max_digits=Tool.MAX_DIGITS, decimal_places=Tool.DECIMAL_PLACES), default=list([]))

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)