# Local import
import ExperimentManager.views as View
from OpenSmoke.SimulationSummary.createSummary import create_summary

# Django import
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK
from django.db.models import Q


class getSimulation(View.ExperimentManagerBaseView):
    """
    Used by: ?
    Used by: API
    """
    viewName = 'getSimulation'
    paramsType = {'exp_id': int}
    required_groups = {'POST': ['READ']}

    def view_post(self, request):
        return Response(create_summary(self.exp_id), status=HTTP_200_OK)
