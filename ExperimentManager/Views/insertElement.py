# Local import
import ExperimentManager.views as View
from ExperimentManager.Models import *
from ExperimentManager.exceptions import *
from ReSpecTh.OptimaPP import TranslatorOptimaPP, OptimaPP
from ReSpecTh.zenodo import *

# Django import
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from django.db import transaction, DatabaseError

import json


def checkExperiment(experiment):
    # ---> INITIAL SPECIES
    initial_species = experiment.initial_species.all()
    if len(initial_species) == 0:
        raise ExperimentConsistencyError('No initial species.')

    units_initial_species = set([])
    value_initial_species = []
    for specie in initial_species:
        units_initial_species.add(specie.units)
        value_initial_species.append(specie.value)

    if len(units_initial_species) != 1 or list(units_initial_species)[0] != 'mole fraction':
        raise ExperimentConsistencyError('Units of initial species are not equal or not expressed in mole fraction.')
    if sum(value_initial_species) != 1:
        raise ExperimentConsistencyError('The sum of mole fraction of the initial species is not 1.')

    # ---> DATA COLUMNS
    data_columns = experiment.data_columns.all()

    unique_column = ['temperature', 'pressure', 'volume', 'time',
                     'residence time', 'distance', 'ignition delay',
                     'laminar burning velocity']
    # TODO migliorare: ci può essere solo una x e questa deve essere unica
    uncertainty_list = []
    profile_list = []
    dg_dict = {}

    # TODO ignition def only for IDT. mandatory e poi non ci deve essere

    # TODO data group sperimentali tra loro consistenti

    # Sort Data Column in uncertainty, profile and data groups
    for column in data_columns:
        if column.uncertainty_kind:
            uncertainty_list.append(column)
        elif column.data_group_profile or column.dg_label in ['V-t history', 'p-t history', 'T-t history']:
            profile_list.append(column)
        else:
            if column.dg_id not in dg_dict:
                dg_dict[column.dg_id] = [column]
            else:
                dg_dict[column.dg_id].append(column)

    profile_type = [profile.dg_label for profile in profile_list]

    # Profiles must have the same type
    if len(set(profile_type)) > 1:
        raise ExperimentConsistencyError('Profile data groups have different types.')

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


class insertElement(View.ExperimentManagerBaseView):
    viewName = 'insertElement'
    paramsType = {'model_name': str, 'property_dict': str}
    required_groups = {'POST': ['WRITE']}

    def view_post(self, request):
        username = request.user.username

        supported_models = ['ExperimentInterpreter', 'ChemModel', 'Experiment']

        self.property_dict = json.loads(self.property_dict)

        if self.model_name not in supported_models:
            return Response(status=HTTP_400_BAD_REQUEST,
                            data=self.viewName + ": Model '{}' not supported yet.".format(self.model_name))

        try:
            model = eval(self.model_name)
        except NameError:
            return Response(status=HTTP_400_BAD_REQUEST,
                            data=self.viewName + ": NameError. Model '{}' not exist.".format(self.model_name))
        try:
            with transaction.atomic():
                try:
                    if self.model_name == 'Experiment':
                        bucket_url, publish_url, doi, deposition_id = reserved_doi()
                        update_description(title=doi,
                                           description=self.property_dict['file_paper']['references'],
                                           deposition_id=deposition_id)
                        self.property_dict['fileDOI'] = doi
                        list_objects = getattr(model, 'create' + self.model_name)(self.property_dict)
                except MandatoryFieldError as e:
                    return Response(self.viewName + ": " + str(e), status=HTTP_400_BAD_REQUEST)

                exp = None
                for obj in list_objects:
                    if isinstance(obj, Experiment):
                        obj.username = username
                        obj.save()
                        exp = obj
                    else:
                        obj.save()
                if exp is not None:
                    checkExperiment(exp)
                    txt = TranslatorOptimaPP.create_OptimaPP_txt(experiment=exp,
                                                                 data_groups=exp.data_columns.all(),
                                                                 initial_species=exp.initial_species.all(),
                                                                 common_properties=exp.common_properties.all(),
                                                                 file_paper=exp.file_paper)
                    try:
                        xml, error = OptimaPP.txt_to_xml(txt)

                        if error:
                            raise OptimaPPError(error)
                        else:
                            exp.xml_file = xml
                            exp.save()
                            upload_respecth(file_string=xml, doi=doi, bucket_url=bucket_url)
                            publish_doi(publish_url)

                    except FileNotFoundError:
                        raise OptimaPPError('Impossible to generate ReSpecTh file using OptimaPP.')
        except (ZenodoError, ExperimentConsistencyError, ConstraintFieldExperimentError, OptimaPPError) as e:
            delete_doi(deposition_id)
            return Response(self.viewName + ": " + str(e), status=HTTP_400_BAD_REQUEST)
        except DatabaseError as e:
            delete_doi(deposition_id)
            return Response(self.viewName + ": " + str(e.__cause__), status=HTTP_400_BAD_REQUEST)
        except Exception as e:
            delete_doi(deposition_id)
            raise e

        return Response("{} element inserted successfully.".format(self.model_name), status=HTTP_200_OK)
