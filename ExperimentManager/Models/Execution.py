from django.db import models
import ExperimentManager.Models as Model
from ExperimentManager.exceptions import *


class Execution(models.Model):
    chemModel = models.ForeignKey(Model.ChemModel, on_delete=models.CASCADE, related_name="executions")
    experiment = models.ForeignKey(Model.Experiment, on_delete=models.CASCADE, related_name="executions")
    execution_start = models.DateTimeField(null=True, blank=True)
    execution_end = models.DateTimeField(null=True, blank=True)
    username = models.CharField(max_length=75, blank=True, null=True)

    class Meta:
        unique_together = ('chemModel', 'experiment',)

    def check_fields(self):
        if not self.username:
            raise ConstraintFieldExperimentError("Execution username is not specified!")

    def save(self, *args, **kwargs):
        self.check_fields()
        super().save(*args, **kwargs)
