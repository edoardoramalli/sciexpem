from django.db import models
import ExperimentManager.Models.Tool as Tool
import ExperimentManager.Models as Model


class CurveMatchingResult(models.Model):  # TODO nessun campo è controllato
    # Mandatory
    index = models.DecimalField(max_digits=Tool.MAX_DIGITS, decimal_places=Tool.DECIMAL_PLACES)
    error = models.DecimalField(max_digits=Tool.MAX_DIGITS, decimal_places=Tool.DECIMAL_PLACES)

    # Foreign Key
    execution_column = models.OneToOneField(Model.ExecutionColumn, on_delete=models.CASCADE,
                                            related_name="curve_matching_result")

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)