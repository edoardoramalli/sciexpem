# Import django
from django.http import HttpResponse, JsonResponse
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from django.db import transaction, IntegrityError, DatabaseError
from django.core.exceptions import FieldError
from rest_framework.status import *
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist

# Import build-in
import os
import json
import sys

# Local Packages
from SciExpeM import settings
from decimal import Decimal

from ExperimentManager.serializerAPI import *


# Import Local
from ExperimentManager.serializers import *
from ExperimentManager.models import *
from ExperimentManager.Models import *
from ExperimentManager import QSerializer
from ExperimentManager.exceptions import *
import ExperimentManager
import CurveMatching
from OpenSmoke.OpenSmoke import OpenSmokeParser
from ReSpecTh.ReSpecThParser import ReSpecThParser

from SciExpeM.checkPermissionGroup import user_in_group

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
@user_in_group("READ")
def filterExperiment(request):
    return schemaFilter(request=request, model=Experiment, serializer=ExperimentSerializerAPI)


@api_view(['GET'])
@user_in_group("READ")
def filterChemModel(request):
    return schemaFilter(request=request, model=ChemModel, serializer=ChemModelSerializerAPI)


@api_view(['GET'])
@user_in_group("READ")
def filterExecution(request):
    return schemaFilter(request=request, model=Execution, serializer=ExecutionSerializerAPI)


@api_view(['GET'])
@user_in_group("READ")
def filterCurveMatchingResult(request):
    return schemaFilter(request=request, model=CurveMatchingResult, serializer=CurveMatchingResultSerializerAPI)


# END FILTER API


# START INSERT API


def schemaInsert(request, model, unique, main="", dependencies=None):
    if dependencies is None:
        dependencies = []

    username = request.user.username

    logger.info(f'{username} - Insert %s Query', model.__name__)

    response = {'result': None, 'error': ""}

    object_dict = json.loads(request.data['object'])

    unique_fields_dict = {field: object_dict[field] for field in unique}

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


@api_view(['POST'])
@user_in_group("WRITE")
def insertExperiment(request):
    return schemaInsert(request=request, model=Experiment, unique=['fileDOI'], main="experiment",
                        dependencies=["FilePaper", "DataColumn", "CommonProperty", "InitialSpecie"])


@api_view(['POST'])
@user_in_group("WRITE")
def insertChemModel(request):
    return schemaInsert(request=request, model=ChemModel, unique=['name'], dependencies=[])


@api_view(['POST'])
@user_in_group("WRITE")
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
                                      execution_start=timezone.now(),
                                      execution_end=timezone.now())
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


@api_view(['POST'])
@user_in_group("UPDATE")
def insertOSFile(request, pk):
    exp = Experiment.objects.filter(pk=pk)
    file_upload_os = request.data['params']['values']['os_input_file'][0]['response']['data']
    exp.update(os_input_file=file_upload_os)
    return HttpResponse(status=200)


@api_view(['POST'])
@user_in_group("UPDATE")
def insertOSFileAPI(request):
    params = json.loads(request.data['params'])
    exp_id = params.get('experiment')
    osFile = params.get('osFile')
    exp = Experiment.objects.filter(id=exp_id)
    osFile = OpenSmokeParser.parse_input_string(osFile)
    exp.update(os_input_file=osFile)
    return Response(status=HTTP_200_OK, data="OS File added successfully")


@api_view(['POST'])
@user_in_group("WRITE")
def loadXMLExperiment(request):
    username = request.user.username

    logger.info(f'{username} - Insert Experiment from XML file')

    response = {'result': None, 'error': ''}

    query_execution = json.loads(request.data['query'])

    file = query_execution['file']


    try:

        response = from_text_to_experiment(username, file)
    except Exception as err:
        err_type, value, traceback = sys.exc_info()
        response['error'] += "SERVER - " + str(err_type.__name__) + " : " + str(value)
        logger.info(f'{username} - Error Insert Experiment Query')

    reply = JsonResponse(response)

    return reply


