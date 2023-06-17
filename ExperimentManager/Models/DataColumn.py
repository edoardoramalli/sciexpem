from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from SciExpeM import settings

import inspect

import ExperimentManager.Models.Tool as Tool
import ExperimentManager.Models as Model
from ExperimentManager.exceptions import *
from ReSpecTh.ReSpecThParser import ReSpecThValidSpecie, ReSpecThValidProperty, ReSpecThValidExperimentType, \
    ReSpecThAtomSpecie
from ReSpecTh.FuelValid import ValidFuel
from ReSpecTh.phi_to_mol_frac import GetMoleFractionsFromEquivalenceRatio
from ExperimentManager.Models.GeneralManager import GeneralManager

validatorProperty = ReSpecThValidProperty()
# validatorSpecie = ReSpecThValidSpecie()
validatorExperiment = ReSpecThValidExperimentType()
validatorFuel = ValidFuel()


class DataColumnManager(GeneralManager):

    def filter(self, **query):
        super().filter(**query)

        user = query.pop('user')

        username = user.username

        print('ciaooo')

        print(query)

        # lookups = Q(title__icontains=query) | Q(content__icontains=query)

        return self.get_queryset().filter(**{'experiment__username': username, **query})


# More data columns represent the data of an experiment
class DataColumn(models.Model):
    # objects = DataColumnManager()

    # Mandatory - Checked
    name = models.CharField(max_length=100)
    units = models.CharField(max_length=50)
    data = ArrayField(models.DecimalField(max_digits=Tool.MAX_DIGITS, decimal_places=Tool.DECIMAL_PLACES))
    dg_id = models.CharField(max_length=10, null=False)
    dg_label = models.CharField(max_length=40, default='experimental_data')
    source_type = models.CharField(max_length=15)

    # Optional - Checked
    # TODO aggiungere controllo che label e species siano uguali
    label = models.CharField(max_length=100, null=True, blank=True)
    species = ArrayField(models.CharField(max_length=40), null=True, blank=True)
    species_object = models.ManyToManyField(Model.Species, related_name="species_list", blank=True)

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

    _is_x_data = models.BooleanField(null=True, blank=True)
    _is_y_data = models.BooleanField(null=True, blank=True)

    _x_dataColumn = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True,
                                      related_name="_ys_columns")

    _mapping = models.ForeignKey(Model.MappingInterpreter, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name="_data_columns")

    # def __init__(self, *args, species_object=[], **kwargs):
    #     super(DataColumn, self).__init__(*args, **kwargs)
    #     self.save()
    #     if species_object:
    #         for specie in species_object:
    #             self.species_object.add(specie)  # Non importa fare save dopo many to many add
    #     # self.save()

    def what_am_i(self):
        # TODO si può fare solo    experiment_interpreter esiste!!!!
        mappings = self.experiment.experiment_interpreter.mappings.all()
        my_mapping = None
        is_x = None
        for mapping in mappings:
            if self.__getattribute__(mapping.x_exp_location) == mapping.x_exp_name:
                if mapping.x_sim_location and mapping.x_sim_name is not None and mapping.x_sim_name != 'None':  # TODO fix it --> None è come stringa non come null
                    my_mapping = mapping
                    is_x = True
                    return is_x, my_mapping
                return is_x, my_mapping
            elif self.__getattribute__(mapping.y_exp_location) == mapping.y_exp_name:
                if mapping.y_sim_location and mapping.y_sim_name is not None and mapping.y_sim_name != 'None':
                    my_mapping = mapping
                    is_x = False
                    return is_x, my_mapping
                return is_x, my_mapping
        return is_x, my_mapping

    @property
    def is_x(self):
        if self._is_x_data is None:
            new_is_x, new_mapping = self.what_am_i()

            self._is_x_data = new_is_x
            print(new_is_x)
            self._mapping = new_mapping
            if self._is_x_data is not None:
                self._is_y_data = not new_is_x

                if not new_is_x:
                    query_set = self.experiment.data_columns.filter(dg_id=self.dg_id, _is_x_data=True)
                    if len(query_set) > 1:
                        raise ValueError('Error more than one x for data group!')
                    if query_set.exists():
                        self._x_dataColumn = query_set[0]
                else:
                    query_set = self.experiment.data_columns.filter(dg_id=self.dg_id, _x_dataColumn=None,
                                                                    _is_y_data=True)

                    for dc in query_set:
                        dc._x_dataColumn = self
                        dc.save()

                # TODO aggiornare _x_dataColumn_id

            self.save()

            return new_is_x
        else:
            return self._is_x_data

    @property
    def is_y(self):
        if self._is_y_data is None:
            self.is_x
        return self._is_y_data

    @property
    def transformation(self):
        if self._mapping:
            return self._mapping.x_transformation if self.is_x else self._mapping.y_transformation
        else:
            return None

    @property
    def get_raw_dataColumn(self):
        from ExperimentManager.Serializers import DataColumnSerializer
        return DataColumnSerializer(self, fields=('id', 'name', 'units', 'data', 'dg_id', 'label',
                                                  'uncertainty_reference', 'species_object',
                                                  'is_x', 'is_y', 'transformation')).data

    # @property
    # def is_x(self):
    #     mappings = self.experiment.experiment_interpreter.mappings.all()
    #     for mapping in mappings:
    #         if self.__getattribute__(mapping.x_exp_location) == mapping.x_exp_name:
    #             if mapping.x_sim_location and mapping.x_sim_name is not None and mapping.x_sim_name != 'None': # TODO fix it --> None è come stringa non come null
    #                 return True
    #             return None
    #         elif self.__getattribute__(mapping.y_exp_location) == mapping.y_exp_name:
    #             if mapping.y_sim_location and mapping.y_sim_name is not None and mapping.y_sim_name != 'None':
    #                 return False
    #             return None
    #     return None

    # @property
    # def is_y(self):
    #     return not self.is_x if self.is_x is not None else None

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
        species_object = text_dict.get('species_object')
        data_group_profile = text_dict.get('data_group_profile')

        list_species = None
        if species_object:
            list_species = []
            for specie in species_object:
                list_species.append(Model.Species.objects.get(id=int(specie)))

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

            # atoms = ReSpecThAtomSpecie()

            # oxis_dict = {atoms.to_atoms[oxi['specie'].upper()]: oxi['value'] for oxi in oxidizers}
            # fuels_dict = {atoms.to_atoms[f['specie'].upper()]: f['value'] for f in fuels}

            oxis_dict = {Model.Species.objects.get(id=oxi['specie']).formula: oxi['value'] for oxi in oxidizers}
            fuels_dict = {Model.Species.objects.get(id=f['specie']).formula: f['value'] for f in fuels}

            back_dict = {}

            for x in fuels + oxidizers:
                species_object = Model.Species.objects.get(id=x['specie'])
                formula = species_object.formula
                if formula not in back_dict:
                    back_dict[formula] = species_object
                elif formula in back_dict and back_dict[formula] == species_object:
                    continue
                else:
                    # La stessa formula C1H2... può essere associata a più inchi ma dopo non so come tornare indietro
                    raise ValueError('TODO: Situazione non ancora gestita. Contattare Edoardo!')

            results = []

            for phi in data:
                results.append(
                    GetMoleFractionsFromEquivalenceRatio(equivalence_ratio=phi, fuels=fuels_dict, oxidizers=oxis_dict))

            species_division = {}

            # print(results)

            for r in results:
                for specie in r:
                    species_division[back_dict[specie.upper()]] = species_division.get(
                        back_dict[specie.upper()], []) + [r[specie]]

            # print(species_division)

            # raise ValueError('Edoooo')

            for division in species_division:
                current = DataColumn.objects.create(name='composition', units='mole fraction',
                                                    data=species_division[division],
                                                    dg_id=dg_id,
                                                    source_type='calculated',
                                                    dg_label=dg_label,
                                                    experiment=experiment)
                if [division]:
                    for specie in [division]:
                        current.species_object.add(specie)

                others.append(current)

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
            uncertainty = DataColumn.objects.create(**uncertainty_reference)

        current = DataColumn.objects.create(name=name, units=units, data=data, dg_id=dg_id, label=label,
                                            source_type=source_type, dg_label=dg_label,
                                            data_group_profile=data_group_profile,
                                            uncertainty_reference=uncertainty, uncertainty_kind=uncertainty_kind,
                                            uncertainty_bound=uncertainty_bound,
                                            experiment=experiment)

        if list_species:
            for specie in list_species:
                current.species_object.add(specie)  # Non importa fare save dopo many to many add
        # self.save()

        # TODO Accordance between species array and label
        if current.name == 'composition' or current.name == 'concentration':
            list_species = [specie.preferredKey for specie in current.species_object.all()]
            current.label = '[' + ','.join(list_species) + ']'.replace(',', '+')
            current.save()
        # TODO fix specie in fule oxi + salva incertezza
        return [uncertainty, current] + others if uncertainty else [current] + others

    def __str__(self):
        return "DC:[%s %s %s %s %s]" % (self.name, self.species, self.units, self.label, self.dg_id)

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
        if not all(float(e) >= 0 for e in data):
            raise ConstraintFieldExperimentError("Amount data column '%s' must be positive!" % str(data))

        if self._is_x_data and self._is_y_data:
            raise ConstraintFieldExperimentError("A data column could be only an x or a y!")

        if self._is_x_data and (self._x_dataColumn is not None):
            raise ConstraintFieldExperimentError("A x-data column could not have an x data column!")

        # if self._is_y_data and (self._x_dataColumn is None):
        #     raise ConstraintFieldExperimentError("A y-data column needs to have an x data column!")

        if (self._is_x_data or self._is_y_data) and (self._mapping is None):
            raise ConstraintFieldExperimentError("A x or y data column could not have a None mapping!")

        # TODO consistency check, per ogni data group c'è solo una x!

    def save(self, *args, **kwargs):
        self.check_fields()
        super().save(*args, **kwargs)

        # TODO Override DELETE and UPDATE
