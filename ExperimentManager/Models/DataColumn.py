from django.db import models
from django.contrib.postgres.fields import ArrayField

import ExperimentManager.Models.Tool as Tool
import ExperimentManager.Models as Model
from ExperimentManager.exceptions import *
from ReSpecTh.ReSpecThParser import ReSpecThValidSpecie, ReSpecThValidProperty, ReSpecThValidExperimentType
from ReSpecTh.FuelValid import ValidFuel


validatorProperty = ReSpecThValidProperty()
validatorSpecie = ReSpecThValidSpecie()
validatorExperiment = ReSpecThValidExperimentType()
validatorFuel = ValidFuel()


# More data columns represent the data of an experiment
class DataColumn(models.Model):
    # Mandatory - Checked
    name = models.CharField(max_length=100)
    units = models.CharField(max_length=50)
    data = ArrayField(models.DecimalField(max_digits=Tool.MAX_DIGITS, decimal_places=Tool.DECIMAL_PLACES))
    dg_id = models.CharField(max_length=10, null=False)

    # Optional - Checked
    label = models.CharField(max_length=100, null=True, blank=True)
    species = ArrayField(models.CharField(max_length=20), null=True, blank=True)
    nominal = models.DecimalField(max_digits=Tool.MAX_DIGITS, decimal_places=Tool.DECIMAL_PLACES, null=True, blank=True)

    # Mandatory with default
    plotscale = models.CharField(max_length=50, default='lin')  # is checked
    ignore = models.BooleanField(default=False)

    # Foreign Key
    experiment = models.ForeignKey(Model.Experiment, on_delete=models.CASCADE, related_name="data_columns")

    def range(self):
        return self.data[0], self.data[-1]

    @staticmethod
    def createDataColumn(text_dict, experiment):
        # Mandatory
        name = text_dict['name']
        units = text_dict['units']
        data = text_dict['data']
        dg_id = text_dict['dg_id']
        plotscale = text_dict['plotscale']
        ignore = text_dict['ignore']
        # Optional
        label = text_dict.get('label')
        species = text_dict.get('species')
        nominal = text_dict.get('nominal')

        return DataColumn(name=name, units=units, data=data, dg_id=dg_id, label=label, species=species,
                          plotscale=plotscale, ignore=ignore, nominal=nominal, experiment=experiment)

    def __str__(self):
        return "%s %s %s %s %s %s" % (self.name, self.species, self.units, self.label, self.data, self.dg_id)

    def check_fields(self):
        name = self.name
        label = self.label
        unit = self.units
        species = list(self.species) if self.species is not None else None
        nominal = self.nominal
        ignore = self.ignore
        plotscale = self.plotscale
        dg_id = self.dg_id
        data = self.data

        if not (dg_id == 'dg1' or dg_id == 'dg2'):
            raise ConstraintFieldExperimentError(
                "Name '%s' is not valid for data group in data column!" % dg_id)
        if not validatorProperty.isValid(unit=unit, name=name):
            raise ConstraintFieldExperimentError(
                "Unit '%s' is not valid for property '%s' in data column!" % (unit, name))
        if label \
                and name != 'composition' \
                and name != 'concentration' \
                and not validatorProperty.isValidSymbolName(symbol=label, name=name):
            raise ConstraintFieldExperimentError(
                "Not correspondence between unit '%s' and label '%s' in data column!" % (unit, label))
        if species and not validatorSpecie.isValid(species):
            raise ConstraintFieldExperimentError("Name species '%s' is not valid in data column!" % str(species))
        # Without next if data could be negative
        if not all(x >= 0 for x in data):
            raise ConstraintFieldExperimentError("Amount data column '%s' must be positive!" % str(data))

        if ignore and nominal is None:
            raise ConstraintFieldExperimentError('Data column is ignored but nominal is not set.')

        if ignore and nominal < 0:
            raise ConstraintFieldExperimentError('Data column nominal must be positive.')

        # Hard-coded since very limited future expansion
        if plotscale not in ['lin', 'log', 'inv', 'log10', 'ln'] and plotscale is not None:
            raise ConstraintFieldExperimentError("Plot scale field value '{}' is not valid.".format(plotscale))

    def save(self, *args, **kwargs):
        self.check_fields()
        super().save(*args, **kwargs)

    # TODO Override DELETE and UPDATE
