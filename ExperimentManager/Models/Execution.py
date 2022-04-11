from django.db import models
from django.db.models import Count
import os

import ExperimentManager.Models as Model
from ExperimentManager.exceptions import *
from django.utils import timezone
from SciExpeM.settings import SCIEXPEM_FILESYSTEM_FOLDER


def get_dir_size(path):
    if os.path.isdir(path):
        total = 0
        with os.scandir(path) as it:
            for entry in it:
                if entry.is_file():
                    total += entry.stat().st_size
                elif entry.is_dir():
                    total += get_dir_size(entry.path)
        return total
    else:
        return None


class Execution(models.Model):
    chemModel = models.ForeignKey(Model.ChemModel, on_delete=models.CASCADE, related_name="executions")
    experiment = models.ForeignKey(Model.Experiment, on_delete=models.CASCADE, related_name="executions")
    execution_created = models.DateTimeField(blank=False, default=timezone.now)
    execution_start = models.DateTimeField(null=True, blank=True)
    execution_end = models.DateTimeField(null=True, blank=True)
    username = models.CharField(max_length=75, blank=True, null=True)
    execution_error = models.TextField(null=True, blank=True)
    computer = models.CharField(max_length=75, blank=True, null=True)

    class Meta:
        unique_together = ('chemModel', 'experiment',)

    def check_fields(self):
        if not self.username:
            raise ConstraintFieldExperimentError("Execution username is not specified!")

    @property
    def num_files(self):
        return Execution.objects.filter(id=self.id).annotate(num=Count('execution_files'))[0].num

    @property
    def absolute_folder_path(self):
        # according to the convention is not sure the folder actually exists
        return os.path.join(SCIEXPEM_FILESYSTEM_FOLDER, 'Execution', str(self.id))

    @property
    def folder_size(self):
        return get_dir_size(self.absolute_folder_path)

    @property
    def has_error(self):
        return bool(self.execution_error)

    def save(self, *args, **kwargs):
        self.check_fields()
        super().save(*args, **kwargs)
