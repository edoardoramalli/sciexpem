# Local import
import FrontEnd.views as View
import ExperimentManager.Models as Models
from ReSpecTh.Tool import visualizeExecution, resultExecutionVisualization

# Django import
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK

# System import
import json


class getPlotExecution(View.FrontEndBaseView):
    viewName = 'getPlotExecution'
    paramsType = {'e_id': int}
    required_groups = {'POST': ['READ']}

    def view_post(self):
        execution = Models.Execution.objects.get(id=self.e_id)
        consistency = visualizeExecution(execution)
        results = resultExecutionVisualization(consistency)
        return Response(json.dumps(results), status=HTTP_200_OK)
