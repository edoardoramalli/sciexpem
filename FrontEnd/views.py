from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.shortcuts import render
from django.http import HttpResponse
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from ExperimentManager import models
from ExperimentManager.Models import *
from FrontEnd import serializers
from FrontEnd import utils
from django.db.models import Avg
from django.db import transaction
import json
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.http import Http404
from collections import defaultdict
from OpenSmoke import OpenSmoke
# from ExperimentManager import boolparser
from rest_framework.parsers import FileUploadParser, MultiPartParser, FormParser, JSONParser
import seaborn as sns
import io
import pandas as pd
from django.http import FileResponse
from rest_framework.views import APIView
import numpy as np
from collections import defaultdict
from pathlib import Path
from rest_framework.status import *
import os
from CurveMatching import CurveMatching
from FrontEnd.serializers import DataColumnSerializer
from SciExpeM.checkPermissionGroup import user_in_group
from django.contrib.auth.decorators import login_required
from django.db import transaction, DatabaseError, close_old_connections
from OpenSmoke.OpenSmoke import OpenSmokeParser
from ReSpecTh.OptimaPP import TranslatorOptimaPP, OptimaPP

import sys

from ReSpecTh.ReSpecThParser import ReSpecThValidSpecie, ReSpecThValidProperty, ReSpecThValidExperimentType, \
    ReSpecThValidReactorType

validatorProperty = ReSpecThValidProperty()
validatorSpecie = ReSpecThValidSpecie()


@login_required
@never_cache
def index(request):
    return render(request, 'FrontEnd/index.html')


dict_excel_names = {"IDT": "ignition delay", "T": "temperature"}

from pint import UnitRegistry

ureg = UnitRegistry()

__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))


# def index(request):
#     return render(request, '../frontend/index.html')



class ExperimentListAPI(generics.ListAPIView):
    queryset = Experiment.objects.all()
    serializer_class = serializers.ExperimentSerializer


class ExperimentFilteredListAPI(generics.ListAPIView):
    serializer_class = serializers.ExperimentSerializer

    def get_queryset(self):
        """
        Optionally restricts the returned purchases to a given user,
        by filtering against a `username` query parameter in the URL.
        """
        queryset = Experiment.objects.all()
        experiments = self.request.query_params.getlist('experiments[]', None)
        if experiments is not None:
            queryset = queryset.filter(id__in=experiments)
        return queryset


def experiment_search_fields(request):
    experiments = Experiment.objects.all()
    reactors_to_types = defaultdict(list)
    for e in experiments:
        if e.experiment_type not in reactors_to_types[e.reactor]:
            reactors_to_types[e.reactor].append(e.experiment_type)

    species = [i for i in InitialSpecie.objects.values_list("name", flat=True).distinct()]
    response = {"reactors": list(reactors_to_types.keys()), "reactors_to_types": reactors_to_types, "species": species}
    return JsonResponse(response)


class SearchExperiments(generics.ListAPIView):
    serializer_class = serializers.ExperimentSerializer

    def get_queryset(self):
        queryset = Experiment.objects.all()

        reactor = self.request.query_params.get('reactor', None)
        experiment_type = self.request.query_params.get('experiment_type', None)
        species = self.request.query_params.getlist('species[]', None)

        if reactor is not None:
            queryset = queryset.filter(reactor=reactor)
        if experiment_type is not None:
            queryset = queryset.filter(experiment_type=experiment_type)
        if species:
            queryset = queryset.filter(initial_species__name__in=species)

        complex_query = self.request.query_params.get('complex_query', None)

        # complex query handling
        if complex_query is not None and len(complex_query) > 0:
            # TODO: validate complex query
            # TODO: better filtering method (custom manager)
            p = boolparser.BooleanParser(complex_query.upper())
            result_list_ids = []
            for e in queryset:
                cond = False
                try:
                    cond = p.evaluate(e.get_params_experiment())
                except:
                    pass
                if cond:
                    result_list_ids.append(e.id)

            queryset = queryset.filter(id__in=result_list_ids)

        # filter based on existence of run_type # TODO: improve
        result_list_ids = [e.id for e in queryset if e.run_type() is not None]
        queryset = queryset.filter(id__in=result_list_ids)

        return queryset


