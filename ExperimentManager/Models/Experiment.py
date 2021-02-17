from django.db import models
from django.contrib.postgres.fields import ArrayField

import ExperimentManager.Models as Model
import ExperimentManager.models as MM
from ExperimentManager.exceptions import *
from ReSpecTh.ReSpecThParser import ReSpecThValidSpecie, ReSpecThValidProperty, ReSpecThValidExperimentType
from ReSpecTh.FuelValid import ValidFuel
from OpenSmoke.OpenSmoke import OpenSmokeParser
import ExperimentManager.Models.Tool as Tool

from enum import Enum

validatorProperty = ReSpecThValidProperty()
validatorSpecie = ReSpecThValidSpecie()
validatorExperiment = ReSpecThValidExperimentType()
validatorFuel = ValidFuel()


class EType(Enum):
    batch_idt = "batch_idt"
    stirred_parT = "stirred_parT"
    flow_isothermal_parT = "flow_isothermal_parT"
    flame_parPhi = "flame_parPhi"
    rcm_idt = "rcm_idt"

    @staticmethod
    def _check_existence(common_names, columns_names, mandatory_common, mandatory_columns):
        return all([i in common_names for i in mandatory_common]) and all(
            [i in columns_names for i in mandatory_columns])

    @staticmethod
    def _check_not_existence(common_names, columns_names, forbidden_common, forbidden_columns):
        return all([i not in common_names for i in forbidden_common]) and all(
            [i not in columns_names for i in forbidden_columns])

    @staticmethod
    def retrieve_type(e):
        common_properties = e.common_properties.all()
        common_properties_names = set([c.name for c in common_properties])

        data_columns = e.data_columns.all()
        data_columns_names = set([d.name for d in data_columns])

        if e.reactor == "flow reactor":

            mandatory_common = ['residence time', 'pressure']
            mandatory_columns = ['temperature', 'composition']
            forbidden_columns = ['dT']
            o1 = EType._check_existence(common_properties_names, data_columns_names, mandatory_common,
                                        mandatory_columns)
            o2 = EType._check_not_existence(common_properties_names, data_columns_names, [], forbidden_columns)
            if o1 and o2:
                return EType.flow_isothermal_parT

        if e.reactor == "stirred reactor":

            mandatory_common = ['pressure', 'volume', 'residence time']
            mandatory_columns = ['temperature', 'composition']
            o = EType._check_existence(common_properties_names, data_columns_names, mandatory_common, mandatory_columns)
            if o:
                return EType.stirred_parT

        if e.reactor == "shock tube":

            mandatory_common = ['pressure']
            mandatory_columns = ['ignition delay', 'temperature', 'volume', 'time']
            o = EType._check_existence(common_properties_names, data_columns_names, mandatory_common, mandatory_columns)
            if o:
                # return EType.rcm_idt
                return None

            mandatory_common = ['pressure']
            mandatory_columns = ['ignition delay', 'temperature']
            o = EType._check_existence(common_properties_names, data_columns_names, mandatory_common, mandatory_columns)
            if o:
                return EType.batch_idt

        if e.reactor == "flame":
            mandatory_common = ['temperature', 'pressure']
            mandatory_columns = ['laminar burning velocity', 'phi']
            o = EType._check_existence(common_properties_names, data_columns_names, mandatory_common, mandatory_columns)
            if o:
                return EType.flame_parPhi

        return None


