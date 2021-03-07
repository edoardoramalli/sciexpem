# Local import
import ExperimentManager.views as View
from ExperimentManager.Models import *

# Django import
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN

import json


class deleteElement(View.ExperimentManagerBaseView):
    viewName = 'deleteElement'
    paramsType = {'model_name': str, 'element_id': int}
    required_groups = {'POST': []}

    def view_post(self, request):
        if not request.user.is_authenticated:
            return Response("deleteElement. User is not authenticated.", status=HTTP_401_UNAUTHORIZED)

        supported_models = ['ChemModel', 'FilePaper', 'Experiment', 'Execution', 'CurveMatchingResult',
                            'ExperimentInterpreter']

        if self.model_name not in supported_models:
            return Response(status=HTTP_400_BAD_REQUEST,
                            data=self.viewName + ": Model '{}' not supported yet.".format(self.model_name))

        try:
            model = eval(self.model_name)
        except NameError:
            return Response(status=HTTP_400_BAD_REQUEST,
                            data=self.viewName + ": NameError. Model '{}' not exist.".format(self.model_name))

        if self.model_name == 'Experiment' and model.objects.get(pk=self.element_id).status == 'verified':
            if not (request.user.is_superuser or request.user.groups.filter(name="DELETE").exists()):
                return Response(self.viewName + ": User does not have permission.", status=HTTP_403_FORBIDDEN)
        elif self.model_name == 'Execution' and model.objects.get(pk=self.element_id).execution_end:
            if not (request.user.is_superuser or request.user.groups.filter(name="DELETE").exists()):
                return Response(self.viewName + ": User does not have permission.", status=HTTP_403_FORBIDDEN)
        elif self.model_name != 'Experiment':
            if not (request.user.is_superuser or request.user.groups.filter(name="DELETE").exists()):
                return Response(self.viewName + ": User does not have permission.", status=HTTP_403_FORBIDDEN)

        model.objects.get(pk=self.element_id).delete()

        return Response("{} element deleted successfully.".format(self.model_name), status=HTTP_200_OK)
