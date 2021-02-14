from django.db import models
from django.contrib.postgres.fields import ArrayField
import ExperimentManager.Models.Tool as Tool
import ExperimentManager.Models as Model


class ExecutionColumn(models.Model):  # TODO nessun campo viene controllato
    name = models.CharField(max_length=100, null=True, blank=True)
    label = models.CharField(max_length=100)
    units = models.CharField(max_length=50)
    species = ArrayField(models.CharField(max_length=20), null=True, blank=True)
    data = ArrayField(models.DecimalField(max_digits=Tool.MAX_DIGITS, decimal_places=Tool.DECIMAL_PLACES))
    execution = models.ForeignKey(Model.Execution, on_delete=models.CASCADE, related_name="execution_columns")
    file_type = models.CharField(max_length=100)

    def range(self):
        return self.data[0], self.data[-1]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