@api_view(['POST'])
# @user_in_group("WRITE")
def loadXMLExperimentSimple(request):
    # username = request.user.username
    username = 'root'
    logger.info(f'{username} - Insert Experiment from XML file')

    text_file = request.data['data'].file.read().decode("utf8")

    response = from_text_to_experiment(username, text_file)

    if response['error']:
        return HttpResponse(content="Error Uploading Experiment", status=500)
    elif response['result'] == "DUPLICATE":
        return HttpResponse(content="Error Duplicate Experiment", status=500)
    else:
        return HttpResponse(status=200)

# END INSERT

# START DELETE

@api_view(['GET'])
def deleteExperiment(request, pk):
    if not request.user.is_authenticated:
        return HttpResponse(status=403)

    owner = LoggerModel.objects.get(model_name="Experiment", pk_model=pk).username

    if owner != request.user.username:
        if not(request.user.is_superuser | request.user.groups.filter(name="DELETE").exists()):
            return HttpResponse(status=403)
    try:
        Experiment.objects.get(pk=pk).delete()
        log = LoggerModel(model_name="Experiment",
                          pk_model=pk,
                          username=request.user.username,
                          action="DELETE",
                          date=timezone.now())
        log.save()
    except Exception:
        return HttpResponse(content="Error Deleting Experiment", status=500)
    return HttpResponse(status=200)


# END DELETE

# START VALIDATE

@api_view(['POST'])
@user_in_group("VALIDATE")
def verifyExperiment(request):
    username = request.user.username
    params = dict(request.data)
    try:
        status = params['status'][0]
        exp_id = params['id'][0]
    except KeyError:
        return Response(status=HTTP_400_BAD_REQUEST,
                        data="verifyExperiment: KeyError in HTTP parameters. Missing parameter.")
    try:
        exp = Experiment.objects.get(pk=exp_id)
        exp.status = status
        exp.save(username=username)
    except ConstraintFieldExperimentError as e:
        return Response(status=HTTP_400_BAD_REQUEST,  data="verifyExperiment: " + str(e))
    except Exception as err:
        err_type, value, traceback = sys.exc_info()
        logger.info(f'{username} - Error Verify Experiment' + str(err_type.__name__) + " : " + str(value))
        return Response(status=HTTP_500_INTERNAL_SERVER_ERROR,
                        data="verifyExperiment: Generic error in experiment verification."
                             + str(err_type.__name__) + " : " + str(value))
    return Response(status=HTTP_200_OK, data="Experiment verified successfully.")



@api_view(['POST'])
@user_in_group("VALIDATE")
def validateExperiment(request):
    params = request.data['params']
    exp_id = params.get('exp_id')
    phi_inf = params.get('phi_inf')
    phi_sup = params.get('phi_sup')
    t_inf = params.get('t_inf')
    t_sup = params.get('t_sup')
    p_inf = params.get('p_inf')
    p_sup = params.get('p_sup')
    fuels = params.get('fuels')

    exp = Experiment.objects.filter(pk=exp_id)
    c_exp = exp[0]

    if not c_exp.os_input_file:
        return Response(status=HTTP_500_INTERNAL_SERVER_ERROR, data="Missing OS input file")
    if not c_exp.experiment_classifier:
        return Response(status=HTTP_500_INTERNAL_SERVER_ERROR, data="Experiment not managed")

    exp.update(
        status='valid',
        phi_inf=phi_inf,
        phi_sup=phi_sup,
        t_inf=t_inf,
        t_sup=t_sup,
        p_inf=p_inf,
        p_sup=p_sup,
        fuels=fuels
    )

    return HttpResponse(status=200)

# END VALIDATE


