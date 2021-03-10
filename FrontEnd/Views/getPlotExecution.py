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


class getPlotExecution(View.FrontEndBaseView):
    viewName = 'getPlotExecution'
    paramsType = {'element_id': int}
    required_groups = {'POST': ['READ']}

    def view_post(self):
        execution = Models.Execution.objects.get(id=self.element_id)
        try:
            consistency = visualizeExecution(execution)
            results = resultExecutionVisualization(consistency)
            return Response(json.dumps(results), status=HTTP_200_OK)
        except ExecutionColumnError as e:
            return Response(str(e), status=HTTP_400_BAD_REQUEST)
