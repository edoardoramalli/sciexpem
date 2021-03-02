# Import django
from django.db import transaction, DatabaseError, close_old_connections
from django.core.exceptions import FieldError
from rest_framework.status import *
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.views import APIView

# Import build-in
import os
import json
import sys
from decimal import Decimal

# Local Packages
from SciExpeM import settings
from ReSpecTh.OptimaPP import TranslatorOptimaPP, OptimaPP

# Import Local

import ExperimentManager.Serializers as Serializers
from ExperimentManager.Models import *
from SciExpeM.checkPermissionGroup import HasGroupPermission
from ExperimentManager import QSerializer
from ExperimentManager.exceptions import *
import ExperimentManager
import CurveMatching
from ReSpecTh.ReSpecThParser import ReSpecThParser
from SciExpeM.checkPermissionGroup import user_in_group

# START LOGGER
# Logging
import logging

logger = logging.getLogger("ExperimentManager")
logger.addHandler(ExperimentManager.apps.logger_handler)
logger.setLevel(logging.INFO)


# END LOGGER


class ExperimentManagerBaseView(APIView):
    viewName = 'BaseView'
    paramsType = {}
    permission_classes = [HasGroupPermission] if settings.GROUP_ACTIVE else []

    def view_post(self, request):
        pass

    def view_get(self, request):
        pass

    # def get(self, request):
    #     try:
    #         params = dict(request.query_params)
    #         try:
    #             for par in self.paramsType:
    #                 self.__setattr__(par, self.paramsType[par](params[par][0]))
    #         except KeyError:
    #             return Response(status=HTTP_400_BAD_REQUEST,
    #                             data=self.viewName + ": KeyError in HTTP parameters. Missing parameter.")
    #
    #         return self.view_get()
    #
    #     except Exception:
    #         err_type, value, traceback = sys.exc_info()
    #         logger.info('Error ' + self.viewName + ': ' + str(err_type.__name__) + " : " + str(value))
    #         return Response(status=HTTP_500_INTERNAL_SERVER_ERROR,
    #                         data=self.viewName + ": Generic error. " + str(err_type.__name__) + " : " + str(value))
    #     finally:
    #         close_old_connections()

    def post(self, request):
        try:
            params = request.data
            try:
                for par in self.paramsType:
                    self.__setattr__(par, self.paramsType[par](params[par]))
            except KeyError:
                return Response(status=HTTP_400_BAD_REQUEST,
                                data=self.viewName + ": KeyError in HTTP parameters. Missing parameter.")

            return self.view_post(request=request)

        except Exception:
            err_type, value, traceback = sys.exc_info()
            logger.info('Error ' + self.viewName + ': ' + str(err_type.__name__) + " : " + str(value))
            return Response(status=HTTP_500_INTERNAL_SERVER_ERROR,
                            data=self.viewName + ": Generic error. " + str(err_type.__name__) + " : " + str(value))
        finally:
            close_old_connections()







# START VALIDATE

@api_view(['POST'])
@user_in_group("VALIDATE")
def verifyExperiment(request):
    try:
        username = request.user.username
        params = dict(request.data)
        try:
            status = params['status'][0]
            exp_id = params['experiment_id'][0]
        except KeyError:
            return Response(status=HTTP_400_BAD_REQUEST,
                            data="verifyExperiment: KeyError in HTTP parameters. Missing parameter.")
        try:
            exp = Experiment.objects.get(pk=exp_id)
            exp.status = status
            exp.save()
        except ConstraintFieldExperimentError as e:
            return Response(status=HTTP_400_BAD_REQUEST, data="verifyExperiment: " + str(e))

        return Response(status=HTTP_200_OK, data="Experiment verified successfully.")

    except Exception as err:
        err_type, value, traceback = sys.exc_info()
        logger.info('Error Verify Experiment' + str(err_type.__name__) + " : " + str(value))
        return Response(status=HTTP_500_INTERNAL_SERVER_ERROR,
                        data="verifyExperiment: Generic error in experiment verification."
                             + str(err_type.__name__) + " : " + str(value))
    finally:
        close_old_connections()



