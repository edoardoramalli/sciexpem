from django.db import models

import ExperimentManager.Models.Tool as Tool
import ExperimentManager.Models as Model
from ExperimentManager.exceptions import *
from ReSpecTh.ReSpecThParser import ReSpecThValidProperty, ReSpecThValidSpecie

validatorProperty = ReSpecThValidProperty()
validatorSpecie = ReSpecThValidSpecie()


# Initial species of the fuel
class InitialSpecie(models.Model):
    # Mandatory - Checked Field
    name = models.CharField(max_length=20)
    units = models.CharField(max_length=50)
    value = models.DecimalField(max_digits=Tool.MAX_DIGITS, decimal_places=Tool.DECIMAL_PLACES)

    experiment = models.ForeignKey(Model.Experiment, on_delete=models.CASCADE, related_name="initial_species")

    def __str__(self):
        return "%s %s %s" % (self.name, self.value, self.units)

    def check_fields(self):
        name = self.name
        unit = self.units
        value = self.value

        if float(value) < 0:
            raise ConstraintFieldExperimentError("Value initial specie '%s' must be positive!" % value)
        if not validatorSpecie.isValid(name):
            raise ConstraintFieldExperimentError("Name initial specie '%s' is not valid!" % name)
        if not validatorProperty.isValid(unit=unit, name="composition"):
            raise ConstraintFieldExperimentError(
                "Unit initial specie '%s' is not valid for 'composition' element!" % unit)

    @staticmethod
    def createInitialSpecie(text_dict, experiment):
        name = text_dict['name']
        units = text_dict['units']
        value = text_dict['value']

        return InitialSpecie(name=name, units=units, value=value, experiment=experiment)

    def save(self, *args, **kwargs):
        if 'username' in kwargs:
            kwargs.pop('username')
        self.check_fields()

        super().save(*args, **kwargs)

    # TODO Override DELETE and UPDATE