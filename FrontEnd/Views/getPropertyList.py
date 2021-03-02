# Local import
import FrontEnd.views as View
from ExperimentManager.Models import *  # TODO capire perchè questo cosi va ma se lo metto come quello dopo no
import ExperimentManager.Serializers as Serializers

# Django import
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK

# System import
import json


class getPropertyList(View.FrontEndBaseView):
    viewName = 'getPropertyList'
    paramsType = {'fields': tuple, 'name': str, 'exp_id': int}
    required_groups = {'POST': ['READ']}

    def view_post(self):
        model = eval(self.name)
        queryset = model.objects.filter(experiment__id=self.exp_id)
        results = []
        serializer = eval('Serializers.' + self.name + 'Serializer')
        for element in queryset:
            results.append(serializer(element, fields=self.fields).data)
        return Response(json.dumps(results), status=HTTP_200_OK)

