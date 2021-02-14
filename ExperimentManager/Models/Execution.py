from django.db import models
import ExperimentManager.Models.Tool as Tool
import ExperimentManager.Models as Model


class Execution(models.Model):
    chemModel = models.ForeignKey(Model.ChemModel, on_delete=models.CASCADE, related_name="executions")
    experiment = models.ForeignKey(Model.Experiment, on_delete=models.CASCADE, related_name="executions")
    execution_start = models.DateTimeField(null=True, blank=True)
    execution_end = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('chemModel', 'experiment',)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