# START  NEW
@api_view(['POST'])
@user_in_group("READ")
def filterDataBase(request):
    try:
        params = json.loads(request.data)

        try:
            model_name = params['model_name']
            query_str = params['query']
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

            serializer = eval('Serializers.' + model_name + 'Serializer')
            for query_result in query_set:
                result.append(serializer(query_result).data)

            return Response(result, status=HTTP_200_OK)
        except FieldError:
            return Response(status=HTTP_400_BAD_REQUEST,
                            data="filterDataBase: FieldError. Query '{}' is incorrect for model '{}'."
                            .format(query, model_name))
    except Exception as err:
        err_type, value, traceback = sys.exc_info()
        logger.info('Error Filter Database' + str(err_type.__name__) + " : " + str(value))
        return Response(status=HTTP_500_INTERNAL_SERVER_ERROR,
                        data="filterDataBase: Generic error filtering the database. "
                             + str(err_type.__name__) + " : " + str(value))
    finally:
        close_old_connections()


@api_view(['POST'])
# @user_in_group("READ")
def requestProperty(request):
    try:
        params = dict(request.data)
        try:
            model_name = params['model_name'][0]
            element_id = int(params['element_id'][0])
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
            return Response(
                "requestProperty: AttributeError. Property '{}' not exist for model '{}'.".format(property_name,
                                                                                                  model_name),
                status=HTTP_400_BAD_REQUEST)
    except Exception as err:
        err_type, value, traceback = sys.exc_info()
        logger.info('Error Request Property' + str(err_type.__name__) + " : " + str(value))
        return Response(status=HTTP_500_INTERNAL_SERVER_ERROR,
                        data="requestProperty: Generic error requesting property. "
                             + str(err_type.__name__) + " : " + str(value))
    finally:
        close_old_connections()


# START  NEW
@api_view(['POST'])
@user_in_group("WRITE")
def loadExperiment(request):
    try:
        username = request.user.username
        params = dict(request.data)
        try:
            format_file = params['format_file'][0]
            file_text = params['file_text'][0]
        except KeyError:
            return Response(status=HTTP_400_BAD_REQUEST,
                            data="loadExperiment: KeyError in HTTP parameters. Missing parameter.")

        if format_file == 'XML_ReSpecTh':
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

        else:
            return Response(status=HTTP_400_BAD_REQUEST,
                            data="loadExperiment: Format Not supported.")

        logger.info(f'{username} - Insert Experiment from XML file')
        return Response("Experiment inserted successfully.", status=HTTP_200_OK)

    except Exception as err:
        err_type, value, traceback = sys.exc_info()
        logger.info('Error Load Experiment from file' + str(err_type.__name__) + " : " + str(value))
        return Response(status=HTTP_500_INTERNAL_SERVER_ERROR,
                        data="loadExperiment: Generic error inserting Experiment from file. "
                             + str(err_type.__name__) + " : " + str(value))
    finally:
        close_old_connections()


@api_view(['POST'])
@user_in_group("UPDATE")
def updateElement(request):
    try:
        params = dict(request.data)
        try:
            model_name = params['model_name'][0]
            property_dict = json.loads(params['property'][0])
            element_id = int(params['element_id'][0])
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
                                    data="updateElement: Attribute '{}' not exist in model '{}'".format(prop,
                                                                                                        model_name))
            element.save()
        except ObjectDoesNotExist:
            return Response(status=HTTP_400_BAD_REQUEST,
                            data="updateElement: ID Error. Element ID '{}' in Model '{}' not exist."
                            .format(element_id, model_name))

        logger.info('Update Element ID {element_id} in Model {model_name}')
        return Response("{} element updated successfully.".format(model_name), status=HTTP_200_OK)

    except Exception as err:
        err_type, value, traceback = sys.exc_info()
        logger.info('Error Update Query' + str(err_type.__name__) + " : " + str(value))
        return Response(status=HTTP_500_INTERNAL_SERVER_ERROR,
                        data="updateElement: Generic error updating Experiment. "
                             + str(err_type.__name__) + " : " + str(value))
    finally:
        close_old_connections()


