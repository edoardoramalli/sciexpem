# Local import
import ExperimentManager.views as View
from ExperimentManager.Models import *
import ExperimentManager.Serializers as Serializers

# Django import
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST

import json


class requestPropertyList(View.ExperimentManagerBaseView):
    viewName = 'requestPropertyList'
    paramsType = {'model_name': str, 'element_id': int, 'fields': tuple}
    required_groups = {'POST': ['READ']}

    def view_post(self, request):
        model = eval(self.model_name)

        element = model.objects.get(id=self.element_id)

        serializer = eval('Serializers.' + self.model_name + 'Serializer')

        results = serializer(element, fields=self.fields).data

        return Response(json.dumps(results), status=HTTP_200_OK)

