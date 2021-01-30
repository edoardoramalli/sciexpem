# Django import
from django.db import models
from django.contrib.postgres.fields import JSONField
from django.contrib.postgres.fields import ArrayField
from django.urls import reverse
from django.utils import timezone

# System import
from enum import Enum
import sys

# Local import
from ReSpecTh.ReSpecThParser import ReSpecThValidSpecie, ReSpecThValidProperty, ReSpecThValidExperimentType
from ReSpecTh.ExperimentClassifier import Classifier
from ReSpecTh.FuelValid import ValidFuel

validatorProperty = ReSpecThValidProperty()
validatorSpecie = ReSpecThValidSpecie()
validatorExperiment = ReSpecThValidExperimentType()
validatorFuel = ValidFuel()


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


def generic_save(*args, **kwargs):
    if 'username' in kwargs and 'object' in kwargs:
        username = kwargs.pop('username')
        obj = kwargs.pop('object')
        super(obj.__class__, obj).save(*args, **kwargs)
        log = LoggerModel(model_name=obj.__class__.__name__,
                          pk_model=obj.pk,
                          username=username,
                          action="save",
                          date=timezone.now())
        log.save()
    else:
        raise ValueError("Username field not specified!")


def generic_delete(*args, **kwargs):
    if 'username' in kwargs and 'object' in kwargs:
        username = kwargs.pop('username')
        obj = kwargs.pop('object')
        super(obj.__class__, obj).delete(*args, **kwargs)
        log = LoggerModel(model_name=obj.__class__.__name__,
                          pk_model=obj.pk,
                          username=username,
                          action="delete",
                          date=timezone.now())
        log.save()
    else:
        raise ValueError("Username field not specified!")


class FilePaper(models.Model):
    title = models.CharField(max_length=500)
    reference_doi = models.CharField(max_length=100, unique=True, blank=True, null=True)  # DOI paper

    def get_absolute_url(self):
        return reverse('filepaper', kwargs={'pk': self.pk})

    def save(self, *args, **kwargs):
        kwargs['object'] = self
        generic_save(*args, **kwargs)


class Experiment(models.Model):
    reactor = models.CharField(max_length=100)
    experiment_type = models.CharField(max_length=100)  # is checked
    fileDOI = models.CharField(max_length=100, unique=True)  # DOI experiment
    file_paper = models.ForeignKey(FilePaper, on_delete=models.CASCADE, default=None, null=True)
    ignition_type = models.CharField(max_length=100, blank=True, null=True)

    xml_file = models.TextField(blank=True, null=True)
    os_input_file = models.TextField(blank=True, null=True)

    # Meta Data
    fuels = ArrayField(models.CharField(max_length=40), null=True, blank=True)  # is checked

    status = models.CharField(max_length=50)

    phi_inf = models.DecimalField(max_digits=MAX_DIGITS, decimal_places=3, null=True, blank=True)  # is checked
    phi_sup = models.DecimalField(max_digits=MAX_DIGITS, decimal_places=3, null=True, blank=True)  # is checked

    t_inf = models.DecimalField(max_digits=MAX_DIGITS, decimal_places=3, null=True, blank=True)  # is checked
    t_sup = models.DecimalField(max_digits=MAX_DIGITS, decimal_places=3, null=True, blank=True)  # is checked

    p_inf = models.DecimalField(max_digits=MAX_DIGITS, decimal_places=3, null=True, blank=True)  # is checked
    p_sup = models.DecimalField(max_digits=MAX_DIGITS, decimal_places=3, null=True, blank=True)  # is checked

    def check_fields(self):
        experiment_type = self.experiment_type
        fuels = list(self.fuels) if self.fuels is not None else []
        phi_inf = self.phi_inf if self.phi_inf is not None else 0
        phi_sup = self.phi_sup if self.phi_sup is not None else 0
        t_inf = self.t_inf if self.t_inf is not None else 0
        t_sup = self.t_sup if self.t_sup is not None else 0
        p_inf = self.p_inf if self.p_inf is not None else 0
        p_sup = self.p_sup if self.p_sup is not None else 0

        if experiment_type is None:
            raise ValueError("Experiment type field is not specified!")

        if not validatorExperiment.isValid(experiment_type):
            raise ValueError("Experiment type '%s' is not valid!" % str(experiment_type))

        for fuel in fuels:
            if not validatorFuel.isValid(fuel):
                raise ValueError("Fuel type '%s' is not valid!" % str(fuel))

        if not 0 <= phi_inf <= phi_sup:
            raise ValueError("Invalid values for phi: 0 <= phi_inf <= phi_sup")

        if not 0 <= t_inf <= t_sup:
            raise ValueError("Invalid values for temperature profile: 0 <= t_inf <= t_sup")

        if not 0 <= p_inf <= p_sup:
            raise ValueError("Invalid values for pressure profile: 0 <= p_inf <= p_sup")

    def save(self, *args, **kwargs):
        kwargs['object'] = self
        self.check_fields()
        generic_save(*args, **kwargs)

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

    def run_experiment_classifier(self):
        classifier = Classifier()
        par_input_list = [column.name for column in DataColumn.objects.filter(experiment__pk=self.pk)]
        e_type = classifier.get_ExperimentClassifier(
            experiment_type=self.experiment_type,
            reactor=self.reactor,
            ignition_type=self.ignition_type.split("-") if self.ignition_type else None,
            par_input_list=par_input_list)
        return e_type

    @property
    def experiment_classifier(self):
        e_type = self.run_experiment_classifier()
        if e_type:
            return e_type.name
        else:
            return None