@api_view(['POST'])
@user_in_group("WRITE")
def insertElement(request):
    try:
        username = request.user.username

        params = dict(request.data)

        supported_models = ['ExperimentInterpreter', 'ChemModel', 'Experiment']
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
                exp = None
                for obj in list_objects:
                    if isinstance(obj, Experiment):
                        obj.username = username
                        obj.save()
                        exp = obj
                    else:
                        obj.save()
                if exp is not None:
                    txt = TranslatorOptimaPP.create_OptimaPP_txt(experiment=exp,
                                                                 data_groups=exp.data_columns.all(),
                                                                 initial_species=exp.initial_species.all(),
                                                                 common_properties=exp.common_properties.all(),
                                                                 file_paper=exp.file_paper)
                    xml, error = OptimaPP.txt_to_xml(txt)
                    if error:
                        raise OptimaPPError(error)
                    else:
                        exp.xml_file = xml
                        exp.save()

        except DatabaseError as e:
            return Response("insertElement: " + str(e.__cause__), status=HTTP_400_BAD_REQUEST)
        except ConstraintFieldExperimentError as e:
            return Response("insertElement: " + str(e), status=HTTP_400_BAD_REQUEST)
        except OptimaPPError as e:
            return Response("insertElement: OptimaPP error. " + str(e),
                            status=HTTP_400_BAD_REQUEST)

        logger.info(f'{username} - Insert %s Object', model_name)
        return Response("{} element inserted successfully.".format(model_name), status=HTTP_200_OK)

    # except Exception as err:
    #     err_type, value, traceback = sys.exc_info()
    #     logger.info('Error Insert Element' + str(err_type.__name__) + " : " + str(value))
    #     return Response(status=HTTP_500_INTERNAL_SERVER_ERROR,
    #                     data="insertElement: Generic error in insert experiment. "
    #                          + str(err_type.__name__) + " : " + str(value))
    finally:
        close_old_connections()


@api_view(['POST'])
def deleteElement(request):
    try:
        if not request.user.is_authenticated:
            return Response("deleteElement. User is not authenticated.", status=HTTP_401_UNAUTHORIZED)

        params = dict(request.data)

        supported_models = ['ChemModel', 'FilePaper', 'Experiment', 'Execution', 'CurveMatchingResult',
                            'ExperimentInterpreter']

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

        if model_name == 'Experiment' and model.objects.get(pk=element_identifier).status == 'verified':
            if not (request.user.is_superuser or request.user.groups.filter(name="DELETE").exists()):
                return Response("deleteElement. User does not have permission.", status=HTTP_403_FORBIDDEN)
        elif model_name != 'Experiment':
            if not (request.user.is_superuser or request.user.groups.filter(name="DELETE").exists()):
                return Response("deleteElement. User does not have permission.", status=HTTP_403_FORBIDDEN)

        model.objects.get(pk=element_identifier).delete()

        logger.info(f'{request.user.username} - Delete %s Object', model_name)
        return Response("{} element deleted successfully.".format(model_name), status=HTTP_200_OK)

    except Exception as err:
        err_type, value, traceback = sys.exc_info()
        logger.info('Error Delete Element' + str(err_type.__name__) + " : " + str(value))
        return Response(status=HTTP_500_INTERNAL_SERVER_ERROR,
                        data="deleteElement: Generic error in experiment verification. "
                             + str(err_type.__name__) + " : " + str(value))
    finally:
        close_old_connections()



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
            data_columns_data[key] = [float(x) / (10 ** 6) for x in data_columns_data[key]]
        elif data_columns_unit[key] == "ms" and execution_columns_unit[mapping[key]] == "s":
            data_columns_data[key] = [float(x) / (10 ** 3) for x in data_columns_data[key]]

    path_executable_cm = os.path.join(settings.BASE_DIR, CurveMatching.__name__, "CurveMatchingPython.o")
    # cm = CurveMatching.CurveMatchingPython.CurveMatching(library_path=path_executable_cm)

    data_columns_keys = list(data_columns_data.keys())
    # print(path_executable_cm)

    if not CurveMatchingResult.objects.filter(execution_column=y_exec).exists():
        index, error = CurveMatching.CurveMatchingPython.CurveMatching.execute(
            x_exp=data_columns_data[data_columns_keys[0]],
            y_exp=data_columns_data[data_columns_keys[1]],
            x_sim=execution_columns_data[mapping[data_columns_keys[0]]],
            y_sim=execution_columns_data[mapping[data_columns_keys[1]]],
            library_path=path_executable_cm)

        cm_result = CurveMatchingResult(execution_column=y_exec,
                                        index=index,
                                        error=error)
        cm_result.save()

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

            # TODO non viene controllato se c'è il DOI
            # TODO non viene controllato se esiste già

            paper = FilePaper(references=respecth_obj.getBiblio())
            paper.save()

            e = Experiment(reactor=reactor,
                           experiment_type=experiment_type,
                           fileDOI=fileDOI,
                           ignition_type=ignition_type,
                           file_paper=paper,
                           xml_file=file,
                           status=status,
                           username=username)
            e.save()

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