# START  NEW
@api_view(['POST'])
@user_in_group("READ")
def filterDataBase(request):
    username = request.user.username
    params = dict(request.data)
    try:
        model_name = params['model'][0]
        query_str = params['query'][0]
    except KeyError:
        return Response(status=HTTP_400_BAD_REQUEST,
                        data="filterDataBase: KeyError in HTTP parameters. Missing parameter.")

    try:
        model = eval(model_name)
    except NameError:
        return Response(status=HTTP_400_BAD_REQUEST,
                        data="filterDataBase: NameError. Model '{}' not exist.".format(model_name))

    q_serializer = QSerializer.QSerializer()
    query = q_serializer.loads(query_str)


    try:
        result = []
        query_set = model.objects.filter(query)

        serializer = eval('New' + model_name + 'SerializerAPI')
        for query_result in query_set:
            result.append(serializer(query_result).data)

        return Response(result, status=HTTP_200_OK)
    except FieldError:
        return Response(status=HTTP_400_BAD_REQUEST,
                        data="filterDataBase: FieldError. Query '{}' is incorrect for model '{}'."
                        .format(query, model_name))
    except Exception as err:
        err_type, value, traceback = sys.exc_info()
        logger.info(f'{username} - Error Filter Database' + str(err_type.__name__) + " : " + str(value))
        return Response(status=HTTP_500_INTERNAL_SERVER_ERROR,
                        data="filterDataBase: Generic error filtering the database. "
                             + str(err_type.__name__) + " : " + str(value))


@api_view(['POST'])
@user_in_group("READ")
def requestProperty(request):
    username = request.user.username
    params = dict(request.data)
    try:
        model_name = params['model'][0]
        element_id = int(params['id'][0])
        property_name = params['property'][0]
    except KeyError:
        return Response(status=HTTP_400_BAD_REQUEST,
                        data="requestProperty: KeyError in HTTP parameters. Missing parameter.")

    try:
        model = eval(model_name)
    except NameError:
        return Response(status=HTTP_400_BAD_REQUEST,
                        data="requestProperty: NameError. Model '{}' not exist.".format(model_name))

    try:
        element = model.objects.get(id=element_id)
        property_object = getattr(element, property_name)
        property_object_type = type(property_object)

        if property_object is None:
            return Response('', status=HTTP_200_OK)
        elif property_object is []:
            return Response('', status=HTTP_200_OK)
        elif property_object_type is str:
            return Response(property_object, status=HTTP_200_OK)
        elif property_object_type is Decimal:
            return Response(property_object, status=HTTP_200_OK)
        elif property_object_type is int:
            return Response(property_object, status=HTTP_200_OK)
        elif property_object_type is bool:
            return Response(property_object, status=HTTP_200_OK)
        elif property_object_type is list:
            test = property_object[0]
            if type(test) is Decimal:
                return Response(json.dumps([float(x) for x in property_object]), status=HTTP_200_OK)
            elif type(test) is str:
                return Response(json.dumps([str(x) for x in property_object]), status=HTTP_200_OK)
            else:
                return Response(status=HTTP_400_BAD_REQUEST,
                                data="requestProperty: Data type List not supported.")
        else:
            return Response(status=HTTP_400_BAD_REQUEST,
                            data="requestProperty: Data type not supported.")
    except AttributeError:
        return Response("requestProperty: AttributeError. Property '{}' not exist for model '{}'.".format(property_name, model_name),
                        status=HTTP_400_BAD_REQUEST)
    except Exception as err:
        err_type, value, traceback = sys.exc_info()
        logger.info(f'{username} - Error Request Property' + str(err_type.__name__) + " : " + str(value))
        return Response(status=HTTP_500_INTERNAL_SERVER_ERROR,
                        data="requestProperty: Generic error requesting property. "
                             + str(err_type.__name__) + " : " + str(value))


# START  NEW
@api_view(['POST'])
@user_in_group("WRITE")
def loadExperiment(request):
    username = request.user.username
    params = dict(request.data)
    try:
        format_name = params['format_file'][0]
        file_text = params['file_text'][0]
    except KeyError:
        return Response(status=HTTP_400_BAD_REQUEST,
                        data="loadExperiment: KeyError in HTTP parameters. Missing parameter.")

    if format_name == 'XML_ReSpecTh':
        try:
            respecth_text_to_experiment(username, file_text)
        except DuplicateExperimentError:
            return Response(status=HTTP_400_BAD_REQUEST,
                            data="loadExperiment: Duplicated Experiment.")
        except MandatoryFieldExperimentError as e:
            return Response(status=HTTP_400_BAD_REQUEST,
                            data="loadExperiment: " + str(e))
        except ConstraintFieldExperimentError as e:
            return Response(status=HTTP_400_BAD_REQUEST,
                            data="loadExperiment: " + str(e))
        except Exception as err:
            err_type, value, traceback = sys.exc_info()
            logger.info(f'{username} - Error Load Experiment from file' + str(err_type.__name__) + " : " + str(value))
            return Response(status=HTTP_500_INTERNAL_SERVER_ERROR,
                            data="loadExperiment: Generic error inserting Experiment from file. "
                                 + str(err_type.__name__) + " : " + str(value))

    else:
        return Response(status=HTTP_400_BAD_REQUEST,
                        data="loadExperiment: Format Not supported.")

    logger.info(f'{username} - Insert Experiment from XML file')
    return Response("Experiment inserted successfully.", status=HTTP_200_OK)


