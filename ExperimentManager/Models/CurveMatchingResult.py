from django.db import models
import ExperimentManager.Models.Tool as Tool
import ExperimentManager.Models as Model


class CurveMatchingResult(models.Model):  # TODO nessun campo è controllato
    # Mandatory
    score = models.DecimalField(max_digits=Tool.MAX_DIGITS, decimal_places=Tool.DECIMAL_PLACES)
    error = models.DecimalField(max_digits=Tool.MAX_DIGITS, decimal_places=Tool.DECIMAL_PLACES)

    d0L2 = models.DecimalField(max_digits=Tool.MAX_DIGITS, decimal_places=Tool.DECIMAL_PLACES)
    d1L2 = models.DecimalField(max_digits=Tool.MAX_DIGITS, decimal_places=Tool.DECIMAL_PLACES)
    d0Pe = models.DecimalField(max_digits=Tool.MAX_DIGITS, decimal_places=Tool.DECIMAL_PLACES)
    d1Pe = models.DecimalField(max_digits=Tool.MAX_DIGITS, decimal_places=Tool.DECIMAL_PLACES)
    shift = models.DecimalField(max_digits=Tool.MAX_DIGITS, decimal_places=Tool.DECIMAL_PLACES)

    # Foreign Key
    execution_column = models.OneToOneField(Model.ExecutionColumn, on_delete=models.CASCADE,
                                            related_name="curve_matching_result")

    def get_equivalent(self, chemModel):
        execution = Model.Execution.objects.get(chemModel=chemModel, experiment=self.execution_column.execution.experiment)
        execution_column = Model.ExecutionColumn.objects.get(
            execution=execution,
            name=self.execution_column.name,
            label=self.execution_column.label,
            # species=self.execution_column.species,
            # species_object=self.execution_column.species_object,
            file_type=self.execution_column.file_type,
        )

        return CurveMatchingResult.objects.get(execution_column=execution_column)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)