class ChemModelListAPI(generics.ListAPIView):
    queryset = ChemModel.objects.all()
    serializer_class = serializers.ChemModelSerializer


class ExperimentDetailAPI(generics.RetrieveDestroyAPIView):
    queryset = Experiment.objects.all()
    serializer_class = serializers.ExperimentDetailSerializer


# both for experiments and experiments + chem_models
def get_curves(exp_id, chem_models):
    experiment = get_object_or_404(Experiment, pk=exp_id)
    target_executions = []

    if chem_models and len(chem_models) > 0:
        target_executions = experiment.executions.filter(chemModel__id__in=chem_models)

    model_to_dash = dict()
    if chem_models and len(chem_models) > 0:
        if len(chem_models) <= 4:
            model_to_dash = dict(zip([float(j) for j in chem_models], ['solid', 'dash', 'dot', 'dashdot']))
        else:
            model_to_dash = dict(zip([float(j) for j in chem_models], len(chem_models) * ['solid']))

    if experiment.run_type() == EType.batch_idt:
        temp_column = experiment.data_columns.get(name="temperature")
        idt_column = experiment.data_columns.get(name="ignition delay")

        temp = [1000 / float(t) for t in temp_column.data]
        idt = [float(t) for t in idt_column.data]

        ### RE-SORTING
        t_dict = dict(zip(temp, idt))
        sorted_dict = sorted(t_dict.items(), key=lambda kv: kv[0])
        temp, idt = zip(*sorted_dict)
        ###

        x_axis = "1000/T [{}]".format(temp_column.units)
        y_axis = "IDT [{}]".format(idt_column.units)

        # TODO:  ASSUME T NOT ALWAYS IN K
        target_units = idt_column.units

        e_curve = {"x": temp, "y": idt, "name": "Ignition Delay Time", "mode": 'markers', "type": 'scatter'}
        model_curves = []
        for t in target_executions:
            temp_query = models.ExecutionColumn.objects.filter(label="T0", execution=t)[0]
            idt_query = models.ExecutionColumn.objects.filter(label="tau_T(slope)", execution=t)[0]
            # temp_column = models.execution_columns.get(name="temperature")
            # idt_column = models.execution_columns.get(name="ignition delay")

            temp_column = temp_query
            idt_column = idt_query

            temp = [1000 / float(t) for t in temp_column.data]
            idt = [(float(t) * ureg.parse_expression(idt_column.units)).to(target_units).magnitude for t in
                   idt_column.data]

            model_curves.append(
                {"x": temp, "y": idt, "name": t.chemModel.name, "mode": 'lines', "type": 'scatter', 'line': {
                    'dash': model_to_dash[t.chemModel.id]
                }})

        response = utils.curve_io_formatter([[e_curve] + model_curves], x_axis=x_axis, y_axis=y_axis, logY=True)
        return JsonResponse(response)

    elif experiment.run_type() == EType.flame_parPhi:
        phi_column = experiment.data_columns.get(name="phi")
        lfs_column = experiment.data_columns.get(name="laminar burning velocity")

        phi = [float(t) for t in phi_column.data]
        lfs = [float(t) for t in lfs_column.data]

        ### RE-SORTING
        t_dict = dict(zip(phi, lfs))
        sorted_dict = sorted(t_dict.items(), key=lambda kv: kv[0])
        temp, idt = zip(*sorted_dict)
        ###

        x_axis = "phi"
        y_axis = "LFS [{}]".format(lfs_column.units)

        # TODO:  ASSUME T NOT ALWAYS IN K
        target_units = lfs_column.units

        e_curve = {"x": phi, "y": lfs, "name": "LFS", "mode": 'markers', "type": 'scatter'}
        model_curves = []
        for t in target_executions:
            phi_column = t.execution_columns.get(name="phi")
            lfs_column = t.execution_columns.get(name="laminar burning velocity")

            phi = [float(t) for t in phi_column.data]
            lfs = [(float(t) * ureg.parse_expression(lfs_column.units)).to(target_units).magnitude for t in
                   lfs_column.data]

            model_curves.append(
                {"x": phi, "y": lfs, "name": t.chemModel.name, "mode": 'lines', "type": 'scatter', 'line': {
                    'dash': model_to_dash[t.chemModel.id]
                }})

        response = utils.curve_io_formatter([[e_curve] + model_curves], x_axis=x_axis, y_axis=y_axis, logY=True)
        return JsonResponse(response)

    elif experiment.run_type() in (EType.stirred_parT, EType.flow_isothermal_parT):
        temp_column = experiment.data_columns.get(name="temperature")
        comp_column = experiment.data_columns.filter(name="composition")

        comp_column = sorted(comp_column, key=lambda cc: max(cc.data), reverse=True)

        x_axis = "Temperature [{}]".format(temp_column.units)
        y_axis = "{} [{}]".format(comp_column[0].name, comp_column[0].units)

        temp = [float(t) for t in temp_column.data]

        colors = sns.color_palette("hls", len(comp_column))
        colors = ["rgb({},{},{})".format(int(i[0] * 255), int(i[1] * 255), int(i[2] * 255)) for i in colors]

        components = [cc.species[0] for cc in comp_column]
        colors_dict = dict(zip(components, colors))

        e_curves = []
        for index, cc in enumerate(comp_column):
            e_curves.append(
                {"x": temp, "y": [float(c) for c in cc.data], "name": cc.species[0], "mode": 'markers',
                 "type": 'scatter', 'legendgroup': cc.species[0],
                 'marker': {
                     'symbol': index,
                     'color': colors_dict[cc.species[0]]}
                 })

        model_curves = []
        for t in target_executions:
            temp_column = t.execution_columns.get(name="temperature")
            comp_column = t.execution_columns.filter(name="composition")

            temp = [float(t) for t in temp_column.data]

            for index, cc in enumerate(comp_column):
                model_curves.append(
                    {"x": temp, "y": [float(c) for c in cc.data],
                     "name": "{} {}".format(cc.species[0], t.chemModel.name), "mode": 'lines',
                     "type": 'scatter', 'legendgroup': cc.species[0],
                     'marker': {
                         'color': colors_dict[cc.species[0]]},
                     'line': {
                         'dash': model_to_dash[cc.execution.chemModel.id]
                     }
                     })

        response_curves = []
        for e_curve in e_curves:
            related_model_curves = [mc for mc in model_curves if mc['legendgroup'] == e_curve['legendgroup']]
            response_curves.append([e_curve] + related_model_curves)

        response = utils.curve_io_formatter(response_curves, x_axis=x_axis, y_axis=y_axis, logY=False)
        return JsonResponse(response, safe=False)


