from ExperimentManager.exceptions import *
import ExperimentManager.Models as Models
from OpenSmoke.OpenSmoke import OpenSmokeParser


def checkIDT(experiment):
    # TODO check i differenti tipi di ignition definition
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
    value_initial_species = []
    for specie in initial_species:
        units_initial_species.add(specie.units)
        value_initial_species.append(specie.value)

    if len(units_initial_species) != 1 or list(units_initial_species)[0] != 'mole fraction':
        raise ExperimentConsistencyError('Units of initial species are not equal or not expressed in mole fraction.')
    if sum(value_initial_species) != 1:
        raise ExperimentConsistencyError('The sum of mole fraction of the initial species is not 1.')


def checkProfiles(experiment, profile_list, dg_dict):
    # Only for specific reactor or combination of reactor and experiment type you can have a profile
    if profile_list and experiment.reactor not in ['rapid compression machine', 'shock tube', 'flow reactor']:
        raise ExperimentConsistencyError(
            'Profile data groups is not defined for {} reactor.'.format(experiment.reactor))

    dg_label = [dg_dict[dg_id][0].dg_label for dg_id in dg_dict]

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
    if profile_list:
        dg_length = []
        for dg in dg_dict:
            for column in dg_dict[dg]:
                dg_length.append(len(column.data))

        if len(set(dg_length)) != 1:
            raise ExperimentConsistencyError(
                'All the data group when there is a profile should have the same data length')

        # Non ci devono essere interesezioni tra i profili

        profile_coverage_frequency = set([])
        for profile in profile_coverage:
            if profile_coverage_frequency.intersection(set(profile_coverage[profile])):
                raise ExperimentConsistencyError('A data point has multiple profiles.')
            else:
                profile_coverage_frequency = profile_coverage_frequency.union(set(profile_coverage[profile]))

        if set([str(x) for x in range(1, dg_length[0] + 1)]) != profile_coverage_frequency:
            raise ExperimentConsistencyError(
                'A data point has not a profile or there is more coverage than data point.')


def checkUnique(experiment):
    # Remember to exclude 'experiment'
    possible_equal = Models.Experiment.objects.filter(
        experiment_type=experiment.experiment_type,
        reactor=experiment.reactor,
        file_paper__reference_doi=experiment.file_paper.reference_doi).exclude(id=experiment.id)

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
    dg_dict = {}

    # TODO data group sperimentali tra loro consistenti

    # Sort Data Column in uncertainty, profile and data groups
    for column in data_columns:
        if column.uncertainty_kind:
            uncertainty_list.append(column)
        elif column.data_group_profile or column.dg_label in ['V-t history', 'p-t history', 'T-t history',
                                                              'T-l history']:
            profile_list.append(column)
        else:
            if column.dg_id not in dg_dict:
                dg_dict[column.dg_id] = [column]
            else:
                dg_dict[column.dg_id].append(column)

    checkProfiles(experiment=experiment, profile_list=profile_list, dg_dict=dg_dict)

    if opensmoke:
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
