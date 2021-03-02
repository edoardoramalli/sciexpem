# Local import
import FrontEnd.views as View
import ExperimentManager.Models as Models
from ReSpecTh.Tool import visualizeAllExecution, resultExecutionVisualization

# Django import
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK

# System import
import json


class getAllPlotExecution(View.FrontEndBaseView):
    viewName = 'getAllPlotExecution'
    paramsType = {'e_id': int}
    required_groups = {'POST': ['READ']}

    def view_post(self):
        experiment = Models.Experiment.objects.get(id=self.e_id)
        consistency = visualizeAllExecution(experiment)
        results = resultExecutionVisualization(consistency)
        return Response(json.dumps(results), status=HTTP_200_OK)
