# Local import
import FrontEnd.views as View
import ExperimentManager.Models as Models
from ReSpecTh.Tool import visualizeAllExecution, resultExecutionVisualization
from FrontEnd.exceptions import ExecutionColumnError

# Django import
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST

# System import
import json


class getAllPlotExecution(View.FrontEndBaseView):
    viewName = 'getAllPlotExecution'
    paramsType = {'element_id': int}
    required_groups = {'POST': ['READ']}

    def view_post(self):
        try:
            experiment = Models.Experiment.objects.get(id=self.element_id)
            consistency = visualizeAllExecution(experiment)
            results = resultExecutionVisualization(consistency)
            return Response(json.dumps(results), status=HTTP_200_OK)
        except ExecutionColumnError as e:
            return Response(str(e), status=HTTP_400_BAD_REQUEST)
