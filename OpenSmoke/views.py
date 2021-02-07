# Django Packages
from django.db import transaction
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from django.utils import timezone
from django.http import JsonResponse
from django.contrib.auth.decorators import user_passes_test
from rest_framework.response import Response
from rest_framework.status import HTTP_500_INTERNAL_SERVER_ERROR, HTTP_200_OK

# Build-in Packages
import sys
import os
import json

# Local Packages
from SciExpeM import settings
import OpenSmoke
from .OpenSmoke import OpenSmokeParser, OpenSmokeExecutor
from SciExpeM.checkPermissionGroup import *
from ExperimentManager.models import *

# Logging
import logging

logger = logging.getLogger("OpenSmoke")
logger.addHandler(OpenSmoke.apps.logger_handler)
logger.setLevel(logging.INFO)


@api_view(['POST'])
@user_in_group("EXECUTE")
def startSimulation(request):
    user = request.user.username

    logger.info(f'{user} - Receive Execution Simulation Request')

    response = {'result': None, 'error': None}

    params = json.loads(request.data['params'])

    exp_id = params['experiment']
    chemModel_id = params['chemModel']

    if not Experiment.objects.filter(id=exp_id, status='verified').exists():
        return Response(status=HTTP_500_INTERNAL_SERVER_ERROR, data="Experiment not exist or not verified")

    try:
        with transaction.atomic():
            query = Execution.objects.filter(experiment__id=exp_id, chemModel__id=chemModel_id)
            if query.exists():
                return Response(status=HTTP_200_OK, data="Execution already started")
            else:
                from threading import Thread
                exp = Experiment.objects.get(id=exp_id)
                model = ChemModel.objects.get(id=chemModel_id)
                new_exec = Execution(experiment=exp, chemModel=model, execution_start=timezone.localtime())
                new_exec.save(username=user)
                Thread(target=OpenSmokeExecutor.execute, args=(exp_id, chemModel_id, new_exec.id)).start()
                return Response(status=HTTP_200_OK, data="Execution Started")

    except (OSError, TypeError):
        err_type, value, traceback = sys.exc_info()
        logger.info(f'{user} - Error Execution Simulation Request')
        return Response(status=HTTP_500_INTERNAL_SERVER_ERROR, data=str(err_type.__name__) + " : " + str(value))


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

    return Response(status=HTTP_200_OK, data="okokokok")
