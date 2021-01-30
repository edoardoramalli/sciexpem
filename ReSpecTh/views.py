# Django Packages
from rest_framework.decorators import api_view
from django.http import JsonResponse
from django.contrib.auth.decorators import permission_required
from django.db import transaction


# Build-in Packages
import sys
import json

# Local Packages
import ReSpecTh

from ReSpecTh.OptimaPP import OptimaPP
from ExperimentManager import models

# Logging
import logging
logger = logging.getLogger("ReSpecTh")
logger.addHandler(ReSpecTh.apps.logger_handler)
logger.setLevel(logging.INFO)


@api_view(['POST'])
@permission_required('ReSpecTh.execute_optimapp', raise_exception=True)
def executeOptimaPP(request):
    user = request.user.username

    logger.info(f'{user} - Receive Execution OptimaPP Request')

    response = {'result': None, 'error': ''}

    query_execution = json.loads(request.data['query'])

    file = query_execution['file']

    result, error = OptimaPP.txt_to_xml(file)
    response['result'] = result
    response['error'] = error

    reply = JsonResponse(response)

    return reply


