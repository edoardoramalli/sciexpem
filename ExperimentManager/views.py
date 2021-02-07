# Import django
from django.http import HttpResponse, JsonResponse
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.core.exceptions import FieldError
from rest_framework.status import HTTP_500_INTERNAL_SERVER_ERROR, HTTP_200_OK
from rest_framework.response import Response
from rest_framework.decorators import api_view

# Import build-in
import json

# Import Local
from ExperimentManager.serializers import *
from ExperimentManager.models import *
from ExperimentManager import QSerializer
import ExperimentManager
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
@user_in_group("WRITE")
def loadXMLExperimentSimple(request):
    username = request.user.username
    # username = 'root'
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
    params = json.loads(request.data['params'])
    exp_id = params.get('experiment')
    status = params.get('status')

    exp = Experiment.objects.filter(pk=exp_id)
    c_exp = exp[0]

    if status == 'verified':
        if not c_exp.os_input_file:
            return Response(status=HTTP_500_INTERNAL_SERVER_ERROR, data="Missing OS input file")
        if not c_exp.experiment_classifier:
            return Response(status=HTTP_500_INTERNAL_SERVER_ERROR, data="Experiment not managed")
        exp.update(status='verified')
        return Response(status=HTTP_200_OK, data="Experiment verified successfully")

    elif status == 'invalid':
        exp.update(status='invalid')
        return Response(status=HTTP_200_OK, data="Experiment verified successfully")

    else:
        return Response(status=HTTP_500_INTERNAL_SERVER_ERROR, data="Experiment status not valid")




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


def from_text_to_experiment(username, file):
    response = {'result': None, 'error': ''}
    status = "new"
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

    return  response



