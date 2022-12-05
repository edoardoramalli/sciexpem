# Django Packages
from rest_framework.decorators import api_view
from django.http import JsonResponse
from django.contrib.auth.decorators import permission_required
from django.db import transaction
from rest_framework.status import HTTP_500_INTERNAL_SERVER_ERROR, HTTP_200_OK, HTTP_400_BAD_REQUEST
from rest_framework.response import Response


# Build-in Packages
import sys
import json
from pint import UndefinedUnitError, DimensionalityError

# Local Packages
import ReSpecTh
from SciExpeM.checkPermissionGroup import user_in_group
import ExperimentManager.Models as Models
from ReSpecTh.units import convert_list
from ReSpecTh.GetReactor import GetReactor

# Logging
import logging
from ReSpecTh.OptimaPP import TranslatorOptimaPP, OptimaPP
logger = logging.getLogger("ReSpecTh")
logger.addHandler(ReSpecTh.apps.logger_handler)
logger.setLevel(logging.INFO)

@api_view(['POST'])
def executeOptimaPPExperiment(request):
    params = request.data

    try:
        id = int(params['exp_id'])

        exp = Models.Experiment.objects.get(id=id)

        txt = TranslatorOptimaPP.create_OptimaPP_txt(experiment=exp,
                                                     data_groups=exp.data_columns.all(),
                                                     initial_species=exp.initial_species.all(),
                                                     common_properties=exp.common_properties.all(),
                                                     file_paper=exp.file_paper)

        result, error = OptimaPP.txt_to_xml(txt)

        if result:
            return Response(data=result, status=HTTP_200_OK)
        else:
            return Response(data=error, status=HTTP_400_BAD_REQUEST)

    except KeyError:
        return Response(status=HTTP_400_BAD_REQUEST,
                        data="executeOptimaPPExperiment: KeyError in HTTP parameters. Missing parameter.")

    except Exception:
        err_type, value, traceback = sys.exc_info()
        return Response(status=HTTP_500_INTERNAL_SERVER_ERROR,
                        data="executeOptimaPPExperiment: Generic error. " + str(err_type.__name__) + " : " + str(value))


@api_view(['POST'])
def createTxtOptimaPP(request):
    params = request.data

    try:
        exp_id = int(params['exp_id'])

        exp = Models.Experiment.objects.get(id=exp_id)

        txt = TranslatorOptimaPP.create_OptimaPP_txt(experiment=exp,
                                                     data_groups=exp.data_columns.all(),
                                                     initial_species=exp.initial_species.all(),
                                                     common_properties=exp.common_properties.all(),
                                                     file_paper=exp.file_paper)

        return Response(data=txt, status=HTTP_200_OK)

    except KeyError:
        return Response(status=HTTP_400_BAD_REQUEST,
                        data="createTxtOptimaPP: KeyError in HTTP parameters. Missing parameter.")


    except Exception:
        err_type, value, traceback = sys.exc_info()
        return Response(status=HTTP_500_INTERNAL_SERVER_ERROR,
                        data="createTxtOptimaPP: Generic error. " + str(err_type.__name__) + " : " + str(value))




@api_view(['POST'])
def executeOptimaPP(request):
    params = request.data

    try:
        text = params['text']
        result, error = OptimaPP.txt_to_xml(text)

        if result:
            return Response(data=result, status=HTTP_200_OK)
        else:
            return Response(data=error, status=HTTP_400_BAD_REQUEST)

    except KeyError:
        return Response(status=HTTP_400_BAD_REQUEST,
                        data="convertList: KeyError in HTTP parameters. Missing parameter.")


    except Exception:
        err_type, value, traceback = sys.exc_info()
        return Response(status=HTTP_500_INTERNAL_SERVER_ERROR,
                        data="convertList: Generic error converting list. " + str(err_type.__name__) + " : " + str(value))



@api_view(['POST'])
@user_in_group("READ")
def convertList(request):
    params = dict(request.data)
    try:
        my_list = params['list']
        unit = params['unit'][0]
        desired_unit = params['desired_unit'][0]
    except KeyError:
        return Response(status=HTTP_400_BAD_REQUEST,
                        data="convertList: KeyError in HTTP parameters. Missing parameter.")

    try:
        result = convert_list(my_list=my_list, unit=unit, desired_unit=desired_unit)
    except UndefinedUnitError:
        return Response(status=HTTP_400_BAD_REQUEST,
                        data='convertList: Unit not defined.')
    except DimensionalityError:
        return Response(status=HTTP_400_BAD_REQUEST,
                        data="convertList: It is not possible to convert '{}' to '{}'.".format(unit, desired_unit))
    except Exception:
        err_type, value, traceback = sys.exc_info()
        return Response(status=HTTP_500_INTERNAL_SERVER_ERROR,
                        data="convertList: Generic error converting list. " + str(err_type.__name__) + " : " + str(value))

    return Response(result, status=HTTP_200_OK)


@api_view(['POST'])
# @user_in_group("READ")
def getReactors(request):
    username = request.user.username
    params = dict(request.data)
    try:
        experiment_type = params['experiment_type'][0]
    except KeyError:
        return Response(status=HTTP_400_BAD_REQUEST,
                        data="getReactors: KeyError in HTTP parameters. Missing parameter.")

    try:
        mapper = GetReactor()
        reactors = mapper.getMapping(experiment_type)  # TODO in teoria si deve lanciare exceptions se exp_tupe non esiste
    except Exception as err:
        err_type, value, traceback = sys.exc_info()
        logger.info(f'{username} - Error getReactors. ' + str(err_type.__name__) + " : " + str(value))
        return Response(status=HTTP_500_INTERNAL_SERVER_ERROR,
                        data="getReactors: Generic error updating Experiment. "
                             + str(err_type.__name__) + " : " + str(value))

    return Response(reactors, status=HTTP_200_OK)


