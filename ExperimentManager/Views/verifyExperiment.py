# Local import
import ExperimentManager.views as View
from ExperimentManager.Models import *
from ExperimentManager.exceptions import *

# Django import
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from django.db import transaction


class verifyExperiment(View.ExperimentManagerBaseView):
    viewName = 'verifyExperiment'
    paramsType = {'status': str, 'exp_id': int}
    required_groups = {'POST': ['VALIDATE']}

    def view_post(self, request):
        try:
            with transaction.atomic():
                exp = Experiment.objects.get(pk=self.exp_id)
                exp.status = self.status
                exp.save()
        except ConstraintFieldExperimentError as e:
            return Response(status=HTTP_400_BAD_REQUEST, data="verifyExperiment: " + str(e))

        return Response(status=HTTP_200_OK, data="Experiment verified successfully.")