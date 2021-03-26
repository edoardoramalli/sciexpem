# Local import
import FrontEnd.views as View
from ExperimentManager.Models import DataColumn
# Django import
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST

# System import
import json
import pandas as pd


def create_header(column):
    text = ''
    if not column.species:
        if column.name != 'uncertainty':
            text = column.name + " [" + column.units + "]" + " (" + str(column.source_type) + ")"
        else:
            text = column.name + " [" + column.units + "]" + " --> " + str(column.uncertainty.name) + " (" + str(
                column.source_type) + ", " + str(column.uncertainty_kind) + ", " + str(
                column.uncertainty_bound) + ")"
    else:
        text = column.label + " [" + column.units + "]" + " (" + str(column.source_type) + ")"
    return text


def sort_columns(columns):
    priority = ['temperature', 'time']
    result = []
    for column in columns:
        if any(word in column for word in priority):
            result.insert(0, column)
        else:
            result.append(column)
    return result


class getRawData(View.FrontEndBaseView):
    viewName = 'getRawData'
    paramsType = {'experiment_id': int, 'type': str}
    required_groups = {'POST': ['WRITE']}

    def view_post(self):
        if self.type == 'data':
            dg_label = ['experimental_data', 'initial_condition']
        elif self.type == 'profile':
            dg_label = ['V-t history', 'p-t history', 'T-t history']
        else:
            return Response(self.viewName + ": Type not valid.", status=HTTP_400_BAD_REQUEST)

        data_columns = DataColumn.objects.filter(experiment__id=self.experiment_id, dg_label__in=dg_label)

        columns_dg = {}
        headers_dg = {}
        type_dg = {}

        for column in data_columns:
            if column.dg_id not in columns_dg:
                columns_dg[column.dg_id] = [list(map(lambda x: float(x), column.data))]
                headers_dg[column.dg_id] = [create_header(column)]
                type_dg[column.dg_id] = column.dg_label
            else:
                columns_dg[column.dg_id].append(list(map(lambda x: float(x), column.data)))
                headers_dg[column.dg_id].append(create_header(column))

        result_dg = {}

        for dg in columns_dg:
            df = pd.DataFrame(dict(zip(headers_dg[dg], columns_dg[dg])))
            columns_header = sort_columns(list(df.columns))
            content = df.to_dict(orient="records")
            result_dg[dg] = {'header': columns_header, 'data': content, 'type': type_dg[dg]}

        # print(headers_dg)
        #
        # if len(data_columns) > 0:
        #     header = [create_header(column) for column in data_columns]
        #
        #     data = [list(map(lambda x: float(x), column.data)) for column in data_columns]
        #     print(header)
        #
        #     df = pd.DataFrame(dict(zip(header, data)))
        #
        #     columns = sort_columns(list(df.columns))
        #     content = df.to_dict(orient="records")
        #     print(columns, content)

        # return Response({"header": columns, "data": content}, status=HTTP_200_OK)

        return Response(result_dg, status=HTTP_200_OK)

