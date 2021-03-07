# Local import
import FrontEnd.views as View
import ExperimentManager.Models as Models
from django.shortcuts import get_object_or_404
from FrontEnd import utils
from FrontEnd.Views.getExecutionColumn import supportGetExecutionColumn

# Django import
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST
from django.http import HttpResponse

# System import
import io
import pandas as pd
import zipfile
from io import BytesIO


class downloadFile(View.FrontEndBaseView):
    viewName = 'downloadFile'
    paramsType = {'element_id': int, 'file': str, 'model_name': str}
    required_groups = {'GET': ['READ']}

    def view_get(self, request):

        response_file = None

        if self.model_name == 'Experiment':
            experiment = get_object_or_404(Models.Experiment, pk=self.element_id)

            if self.file == 'OpenSMOKEpp':
                response_file = experiment.os_input_file
            elif self.file == 'ReSpecTh':
                response_file = experiment.xml_file
            elif self.file == 'excel':
                df = utils.extract_experiment_table(self.element_id, units_brackets=True, reorder=True)
                output = io.BytesIO()
                writer = pd.ExcelWriter(output, engine='xlsxwriter')
                df.to_excel(writer, index=False)
                writer.save()
                response_file = output.getvalue()
            else:
                Response(data=self.viewName + ": KeyError in HTTP parameters. Wrong file type.",
                         status=HTTP_400_BAD_REQUEST)
        elif self.model_name == 'ChemModel':
            if self.file == 'model':
                model = get_object_or_404(Models.ChemModel, pk=self.element_id)
                xml_file_reaction_names = model.xml_file_reaction_names
                xml_file_kinetics = model.xml_file_kinetics

                s = BytesIO()
                zf = zipfile.ZipFile(s, "w")

                zf.writestr(zinfo_or_arcname='reaction_names.xml', data=xml_file_reaction_names)
                zf.writestr(zinfo_or_arcname='kinetics.xml', data=xml_file_kinetics)

                zf.close()
                response_file = s.getvalue()

            else:
                Response(data=self.viewName + ": KeyError in HTTP parameters. Wrong file type.",
                         status=HTTP_400_BAD_REQUEST)
        elif self.model_name == 'Execution':
            if self.file == 'rawData':

                execution = Models.Execution.objects.get(id=self.element_id)

                if not execution.execution_end:
                    return Response('getExecutionColumn. Execution is not ended yet.', status=HTTP_400_BAD_REQUEST)

                df = supportGetExecutionColumn(execution)

                response_file = df.to_csv(index=False)
            else:
                Response(data=self.viewName + ": KeyError in HTTP parameters. Wrong file type.",
                         status=HTTP_400_BAD_REQUEST)
        else:
            Response(data=self.viewName + ": KeyError in HTTP parameters. Wrong model name.",
                     status=HTTP_400_BAD_REQUEST)

        if not response_file:
            return Response('File Not Found!', status=HTTP_400_BAD_REQUEST)

        response = HttpResponse(response_file)
        response['Content-Disposition'] = 'attachment; filename= {}'.format(self.element_id)
        return response