@api_view(['POST'])
@user_in_group("UPDATE")
def updateElement(request):
    username = request.user.username
    params = dict(request.data)
    try:
        model_name = params['model_name'][0]
        property_dict = json.loads(params['property'][0])
        element_id = int(params['id'][0])
    except KeyError:
        return Response(status=HTTP_400_BAD_REQUEST,
                        data="updateElement: KeyError in HTTP parameters. Missing parameter.")

    if model_name == 'Experiment' and 'status' in property_dict:
        return Response(status=HTTP_400_BAD_REQUEST,
                        data="updateElement: It is not possible to verify and experiment.")
    try:
        model = eval(model_name)
    except NameError:
        return Response(status=HTTP_400_BAD_REQUEST,
                        data="updateElement: NameError. Model '{}' not exist.".format(model_name))

    try:
        element = model.objects.get(pk=element_id)
        for prop in property_dict:
            if prop in element.__dict__:
                setattr(element, prop, property_dict[prop])
            else:
                return Response(status=HTTP_400_BAD_REQUEST,
                                data="updateElement: Attribute '{}' not exist in model '{}'".format(prop, model_name))
        element.save(username=username)
    except ObjectDoesNotExist:
        return Response(status=HTTP_400_BAD_REQUEST,
                        data="updateElement: ID Error. Element ID '{}' in Model '{}' not exist."
                        .format(element_id, model_name))
    except Exception as err:
        err_type, value, traceback = sys.exc_info()
        logger.info(f'{username} - Error Insert Experiment Query' + str(err_type.__name__) + " : " + str(value))
        return Response(status=HTTP_500_INTERNAL_SERVER_ERROR,
                        data="updateElement: Generic error updating Experiment. "
                             + str(err_type.__name__) + " : " + str(value))

    logger.info(f'{username} - Update Element ID {element_id} in Model {model_name}')
    return Response("{} element updated successfully.".format(model_name), status=HTTP_200_OK)


@api_view(['POST'])
@user_in_group("WRITE")
def insertElement(request):
    username = request.user.username

    params = dict(request.data)

    supported_models = ['ExperimentClassifier', 'ChemModel', 'Experiment']
    try:
        model_name = params['model_name'][0]
        property_dict = json.loads(params['property'][0])
    except KeyError:
        return Response(status=HTTP_400_BAD_REQUEST,
                        data="insertElement: KeyError in HTTP parameters. Missing parameter.")

    if model_name not in supported_models:
        return Response(status=HTTP_400_BAD_REQUEST,
                        data="insertElement: Model '{}' not supported yet.".format(model_name))

    try:
        model = eval(model_name)
    except NameError:
        return Response(status=HTTP_400_BAD_REQUEST,
                        data="insertElement: NameError. Model '{}' not exist.".format(model_name))

    try:
        with transaction.atomic():
            list_objects = getattr(model, 'create' + model_name)(property_dict)
            for obj in list_objects:
                obj.save(username=username)
    except DatabaseError as e:
        return Response("insertElement: " + str(e.__cause__), status=HTTP_400_BAD_REQUEST)
    except ConstraintFieldExperimentError as e:
        return Response("insertElement: " + str(e), status=HTTP_400_BAD_REQUEST)
    except Exception as err:
        err_type, value, traceback = sys.exc_info()
        logger.info(f'{username} - Error Insert Element' + str(err_type.__name__) + " : " + str(value))
        return Response(status=HTTP_500_INTERNAL_SERVER_ERROR,
                        data="insertElement: Generic error in experiment verification. "
                             + str(err_type.__name__) + " : " + str(value))

    logger.info(f'{username} - Insert %s Object', model_name)
    return Response("{} element inserted successfully.".format(model_name), status=HTTP_200_OK)


