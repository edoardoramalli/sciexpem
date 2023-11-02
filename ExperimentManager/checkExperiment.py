from ExperimentManager.exceptions import *
import ExperimentManager.Models as Models
from OpenSmoke.OpenSmoke import OpenSmokeParser
from django.db.models import Count


def checkIDT(experiment):
    # TODO check i differenti tipi di ignition definition
    # TODO manca tutti i check su i tipi di ignition definito vedi valid_ignition_type method
    if experiment.experiment_type == 'ignition delay measurement':
        if experiment.ignition_type is None:
            raise ExperimentConsistencyError('IDT Experiment, ignition type is not defined.')
    else:
        if experiment.ignition_type:
            raise ExperimentConsistencyError('Ignition type is not defined in this type of experiment.')


def checkInitialSpecies(experiment):
    initial_species = experiment.initial_species.all()
    if len(initial_species) == 0 and experiment.experiment_type != 'laminar burning velocity measurement':
        raise ExperimentConsistencyError('No initial species.')

    if len(initial_species) == 0 and experiment.experiment_type == 'laminar burning velocity measurement':
        return

    units_initial_species = set([])
    value_initial_species = {'premixed': [], 'fuel': [], 'oxidizer': []}
    for specie in initial_species:
        units_initial_species.add(specie.units)
        value_initial_species[specie.configuration].append(specie.value)

    if len(units_initial_species) != 1 or list(units_initial_species)[0] != 'mole fraction':
        raise ExperimentConsistencyError('Units of initial species are not equal or not expressed in mole fraction.')

    if experiment.reactor == 'flame' and 'counterflow' in experiment.reactor_modes:
        if len(value_initial_species['fuel']) == 0 or len(value_initial_species['oxidizer']) == 0:
            raise ExperimentConsistencyError('In the counterflow flame is missing the fuel or oxidizer initial specie')
    elif len(value_initial_species['fuel']) != 0 or len(value_initial_species['oxidizer']) != 0:
        raise ExperimentConsistencyError('Fuel and Oxidizer intial species are possible only for counterflow flames.')

    for config_type in value_initial_species:
        sum_initial = sum(value_initial_species[config_type])
        if sum_initial != 1 and len(value_initial_species[config_type]) > 0:
            raise ExperimentConsistencyError(
                'The sum of mole fraction of the {} initial species is not 1. It is {}. The initial species are {}'.format(config_type,
                                                                                                sum_initial, value_initial_species[config_type]))


