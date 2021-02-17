# Django Packages
from rest_framework.decorators import api_view
from django.http import JsonResponse
from django.contrib.auth.decorators import user_passes_test
from rest_framework.response import Response
from rest_framework.status import *

# Build-in Packages
import sys
import os
import json

# Local Packages
import CurveMatching
from SciExpeM.checkPermissionGroup import user_in_group
from CurveMatching.CurveMatching import executeCurveMatching as ExeCM

# Logging
import logging
logger = logging.getLogger("CurveMatching")
logger.addHandler(CurveMatching.apps.logger_handler)
logger.setLevel(logging.INFO)


@api_view(['POST'])
@user_in_group("EXECUTE")
def executeCurveMatching(request):
    username = request.user.username
    params = dict(request.data)
    try:
        x_sim = params['x_sim']
        y_sim = params['y_sim']
        x_exp = params['x_exp']
        y_exp = params['y_exp']
        uncertainty = json.loads(params['uncertainty'][0])
        configuration = json.loads(params['configuration'][0])

        score, error = ExeCM(x_exp=x_exp, y_exp=y_exp,
                             x_sim=x_sim, y_sim=y_sim,
                             uncertainty=uncertainty, **configuration)

        logger.info(f'{username} - Simulation Start')
        return Response(json.dumps({'score': score, 'error': error}), status=HTTP_200_OK)

    except FileNotFoundError as e:
        return Response(status=HTTP_500_INTERNAL_SERVER_ERROR, data="executeCurveMatching: " + str(e))

    except OSError as e:
        return Response(status=HTTP_500_INTERNAL_SERVER_ERROR, data="executeCurveMatching: " + str(e))

    except KeyError:
        return Response(status=HTTP_400_BAD_REQUEST,
                        data="executeCurveMatching: KeyError in HTTP parameters. Missing parameter.")
    except Exception as e:
        err_type, value, traceback = sys.exc_info()
        logger.info(f'{username} - Error CurveMatching' + str(err_type.__name__) + " : " + str(value))

        return Response(status=HTTP_500_INTERNAL_SERVER_ERROR,
                        data="executeCurveMatching: Generic error. "
                             + str(err_type.__name__) + " : " + str(value))
