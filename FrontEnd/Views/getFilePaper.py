# Local import
import FrontEnd.views as View
import ExperimentManager.Models as Models
import ExperimentManager.Serializers as Serializers

# Django import
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK

# System import
import json


class getFilePaper(View.FrontEndBaseView):
    viewName = 'getFilePaper'
    paramsType = {'fields': tuple, 'exp_id': int}
    required_groups = {'POST': ['READ']}

    def view_post(self):
        file_paper = Models.Experiment.objects.get(id=self.exp_id).file_paper

        results = [Serializers.FilePaperSerializer(file_paper, fields=self.fields).data]

        return Response(json.dumps(results), status=HTTP_200_OK)


