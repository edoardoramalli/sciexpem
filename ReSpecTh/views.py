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
from ReSpecTh.ReSpecThParser import ReSpecThParser
from ReSpecTh.OptimaPP import OptimaPP
from ExperimentManager import models

# Logging
import logging
logger = logging.getLogger("ReSpecTh")
logger.addHandler(ReSpecTh.apps.logger_handler)
logger.setLevel(logging.INFO)


@api_view(['GET'])
@permission_required('ReSpecTh.execute_optimapp', raise_exception=True)
def executeOptimaPP(request):
    user = request.user.username

    logger.info(f'{user} - Receive Execution OptimaPP Request')

    response = {'result': None, 'error': ''}
    parameters = request.query_params
    query_execution = json.loads(parameters['query'])

    file = query_execution['file']

    result, error = OptimaPP.txt_to_xml(file)
    response['result'] = result
    response['error'] = error

    reply = JsonResponse(response)

    return reply


@api_view(['GET'])
@permission_required(('ExperimentManager.add_experiment',
                      'ExperimentManager.add_commonproperty',
                      'ExperimentManager.add_datacolumn',
                      'ExperimentManager.add_filepaper',
                      'ExperimentManager.add_initialspecie'), raise_exception=True)
def loadXMLExperiment(request):
    username = request.user.username

    logger.info(f'{username} - Insert Experiment from XML file')

    response = {'result': None, 'error': ''}
    parameters = request.query_params
    query_execution = json.loads(parameters['query'])

    file = query_execution['file']

    try:
        with transaction.atomic():
            respecth_obj = ReSpecThParser.from_string(file)

            initial_composition = respecth_obj.initial_composition()
            reactor = respecth_obj.apparatus
            experiment_type = respecth_obj.experiment_type
            fileDOI = respecth_obj.fileDOI

            # check duplicates
            if models.Experiment.objects.filter(fileDOI=fileDOI).exists():
                response['result'] = "DUPLICATE"
            else:

                it = respecth_obj.get_ignition_type()
                o = None
                if it is not None:
                    o = it.attrib.get("target") + " " + it.attrib.get("type")

                paper = models.FilePaper(title=respecth_obj.getBiblio())
                paper.save(username=username)

                e = models.Experiment(reactor=reactor,
                                      experiment_type=experiment_type,
                                      fileDOI=fileDOI,
                                      ignition_type=o,
                                      file_paper=paper,
                                      xml_file=file)
                e.save(username=username)

                columns_groups = respecth_obj.extract_columns_multi_dg()
                for g in columns_groups:
                    for c in g:
                        co = models.DataColumn(experiment=e, **c)
                        co.save(username=username)

                common_properties = respecth_obj.common_properties()

                for c in common_properties:
                    cp = models.CommonProperty(experiment=e, **c)
                    cp.save(username=username)

                initial_species = respecth_obj.initial_composition()

                for i in initial_species:
                    ip = models.InitialSpecie(experiment=e, **i)
                    ip.save(username=username)

                response['result'] = "OK"

    except Exception as err:
        err_type, value, traceback = sys.exc_info()
        response['error'] += "SERVER - " + str(err_type.__name__) + " : " + str(value)
        logger.info(f'{username} - Error Insert Experiment Query')

    reply = JsonResponse(response)

    return reply