from django.http import HttpResponse
from django.http import JsonResponse
from django.shortcuts import render
from ExperimentManager.serializers import *

from rest_framework import generics
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from rest_framework.permissions import IsAuthenticated
import json
from django.db import transaction

from ExperimentManager.models import *

from django.contrib.auth.decorators import permission_required

import sys

from ExperimentManager import QSerializer
from django.core.exceptions import FieldError

import ExperimentManager

# START LOGGER
# Logging
import logging
logger = logging.getLogger("ExperimentManager")
logger.addHandler(ExperimentManager.apps.logger_handler)
logger.setLevel(logging.INFO)


# END LOGGER

# print("How print to console during runserver", file=sys.stderr)

# START FILTER API


def schemaFilter(request, model, serializer):
    user = request.user.username

    logger.info(f'{user} - Receive Filter %s Query', model.__name__)

    response = {'result': None, 'error': None}
    q_serializer = QSerializer.QSerializer()
    parameters = request.query_params
    query = q_serializer.loads(parameters['query'])

    try:
        result = []
        query_set = model.objects.filter(query)
        for query_result in query_set:
            result.append(serializer(query_result).data)

        response['result'] = result
    except FieldError:
        err_type, value, traceback = sys.exc_info()
        response['error'] = "SERVER - " + str(err_type.__name__) + " : " + str(value)
        logger.info(f'{user} - Error Filter %s Query %s', model.__name__, query)

    reply = JsonResponse(response)
    dimension = round(sys.getsizeof(response['result']) / 1000.0, 3)
    logger.info(f'{user} - Send Filter %s Query %f KB', model.__name__, dimension)

    return reply


@api_view(['GET'])
@permission_required(('ExperimentManager.view_experiment',
                      'ExperimentManager.view_commonproperty',
                      'ExperimentManager.view_datacolumn',
                      'ExperimentManager.view_filepaper',
                      'ExperimentManager.view_initialspecie'), raise_exception=True)
def filterExperiment(request):
    return schemaFilter(request=request, model=Experiment, serializer=ExperimentSerializerAPI)


@api_view(['GET'])
@permission_required('ExperimentManager.view_chemmodel', raise_exception=True)
def filterChemModel(request):
    return schemaFilter(request=request, model=ChemModel, serializer=ChemModelSerializerAPI)


@api_view(['GET'])
@permission_required(('ExperimentManager.view_chemmodel',
                      'ExperimentManager.view_experiment',
                      'ExperimentManager.view_commonproperty',
                      'ExperimentManager.view_datacolumn',
                      'ExperimentManager.view_filepaper',
                      'ExperimentManager.view_initialspecie',
                      'ExperimentManager.view_execution',
                      'ExperimentManager.view_executioncolumn'), raise_exception=True)
def filterExecution(request):
    return schemaFilter(request=request, model=Execution, serializer=ExecutionSerializerAPI)


@api_view(['GET'])
@permission_required(('ExperimentManager.view_chemmodel',
                      'ExperimentManager.view_experiment',
                      'ExperimentManager.view_commonproperty',
                      'ExperimentManager.view_datacolumn',
                      'ExperimentManager.view_filepaper',
                      'ExperimentManager.view_initialspecie',
                      'ExperimentManager.view_execution',
                      'ExperimentManager.view_executioncolumn',
                      'ExperimentManager.view_curvematchingresult'), raise_exception=True)
def filterCurveMatchingResult(request):
    return schemaFilter(request=request, model=CurveMatchingResult, serializer=CurveMatchingResultSerializerAPI)

# END FILTER API


# START INSERT API

def check_levels(field):
    if "__" in field:
        return True
    else:
        return False

def split_levels(object_dict, field):
    split_field = field.split("__")
    first = split_field[0]
    second = split_field[1]
    return {field: object_dict[first][second]}


