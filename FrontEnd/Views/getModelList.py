# Local import
import FrontEnd.views as View
import ExperimentManager.Models as Models
import ExperimentManager.Serializers as Serializers

# Django import
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK

# System import
import json


class getModelList(View.FrontEndBaseView):
    viewName = 'getModelList'
    paramsType = {'fields': tuple}
    required_groups = {'POST': ['READ']}

    def view_post(self):
        queryset = Models.ChemModel.objects.all()
        results = []

        for element in queryset:
            results.append(Serializers.ChemModelSerializer(element, fields=self.fields).data)

        return Response(json.dumps(results), status=HTTP_200_OK)
