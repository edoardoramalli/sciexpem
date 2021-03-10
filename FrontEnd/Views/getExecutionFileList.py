# Local import
import FrontEnd.views as View
import ExperimentManager.Models as Models

# Django import
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST

# System import
import json


class getExecutionFileList(View.FrontEndBaseView):
    viewName = 'getExecutionFileList'
    paramsType = {'execution_id': int}
    required_groups = {'POST': ['READ']}

    def view_post(self):
        experiment_interpreter = Models.Execution.objects.get(id=self.execution_id).experiment.experiment_interpreter
        mappings = Models.MappingInterpreter.objects.filter(experiment_interpreter__name=experiment_interpreter)
        files = list(set([mapping.file for mapping in mappings]))
        return Response(files, status=HTTP_200_OK)

