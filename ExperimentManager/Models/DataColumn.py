from django.db import models
from django.contrib.postgres.fields import ArrayField

import ExperimentManager.Models.Tool as Tool
import ExperimentManager.Models as Model
from ExperimentManager.exceptions import *
from ReSpecTh.ReSpecThParser import ReSpecThValidSpecie, ReSpecThValidProperty, ReSpecThValidExperimentType, \
    ReSpecThAtomSpecie
from ReSpecTh.FuelValid import ValidFuel
from ReSpecTh.phi_to_mol_frac import GetMoleFractionsFromEquivalenceRatio

validatorProperty = ReSpecThValidProperty()
# validatorSpecie = ReSpecThValidSpecie()
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
    # TODO aggiungere controllo che label e species siano uguali
    label = models.CharField(max_length=100, null=True, blank=True)
    species = ArrayField(models.CharField(max_length=20), null=True, blank=True)
    species_object = models.ManyToManyField(Model.Specie, related_name="species_list", blank=True)

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

    def __init__(self, *args, species_object=[], **kwargs):
        super(DataColumn, self).__init__(*args, **kwargs)
        self.save()
        if species_object:
            for specie in species_object:
                self.species_object.add(specie) # Non importa fare save dopo many to many add
        # self.save()


    def range(self):
        return self.data[0], self.data[-1]

    @staticmethod
    def createDataColumn(text_dict, experiment):
        print(text_dict)
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
        species_object = text_dict.get('species_object')
        data_group_profile = text_dict.get('data_group_profile')

        list_species = None
        if species_object:
            list_species = []
            for specie in species_object:
                list_species.append(Model.Specie.objects.get(id=int(specie)))

        fuel_oxidizer = text_dict.get('fuel_oxidizer')

        others = []

        if fuel_oxidizer:
            oxidizers = []
            fuels = []
            for f_o in fuel_oxidizer:
                if f_o['type'] == 'Oxidizer':
                    oxidizers.append(f_o)
                elif f_o['type'] == 'Fuel':
                    fuels.append(f_o)

            values_oxi = [oxi['value'] for oxi in oxidizers]
            values_fuels = [f['value'] for f in fuels]

            if sum(values_oxi) != 1:
                raise ConstraintFieldExperimentError('The sum of oxidizers percentage must be 1')
            elif sum(values_fuels) != 1:
                raise ConstraintFieldExperimentError('The sum of fuels percentage must be 1')

            atoms = ReSpecThAtomSpecie()

            oxis_dict = {atoms.to_atoms[oxi['specie'].upper()]: oxi['value'] for oxi in oxidizers}
            fuels_dict = {atoms.to_atoms[f['specie'].upper()]: f['value'] for f in fuels}

            results = []

            for phi in data:
                results.append(
                    GetMoleFractionsFromEquivalenceRatio(equivalence_ratio=phi, fuels=fuels_dict, oxidizers=oxis_dict))

            species_division = {}

            for r in results:
                for specie in r:
                    species_division[atoms.to_species[specie.upper()]] = species_division.get(
                        atoms.to_species[specie.upper()], []) + [r[specie]]

            for division in species_division:
                others.append(DataColumn(name='composition', units='mole fraction',
                                         data=species_division[division],
                                         dg_id=dg_id,
                                         species=[division],
                                         source_type='calculated',
                                         dg_label=dg_label,
                                         experiment=experiment))

        if data_group_profile:
            tmp = []
            for e in data_group_profile:
                if e.isdigit():
                    tmp.append(str(int(e)))
                else:
                    raise ValueError('Data type in profile not supported yet.')
            data_group_profile = tmp
        uncertainty_kind = text_dict.get('uncertainty_kind')
        uncertainty_bound = text_dict.get('uncertainty_bound')
        uncertainty_reference = text_dict.get('uncertainty_reference')

        uncertainty = None
        if uncertainty_reference:
            uncertainty_reference['experiment'] = experiment
            uncertainty = DataColumn(**uncertainty_reference)

        current = DataColumn(name=name, units=units, data=data, dg_id=dg_id, label=label, species_object=list_species,
                             source_type=source_type, dg_label=dg_label, data_group_profile=data_group_profile,
                             uncertainty_reference=uncertainty, uncertainty_kind=uncertainty_kind,
                             uncertainty_bound=uncertainty_bound,
                             experiment=experiment)
        current.save()
        # TODO Accordance between species array and label
        if current.name == 'composition' or current.name == 'concentration':
            list_species = [specie.preferredKey for specie in current.species_object.all()]
            current.label = '[' + ','.join(list_species) + ']'.replace(',', '+')
            current.save()
        # TODO fix specie in fule oxi + salva incertezza
        return [uncertainty, current] + others if uncertainty else [current] + others

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

        if dg_label not in ['V-t history', 'p-t history', 'T-t history', 'T-l history', 'experimental_data',
                            'initial_condition']:
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
        if (label == 'composition' or label == 'concentration') and species is None:
            raise ConstraintFieldExperimentError(
                "The label is composition or concentration but no specie is specified!")

        if label \
                and name != 'composition' \
                and name != 'concentration' \
                and not validatorProperty.isValidSymbolName(symbol=label, name=name):
            raise ConstraintFieldExperimentError(
                "Not correspondence between unit '%s' and label '%s' in data column!" % (unit, label))
        # if species and not validatorSpecie.isValid(species):
        #     raise ConstraintFieldExperimentError("Name species '%s' is not valid in data column!" % str(species))
        # Without next if data could be negative
        if not all(float(x) >= 0 for x in data):
            raise ConstraintFieldExperimentError("Amount data column '%s' must be positive!" % str(data))

    def save(self, *args, **kwargs):
        self.check_fields()
        super().save(*args, **kwargs)



        # TODO Override DELETE and UPDATE
