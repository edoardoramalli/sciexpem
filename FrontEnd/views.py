from ExperimentManager.Models import *
from SciExpeM.checkPermissionGroup import HasGroupPermission
from FrontEnd import utils
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.http import JsonResponse

from rest_framework.parsers import FileUploadParser, MultiPartParser, FormParser, JSONParser
import io
import pandas as pd
from rest_framework.views import APIView

from pathlib import Path
from rest_framework.status import *
from SciExpeM import settings
import os
from django.db import transaction, DatabaseError, close_old_connections
from OpenSmoke.OpenSmoke import OpenSmokeParser

import sys

from ReSpecTh.ReSpecThParser import ReSpecThValidSpecie, ReSpecThValidProperty, ReSpecThValidExperimentType, \
    ReSpecThValidReactorType

validatorProperty = ReSpecThValidProperty()
validatorSpecie = ReSpecThValidSpecie()

dict_excel_names = {"IDT": "ignition delay", "T": "temperature"}

__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))


@api_view(['GET'])
def get_username(request):
    username = request.user.username
    return JsonResponse({"username": username})


@api_view(['POST'])
def get_experiment_data_columns(request, pk):
    try:
        data_group = request.data['params']['type']
        data_columns = DataColumn.objects.filter(experiment__pk=pk, dg_id=data_group)
        if data_columns.exists():
            header = [column.name + " [" + column.units + "]" +
                      " - Ignore: " + str(column.ignore) + " Nominal: " + str(column.nominal) +
                      " - Plot Scale: " + column.plotscale + ""
                      if not column.species
                      else column.label + " [" + column.units + "]" +
                           " - Ignore: " + str(column.ignore) + " Nominal: " + str(column.nominal) +
                           " - Plot Scale: " + column.plotscale + ""
                      for column in data_columns]

            data = [list(map(lambda x: float(x), column.data)) for column in data_columns]

            df = pd.DataFrame(dict(zip(header, data)))

            columns = list(df.columns)
            content = df.to_dict(orient="records")
        else:
            columns = None
            content = None
    except Exception as ex:
        print(ex, file=sys.stderr)

    return JsonResponse({"header": columns, "data": content})


@api_view(['GET'])
def get_experiment_type_list(request):
    experiment_type_list = ReSpecThValidExperimentType().experiment_type
    return JsonResponse({"experiment_type_list": experiment_type_list})


@api_view(['GET'])
def get_reactor_type_list(request):
    reactor_type_list = ReSpecThValidReactorType().reactor_type
    return JsonResponse({"reactor_type_list": reactor_type_list})


@api_view(['GET'])
def opensmoke_names(request):
    data_folder = Path(__location__).parents[0] / "Files"
    names = list(
        pd.read_csv(os.path.join(data_folder, "Nomenclatura_originale_POLIMI.txt"), delim_whitespace=True)['NAME'])
    return JsonResponse({"names": names})


@api_view(['GET'])
def fuels_names(request):
    data_folder = Path(__location__).parents[0] / "Files"
    names = list(
        set(pd.read_csv(os.path.join(data_folder, "fuels"), header=None)[0]))
    return JsonResponse({"names": names})


def serialize_DC(col):
    return {'name': col.name, 'units': col.units, 'data': col.data, 'dg_id': col.dg_id, 'label': col.label,
            'species': col.species, 'nominal': col.nominal, 'plotscale': col.plotscale, 'ignore': col.ignore}


class DataExcelUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):  # autenticazione? TODO
        params = dict(request.data)
        excel_file = params['file'][0]
        data_group = params['data_group'][0]

        excel_file_bytes = io.BytesIO(excel_file.read())

        try:
            data_frame = pd.read_excel(excel_file_bytes)
        except Exception as error:
            return Response("Errors checking the file" + str(error), status.HTTP_400_BAD_REQUEST)

        check = utils.check_data_excel(data_frame)  # null ed ha struttura qualcosa [unità]

        if not check:
            return Response("Errors checking the file", status.HTTP_400_BAD_REQUEST)

        columns = list(data_frame.columns)
        content = data_frame.to_dict(orient="records")

        list_dataColumn = []

        for cols in columns:
            split_col = cols.rsplit('[', maxsplit=1)
            name = split_col[0].strip()
            unit = split_col[1].strip().replace(']', '')
            # Check prop
            if not validatorProperty.isValid(unit=unit, name=name):
                # Se non è una prop normale magari è una specie
                new_name = name.replace('[', '').replace(']', '')
                if validatorSpecie.isValid(new_name):
                    list_dataColumn.append(DataColumn(name='composition',
                                                      units='mole fraction',
                                                      data=list(data_frame[cols]),
                                                      label='[' + new_name + ']',
                                                      species=[new_name],
                                                      plotscale='lin',
                                                      ignore=False,
                                                      dg_id=data_group))
                else:
                    return Response("DataExcelUploadView. Name column '{}' is not valid with unit '{}'."
                                    .format(name, unit), status=status.HTTP_400_BAD_REQUEST)
            else:
                list_dataColumn.append(DataColumn(name=name,
                                                  units=unit,
                                                  data=list(data_frame[cols]),
                                                  label=validatorProperty.getSymbol(name),
                                                  species=None,
                                                  plotscale='lin',
                                                  ignore=False,
                                                  dg_id=data_group))

        new_list = [serialize_DC(x) for x in list_dataColumn]

        response = {'names': columns, 'data': content, 'serialized': new_list}

        return Response(response, status=status.HTTP_200_OK)


class FrontEndBaseView(APIView):
    viewName = 'BaseView'
    paramsType = {}
    permission_classes = [HasGroupPermission] if settings.GROUP_ACTIVE else []

    def view_post(self):
        pass

    def view_get(self, request):
        pass

    def get(self, request):
        try:
            params = dict(request.query_params)
            try:
                for par in self.paramsType:
                    self.__setattr__(par, self.paramsType[par](params[par][0]))
            except KeyError as e:
                return Response(status=HTTP_400_BAD_REQUEST,
                                data=self.viewName + ": KeyError in HTTP parameters. Missing parameter {}.".format(e))

            return self.view_get(request)

        except Exception:
            err_type, value, traceback = sys.exc_info()
            return Response(status=HTTP_500_INTERNAL_SERVER_ERROR,
                            data=self.viewName + ": Generic error. " + str(err_type.__name__) + " : " + str(value))
        finally:
            close_old_connections()

    def post(self, request):
        try:
            params = dict(request.data)
            try:
                for par in self.paramsType:
                    self.__setattr__(par, self.paramsType[par](params[par]))
            except KeyError as e:
                return Response(status=HTTP_400_BAD_REQUEST,
                                data=self.viewName + ": KeyError in HTTP parameters. Missing parameter {}.".format(e))

            return self.view_post()

        except Exception:
            err_type, value, traceback = sys.exc_info()
            return Response(status=HTTP_500_INTERNAL_SERVER_ERROR,
                            data=self.viewName + ": Generic error. " + str(err_type.__name__) + " : " + str(value))
        finally:
            close_old_connections()


class prova(FrontEndBaseView):
    viewName = 'BaseView'
    paramsType = {}
    required_groups = {'POST': ['READ']}

    def view_post(self):
        print("here")
        return Response(HTTP_200_OK)


