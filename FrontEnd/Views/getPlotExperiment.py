# Local import
import FrontEnd.views as View
import ExperimentManager.Models as Models
from ReSpecTh.Tool import visualizeExperiment

# Django import
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST

# System import
import json


class getPlotExperiment(View.FrontEndBaseView):
    viewName = 'getPlotExperiment'
    paramsType = {'exp_id': int}
    required_groups = {'POST': ['READ']}

    def view_post(self):
        experiment = Models.Experiment.objects.get(id=self.exp_id)
        if experiment.experiment_interpreter is None:
            return Response(status=HTTP_400_BAD_REQUEST, data="getPlotExperiment: Experiment is not managed.")
        results = visualizeExperiment(experiment)
        return Response(json.dumps(results), status=HTTP_200_OK)


