from django.db import models
from django.utils import timezone
from django.contrib.postgres.fields import ArrayField
import ExperimentManager.Models as Model
import os
from SciExpeM.settings import SCIEXPEM_FILESYSTEM_FOLDER
import ExperimentManager.Models.Tool as Tool
from ExperimentManager.exceptions import *


class ExperimentBackUp(models.Model):
    # Mandatory
    dateTime = models.DateTimeField(blank=False, default=timezone.now)
    username = models.CharField(max_length=75, blank=True, null=True)
    chemModel = models.ForeignKey(Model.ChemModel, on_delete=models.CASCADE, related_name="backups")
    experiment = models.ForeignKey(Model.Experiment, on_delete=models.CASCADE, related_name="backups")
    parameter_name = models.CharField(max_length=75, blank=True, null=True)
    parameter_value = models.DecimalField(max_digits=Tool.MAX_DIGITS, decimal_places=Tool.DECIMAL_PLACES, blank=True,
                                          null=True)
    parameter_unit = models.CharField(max_length=50, blank=True, null=True)
    path = models.TextField()

    class Meta:
        unique_together = ('chemModel', 'experiment', 'parameter_name', 'parameter_value', 'parameter_unit',)

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

    def check_fields(self):
        parameter_name = self.parameter_name
        parameter_value = self.parameter_value
        parameter_unit = self.parameter_unit

        if parameter_name is None and (parameter_value is not None or parameter_unit is not None):
            raise ConstraintFieldExperimentError('No parameter type! parameter unit and value should be none')

        if parameter_name is not None and (parameter_value is None or parameter_unit is  None):
            raise ConstraintFieldExperimentError('No parameter value or unit!')

        if parameter_name is not None:
            names = set(ExperimentBackUp.objects.filter(experiment=self.experiment, chemModel=self.chemModel).values_list('parameter_name'))
            names.add(parameter_name)

            if len(names) > 1:
                raise ConstraintFieldExperimentError('Incongruent backup parameters!')

            units = set(
                ExperimentBackUp.objects.filter(experiment=self.experiment, chemModel=self.chemModel).values_list(
                    'parameter_unit'))
            units.add(parameter_unit)

            if len(units) > 1:
                raise ConstraintFieldExperimentError('Incongruent backup units!')

    def save(self, *args, **kwargs):
        self.check_fields()
        super().save(*args, **kwargs)
