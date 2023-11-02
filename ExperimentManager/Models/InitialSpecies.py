from django.db import models

import ExperimentManager.Models.Tool as Tool
import ExperimentManager.Models as Model
from ExperimentManager.exceptions import *
from ReSpecTh.ReSpecThParser import ReSpecThValidProperty, ReSpecThValidSpecie

validatorProperty = ReSpecThValidProperty()
validatorSpecie = ReSpecThValidSpecie()


# Initial species of the fuel
class InitialSpecies(models.Model): # TODO da chiamare species not species
    # Mandatory - Checked Field
    name = models.CharField(max_length=20) # DA NON USARE !
    species = models.ForeignKey(Model.Species, on_delete=models.CASCADE, related_name="initial_species_object", blank=True, null=True)
    units = models.CharField(max_length=50)
    value = models.DecimalField(max_digits=Tool.MAX_DIGITS, decimal_places=10)

    configuration = models.CharField(max_length=20, default='premixed', blank=False, null=False)

    source_type = models.CharField(max_length=15)

    experiment = models.ForeignKey(Model.Experiment, on_delete=models.CASCADE, related_name="initial_species")

    def __str__(self):
        return "%s %s %s" % (self.name, self.value, self.units)

    def check_fields(self):
        # name = self.name
        unit = self.units
        value = self.value

        source_type = self.source_type

        configuration = self.configuration

        if source_type not in ['reported', 'digitized', 'calculated', 'estimated']:
            raise ConstraintFieldExperimentError(
                "Name '%s' is not valid for source type in Initial Specie!" % source_type)

        if configuration is not None and configuration not in ['premixed', 'fuel', 'oxidizer']:
            raise ConstraintFieldExperimentError(
                "Name '%s' is not configuration for Initial Specie!" % configuration)

        if float(value) < 0:
            raise ConstraintFieldExperimentError("Value initial species '%s' must be positive!" % value)
        # if not validatorSpecie.isValid(name):
        #     raise ConstraintFieldExperimentError("Name initial species '%s' is not valid!" % name)
        if not validatorProperty.isValid(unit=unit, name="composition"):
            raise ConstraintFieldExperimentError(
                "Unit initial species '%s' is not valid for 'composition' element!" % unit)

    @staticmethod
    def createInitialSpecies(text_dict, experiment):
        specie_id = int(text_dict['species'])
        species = Model.Species.objects.get(id=specie_id)
        units = text_dict['units']
        value = text_dict['value']
        source_type = text_dict['source_type']
        configuration = text_dict['configuration']

        return InitialSpecies(species=species, units=units, value=value, experiment=experiment, source_type=source_type, configuration=configuration)

    def save(self, *args, **kwargs):
        self.check_fields()
        super().save(*args, **kwargs)

    # TODO Override DELETE and UPDATE