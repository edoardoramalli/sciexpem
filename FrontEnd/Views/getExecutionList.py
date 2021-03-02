# Local import
import FrontEnd.views as View
import ExperimentManager.Models as Models
import ExperimentManager.Serializers as Serializers

# Django import
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK

# System import
import json


class getExecutionList(View.FrontEndBaseView):
    viewName = 'getExecutionList'
    paramsType = {'fields': tuple, 'exp_id': int}
    required_groups = {'POST': ['READ']}

    def view_post(self):
        queryset = Models.Execution.objects.filter(experiment__id=self.exp_id)
        results = []
        for element in queryset:
            results.append(Serializers.ExecutionSerializer(element, fields=self.fields).data)
        return Response(json.dumps(results), status=HTTP_200_OK)
