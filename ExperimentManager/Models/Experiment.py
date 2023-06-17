from django.db import models
from django.contrib.postgres.fields import ArrayField

import ExperimentManager.Models as Model
from ExperimentManager.exceptions import *
from ReSpecTh.ReSpecThParser import ReSpecThValidSpecie, ReSpecThValidProperty, ReSpecThValidExperimentType
from ReSpecTh.FuelValid import ValidFuel
from OpenSmoke.OpenSmoke import OpenSmokeParser
import ExperimentManager.Models.Tool as Tool
from ExperimentManager.Models import ExperimentInterpreter
from SciExpeM import settings
from setfield import SetField

from enum import Enum
import functools
import operator
import ast
from itertools import chain
from django.db.models import Q

validatorProperty = ReSpecThValidProperty()
validatorSpecie = ReSpecThValidSpecie()
validatorExperiment = ReSpecThValidExperimentType()
validatorFuel = ValidFuel()

from ExperimentManager.Models.GeneralManager import GeneralManager


class ExperimentManager(GeneralManager):

    def filter(self, *args, **kwargs):
        # super().filter(**query)

        # user = query.pop('user')

        print(args)
        print()

        return self.get_queryset().filter(*args, **kwargs)


class Experiment(models.Model):
    # objects = ExperimentManager()

    reactor = models.CharField(max_length=50)
    experiment_type = models.CharField(max_length=50)  # is checked
    fileDOI = models.CharField(max_length=150, unique=True)  # DOI experiment
    file_paper = models.ForeignKey(Model.FilePaper, on_delete=models.SET_NULL, default=None, null=True,
                                   related_name="experiments")
    ignition_type = models.CharField(max_length=75, blank=True, null=True)

    xml_file = models.TextField(blank=True, null=True)
    os_input_file = models.TextField(blank=True, null=True)

    comment = models.CharField(max_length=280, blank=True, null=True)

    notes = models.TextField(blank=True, null=True)

    reactor_modes = ArrayField(models.CharField(max_length=40), null=True, blank=True)  # is checked

    # Meta Data
    # fuels = ArrayField(models.CharField(max_length=40), null=True, blank=True)  # is checked
    fuels = SetField(models.CharField(max_length=40), null=True, blank=True)  # TODO to BE deprecated
    fuels_object = models.ManyToManyField(Model.Species, related_name="fuels_list", blank=True)

    status = models.CharField(max_length=50)

    phi_inf = models.DecimalField(max_digits=Tool.MAX_DIGITS, decimal_places=3, null=True, blank=True)  # is checked
    phi_sup = models.DecimalField(max_digits=Tool.MAX_DIGITS, decimal_places=3, null=True, blank=True)  # is checked

    t_inf = models.DecimalField(max_digits=Tool.MAX_DIGITS, decimal_places=3, null=True, blank=True)  # is checked
    t_sup = models.DecimalField(max_digits=Tool.MAX_DIGITS, decimal_places=3, null=True, blank=True)  # is checked

    p_inf = models.DecimalField(max_digits=Tool.MAX_DIGITS, decimal_places=3, null=True, blank=True)  # is checked
    p_sup = models.DecimalField(max_digits=Tool.MAX_DIGITS, decimal_places=3, null=True, blank=True)  # is checked

    username = models.CharField(max_length=75, blank=True, null=True)

    experiment_interpreter = models.ForeignKey(ExperimentInterpreter, on_delete=models.SET_NULL, default=None,
                                               null=True)

    def check_fields(self):
        # TODO add check on reactor_modes
        experiment_type = self.experiment_type
        # fuels = list(self.fuels) if self.fuels is not None else []
        phi_inf = self.phi_inf if self.phi_inf is not None else 0
        phi_sup = self.phi_sup if self.phi_sup is not None else 0
        t_inf = self.t_inf if self.t_inf is not None else 0
        t_sup = self.t_sup if self.t_sup is not None else 0
        p_inf = self.p_inf if self.p_inf is not None else 0
        p_sup = self.p_sup if self.p_sup is not None else 0
        self.status = self.status if self.status is not None else 'unverified'
        status = self.status if self.status is not None else None
        username = self.username

        reactor_modes = self.reactor_modes

        if not username:
            raise ConstraintFieldExperimentError("Experiment username is not specified!")

        if status not in ['verified', 'invalid', 'unverified']:
            raise ConstraintFieldExperimentError("Experiment status field '{}' is not valid!".format(status))

        if experiment_type is None:
            raise ConstraintFieldExperimentError("Experiment type field is not specified!")

        if not validatorExperiment.isValid(experiment_type):
            raise ConstraintFieldExperimentError("Experiment type '%s' is not valid!" % str(experiment_type))

        # for fuel in fuels:
        #     if not validatorFuel.isValid(fuel):
        #         raise ConstraintFieldExperimentError("Fuel type '%s' is not valid!" % str(fuel))

        if not 0 <= phi_inf <= phi_sup <= 100:
            raise ConstraintFieldExperimentError("Invalid phi: 0 <= phi_inf <= phi_sup <= 100 (+inf)")

        if not 0 <= t_inf <= t_sup <= 3500:
            raise ConstraintFieldExperimentError("Invalid temperature range profile [K]: 0 <= t_inf <= t_sup <= 3500")

        if not 0 <= p_inf <= p_sup <= 1200:
            raise ConstraintFieldExperimentError("Invalid pressure range profile [bar]: 0 <= p_inf <= p_sup <= 1200")

        # if len(reactor_modes) > 1: TODO anche se reactor_m odes è un array la
        #     print(reactor_modes, len(reactor_modes), type(reactor_modes))
        #     raise ConstraintFieldExperimentError("Too many reactor modes.")

    def check_verify(self):
        list_property = ['phi_inf', 'phi_sup', 't_inf', 't_sup', 'p_inf', 'p_sup', 'fuels', 'os_input_file']
        for prop in list_property:
            if getattr(self, prop) is None or getattr(self, prop) == []:
                raise ConstraintFieldExperimentError("'{}' field is not set.".format(prop))
        if not self.experiment_interpreter:
            raise ConstraintFieldExperimentError("Experiment is not managed yet.")

    def check_and_generate_os_file(self):
        if self.os_input_file:
            self.os_input_file = OpenSmokeParser.parse_input_string(self.os_input_file)

    def save(self, *args, **kwargs):
        self.check_and_generate_os_file()
        self.check_fields()
        if self.status == 'verified':
            self.check_verify()
        super().save(*args, **kwargs)

    @staticmethod
    def createExperiment(text_dict):
        file_paper = text_dict['file_paper']
        paper = Model.FilePaper.createFilePaper(file_paper)

        # Model Optional
        p_sup = text_dict.get('p_sup')
        p_inf = text_dict.get('p_inf')
        t_sup = text_dict.get('t_sup')
        t_inf = text_dict.get('t_inf')
        phi_sup = text_dict.get('phi_sup')
        phi_inf = text_dict.get('phi_inf')
        fuels = text_dict.get('fuels')
        comment = text_dict.get('comment')
        os_input_file = text_dict.get('os_input_file')
        ignition_type = text_dict.get('ignition_type')
        reactor_modes = text_dict.get('reactor_modes')

        # Model Mandatory
        try:
            fileDOI = text_dict['fileDOI']
            reactor = text_dict['reactor']
            experiment_type = text_dict['experiment_type']
            username = text_dict['username']
        except KeyError as error:
            raise MandatoryFieldError(error)

        exp = Experiment(experiment_type=experiment_type, reactor=reactor, fileDOI=fileDOI, os_input_file=os_input_file,
                         ignition_type=ignition_type, p_sup=p_sup, p_inf=p_inf, t_sup=t_sup, t_inf=t_inf,
                         phi_sup=phi_sup, phi_inf=phi_inf, fuels=fuels, status='unverified', file_paper=paper,
                         comment=comment, username=username, reactor_modes=reactor_modes)

        paper.save()
        exp.save()

        data_columns = text_dict['data_columns']
        tmp1 = functools.reduce(operator.iconcat,
                                [Model.DataColumn.createDataColumn(column, exp) for column in data_columns], [])

        common_properties = text_dict.get('common_properties')
        if common_properties:
            tmp2 = [Model.CommonProperty.createCommonProperty(prop, exp) for prop in common_properties]
        else:
            tmp2 = []

        initial_species = text_dict['initial_species']
        tmp3 = [Model.InitialSpecie.createInitialSpecie(init, exp) for init in initial_species]

        for item in tmp1 + tmp2 + tmp3:
            item.save()

        return [paper] + [exp] + tmp1 + tmp2 + tmp3

    def get_params_experiment(self):
        common_properties = self.common_properties
        data_columns = self.data_columns

        params = dict()
        pressure_common = common_properties.filter(name="pressure").first()
        temperature_common = common_properties.filter(name="temperature").first()
        phi_common = common_properties.filter(name="phi").first()

        temperature_column = data_columns.filter(name="temperature").first()
        phi_column = data_columns.filter(name="phi").first()

        if pressure_common:
            params["P"] = pressure_common.value

        if temperature_common:
            params["T"] = temperature_common.value
        elif temperature_column:
            params["T"] = min(temperature_column.data)

        if phi_common:
            params["phi"] = phi_common.value
        elif phi_column:
            params["phi"] = min(phi_column.data)

        return params

    def run_experiment_interpreter(self):
        # Rispettare le regole
        types_list = Model.ExperimentInterpreter.objects.all()
        names_data_columns = set(
            [column.name for column in self.data_columns.all() if column.dg_label == 'experimental_data'])
        names_data_columns.discard('uncertainty')
        names_data_columns.discard('evaluated standard deviation')

        result = None
        for exp_type in types_list:
            for rule in Model.RuleInterpreter.objects.filter(experiment_interpreter=exp_type):
                property_name = rule.property_name
                property_value = rule.property_value
                if property_name == 'reactor_modes' and self.reactor == 'flame':
                    rule_value = set(ast.literal_eval(property_value))
                    tmp_value = getattr(self, property_name)
                    if tmp_value == None:
                        continue

                    exp_value = set(tmp_value)

                    if rule_value != exp_value:
                        break
                    else:
                        continue
                if not getattr(self, property_name) == property_value:
                    break
            else:
                mapping_fields = Model.MappingInterpreter.objects.filter(experiment_interpreter=exp_type).values(
                    'x_exp_name', 'y_exp_name')
                mapping_fields_list = []
                for diz in list(mapping_fields):
                    mapping_fields_list += list(diz.values())

                mapping_set = set(mapping_fields_list)

                if names_data_columns != mapping_set:
                    continue
                else:
                    result = exp_type

        return result

    @property
    def pairs(self):
        # TODO da fixare: ho paura che se c'è un profilo lo restituisca
        # TODO anche da ottimizzare
        query = self.data_columns.all()

        dg = {}

        for dc in query:
            dg[dc.dg_id] = dg.get(dc.dg_id, []) + [dc]

        pairs = []

        for dg_id in dg:
            x = None
            for dc in dg[dg_id]:
                if dc.is_x:
                    x = dc
                    break
            dg[dg_id].remove(x)
            for dc in dg[dg_id]:
                if dc.is_y:
                    pairs.append({'x': x, 'y': dc})

        return pairs

    @property
    def data_pairs_objects(self):
        # TODO da fixare: ho paura che se c'è un profilo lo restituisca
        # TODO anche da ottimizzare
        query = self.data_columns.filter(Q(dg_label='experimental_data') & ~Q(name='uncertainty'))

        dg = {}

        for dc in query:
            dg[dc.dg_id] = dg.get(dc.dg_id, []) + [dc]

        pairs = []

        for dg_id in dg:
            x = None
            ys = []
            for dc in dg[dg_id]:
                if dc.is_x:
                    x = dc
                else:
                    ys.append(dc)

            if x is not None:
                pairs += [{'x': e[0], 'y': e[1]} for e in zip([x] * len(ys), ys)]
            else:
                raise ValueError('None Error pairing')

        return pairs

    @property
    def data_pairs_raw(self):
        pairs = self.data_pairs_objects

        result = []

        for pair in pairs:
            result.append({'x': pair['x'].get_raw_dataColumn, 'y': pair['y'].get_raw_dataColumn})

        return result

    @property
    def interpreter(self):
        # if self.experiment_interpreter is None and settings.DEBUG:
        if self.experiment_interpreter is None:
            new_type = self.run_experiment_interpreter()
            if new_type:
                self.experiment_interpreter = new_type
                self.save()
            return self.experiment_interpreter
        else:
            return self.experiment_interpreter

    @property
    def interpreter_name(self):
        if self.interpreter is None:
            return None
        else:
            return self.interpreter.name

    def compare_equality(self, other, prop) -> bool:
        def similarity(elem, dict_other, threshold):
            if threshold == 0:
                return elem in dict_other
            else:
                pass

        if prop == 'InitialSpecie':
            list_element_other = other.initial_species.all()
            list_element = self.initial_species.all()
            dict_element_other = [{'species': element.species.InChI, 'units': element.units, 'value': element.value} for
                                  element in
                                  list_element_other]
            dict_element = [{'name': element.species.InChI, 'units': element.units, 'value': element.value} for element
                            in
                            list_element]
        elif prop == 'CommonProperty':
            list_element_other = other.common_properties.all()
            list_element = self.common_properties.all()
            dict_element_other = [{'name': element.name, 'units': element.units, 'value': element.value} for element in
                                  list_element_other]
            dict_element = [{'name': element.name, 'units': element.units, 'value': element.value} for element in
                            list_element]
        else:
            raise Exception

        unique = []
        if len(dict_element_other) == len(dict_element):
            for element in dict_element:
                if element in dict_element_other:
                    unique.append(True)
                    continue
                else:
                    unique.append(False)
                    break
            return all(unique)
        else:
            return False

    def __repr__(self):
        return "<Experiment ({})>".format(self.id)