# Initial condition of the experiment
class CommonProperty(models.Model):
    name = models.CharField(max_length=100)  # is checked
    units = models.CharField(max_length=50)  # is checked
    value = models.DecimalField(max_digits=MAX_DIGITS, decimal_places=DECIMAL_PLACES)  # is checked

    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE, related_name="common_properties")

    def __str__(self):
        return "%s %s %s" % (self.name, self.value, self.units)

    def check_fields(self):
        name = self.name
        unit = self.units
        value = self.value

        if float(value) < 0:
            raise ValueError("Value common property '%s' must be positive!" % value)
        if not validatorProperty.isValidName(name):
            raise ValueError("Name common property '%s' is not valid!" % name)
        if not validatorProperty.isValid(unit=unit, name=name):
            raise ValueError("Unit common property '%s' is not valid for '%s' element!" % (unit, name))

    def save(self, *args, **kwargs):
        if 'username' in kwargs:
            kwargs.pop('username')
        self.check_fields()
        super().save(*args, **kwargs)


# Initial species of the fuel
class InitialSpecie(models.Model):
    name = models.CharField(max_length=20)  # is checked
    units = models.CharField(max_length=50)  # is checked
    value = models.DecimalField(max_digits=MAX_DIGITS, decimal_places=DECIMAL_PLACES)  # is checked

    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE, related_name="initial_species")

    def __str__(self):
        return "%s %s %s" % (self.name, self.value, self.units)

    def check_fields(self):
        name = self.name
        unit = self.units
        value = self.value

        if float(value) < 0:
            raise ValueError("Value initial specie '%s' must be positive!" % value)
        if not validatorSpecie.isValid(name):
            raise ValueError("Name initial specie '%s' is not valid!" % name)
        if not validatorProperty.isValid(unit=unit, name="composition"):
            raise ValueError("Unit initial specie '%s' is not valid for 'composition' element!" % unit)

    def save(self, *args, **kwargs):
        if 'username' in kwargs:
            kwargs.pop('username')
        self.check_fields()

        super().save(*args, **kwargs)

    # TODO Override DELETE and UPDATE