@api_view(['POST'])
@user_in_group("READ")
def getCurveMatching(request):
    try:
        params = dict(request.data)

        try:
            experiment_id = params['exp_id'][0]
        except KeyError:
            return Response(status=HTTP_400_BAD_REQUEST,
                            data="getCurveMatching: KeyError in HTTP parameters. Missing parameter.")

        # All the CM of an experiment
        cm_results = CurveMatchingResult.objects.filter(execution_column__execution__experiment__id=experiment_id)

        model_list = {}

        for result in cm_results:
            model_name = result.execution_column.execution.chemModel.name
            model_list[model_name] = {'score': result.score, 'error': result.error}

        return Response(model_list, status=HTTP_200_OK)

    except Exception as err:
        err_type, value, traceback = sys.exc_info()
        logger.info('Error Get Curve Matching' + str(err_type.__name__) + " : " + str(value))
        return Response(status=HTTP_500_INTERNAL_SERVER_ERROR,
                        data="getCurveMatching: Generic error in get execution. "
                             + str(err_type.__name__) + " : " + str(value))
    finally:
        close_old_connections()


@api_view(['POST'])
@user_in_group("READ")
def requestPropertyList(request):
    try:
        params = dict(request.data)
        try:
            model_name = params['model_name']
            element_id = int(params['id'])
            fields = tuple(params['fields'])
        except KeyError:
            return Response(status=HTTP_400_BAD_REQUEST,
                            data="requestPropertyList: KeyError in HTTP parameters. Missing parameter.")

        model = eval(model_name)

        element = model.objects.get(id=element_id)

        serializer = eval('Serializers.' + model_name + 'Serializer')

        results = serializer(element, fields=fields).data

        return Response(json.dumps(results), status=HTTP_200_OK)

    except Exception:
        err_type, value, traceback = sys.exc_info()
        return Response(status=HTTP_500_INTERNAL_SERVER_ERROR,
                        data="requestPropertyList: Generic error filtering the database. "
                             + str(err_type.__name__) + " : " + str(value))
    finally:
        close_old_connections()


@api_view(['POST'])
def prova(request):
    # fp = Experiment.objects.get(id=5)
    #
    # a = ExperimentSerializer(fp)
    #
    # print(json.dumps(a.data))

    # data = {'id': 2, 'references': 'edo', 'pippo': 90}
    #
    # serializer = FilePaperSerializer(data=data)
    # print(serializer.is_valid())
    # print(serializer.validated_data)

    return Response("OK", status=HTTP_200_OK)