class Experiment(models.Model):
    reactor = models.CharField(max_length=50)
    experiment_type = models.CharField(max_length=50)  # is checked
    fileDOI = models.CharField(max_length=50, unique=True)  # DOI experiment
    file_paper = models.ForeignKey(Model.FilePaper, on_delete=models.SET_NULL, default=None, null=True)
    ignition_type = models.CharField(max_length=75, blank=True, null=True)

    xml_file = models.TextField(blank=True, null=True)
    os_input_file = models.TextField(blank=True, null=True)

    comment = models.CharField(max_length=280, blank=True, null=True)

    # Meta Data
    fuels = ArrayField(models.CharField(max_length=40), null=True, blank=True)  # is checked

    status = models.CharField(max_length=50)

    phi_inf = models.DecimalField(max_digits=Tool.MAX_DIGITS, decimal_places=3, null=True, blank=True)  # is checked
    phi_sup = models.DecimalField(max_digits=Tool.MAX_DIGITS, decimal_places=3, null=True, blank=True)  # is checked

    t_inf = models.DecimalField(max_digits=Tool.MAX_DIGITS, decimal_places=3, null=True, blank=True)  # is checked
    t_sup = models.DecimalField(max_digits=Tool.MAX_DIGITS, decimal_places=3, null=True, blank=True)  # is checked

    p_inf = models.DecimalField(max_digits=Tool.MAX_DIGITS, decimal_places=3, null=True, blank=True)  # is checked
    p_sup = models.DecimalField(max_digits=Tool.MAX_DIGITS, decimal_places=3, null=True, blank=True)  # is checked

    username = models.CharField(max_length=75, blank=True, null=True)

    def check_fields(self):
        experiment_type = self.experiment_type
        fuels = list(self.fuels) if self.fuels is not None else []
        phi_inf = self.phi_inf if self.phi_inf is not None else 0
        phi_sup = self.phi_sup if self.phi_sup is not None else 0
        t_inf = self.t_inf if self.t_inf is not None else 0
        t_sup = self.t_sup if self.t_sup is not None else 0
        p_inf = self.p_inf if self.p_inf is not None else 0
        p_sup = self.p_sup if self.p_sup is not None else 0
        self.status = self.status if self.status is not None else 'unverified'
        status = self.status if self.status is not None else None
        username = self.username

        if not username:
            raise ConstraintFieldExperimentError("Experiment username is not specified!")

        if status not in ['verified', 'invalid', 'unverified']:
            raise ConstraintFieldExperimentError("Experiment status field '{}' is not valid!".format(status))

        if experiment_type is None:
            raise ConstraintFieldExperimentError("Experiment type field is not specified!")

        if not validatorExperiment.isValid(experiment_type):
            raise ConstraintFieldExperimentError("Experiment type '%s' is not valid!" % str(experiment_type))

        for fuel in fuels:
            if not validatorFuel.isValid(fuel):
                raise ConstraintFieldExperimentError("Fuel type '%s' is not valid!" % str(fuel))

        if not 0 <= phi_inf <= phi_sup <= 100:
            raise ConstraintFieldExperimentError("Invalid phi: 0 <= phi_inf <= phi_sup <= 100 (+inf)")

        if not 0 <= t_inf <= t_sup <= 3500:
            raise ConstraintFieldExperimentError("Invalid temperature range profile [K]: 0 <= t_inf <= t_sup <= 3500")

        if not 0 <= p_inf <= p_sup <= 200:
            raise ConstraintFieldExperimentError("Invalid pressure range profile [bar]: 0 <= p_inf <= p_sup <= 200")

    def check_verify(self):
        list_property = ['phi_inf', 'phi_sup', 't_inf', 't_sup', 'p_inf', 'p_sup', 'fuels', 'os_input_file']
        for prop in list_property:
            if getattr(self, prop) is None or getattr(self, prop) == []:
                raise ConstraintFieldExperimentError("'{}' field is not set.".format(prop))
        if not self.experiment_interpreter:
            raise ConstraintFieldExperimentError("Experiment is not managed yet.")

    def check_os_file(self):  # TODO in realta non fa il check ma genera solo il file template
        if self.os_input_file:
            self.os_input_file = OpenSmokeParser.parse_input_string(self.os_input_file)

    def save(self, *args, **kwargs):
        self.check_os_file()
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

        # Model Mandatory
        fileDOI = text_dict['fileDOI']
        reactor = text_dict['reactor']
        experiment_type = text_dict['experiment_type']

        exp = Experiment(experiment_type=experiment_type, reactor=reactor, fileDOI=fileDOI, os_input_file=os_input_file,
                         ignition_type=ignition_type, p_sup=p_sup, p_inf=p_inf, t_sup=t_sup, t_inf=t_inf,
                         phi_sup=phi_sup, phi_inf=phi_inf, fuels=fuels, status='unverified', file_paper=paper,
                         comment=comment)

        data_columns = text_dict['data_columns']
        tmp1 = [Model.DataColumn.createDataColumn(column, exp) for column in data_columns]

        common_properties = text_dict['common_properties']
        tmp2 = [Model.CommonProperty.createCommonProperty(prop, exp) for prop in common_properties]

        initial_species = text_dict['initial_species']
        tmp3 = [Model.InitialSpecie.createInitialSpecie(init, exp) for init in initial_species]

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

    def run_type(self):
        return EType.retrieve_type(self)

    @property
    def run_type_str(self):
        e_type = self.run_type()
        if e_type is not None:
            return e_type.value
        else:
            return None

    def run_experiment_interpreter(self):
        # Rispettare le regole
        types = MM.ExperimentInterpreter.objects.all()

        result = None

        for t in types:
            test_rule = True
            for r in MM.RuleInterpreter.objects.filter(experiment_interpreter=t):
                property_name = r.property_name
                property_value = r.property_value
                if not getattr(self, property_name) == property_value:
                    test_rule = False
                    break
            if test_rule is False:
                continue
            # Se arrivo qui ho rispettato tutte le rules. Adesso controllo i campi
            # TODO il problema è che experiment non deve avere altri campi !
            test_mapping = True
            # Controllo che esista un mapping
            mapping_set = set([])
            for m in MM.MappingInterpreter.objects.filter(experiment_interpreter=t):
                x_exp_name = m.x_exp_name
                x_exp_location = m.x_exp_location
                mapping_set.add(x_exp_name)
                diz_x = {'experiment': self, x_exp_location: x_exp_name}
                if not Model.DataColumn.objects.filter(**diz_x).exists():
                    test_mapping = False
                    break
                y_exp_name = m.y_exp_name
                y_exp_location = m.y_exp_location
                mapping_set.add(y_exp_name)
                diz_y = {'experiment': self, y_exp_location: y_exp_name}
                if not Model.DataColumn.objects.filter(**diz_y).exists():
                    test_mapping = False
                    break
            experiment_set = set([])
            for DC in Model.DataColumn.objects.filter(experiment=self):
                experiment_set.add(DC.name)
            if mapping_set != experiment_set:
                test_mapping = False
            if test_mapping:
                result = t.name

        return result

    @property
    def experiment_interpreter(self):
        return self.run_experiment_interpreter()