@api_view(['GET'])
def experiment_models_curve_API(request):
    exp_id = request.query_params.get('experiment', None)
    chem_models = request.query_params.getlist('chemModels[]', None)
    return get_curves(exp_id, chem_models)


@api_view(['GET'])
def experiment_info_API(request, pk):
    model_name = "Experiment"
    action = "save"
    log = models.LoggerModel.objects.get(model_name=model_name,
                                         pk_model=pk,
                                         action=action)
    response = {
        "author": log.username,
        "date": log.date.strftime('%Y.%m.%d %H:%M')
    }
    return Response(response)


@api_view(['GET'])
def experiment_curve_API(request, pk):
    response = get_curves(pk, None)
    if response is None:
        content = 'This experiment is currently not supported'
        return Response(content, status=status.HTTP_501_NOT_IMPLEMENTED)
    return response


@api_view(['GET'])
def curve_matching_results_API(request):
    exp_id = request.query_params.get('experiment', None)
    experiment = get_object_or_404(Experiment, pk=exp_id)
    chem_models = request.query_params.getlist('chemModels[]', None)

    executions = models.Execution.objects.filter(chemModel__id__in=chem_models, experiment=experiment)

    data = []
    names = []
    for exe in executions:
        target_CM_results = models.CurveMatchingResult.objects.filter(execution_column__execution=exe)
        exe_data = dict()
        exe_data['model'] = exe.chemModel.name

        average_index = average_error = 0
        if len(target_CM_results) > 0:
            averages = target_CM_results.aggregate(Avg('index'), Avg('error'))
            average_index, average_error = averages['index__avg'], averages['error__avg']

        exe_data['average_index'] = round(average_index, 7)
        exe_data['average_error'] = round(average_error, 7)

        for t in target_CM_results:
            execution_column = t.execution_column
            name = execution_column.name if not execution_column.species else execution_column.species[0]
            names.append(name)
            # exe_data[name] = {'index' : float(t.index), 'error' : float(t.error)}
            exe_data[name + '_index'] = round(t.index, 7) if t.index is not None else None
            exe_data[name + '_error'] = round(t.error, 7) if t.error is not None else None
        data.append(exe_data)

    return JsonResponse({'data': data, 'names': list(set(names))})


