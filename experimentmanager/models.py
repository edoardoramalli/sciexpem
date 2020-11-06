from django.db import models
from django.contrib.postgres.fields import JSONField
from django.contrib.postgres.fields import ArrayField
from django.urls import reverse
from enum import Enum


MAX_DIGITS = 42
DECIMAL_PLACES = 10


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
            o1 = EType._check_existence(common_properties_names, data_columns_names, mandatory_common, mandatory_columns)
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


class FilePaper(models.Model):
    title = models.CharField(max_length=500)
    reference_doi = models.CharField(max_length=100, unique=True, blank=True, null=True)  # DOI paper

    def get_absolute_url(self):
            return reverse('filepaper', kwargs={'pk': self.pk})


class Experiment(models.Model):
    reactor = models.CharField(max_length=100)
    experiment_type = models.CharField(max_length=100)
    fileDOI = models.CharField(max_length=100, unique=True)  # DOI experiment
    temp = models.BooleanField()  # For tmp experiment
    file_paper = models.ForeignKey(FilePaper, on_delete=models.CASCADE, default=None, null=True)
    ignition_type = models.CharField(max_length=100, blank=True, null=True)
    xml_file = models.TextField(blank=True, null=True)


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
        e_type =  self.run_type()
        if e_type is not None:
            return e_type.value
        else:
            return None


class CommonProperty(models.Model):  # Sono
    name = models.CharField(max_length=100)
    units = models.CharField(max_length=50)
    value = models.DecimalField(max_digits=MAX_DIGITS, decimal_places=DECIMAL_PLACES)
    sourcetype = models.CharField(max_length=50, null=True, blank=True)

    experiment = models.ForeignKey(Experiment,  on_delete=models.CASCADE, related_name="common_properties")

    def __str__(self):
        return "%s %s %s" % (self.name, self.value, self.units)


class InitialSpecie(models.Model):  # Le cose che bruci, i componenti iniziali
    name = models.CharField(max_length=20)
    units = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=MAX_DIGITS, decimal_places=DECIMAL_PLACES)
    cas = models.CharField(max_length=20, null=True, blank=True)
    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE, related_name="initial_species")
    role = models.CharField(max_length=20, null=True, blank=True)  # "fuel' and 'oxidizer'

    def __str__(self):
        return "%s %s %s" % (self.name, self.amount, self.units)


class DataColumn(models.Model):
    name = models.CharField(max_length=100)
    label = models.CharField(max_length=100, null=True, blank=True)
    units = models.CharField(max_length=50)
    species = ArrayField(models.CharField(max_length=20), null=True, blank=True)
    data = ArrayField(models.DecimalField(max_digits=MAX_DIGITS, decimal_places=DECIMAL_PLACES))
    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE, related_name="data_columns")
    dg_id = models.CharField(max_length=10, null=False)

    def range(self):
        return self.data[0], self.data[-1]

    def __str__(self):
        return "%s %s %s" % (self.name, self.species, self.units)


class ChemModel(models.Model):
    name = models.CharField(max_length=100)
    version = models.CharField(max_length=200, null=True, blank=True)
    xml_file_kinetics = models.TextField()
    xml_file_reaction_names = models.TextField()


class Execution(models.Model):
    chemModel = models.ForeignKey(ChemModel, on_delete=models.CASCADE, related_name="executions")
    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE, related_name="executions")
    execution_start = models.DateTimeField(null=True, blank=True)
    execution_end = models.DateTimeField(null=True, blank=True)


# todo: subclass as datacolumn
class ExecutionColumn(models.Model):
    name = models.CharField(max_length=100, null=True, blank=True)
    label = models.CharField(max_length=100)
    units = models.CharField(max_length=50)
    species = ArrayField(models.CharField(max_length=20), null=True, blank=True)
    data = ArrayField(models.DecimalField(max_digits=MAX_DIGITS, decimal_places=DECIMAL_PLACES))
    execution = models.ForeignKey(Execution, on_delete=models.CASCADE, related_name="execution_columns")

    def range(self):
        return self.data[0], self.data[-1]


class CurveMatchingResult(models.Model):
    execution = models.OneToOneField(Execution, on_delete=models.CASCADE, related_name="curve_matching_result")
    index = models.DecimalField(max_digits=MAX_DIGITS, decimal_places=DECIMAL_PLACES, null=True, blank=True)
    error = models.DecimalField(max_digits=MAX_DIGITS, decimal_places=DECIMAL_PLACES, null=True, blank=True)


class OpenSmokeInput(models.Model):
    experiment = models.OneToOneField(Experiment, on_delete=models.CASCADE, related_name="open_smoke_input")
    file = models.TextField()


class IOReSpecThOS(models.Model):
    experiment_type = models.CharField(max_length=100)
    reactor = models.CharField(max_length=100)
    data_group_fields = ArrayField(models.CharField(max_length=100))
    additional_info = models.CharField(max_length=100, null=True, blank=True)
    output_file = models.CharField(max_length=100)
    output_fields = ArrayField(models.CharField(max_length=100))