def checkProfiles(experiment, profile_list, dg_dict):
    # Only for specific reactor or combination of reactor and experiment type you can have a profile
    if profile_list and experiment.reactor not in ['rapid compression machine', 'shock tube', 'flow reactor']:
        raise ExperimentConsistencyError(
            'Profile data groups is not defined for {} reactor.'.format(experiment.reactor))

    dg_label = set([dg_dict[dg_id][0].dg_label for dg_id in dg_dict])

    dg_general = [dg_dict[dg_id][0].dg_label for dg_id in dg_dict]

    initial_condition_len = None

    if profile_list:
        for dg_id in dg_dict:
            if dg_dict[dg_id][0].dg_label == 'initial_condition':
                initial_condition_len = len(dg_dict[dg_id][0].data)
                break

    # print(dg_label)
    # print(profile_list)
    # print(dg_dict)

    if profile_list and len(dg_label) > 2:
        raise ExperimentConsistencyError('Too many data groups for an experiment with a profile.')

    if not profile_list and 'initial_condition' in dg_label:
        raise ExperimentConsistencyError('Missing profile for experiment with a initial condition measured data.')

    # If there are two profile then 1 can be an initial_condition
    if profile_list and len(dg_label) == 2 and not set(dg_label) == {'experimental_data', 'initial_condition'}:
        raise ExperimentConsistencyError('Too many data groups for an experiment with a profile.')

    # Profiles must have the same type
    profile_type = [profile.dg_label for profile in profile_list]

    if len(set(profile_type)) > 1:
        raise ExperimentConsistencyError('Profile data groups have different types.')

    # Numero di profili uguale al numero di pointi nelle initial conditions
    if len(profile_type) / 2 != initial_condition_len and dg_general.count('initial_condition') == 1:
        raise ExperimentConsistencyError('Number of profiles and initial conditions should be the same.')

    profile_coverage = {}
    # I profili dello stesso dg devono avere la stessa coverage
    # Nella coverage di un profilo non ci devono essere elementi duplicati
    for profile in profile_list:
        if profile.dg_id not in profile_coverage:
            coverage = profile.data_group_profile
            if len(set(coverage)) != len(coverage):
                raise ExperimentConsistencyError('Profiles coverage with duplicates points')
            profile_coverage[profile.dg_id] = coverage
        else:
            if len(profile_coverage[profile.dg_id]) != len(profile.data_group_profile):
                raise ExperimentConsistencyError('Profiles belonging to the same data group have different data length')
            if set(profile_coverage[profile.dg_id]) != set(profile.data_group_profile):
                raise ExperimentConsistencyError('Profiles belonging to the same data group with different coverage')

    # Se ho un profilo, tutti i data group devono avere la stessa lunghezza e
    # TODO implementare il fatto che i data group di dati sperimentali non possono essere in numero di righe maggiori
    # a quelli delle initial condition. Può accadare che un datagroup sperimentale usi meno punti di profilo
    if profile_list:
        flat_list = sorted([int(item) for sublist in profile_coverage.values() for item in sublist])

        if len(flat_list) != len(set(flat_list)):
            raise ExperimentConsistencyError('Multiple profiles for the same initial condition. Check association.')

        desidered_coverage = list(range(1, initial_condition_len + 1))

        if desidered_coverage != flat_list:
            raise ExperimentConsistencyError(
                'Not all data points of the initial condition are covered by a profile. Numeration starts from 1. Missing positions {}.'.format(
                    set(desidered_coverage) - set(flat_list)))


def checkUnique(experiment):
    # Remember to exclude 'experiment'
    possible_equal = Models.Experiment.objects.filter(
        experiment_type=experiment.experiment_type,
        reactor=experiment.reactor,
        file_paper__reference_doi=experiment.file_paper.reference_doi).annotate(num_species=Count('initial_species'),
                                                                                num_common=Count(
                                                                                    'common_properties')).filter(
        num_species=len(experiment.initial_species.all()), num_common=len(experiment.common_properties.all())).exclude(
        id=experiment.id)

    if possible_equal.exists():
        for possible in possible_equal:
            initial_equal = experiment.compare_equality(other=possible, prop='InitialSpecie')
            common_equal = experiment.compare_equality(other=possible, prop='CommonProperty')
            if initial_equal and common_equal:
                raise ExperimentConsistencyError(
                    'Duplicate Experiment (ID: {}, DOI: {})'.format(possible.id, possible.fileDOI))


def check_OS_input_file(experiment, profile_list):
    os_file_string = experiment.os_input_file

    if not os_file_string:
        raise ExperimentConsistencyError('OpenSmoke input file is empty.')

    check_result = OpenSmokeParser.check_input_string(experiment.os_input_file)

    KineticsFolder = check_result['KineticsFolder']
    OutputFolder = check_result['OutputFolder']
    Output = check_result['Output']
    ListOfProfiles = check_result['ListOfProfiles']
    Profile = check_result['Profile']
    Profile = False

    if not (KineticsFolder and (OutputFolder or Output)):
        raise ExperimentConsistencyError('OpenSmoke input missing @KineticsFolder or @Output keyword.')

    if bool(len(profile_list)) != (ListOfProfiles or Profile):
        raise ExperimentConsistencyError('Inconsistency between the profile data and OS input profile keyword.')


