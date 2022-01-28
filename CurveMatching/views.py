# Django Packages
from rest_framework.decorators import api_view
from django.http import JsonResponse
from django.contrib.auth.decorators import user_passes_test
from rest_framework.response import Response
from rest_framework.status import *

# Build-in Packages
import sys
import os
from threading import Thread
import json

# Local Packages
import CurveMatching
from SciExpeM.checkPermissionGroup import user_in_group
from CurveMatching.CurveMatching import blocking_execute_cm, curveMatchingExecution, running_cm
import ExperimentManager.Models as Models


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

        uncertainty = json.loads(params['uncertainty'])
        configuration = json.loads(params['configuration'])

        result = blocking_execute_cm(x_exp=x_exp, y_exp=y_exp,
                                     x_sim=x_sim, y_sim=y_sim,
                                     uncertainty=uncertainty, **configuration)

        return Response(json.dumps(result), status=HTTP_200_OK)

    except FileNotFoundError as e:
        return Response(status=HTTP_500_INTERNAL_SERVER_ERROR, data="executeCurveMatching: " + str(e))

    except OSError as e:
        return Response(status=HTTP_500_INTERNAL_SERVER_ERROR, data="executeCurveMatching: " + str(e))

    except KeyError:
        return Response(status=HTTP_400_BAD_REQUEST,
                        data="executeCurveMatching: KeyError in HTTP parameters. Missing parameter.")
    except Exception as e:
        err_type, value, traceback = sys.exc_info()

        return Response(status=HTTP_500_INTERNAL_SERVER_ERROR,
                        data="executeCurveMatching: Generic error. "
                             + str(err_type.__name__) + " : " + str(value))


@api_view(['POST'])
def curveMatchingIsRunning(request):
    return Response(json.dumps(running_cm), status=HTTP_200_OK)


@api_view(['POST'])
@user_in_group("EXECUTE")
def createUpdateExecutionCurveMatching(request):
    params = dict(request.data)
    try:
        execution_id = int(params['execution_id'])

        execution = Models.Execution.objects.filter(id=execution_id)

        if not execution.exists():
            return Response(status=HTTP_400_BAD_REQUEST,
                            data="createUpdateExecutionCurveMatching: Execution not found.")
        else:
            execution = execution[0]

        if execution.execution_end is None or execution.execution_error is not None:
            return Response(status=HTTP_400_BAD_REQUEST,
                            data="createUpdateExecutionCurveMatching: Execution ({}) not ended or with errors.".format(execution_id))
        if len(execution.execution_columns.all()) <= 1:
            return Response(status=HTTP_400_BAD_REQUEST,
                            data="createUpdateExecutionCurveMatching: Execution ({}) not enough columns.".format(execution_id))
        if any([ll > 100 for ll in [len(c.data) for c in execution.execution_columns.all()]]):
            return Response(status=HTTP_400_BAD_REQUEST,
                            data="createUpdateExecutionCurveMatching: Execution ({}) with too many data.".format(execution_id))

        Thread(target=curveMatchingExecution, args=(execution,)).start()
        return Response(status=HTTP_200_OK)


    except FileNotFoundError as e:
        return Response(status=HTTP_500_INTERNAL_SERVER_ERROR, data="createUpdateExecutionCurveMatching: " + str(e))

    except OSError as e:
        return Response(status=HTTP_500_INTERNAL_SERVER_ERROR, data="createUpdateExecutionCurveMatching: " + str(e))

    except KeyError:
        return Response(status=HTTP_400_BAD_REQUEST,
                        data="createUpdateExecutionCurveMatching: KeyError in HTTP parameters. Missing parameter.")
    except Exception as e:
        err_type, value, traceback = sys.exc_info()

        return Response(status=HTTP_500_INTERNAL_SERVER_ERROR,
                        data="createUpdateExecutionCurveMatching: Generic error. "
                             + str(err_type.__name__) + " : " + str(value))