# More data columns represent the data of an experiment
class DataColumn(models.Model):
    name = models.CharField(max_length=100)  # is checked
    label = models.CharField(max_length=100, null=True, blank=True)  # is checked
    units = models.CharField(max_length=50)  # is checked
    species = ArrayField(models.CharField(max_length=20), null=True, blank=True)  # is checked
    data = ArrayField(models.DecimalField(max_digits=MAX_DIGITS, decimal_places=DECIMAL_PLACES))  # is checked

    plotscale = models.CharField(max_length=50)
    ignore = models.BooleanField()
    nominal = models.DecimalField(max_digits=MAX_DIGITS, decimal_places=DECIMAL_PLACES, null=True, blank=True)

    dg_id = models.CharField(max_length=10, null=False)

    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE, related_name="data_columns")

    def range(self):
        return self.data[0], self.data[-1]

    def __str__(self):
        return "%s %s %s %s %s" % (self.name, self.species, self.units, self.label, self.data)

    def check_fields(self):
        name = self.name
        label = self.label
        unit = self.units
        species = list(self.species) if self.species is not None else None
        nominal = self.nominal
        ignore = self.ignore
        plotscale = self.plotscale
        # data = [float(x) for x in self.data]

        if not validatorProperty.isValid(unit=unit, name=name):
            raise ValueError("Unit '%s' is not valid for property '%s' in data column!" % (unit, name))
        if label \
                and name != 'composition' \
                and name != 'concentration' \
                and not validatorProperty.isValidSymbolName(symbol=label, name=name):
            raise ValueError("Not correspondence between unit '%s' and label '%s' in data column!" % (unit, label))
        if species and not validatorSpecie.isValid(species):
            raise ValueError("Name species '%s' is not valid in data column!" % str(species))
        # Without next if data could be negative
        # if not all(x >= 0 for x in data):
        #     raise ValueError("Amount data column '%s' must be positive!" % str(data))

        if ignore and nominal is None:
            raise ValueError('Data column is ignored but nominal is not set.')

        if ignore and nominal < 0:
            raise ValueError('Data column nominal must be positive.')

        if plotscale not in ['lin', 'log', 'inv']:  # Hard-coded since very limited future expansion
            raise ValueError('Plot scale is not valid.')

    def save(self, *args, **kwargs):
        if 'username' in kwargs:
            kwargs.pop('username')
        self.check_fields()
        super().save(*args, **kwargs)

    # TODO Override DELETE and UPDATE


class ChemModel(models.Model):
    name = models.CharField(max_length=100)
    version = models.CharField(max_length=200, null=True, blank=True)
    xml_file_kinetics = models.TextField()
    xml_file_reaction_names = models.TextField()

    def save(self, *args, **kwargs):
        kwargs['object'] = self
        generic_save(*args, **kwargs)


class Execution(models.Model):
    chemModel = models.ForeignKey(ChemModel, on_delete=models.CASCADE, related_name="executions")
    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE, related_name="executions")
    execution_start = models.DateTimeField(null=True, blank=True)
    execution_end = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        kwargs['object'] = self
        generic_save(*args, **kwargs)


class ExecutionColumn(models.Model):
    name = models.CharField(max_length=100, null=True, blank=True)
    label = models.CharField(max_length=100)
    units = models.CharField(max_length=50)
    species = ArrayField(models.CharField(max_length=20), null=True, blank=True)
    data = ArrayField(models.DecimalField(max_digits=MAX_DIGITS, decimal_places=DECIMAL_PLACES))
    execution = models.ForeignKey(Execution, on_delete=models.CASCADE, related_name="execution_columns")
    file_type = models.CharField(max_length=100)

    def range(self):
        return self.data[0], self.data[-1]

    def save(self, *args, **kwargs):
        if 'username' in kwargs:
            kwargs.pop('username')
        super().save(*args, **kwargs)


class CurveMatchingResult(models.Model):
    execution_column = models.OneToOneField(ExecutionColumn, on_delete=models.CASCADE,
                                            related_name="curve_matching_result")
    index = models.DecimalField(max_digits=MAX_DIGITS, decimal_places=DECIMAL_PLACES)
    error = models.DecimalField(max_digits=MAX_DIGITS, decimal_places=DECIMAL_PLACES)

    def save(self, *args, **kwargs):
        kwargs['object'] = self
        generic_save(*args, **kwargs)


class LoggerModel(models.Model):
    model_name = models.CharField(max_length=100)
    pk_model = models.IntegerField()
    username = models.CharField(max_length=100)
    action = models.CharField(max_length=50)
    date = models.DateTimeField()