def schemaInsert(request, model, unique, main="", dependencies=None):
    if dependencies is None:
        dependencies = []

    username = request.user.username

    logger.info(f'{username} - Insert %s Query', model.__name__)

    response = {'result': None, 'error': ""}

    parameters = request.query_params
    object_dict = json.loads(parameters['object'])

    unique_fields_dict = {field: object_dict[field]  for field in unique}

    dependencies_dict = {dependency: object_dict[dependency] for dependency in dependencies}

    main_object_dict = dict(object_dict)
    for dependency in dependencies:
        main_object_dict.pop(dependency, None)

    if model.objects.filter(**unique_fields_dict).exists():
        response['result'] = "DUPLICATE"
    else:
        try:
            with transaction.atomic():
                main_obj = model(**main_object_dict)
                main_obj.save(username=username)
                logger.info(f'{username} - Insert %s Object', main_obj.__class__.__name__)
                for dependency_list in dependencies_dict:
                    if not type(dependencies_dict[dependency_list]) == list:
                        outer = [dependencies_dict[dependency_list]]
                    else:
                        outer = dependencies_dict[dependency_list]
                    for element_dict in outer:
                        element_dict[main] = main_obj
                        tmp_obj = eval(dependency_list)(**element_dict)
                        tmp_obj.save(username=username)
                        logger.info(f'{username} - Insert %s Object', tmp_obj.__class__.__name__)

                response['result'] = "OK"
        except Exception:
            err_type, value, traceback = sys.exc_info()
            response['error'] += "SERVER - " + str(err_type.__name__) + " : " + str(value)
            logger.info(f'{username} - Error Insert %s Query', model.__name__)

    return JsonResponse(response)


@api_view(['GET'])
@permission_required(('ExperimentManager.add_experiment',
                      'ExperimentManager.add_commonproperty',
                      'ExperimentManager.add_datacolumn',
                      'ExperimentManager.add_filepaper',
                      'ExperimentManager.add_initialspecie'), raise_exception=True)
def insertExperiment(request):
    return schemaInsert(request=request, model=Experiment, unique=['fileDOI'], main="experiment",
                        dependencies=["FilePaper", "DataColumn", "CommonProperty", "InitialSpecie"])


@api_view(['GET'])
@permission_required('ExperimentManager.add_chemmodel', raise_exception=True)
def insertChemModel(request):
    return schemaInsert(request=request, model=ChemModel, unique=['name'], dependencies=[])


@api_view(['GET'])
@permission_required('ExperimentManager.add_experiment', raise_exception=True)
def insertExecution(request):
    username = request.user.username

    logger.info(f'{username} - Insert %s Query', Execution.__name__)

    response = {'result': None, 'error': ""}

    parameters = request.query_params
    object_dict = json.loads(parameters['object'])

    # An Execution is unique if doesn't exist the pair chemModel-Experiment in Execution Table
    chemModel_name = object_dict['chemModel']['name']
    experiment_DOI = object_dict['experiment']['fileDOI']

    # Check if chemModel Exist and get it
    try:
        chemModel = ChemModel.objects.get(name=chemModel_name)
    except ChemModel.DoesNotExist:
        response['error'] += "SERVER: " + "Does not exist a model with name " + chemModel_name
        logger.info(f"{username} - Error Insert %s Query. ChemModel %s doesn't exist",
                     Execution.__name__, chemModel_name)
        return JsonResponse(response)

    # Check if Experiment Exist and get it
    try:
        experiment = Experiment.objects.get(fileDOI=experiment_DOI)
    except Experiment.DoesNotExist:
        response['error'] += "SERVER: " + "Does not exist a model with name " + experiment_DOI
        logger.info(f"{username} - Error Insert %s Query. Experiment %s doesn't exist",
                     Execution.__name__, experiment_DOI)
        return JsonResponse(response)

    if Execution.objects.filter(chemModel=chemModel, experiment=experiment).exists():
        response['result'] = "DUPLICATE"
    else:
        try:
            with transaction.atomic():

                execution = Execution(chemModel=chemModel,
                                      experiment=experiment,
                                      execution_start=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                      execution_end=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                execution.save(username=username)

                execution_columns = object_dict['ExecutionColumn']
                for execution_column in execution_columns:
                    execution_column['execution'] = execution
                    exec_column = ExecutionColumn(**execution_column)
                    exec_column.save(username=username)

                response['result'] = "OK"

        except Exception:
            err_type, value, traceback = sys.exc_info()
            response['error'] += "SERVER - " + str(err_type.__name__) + " : " + str(value)
            logger.info(f'{username} - Error Insert %s Query', Execution.__name__)

    return JsonResponse(response)


