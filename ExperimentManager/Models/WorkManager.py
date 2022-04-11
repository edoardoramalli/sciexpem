from django.db import models
import ExperimentManager.Models as Model
import os
from SciExpeM.settings import SCIEXPEM_FILESYSTEM_FOLDER


class WorkManager(models.Model):
    last_contact = models.DateTimeField(null=True, blank=True)
    computer = models.CharField(max_length=75, blank=True, null=True, unique=True)

    free_cores = models.IntegerField(null=True, blank=True)
    num_cores = models.IntegerField(null=True, blank=True)

    max_jobs = models.IntegerField(null=True, blank=True)
    active_jobs = models.IntegerField(null=True, blank=True)

    def save(self, *args, **kwargs):
        self.check_fields()
        super().save(*args, **kwargs)

    def check_fields(self):
        pass


