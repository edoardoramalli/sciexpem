# Django Packages
from rest_framework.decorators import api_view
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
import CurveMatching
from SciExpeM.checkPermissionGroup import *

# Logging
import logging
logger = logging.getLogger("CurveMatching")
logger.addHandler(CurveMatching.apps.logger_handler)
logger.setLevel(logging.INFO)


@api_view(['POST'])
@user_in_group("EXECUTE")
def executeCurveMatchingBase(request):
    user = request.user.username

    logger.info(f'{user} - Receive Execution Curve Matching Request')

    # response = {'result': None, 'error': None}
    #
    # query_execution = json.loads(request.data['query'])

    x = [1, 2, 3, 4, 5]
    y = [1, 2, 3, 4, 5]

    path_executable_cm = os.path.join(settings.BASE_DIR, CurveMatching.__name__, "CurveMatchingPython.o")

    path_executable_cm = '/home/eramalli/CurveMatchingPython/CurveMatchingPython/CurveMatchingPython.o'

    score, error = CurveMatching.CurveMatchingPython.CurveMatching.execute(
        x_exp=x,
        y_exp=y,
        x_sim=x,
        y_sim=y,
        library_path=path_executable_cm)

    print(score, error)

    return Response(status=HTTP_200_OK, data="Experiment verified successfully")

    # try:
    #     path_executable_cm = os.path.join(settings.BASE_DIR, CurveMatching.__name__, "CurveMatchingPython.o")
    #     cm = CurveMatching.CurveMatchingPython.CurveMatchingPython(library_path=path_executable_cm)
    #     index, error = cm.execute(**query_execution)
    #     response['result'] = (index, error)
    #     # return Response(status=HTTP_500_INTERNAL_SERVER_ERROR, data="Experiment not exist or not verified")
    # except (OSError, TypeError):
    #     err_type, value, traceback = sys.exc_info()
    #     response['error'] = "SERVER - " + str(err_type.__name__) + " : " + str(value)
    #     logger.info(f'{user} - Error Execution Curve Matching Request')
    #
    # reply = JsonResponse(response)
    # dimension = round(sys.getsizeof(response['result']) / 1000.0, 3)
    # logger.info(f'{user} - Send Execution Curve Matching Request  %f KB', dimension)
    #
    # return reply
