# Local import
import ExperimentManager.views as View
from ExperimentManager.Models import *

# Django import
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK


class getCurveMatching(View.ExperimentManagerBaseView):
    viewName = 'getCurveMatching'
    paramsType = {'exp_id': int}
    required_groups = {'POST': ['READ']}

    def view_post(self, request):
        # All the CM of an experiment
        cm_results = CurveMatchingResult.objects.filter(execution_column__execution__experiment__id=self.exp_id)

        model_list = []

        for result in cm_results:
            model_name = result.execution_column.execution.chemModel.name
            model_list.append({'name': model_name, 'score': result.score, 'error': result.error})

        return Response(model_list, status=HTTP_200_OK)
