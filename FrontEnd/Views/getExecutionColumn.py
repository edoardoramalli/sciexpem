# Local import
import FrontEnd.views as View
import ExperimentManager.Models as Models
from ReSpecTh.Tool import visualizeExecution, resultExecutionVisualization
from FrontEnd.exceptions import ExecutionColumnError

# Django import
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST

# System import
import json
import pandas as pd

def supportGetExecutionColumn(execution):
    experiment = execution.experiment

    experiment_interpreter = experiment.experiment_interpreter

    mappings = Models.MappingInterpreter.objects.filter(experiment_interpreter__name=experiment_interpreter)

    result = {}

    for mapping in mappings:
        file = mapping.file
        y_sim_name = mapping.y_sim_name
        y_sim_location = mapping.y_sim_location
        x_sim_name = mapping.x_sim_name
        x_sim_location = mapping.x_sim_location

        # X SIM
        execution_filter_x = {'execution': execution, 'file_type': file, x_sim_location: x_sim_name}
        x_execution_column = Models.ExecutionColumn.objects.filter(**execution_filter_x)[0]

        x_sim_data = [float(x) for x in x_execution_column.data]
        x_sim_units = x_execution_column.units
        x_sim_label = x_execution_column.label

        # Y SIM
        execution_filter_y = {'execution': execution, 'file_type': file, y_sim_location: y_sim_name}
        y_execution_column = Models.ExecutionColumn.objects.filter(**execution_filter_y)[0]

        y_sim_data = [float(y) for y in y_execution_column.data]
        y_sim_units = y_execution_column.units
        y_sim_label = y_execution_column.label

        result[x_sim_label + '[' + x_sim_units + ']'] = x_sim_data
        result[y_sim_label + '[' + y_sim_units + ']'] = y_sim_data

    return pd.DataFrame.from_dict(result)


class getExecutionColumn(View.FrontEndBaseView):
    viewName = 'getExecutionColumn'
    paramsType = {'execution_id': int}
    required_groups = {'POST': ['READ']}

    def view_post(self):
        execution = Models.Execution.objects.get(id=self.execution_id)

        if not execution.execution_end:
            return Response('getExecutionColumn. Execution is not ended yet.', status=HTTP_400_BAD_REQUEST)

        df = supportGetExecutionColumn(execution)

        return Response(df.to_dict(orient="records"), HTTP_200_OK)