# deprecated
@api_view(['GET'])
def curve_matching_global_results_API_OLD(request):
    exp_ids = request.query_params.getlist('experiments[]', None)
    chem_models_ids = request.query_params.getlist('chemModels[]', None)

    details = request.query_params.get('details', "1")

    data = []
    names = []

    chem_models = ChemModel.objects.filter(id__in=chem_models_ids)

    for cm in chem_models:
        executions = models.Execution.objects.filter(chemModel=cm, experiment__id__in=exp_ids)
        cmr = models.CurveMatchingResult.objects.filter(execution_column__execution__in=executions)

        ind = defaultdict(list)
        err = defaultdict(list)

        result = dict()
        for c in cmr:
            result["model"] = cm.name

            execution_column = c.execution_column
            name = execution_column.name if not execution_column.species else execution_column.species[0]
            ind[name].append(c.index)
            err[name].append(c.error)

            if details == "1":
                names.append(name)

        for name, i in ind.items():
            result[name + '_index'] = round(float(np.mean(i)), 7)

        for name, e in err.items():
            result[name + '_error'] = round(float(np.mean(e)), 7)

            average_index = average_error = 0
            if len(cmr) > 0:
                averages = cmr.aggregate(Avg('index'), Avg('error'))
                average_index, average_error = averages['index__avg'], averages['error__avg']

            result['average_index'] = round(average_index, 7)
            result['average_error'] = round(average_error, 7)

        data.append(result)

    return JsonResponse({'data': data, 'names': list(set(names))})


