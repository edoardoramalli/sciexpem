# Django Packages
from rest_framework.decorators import api_view
from django.http import JsonResponse
from django.contrib.auth.decorators import permission_required

# Build-in Packages
import sys
import os
import json

# Local Packages
from SciExpeM import settings
import CurveMatching

# Logging
import logging
logger = logging.getLogger("CurveMatching")
logger.addHandler(CurveMatching.apps.logger_handler)
logger.setLevel(logging.INFO)


@api_view(['POST'])
@permission_required('CurveMatching.execute_curve_matching', raise_exception=True)
def executeCurveMatchingBase(request):
    user = request.user.username

    logger.info(f'{user} - Receive Execution Curve Matching Request')

    response = {'result': None, 'error': None}

    query_execution = json.loads(request.data['query'])

    try:
        path_executable_cm = os.path.join(settings.BASE_DIR, CurveMatching.__name__, "CurveMatchingPython.o")
        cm = CurveMatching.CurveMatchingPython.CurveMatchingPython(library_path=path_executable_cm)
        index, error = cm.execute(**query_execution)
        response['result'] = (index, error)
    except (OSError, TypeError):
        err_type, value, traceback = sys.exc_info()
        response['error'] = "SERVER - " + str(err_type.__name__) + " : " + str(value)
        logger.info(f'{user} - Error Execution Curve Matching Request')

    reply = JsonResponse(response)
    dimension = round(sys.getsizeof(response['result']) / 1000.0, 3)
    logger.info(f'{user} - Send Execution Curve Matching Request  %f KB', dimension)

    return reply


# @api_view(['GET'])
# @permission_required('CurveMatching.execute_curve_matching', raise_exception=True)
# def prova(request):
#     response = {'result': None, 'error': None}
#     parameters = request.query_params
#     query_execution = json.loads(parameters['query'])
#
#     import time
#     time.sleep(20)
#
#     response['result'] = "EDO"
#
#     reply = JsonResponse(response)
#     return reply