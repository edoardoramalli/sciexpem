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
    dg_label = models.CharField(max_length=20, default='experimental_data')
    source_type = models.CharField(max_length=15)

    # Optional - Checked
    label = models.CharField(max_length=100, null=True, blank=True)
    species = ArrayField(models.CharField(max_length=20), null=True, blank=True)

    # Mandatory

    # Profile - pressure-time history, volume-time history or temperature-time history
    data_group_profile = ArrayField(models.CharField(max_length=25), null=True, blank=True)  # TODO

    # Uncertainty
    uncertainty_reference = models.OneToOneField('self', on_delete=models.CASCADE, related_name="uncertainty",
                                              null=True, blank=True)
    uncertainty_kind = models.CharField(max_length=10, null=True, blank=True)
    uncertainty_bound = models.CharField(max_length=10, null=True, blank=True)

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
        source_type = text_dict['source_type']

        # Optional
        label = text_dict.get('label')
        dg_label = text_dict.get('dg_label')
        species = text_dict.get('species')
        data_group_profile = text_dict.get('data_group_profile')
        uncertainty_kind = text_dict.get('uncertainty_kind')
        uncertainty_bound = text_dict.get('uncertainty_bound')
        uncertainty_reference = text_dict.get('uncertainty_reference')

        uncertainty = None
        if uncertainty_reference:
            uncertainty_reference['experiment'] = experiment
            uncertainty = DataColumn(**uncertainty_reference)

        current = DataColumn(name=name, units=units, data=data, dg_id=dg_id, label=label, species=species,
                             source_type=source_type, dg_label=dg_label, data_group_profile=data_group_profile,
                             uncertainty_reference=uncertainty, uncertainty_kind=uncertainty_kind,
                             uncertainty_bound=uncertainty_bound,
                             experiment=experiment)

        return [uncertainty, current] if uncertainty else [current]

    def __str__(self):
        return "%s %s %s %s %s %s" % (self.name, self.species, self.units, self.label, self.data, self.dg_id)

    def check_fields(self):
        name = self.name
        label = self.label
        unit = self.units
        species = list(self.species) if self.species is not None else None
        dg_id = self.dg_id
        data = self.data
        source_type = self.source_type
        if hasattr(self, 'uncertainty'):
            uncertainty = self.uncertainty
        else:
            uncertainty = None
        uncertainty_kind = self.uncertainty_kind
        uncertainty_bound = self.uncertainty_bound
        dg_label = self.dg_label  # For sure is not empty

        if dg_label not in ['V-t history', 'p-t history', 'T-t history', 'experimental_data', 'initial_condition']:
            raise ConstraintFieldExperimentError("Data Group Label not valid")
        if uncertainty:
            if bool(uncertainty_kind) != bool(uncertainty_bound):
                raise ConstraintFieldExperimentError("Missing uncertainty argument!")

        if uncertainty and uncertainty_kind and uncertainty_kind not in ['absolute', 'relative']:
            raise ConstraintFieldExperimentError("Uncertainty {} argument is not valid!".format(uncertainty_kind))

        if uncertainty and uncertainty_bound and uncertainty_bound not in ['plusminus', 'plus', 'minus']:
            raise ConstraintFieldExperimentError("Uncertainty {} argument is not valid!".format(uncertainty_bound))

        if source_type not in ['reported', 'digitized', 'calculated', 'estimated']:
            raise ConstraintFieldExperimentError(
                "Name '%s' is not valid for source type in data column!" % source_type)

        # TODO dg_id deve avere un formato prestability dgx. Ex dg1 dg2 dg3 ...

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
        if not all(float(x) >= 0 for x in data):
            raise ConstraintFieldExperimentError("Amount data column '%s' must be positive!" % str(data))

    def save(self, *args, **kwargs):
        self.check_fields()
        super().save(*args, **kwargs)

        # TODO Override DELETE and UPDATE
