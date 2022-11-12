from django.db import models
from django.utils import timezone
from django.contrib.postgres.fields import ArrayField
import ExperimentManager.Models as Model
import os
from SciExpeM.settings import SCIEXPEM_FILESYSTEM_FOLDER
import ExperimentManager.Models.Tool as Tool


class ExperimentBackUp(models.Model):
    # Mandatory
    dateTime = models.DateTimeField(blank=False, default=timezone.now)
    username = models.CharField(max_length=75, blank=True, null=True)
    chemModel = models.ForeignKey(Model.ChemModel, on_delete=models.CASCADE, related_name="backups")
    experiment = models.ForeignKey(Model.Experiment, on_delete=models.CASCADE, related_name="backups")
    parameter_name = models.CharField(max_length=75, blank=True, null=True)
    parameter_value = models.DecimalField(max_digits=Tool.MAX_DIGITS, decimal_places=Tool.DECIMAL_PLACES, blank=True, null=True)
    parameter_unit = models.CharField(max_length=50, blank=True, null=True)
    path = models.TextField()

    class Meta:
        unique_together = ('chemModel', 'experiment', 'parameter_name', 'parameter_value', 'parameter_unit', )

    # On delete delete also i file!!!! anche per chemmodel ed executin

    @property
    def file_binary(self):
        with open(self.absolute_file_path, 'rb') as file:
            return file.read()

    @property
    def file(self):
        with open(self.absolute_file_path, 'r') as file:
            return file.read()

    @property
    def absolute_folder_path(self):
        return os.path.dirname(os.path.join(SCIEXPEM_FILESYSTEM_FOLDER, self.path))

    @property
    def absolute_file_path(self):
        return os.path.join(SCIEXPEM_FILESYSTEM_FOLDER, self.path)


