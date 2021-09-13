# Local import
import FrontEnd.views as View
import ExperimentManager.Models as Models
import ExperimentManager.Serializers as Serializers

# Django import
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK

# System import
import json


class getSpecieList(View.FrontEndBaseView):
    viewName = 'getSpecieList'
    paramsType = {'fields': tuple, 'args': dict}
    required_groups = {'POST': ['READ']}

    def view_post(self, request):
        queryset = Models.Specie.objects.filter(**self.args).distinct()
        results = []
        for element in queryset:
            results.append(Serializers.SpecieSerializer(element).data)
        return Response(json.dumps(results), status=HTTP_200_OK)