@api_view(['POST'])
def deleteElement(request):
    if not request.user.is_authenticated:
        return Response("deleteElement. User is not authenticated.", status=HTTP_401_UNAUTHORIZED)

    params = dict(request.data)

    supported_models = ['ChemModel', 'FilePaper', 'Experiment', 'Execution', 'CurveMatchingResult']

    try:
        model_name = params['model_name'][0]
        element_identifier = int(json.loads(params['id'][0]))
    except KeyError:
        return Response(status=HTTP_400_BAD_REQUEST,
                        data="deleteElement: KeyError in HTTP parameters. Missing parameter.")

    if model_name not in supported_models:
        return Response(status=HTTP_400_BAD_REQUEST,
                        data="deleteElement: Model '{}' not supported yet.".format(model_name))

    try:
        model = eval(model_name)
    except NameError:
        return Response(status=HTTP_400_BAD_REQUEST,
                        data="deleteElement: NameError. Model '{}' not exist.".format(model_name))

    owner = LoggerModel.objects.get(model_name=model_name, pk_model=element_identifier).username

    if owner != request.user.username:
        if not(request.user.is_superuser | request.user.groups.filter(name="DELETE").exists()):
            return Response("deleteElement. User does not have permission.", status=HTTP_403_FORBIDDEN)
    try:
        model.objects.get(pk=element_identifier).delete()
        log = LoggerModel(model_name="Experiment",
                          pk_model=element_identifier,
                          username=request.user.username,
                          action="DELETE",
                          date=timezone.now())
        log.save()
    except Exception as err:
        err_type, value, traceback = sys.exc_info()
        logger.info(f'{request.user.username} - Error Delete Element' + str(err_type.__name__) + " : " + str(value))
        return Response(status=HTTP_500_INTERNAL_SERVER_ERROR,
                        data="deleteElement: Generic error in experiment verification. "
                             + str(err_type.__name__) + " : " + str(value))

    logger.info(f'{request.user.username} - Delete %s Object', model_name)
    return Response("{} element deleted successfully.".format(model_name), status=HTTP_200_OK)

# END  NEW

# START ANALISYS

@api_view(['POST'])
@user_in_group("VALIDATE")
def analyzeExecution(request):
    username = request.user.username
    params = json.loads(request.data['params'])
    exec_id = params.get('execution')
    status = params.get('status')

    execution = Execution.objects.get(pk=exec_id)

    experiment = execution.experiment

    exp_type = experiment.run_experiment_classifier()

    output_file = exp_type.output_file
    mapping = exp_type.mapping

    data_columns_data = {}
    execution_columns_data = {}

    data_columns_unit = {}
    execution_columns_unit = {}

    y_exec = ExecutionColumn.objects.get(execution=execution, label='tau_T(slope)', file_type=output_file)

    # print(mapping, file=sys.stderr)

    for key in mapping:
        data_column = DataColumn.objects.get(experiment=experiment, name=key)
        data_columns_data[key] = [float(x) for x in data_column.data]
        data_columns_unit[key] = data_column.units
        execution_column = ExecutionColumn.objects.get(execution=execution, label=mapping[key], file_type=output_file)
        execution_columns_data[mapping[key]] = [float(x) for x in execution_column.data]
        execution_columns_unit[mapping[key]] = execution_column.units


    for key in data_columns_unit:
        if data_columns_unit[key] == "K":
            continue
        elif data_columns_unit[key] == "us" and execution_columns_unit[mapping[key]] == "s":
            data_columns_data[key] = [float(x) / (10**6) for x in data_columns_data[key]]
        elif data_columns_unit[key] == "ms" and execution_columns_unit[mapping[key]] == "s":
            data_columns_data[key] = [float(x) / (10**3) for x in data_columns_data[key]]

    path_executable_cm = os.path.join(settings.BASE_DIR, CurveMatching.__name__, "CurveMatchingPython.o")
    # cm = CurveMatching.CurveMatchingPython.CurveMatching(library_path=path_executable_cm)

    data_columns_keys = list(data_columns_data.keys())
    # print(path_executable_cm)

    if not CurveMatchingResult.objects.filter(execution_column=y_exec).exists():

        index, error = CurveMatching.CurveMatchingPython.CurveMatching.execute(x_exp=data_columns_data[data_columns_keys[0]],
                                  y_exp=data_columns_data[data_columns_keys[1]],
                                  x_sim=execution_columns_data[mapping[data_columns_keys[0]]],
                                  y_sim=execution_columns_data[mapping[data_columns_keys[1]]],
                                  library_path=path_executable_cm)

        cm_result = CurveMatchingResult(execution_column=y_exec,
                                        index=index,
                                        error=error)
        cm_result.save(username=username)

        # print(data_columns_data, file=sys.stderr)
        # print(execution_columns_data)
        # print(data_columns_unit, file=sys.stderr)
        # print(execution_columns_unit)
        # print("EDOOOO", index, error)

    return Response(status=HTTP_200_OK, data="Experiment verified successfully")

