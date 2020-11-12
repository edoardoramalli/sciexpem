from ExperimentManager import models
import pandas as pd
import zipfile
import os
import re

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
    dc = models.DataColumn.objects.filter(experiment_id=exp_id)

    # dict: name -> (units, data)
    column_names_units_data = {d.name if d.species is None else ",".join(d.species): (d.units, d.data) for d in dc}

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

    r = pd.DataFrame(dict(zip(column_names, column_data)))

    return r


def zip_folders(f, folders, zipname, remove_trailing=""):
    with zipfile.ZipFile(f, 'w') as myzip:
        for fp in folders:
            for root, dirs, files in os.walk(fp):
                for f in files:
                    new_name = os.path.relpath(os.path.join(root,f), remove_trailing)
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