@api_view(['GET'])
def curve_matching_global_results_API(request):
    exp_ids = request.query_params.getlist('experiments[]', None)
    chem_models_ids = request.query_params.getlist('chemModels[]', None)
    details = request.query_params.get('details', "1")

    cmr = []
    mancanti = []

    for exp, model in zip(exp_ids, chem_models_ids):
        current = models.CurveMatchingResult.objects.filter(execution__chemModel__pk=model,
                                                            execution__experiment__pk=exp)

        cmr += current

        if not current.exists():
            mancanti.append((exp, model))

    # cmr = models.CurveMatchingResult.objects.filter(execution__chemModel__in=chem_models_ids,
    #                                                 execution__experiment__in=exp_ids)
    # Se non ci sono i risultati calcolali

    for item in mancanti:
        exp_id, model_id = item
        exp = Experiment.objects.filter(pk=exp_id)[0]
        chemModel = ChemModel.objects.filter(pk=model_id)[0]
        try:
            with transaction.atomic():
                execution = models.Execution.objects.filter(experiment=exp, chemModel=chemModel)
                if execution.exists():
                    execution = execution[0]
                else:
                    OpenSmoke.OpenSmokeExecutor.execute(experiment=exp, chemModel=chemModel)
        except Exception as err:
            pass

        # t0 = models.ExecutionColumn.objects.filter(execution=execution, label="T0")[0]
        # slope = models.ExecutionColumn.objects.filter(execution=execution, label="tau_T(slope)")[0]
        #
        # curve_matching_executor = curve_matching.CurveMatchingExecutor("path")
        # curve_matching_executor.execute_CM(execution_column_x=t0, execution_column_y=slope)

        CurveMatching.execute_curve_matching_django(execution)

        current = models.CurveMatchingResult.objects.filter(execution__chemModel__pk=model_id,
                                                            execution__experiment__pk=exp_id)

        cmr += current

    result = []
    for i in cmr:
        if i.index is None or i.error is None:
            continue
        modelName = i.execution.chemModel.name
        experimentDOI = i.execution.experiment.fileDOI

        # execution_column = i.execution_column
        # name = execution_column.name if not execution_column.species else execution_column.species[0]

        r = dict()
        r['model'] = modelName
        r['experiment'] = experimentDOI
        r['name'] = experimentDOI
        r['ind'] = float(i.index)
        r['err'] = float(i.error)
        result.append(r)

    df = pd.DataFrame.from_dict(result)[['model', 'experiment', 'name', 'ind', 'err']]
    df = df.groupby(["model", "name"]).mean()

    data = []
    names = set()
    for model, new_df in df.groupby(level=0):
        d = {'model': model}
        overall = new_df.groupby(['model']).mean()
        d['average_index'] = round(new_df['ind'].mean(), 7)
        d['average_error'] = round(new_df['err'].mean(), 7)

        if details == "1":
            for i, t in new_df.iterrows():
                d[i[1] + "_index"] = round(t['ind'], 7)
                d[i[1] + "_error"] = round(t['err'], 7)
                names.add(i[1])
        data.append(d)

    result = {"data": data, "names": list(names)}
    return JsonResponse(result, safe=False)


@api_view(['GET'])
def curve_matching_global_results_dict_API(request):
    exp_ids = request.query_params.getlist('experiments[]', None)
    chem_models_ids = request.query_params.getlist('chemModels[]', None)

    cmr = []
    mancanti = []

    for exp, model in zip(exp_ids, chem_models_ids):
        current = models.CurveMatchingResult.objects.filter(execution__chemModel__pk=model,
                                                            execution__experiment__pk=exp)

        cmr += current

        if not current.exists():
            mancanti.append((exp, model))

    # cmr = models.CurveMatchingResult.objects.filter(execution__chemModel__in=chem_models_ids,
    #                                                 execution__experiment__in=exp_ids)
    # Se non ci sono i risultati calcolali

    for item in mancanti:
        exp_id, model_id = item
        exp = Experiment.objects.filter(pk=exp_id)[0]
        chemModel = ChemModel.objects.filter(pk=model_id)[0]
        try:
            with transaction.atomic():
                execution = models.Execution.objects.filter(experiment=exp, chemModel=chemModel)
                if execution.exists():
                    execution = execution[0]
                else:
                    OpenSmoke.OpenSmokeExecutor.execute(experiment=exp, chemModel=chemModel)
        except Exception as err:
            pass

        # t0 = models.ExecutionColumn.objects.filter(execution=execution, label="T0")[0]
        # slope = models.ExecutionColumn.objects.filter(execution=execution, label="tau_T(slope)")[0]
        #
        # curve_matching_executor = curve_matching.CurveMatchingExecutor("path")
        # curve_matching_executor.execute_CM(execution_column_x=t0, execution_column_y=slope)

        CurveMatching.execute_curve_matching_django(execution)

        current = models.CurveMatchingResult.objects.filter(execution__chemModel__pk=model_id,
                                                            execution__experiment__pk=exp_id)

        cmr += current

    result = []
    for i in cmr:
        if i.index is None or i.error is None:
            continue
        modelName = i.execution.chemModel.name
        experimentDOI = i.execution.experiment.fileDOI

        # execution_column = i.execution_column
        # name = execution_column.name if not execution_column.species else execution_column.species[0]

        r = dict()
        r['model'] = modelName
        r['experiment'] = experimentDOI
        # r['name'] = name
        r['name'] = experimentDOI
        r['ind'] = float(i.index)
        r['err'] = float(i.error)
        result.append(r)

    df = pd.DataFrame.from_dict(result)[['model', 'experiment', 'name', 'ind', 'err']]
    df = df.groupby(["model", "name"]).mean()

    result = []
    for model, new_df in df.groupby(level=0):
        d = pd.Series(new_df.ind.values, index=new_df.index.levels[1]).to_dict()
        result.append({"model": model, "data": d})

    return JsonResponse(result, safe=False)


