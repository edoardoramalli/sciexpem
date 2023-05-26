from ExperimentManager import models
from ExperimentManager.Models import *
import pandas as pd
import zipfile
import os
import re
from django.db.models import Q

# def curve_io_formatter(x_column, y_columns, y_names, x_axis, y_axis, log=False):
#     curves = []
#     for index, output in enumerate(y_columns):
#         curve = {round(float(k), 3): round(float(v), 3) for k, v in zip(x_column, output)}
#         curves.append({"name": y_names[index], "data": curve})
#     return {"curves": curves, "x_axis": x_axis, "y_axis": y_axis, "log": log}

excel_column_pattern = re.compile("(?P<name>[A-Za-z 0-9_/]*)[ \t]+\[(?P<units>[(A-Za-z 0-9_/)]*)\]")


def curve_io_formatter(curves, x_axis, y_axis, logY=False):
    return {"curves": curves, "x_axis": x_axis, "y_axis": y_axis, "logY": logY}


def extract_experiment_table(exp_id, units_row=False, units_brackets=True, reorder=True):
    # TODO ci deve essere in tutto sciexpem UNA SINGOLA funzione che dato un exp telo trasforma in una lista di df
    # uno per dg. e può contenere o meno i profili. incertezze con le giuste info etc....
    dgs = sorted([x[0] for x in set(DataColumn.objects.filter(experiment_id=exp_id).values_list('dg_id'))]) # TODO non funziona il sort. sorta le string e non i numeri nella stringa...

    sheets = {}

    for dg in dgs:
        dc = DataColumn.objects.filter(experiment_id=exp_id, dg_id=dg)

        # dict: name -> (units, data)
        column_names_units_data = {d.name if not d.species_object.all().exists() else ",".join([s.preferredKey for s in d.species_object.all()]): (d.units, d.data) for d in dc}

        column_names = list(column_names_units_data.keys())

        # we can freely reorder names
        # if reorder:
        #     e = models.Experiment.objects.get(pk=exp_id)
        #     # if (
        #     #         e.reactor == "shock tube" and e.experiment_type == "ignition delay measurement") or e.reactor == "stirred reactor":
        #     #     column_names.remove("temperature")
        #     #     column_names.insert(0, "temperature")

        # units and data are taken as a consequence of the reordered names
        column_units = [column_names_units_data[cn][0] for cn in column_names]
        column_data = [[float(i) for i in column_names_units_data[cn][1]] for cn in
                       column_names]  # decimal to float (for excel seeing it as a number)

        if units_row:
            column_data = [[i] + j for i, j in zip(column_units, column_data)]

        if units_brackets:
            column_names = ["{} [{}]".format(i, j) for i, j in zip(column_names, column_units)]

        # print(dict(zip(column_names, column_data)))
        # print(len(column_names[0]))
        # print(len(column_data[0]), len(column_data[1]))
        # print(column_names)

        sheets[dg] = pd.DataFrame(dict(zip(column_names, column_data)))

    return sheets


def zip_folders(f, folders, zipname, remove_trailing=""):
    with zipfile.ZipFile(f, 'w') as myzip:
        for fp in folders:
            for root, dirs, files in os.walk(fp):
                for f in files:
                    new_name = os.path.relpath(os.path.join(root, f), remove_trailing)
                    myzip.write(os.path.join(root, f), arcname=new_name)


def check_data_excel(df):
    # check if the dataframe contain nan
    has_nan = df.isnull().values.any()

    if has_nan:
        return False

    columns = df.columns

    for column in columns:
        p = excel_column_pattern.match(column)
        if not p:
            return False

    return True


def split_header(line):
    line = line.strip()
    index_start = line.find("[")
    index_end = line.rfind("]")
    name = line[: index_start].strip()
    unit = line[index_start + 1: index_end].strip()
    return name, unit


def common_execution_experiment_id(modelA_id, modelB_id):
    e_a = Execution.objects.filter(Q(chemModel__id=modelA_id) & ~Q(execution_end=None) & (Q(execution_error='') | Q(execution_error=None))).values_list('experiment__id', flat=True)
    e_b = Execution.objects.filter(Q(chemModel__id=modelB_id) & ~Q(execution_end=None) & (Q(execution_error='') | Q(execution_error=None))).values_list('experiment__id', flat=True)
    return list(set(e_a).intersection(set(e_b)))


def check_models(input_models: list):
    # Assumo che indici validi dell'id del modello siano >=0
    return [model_id for model_id in input_models if model_id and model_id >= 0]