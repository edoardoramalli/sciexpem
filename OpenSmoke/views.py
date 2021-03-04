# Django Packages
from django.db import transaction
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from django.utils import timezone
from django import db
from django.http import JsonResponse
from django.contrib.auth.decorators import user_passes_test
from rest_framework.response import Response
from rest_framework.status import *
from django.core.exceptions import ObjectDoesNotExist

# Build-in Packages
import sys
import os
import json
from threading import Thread

# Local Packages
from SciExpeM import settings
import OpenSmoke
from .OpenSmoke import OpenSmokeParser, OpenSmokeExecutor
from SciExpeM.checkPermissionGroup import *
from ExperimentManager.Models import *

# Logging
import logging

logger = logging.getLogger("OpenSmoke")
logger.addHandler(OpenSmoke.apps.logger_handler)
logger.setLevel(logging.INFO)


@api_view(['POST'])
@user_in_group("EXECUTE")
def startSimulation(request):
    username = request.user.username
    params = request.data
    try:
        model_id = int(params['chemModel'])
        experiment_id = int(params['experiment'])
    except KeyError:
        return Response(status=HTTP_400_BAD_REQUEST,
                        data="updateElement: KeyError in HTTP parameters. Missing parameter.")

    query_exp = Experiment.objects.filter(id=experiment_id)
    if query_exp.exists():
        if not query_exp[0].status == 'verified':
            return Response(status=HTTP_400_BAD_REQUEST, data="startSimulation: Experiment not verified.")
    else:
        return Response(status=HTTP_400_BAD_REQUEST, data="startSimulation: Experiment not exist.")

    if not ChemModel.objects.filter(id=model_id).exists():
        return Response(status=HTTP_400_BAD_REQUEST, data="startSimulation: ChemModel not exist.")

    try:
        with transaction.atomic():
            query = Execution.objects.filter(experiment__id=experiment_id, chemModel__id=model_id)
            if query.exists():
                return Response(status=HTTP_200_OK, data="startSimulation: Execution already started.")
            else:
                try:
                    exp = query_exp[0]
                    model = ChemModel.objects.get(id=model_id)
                except ObjectDoesNotExist:
                    return Response(status=HTTP_400_BAD_REQUEST,
                                    data="startSimulation: ID Error.")

                new_exec = Execution(experiment=exp, chemModel=model,
                                     execution_start=timezone.localtime(),
                                     username=username)
                new_exec.save()

                solver = ExperimentInterpreter.objects.get(name=exp.experiment_interpreter).solver

                mapping_files = list(set([mapping.file for mapping in MappingInterpreter.objects.filter(
                    experiment_interpreter__name=exp.experiment_interpreter)]))

                Thread(target=OpenSmokeExecutor.execute,
                       args=(experiment_id, model_id, new_exec.id, solver, mapping_files)).start()

        return Response('startSimulation: Simulation started.', status=HTTP_200_OK)

    except Exception as err:
        err_type, value, traceback = sys.exc_info()
        logger.info(f'{username} - Error Simulate' + str(err_type.__name__) + " : " + str(value))

        return Response(status=HTTP_500_INTERNAL_SERVER_ERROR,
                        data="startSimulation: Generic error in start simulation. "
                             + str(err_type.__name__) + " : " + str(value))
    finally:
        db.close_old_connections()
        logger.info(f'{username} - Simulation Start')


@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def returnResult(request):
    params = json.loads(request.data['params'])

    exec_id = params['execution']
    file = params['file']
    file_type = params['file_type']

    execution = Execution.objects.filter(id=exec_id)

    execution.update(execution_end=timezone.localtime())

    dataframe, units = OpenSmokeParser.parse_output_string(file)

    list_header = list(dataframe)
    for header in list_header:
        data = ExecutionColumn(label=header,
                               units=units[header],
                               data=list(dataframe[header]),
                               execution=execution[0],
                               file_type=file_type)
        data.save()

    return Response(status=HTTP_200_OK)
