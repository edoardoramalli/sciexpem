# Local import
import ExperimentManager.views as View
from ExperimentManager.Models import *
from CurveMatching import CurveMatching

# Django import
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK


class getCurveMatching(View.ExperimentManagerBaseView):
    """
    Used by: UI -> {ExperimentTable: CurveMatching Raw Data, CurveMatching Bar Plot}
    Used by: API
    """
    viewName = 'getCurveMatching'
    paramsType = {'exp_id': list}
    required_groups = {'POST': ['READ']}

    def view_post(self, request):
        self.exp_id = [int(x) for x in self.exp_id]
        query = {'execution_column__execution__experiment__id__in': self.exp_id}
        result = CurveMatching.getCurveMatching(query)
        return Response(result, status=HTTP_200_OK)
