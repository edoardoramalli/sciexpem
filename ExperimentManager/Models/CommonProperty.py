from django.db import models

import ExperimentManager.Models.Tool as Tool
import ExperimentManager.Models as Model
from ExperimentManager.exceptions import *
from ReSpecTh.ReSpecThParser import ReSpecThValidProperty

validatorProperty = ReSpecThValidProperty()


# Initial condition of the experiment
class CommonProperty(models.Model):
    # Mandatory - Checked Field
    name = models.CharField(max_length=50)
    units = models.CharField(max_length=50)
    value = models.DecimalField(max_digits=Tool.MAX_DIGITS, decimal_places=Tool.DECIMAL_PLACES)

    # Foreign Key
    experiment = models.ForeignKey(Model.Experiment, on_delete=models.CASCADE, related_name="common_properties")

    def __str__(self):
        return "%s %s %s" % (self.name, self.value, self.units)

    def check_fields(self):
        name = self.name
        unit = self.units
        value = self.value

        if float(value) < 0:
            raise ConstraintFieldExperimentError("Value common property '%s' must be positive!" % value)
        if not validatorProperty.isValidName(name):
            raise ConstraintFieldExperimentError("Name common property '%s' is not valid!" % name)
        if not validatorProperty.isValid(unit=unit, name=name):
            raise ConstraintFieldExperimentError(
                "Unit common property '%s' is not valid for '%s' element!" % (unit, name))

    @staticmethod
    def createCommonProperty(text_dict, experiment):
        # Mandatory
        name = text_dict['name']
        units = text_dict['units']
        value = text_dict['value']

        return CommonProperty(name=name, units=units, value=value, experiment=experiment)

    def save(self, *args, **kwargs):
        self.check_fields()
        super().save(*args, **kwargs)