@api_view(['GET'])
def download_input_file(request, pk):
    experiment = get_object_or_404(Experiment, pk=pk)
    input_opensmoke = experiment.os_input_file
    if not input_opensmoke:
        content = 'Unable to create this input file'
        return Response(content, status=status.HTTP_404_NOT_FOUND)
    input_file = OpenSmoke.OpenSmokeParser.create_output(input_opensmoke, "$KINETICS$", "$OUTPUT")

    response = HttpResponse(str(input_file))
    # response['content_type'] = 'application/pdf'
    response['Content-Disposition'] = 'attachment; filename= {}.dic'.format(pk)
    return response


@api_view(['GET'])
def download_respecth_file(request, pk):
    experiment = get_object_or_404(Experiment, pk=pk)
    respecth_file = experiment.xml_file
    if not respecth_file:
        content = 'Unable to create this input file'
        return Response(content, status=status.HTTP_404_NOT_FOUND)
    input_file = respecth_file

    response = HttpResponse(str(input_file))
    response['Content-Disposition'] = 'attachment; filename= {}.xml'.format(pk)
    return response


@api_view(['GET'])
def download_experiment_excel(request, pk):
    import sys

    df = utils.extract_experiment_table(pk, units_brackets=True, reorder=True)

    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False)
    writer.save()

    # FileResponse sets the Content-Disposition header so that browsers
    # present the option to save the file.
    response = HttpResponse(output.getvalue())
    response['content-type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    response['Content-Disposition'] = 'attachment; filename= {}.xlsx'.format(pk)

    return response


@api_view(['GET'])
def download_output_zip(request):
    output_root = Path(__location__) / 'output_experiments'
    exp_id = request.query_params.get('experiment', None)
    chem_models = request.query_params.getlist('chemModels[]', None)

    fp = OpenSmoke.retrieve_opensmoke_execution(exp_id, model_ids=chem_models, output_root=output_root)
    file = io.BytesIO()
    utils.zip_folders(file, fp, "{}__{}".format(exp_id, "-".join(chem_models)), remove_trailing=output_root)

    response = HttpResponse(file.getvalue())
    response['content-type'] = 'application/octet-stream'
    response['Content-Disposition'] = "attachment; filename={}__{}.zip".format(exp_id, "-".join(chem_models))

    return response


# TODO: rivedere, groupby df
@api_view(['GET'])
def download_cm_global(request):
    exp_ids = request.query_params.getlist('experiments[]', None)
    chem_models_ids = request.query_params.getlist('chemModels[]', None)

    cmr = models.CurveMatchingResult.objects.filter(execution_column__execution__chemModel__in=chem_models_ids,
                                                    execution_column__execution__experiment__in=exp_ids)

    result = []
    for i in cmr:
        if i.index is None or i.error is None:
            continue

        model_name = i.execution_column.execution.chemModel.name
        experiment_DOI = i.execution_column.execution.experiment.fileDOI
        execution_column = i.execution_column
        name = execution_column.name if not execution_column.species else execution_column.species[0]

        r = dict()
        r['model'] = model_name
        r['experiment'] = experiment_DOI
        r['name'] = name
        r['index'] = float(i.index)
        r['error'] = float(i.error)
        result.append(r)

    df = pd.DataFrame.from_dict(result)[['model', 'experiment', 'name', 'index', 'error']]
    df = df.groupby(["model", "name"]).mean()

    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer)
    writer.save()

    # FileResponse sets the Content-Disposition header so that browsers
    # present the option to save the file.
    response = HttpResponse(output.getvalue())
    response['content-type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    response['Content-Disposition'] = 'attachment; filename= curve_matching.xlsx'

    return response


@api_view(['GET'])
def get_username(request):
    username = request.user.username
    return JsonResponse({"username": username})


@api_view(['POST'])
def get_experiment_file(request, pk):
    exp = Experiment.objects.get(pk=pk)
    type = request.data['params']['type']
    if type == "OS":
        file = exp.os_input_file
    elif type == "ReSpecTh":
        file = exp.xml_file
    else:
        file = None

    response = {
        "file": file
    }
    return Response(response)


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

        check = utils.check_data_excel(data_frame) # null ed ha struttura qualcosa [unità]

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


class OSInputUploadView(APIView):

    def post(self, request):
        data = request.data['data'].read().decode("utf8")
        result = OpenSmokeParser.parse_input_string(data)
        return JsonResponse({"data": result})


class InputUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        data = request.data['input_dic'].read().decode("utf8")

        return JsonResponse({"data": data})



import ExperimentManager.Serializers as Serializers


@api_view(['POST'])
# @user_in_group("READ")
def getExperimentList(request):
    try:
        params = dict(request.data)
        try:
            fields = tuple(params['fields'])
        except KeyError:
            return Response(status=HTTP_400_BAD_REQUEST,
                            data="getExperimentList: KeyError in HTTP parameters. Missing parameter.")

        queryset = Experiment.objects.all()
        results = []

        for element in queryset:
            results.append(Serializers.ExperimentSerializer(element, fields=fields).data)

        return Response(json.dumps(results), status=HTTP_200_OK)

    except Exception:
        err_type, value, traceback = sys.exc_info()
        return Response(status=HTTP_500_INTERNAL_SERVER_ERROR,
                        data="getExperimentList: Generic error filtering the database. "
                             + str(err_type.__name__) + " : " + str(value))
    finally:
        close_old_connections()


@api_view(['POST'])
# @user_in_group("READ")
def getPropertyList(request):
    try:
        params = dict(request.data)
        try:
            name = params['name']
            exp_id = int(params['experiment'])
            fields = tuple(params['fields'])
        except KeyError:
            return Response(status=HTTP_400_BAD_REQUEST,
                            data="getCommonPropertyList: KeyError in HTTP parameters. Missing parameter.")

        model = eval(name)

        queryset = model.objects.filter(experiment__id=exp_id)
        results = []

        serializer = eval('Serializers.' + name + 'Serializer')

        for element in queryset:
            results.append(serializer(element, fields=fields).data)

        return Response(json.dumps(results), status=HTTP_200_OK)

    except Exception:
        err_type, value, traceback = sys.exc_info()
        return Response(status=HTTP_500_INTERNAL_SERVER_ERROR,
                        data="getCommonPropertyList: Generic error filtering the database. "
                             + str(err_type.__name__) + " : " + str(value))
    finally:
        close_old_connections()


@api_view(['POST'])
# @user_in_group("READ")
def getFilePaper(request):
    try:
        params = dict(request.data)
        try:
            exp_id = int(params['experiment'])
            fields = tuple(params['fields'])
        except KeyError:
            return Response(status=HTTP_400_BAD_REQUEST,
                            data="getCommonPropertyList: KeyError in HTTP parameters. Missing parameter.")

        file_paper = Experiment.objects.get(id=exp_id).file_paper

        results = [Serializers.FilePaperSerializer(file_paper, fields=fields).data]

        return Response(json.dumps(results), status=HTTP_200_OK)

    except Exception:
        err_type, value, traceback = sys.exc_info()
        return Response(status=HTTP_500_INTERNAL_SERVER_ERROR,
                        data="getCommonPropertyList: Generic error filtering the database. "
                             + str(err_type.__name__) + " : " + str(value))
    finally:
        close_old_connections()