# END ANALISYS



def respecth_text_to_experiment(username, file):
    status = "unverified"
    with transaction.atomic():
        respecth_obj = ReSpecThParser.from_string(file)

        # Check Mandatory Field
        reactor = respecth_obj.apparatus
        experiment_type = respecth_obj.experiment_type
        fileDOI = respecth_obj.fileDOI

        if not reactor:
            raise MandatoryFieldExperimentError("Reactor")
        elif not experiment_type:
            raise MandatoryFieldExperimentError("Experiment type")
        elif not fileDOI:
            raise MandatoryFieldExperimentError("File DOI")

        # check duplicates
        if Experiment.objects.filter(fileDOI=fileDOI).exists():
            raise DuplicateExperimentError
        else:
            ignition_type = respecth_obj.get_ignition_type()

            paper = FilePaper(title=respecth_obj.getBiblio())
            paper.save(username=username)

            e = Experiment(reactor=reactor,
                           experiment_type=experiment_type,
                           fileDOI=fileDOI,
                           ignition_type=ignition_type,
                           file_paper=paper,
                           xml_file=file,
                           status=status)
            e.save(username=username)

            columns_groups = respecth_obj.extract_columns_multi_dg()

            for g in columns_groups:
                for c in g:
                    co = DataColumn(experiment=e, **c)
                    co.save()

            common_properties = respecth_obj.common_properties()

            for c in common_properties:
                cp = CommonProperty(experiment=e, **c)
                cp.save()

            initial_species = respecth_obj.initial_composition()

            for i in initial_species:
                ip = InitialSpecie(experiment=e, **i)
                ip.save()




def from_text_to_experiment(username, file):
    response = {'result': None, 'error': ''}
    status = "unverified"
    with transaction.atomic():
        respecth_obj = ReSpecThParser.from_string(file)

        reactor = respecth_obj.apparatus
        experiment_type = respecth_obj.experiment_type
        fileDOI = respecth_obj.fileDOI

        # check duplicates
        if Experiment.objects.filter(fileDOI=fileDOI).exists():
            response['result'] = "DUPLICATE"
        else:

            ignition_type = respecth_obj.get_ignition_type()

            paper = FilePaper(title=respecth_obj.getBiblio())
            paper.save(username=username)

            e = Experiment(reactor=reactor,
                           experiment_type=experiment_type,
                           fileDOI=fileDOI,
                           ignition_type=ignition_type,
                           file_paper=paper,
                           xml_file=file,
                           status=status)
            e.save(username=username)

            columns_groups = respecth_obj.extract_columns_multi_dg()

            for g in columns_groups:
                for c in g:
                    co = DataColumn(experiment=e, **c)
                    co.save()

            common_properties = respecth_obj.common_properties()

            for c in common_properties:
                cp = CommonProperty(experiment=e, **c)
                cp.save()

            initial_species = respecth_obj.initial_composition()

            for i in initial_species:
                ip = InitialSpecie(experiment=e, **i)
                ip.save()

            response['result'] = "OK"

    return response