def checkDistribution(experiment, distribution_position, dg_dict):
    if distribution_position:
        if len(distribution_position) > 1:
            raise ExperimentConsistencyError('More than 1 distribution_position data group')

        # if 'initial_condition' in dg_dict:
        #     raise ExperimentConsistencyError('No initial_condition data group with distribution_position')

        number_of_distribution = len(distribution_position[0].data)

        if len(dg_dict) < number_of_distribution:
            raise ExperimentConsistencyError(
                'Inconsistency between number of distribution_position and number of distribution')

        taken = set([])

        for dg_id in dg_dict:
            # if len(dg_dict[dg_id]) != 2:
            #     raise ExperimentConsistencyError('A distribution needs two columns, given {}'.format(len(dg_dict[dg_id])))
            association_row = set([])
            for column in dg_dict[dg_id]:
                if column.data_group_profile:
                    if len(dg_dict[dg_id]) != 2:
                        raise ExperimentConsistencyError(
                            'A distribution experiment needs two column for the distribution data')
                    if len(column.data_group_profile) != 1:
                        raise ExperimentConsistencyError(
                            'A distribution can be associated only to one value')
                    association_row.add(column.data_group_profile[0])
            if len(association_row) > 1:
                raise ExperimentConsistencyError('Distribution data group not consistent with association row')
            if association_row:
                taken.add(association_row.pop())

        theoretical = set([str(i) for i in range(1, number_of_distribution + 1)])

        if theoretical != taken:
            raise ExperimentConsistencyError(
                'A distribution position is not associated. Missing {}'.format(theoretical - taken))


def checkExperiment(experiment, opensmoke=True):
    # ---> Unique: if different experiment_type, reactor, or paper doi. Then check initial species and common property
    checkUnique(experiment=experiment)

    # ---> IDT Experiment
    checkIDT(experiment=experiment)

    # ---> INITIAL SPECIES
    checkInitialSpecies(experiment=experiment)

    # ---> DATA COLUMNS
    data_columns = experiment.data_columns.all()

    if not list(data_columns):
        raise ExperimentConsistencyError('Experiment does not have any data columns.')

    unique_column = ['temperature', 'pressure', 'volume', 'time',
                     'residence time', 'distance', 'ignition delay',
                     'laminar burning velocity']

    # TODO migliorare: ci può essere solo una x e questa deve essere unica
    uncertainty_list = []
    profile_list = []
    distribution_position = []
    dg_dict = {}

    # TODO data group sperimentali tra loro consistenti

    # Sort Data Column in uncertainty, profile and data groups
    for column in data_columns:
        if column.uncertainty_kind:
            uncertainty_list.append(column)
        elif column.data_group_profile and column.dg_label in ['V-t history', 'p-t history', 'T-t history',
                                                               'T-l history']:
            profile_list.append(column)
        elif column.dg_label in ['distribution_position']:
            distribution_position.append(column)
        else:
            if column.dg_id not in dg_dict:
                dg_dict[column.dg_id] = [column]
            else:
                dg_dict[column.dg_id].append(column)

    checkProfiles(experiment=experiment, profile_list=profile_list, dg_dict=dg_dict)

    checkDistribution(experiment=experiment, distribution_position=distribution_position, dg_dict=dg_dict)

    if opensmoke and experiment.os_input_file:
        check_OS_input_file(experiment=experiment, profile_list=profile_list)

    # Uncertainty length and units must be the same of the referred property. If relative 0 <= x <= 1.
    for uncertainty in uncertainty_list:
        if len(uncertainty.data) != len(uncertainty.uncertainty.data):
            raise ExperimentConsistencyError('Uncertainty data length must be equal to data length.')
        if uncertainty.uncertainty_kind == 'relative':
            if not all(0 <= float(x) <= 1 for x in uncertainty.data):
                raise ExperimentConsistencyError('Uncertainty relative data must be 0 <= x <= 1.')
        if uncertainty.units != uncertainty.uncertainty.units:
            raise ExperimentConsistencyError('Uncertainty unit and Data units must be the same.')

    # All the elements in the same dg has same length, check for unique property
    for dg in dg_dict:
        data_length = [len(column.data) for column in dg_dict[dg]]
        data_name = [column.name for column in dg_dict[dg]]
        if len(set(data_length)) != 1:
            raise ExperimentConsistencyError('Data columns have different lengths.')
        for unique in unique_column:
            if data_name.count(unique) > 1:
                raise ExperimentConsistencyError("Data name '{}' is unique.".format(unique))
