# Local import
import FrontEnd.views as View
import ExperimentManager.Models as Models
from django.shortcuts import get_object_or_404
from FrontEnd import utils

# Django import
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST
from django.http import HttpResponse

# System import
import io
import pandas as pd


class downloadExperimentFile(View.FrontEndBaseView):
    viewName = 'downloadExperimentFile'
    paramsType = {'exp_id': int, 'file': str}
    required_groups = {'GET': ['READ']}

    def view_get(self):
        experiment = get_object_or_404(Models.Experiment, pk=self.exp_id)

        response_file = None

        if self.file == 'OpenSMOKEpp':
            response_file = experiment.os_input_file
        elif self.file == 'ReSpecTh':
            response_file = experiment.xml_file
        elif self.file == 'excel':
            df = utils.extract_experiment_table(self.exp_id, units_brackets=True, reorder=True)
            output = io.BytesIO()
            writer = pd.ExcelWriter(output, engine='xlsxwriter')
            df.to_excel(writer, index=False)
            writer.save()
            response_file = output.getvalue()
        else:
            Response(data=self.viewName + ": KeyError in HTTP parameters. Wrong file type.",
                     status=HTTP_400_BAD_REQUEST)

        if not response_file:
            return Response('File Not Found!', status=HTTP_400_BAD_REQUEST)

        response = HttpResponse(response_file)
        response['Content-Disposition'] = 'attachment; filename= {}'.format(self.exp_id)
        return response


