# Local import
import FrontEnd.views as View
import ExperimentManager.Models as Models
from django.shortcuts import get_object_or_404
from FrontEnd import utils
from FrontEnd.Views.getExecutionColumn import supportGetExecutionColumn

# Django import
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_200_OK
from django.http import HttpResponse

# System import
import io
import pandas as pd
import zipfile
from io import BytesIO


class downloadFile(View.FrontEndBaseView):
    viewName = 'downloadFile'
    paramsType = {'element_id': int, 'file': str, 'model_name': str}
    required_groups = {'POST': []}

    def view_post(self, request):

        response_file = None

        # print(self.element_id, self.file, self.model_name)

        if self.model_name == 'Experiment':
            experiment = get_object_or_404(Models.Experiment, pk=self.element_id)
            if self.file == 'OpenSMOKEpp':
                response_file = bytes(experiment.os_input_file, 'utf-8')
            elif self.file == 'ReSpecTh':
                response_file = bytes(experiment.xml_file, 'utf-8')
            elif self.file == 'excel':
                sheets = utils.extract_experiment_table(self.element_id, units_brackets=True, reorder=True)
                output = io.BytesIO()
                writer = pd.ExcelWriter(output, engine='xlsxwriter')
                for sheet in sheets:
                    sheets[sheet].to_excel(writer, sheet_name=sheet, index=False)
                writer.save()
                response_file = output.getvalue()
            else:
                Response(data=self.viewName + ": KeyError in HTTP parameters. Wrong file type.",
                         status=HTTP_400_BAD_REQUEST)
        elif self.model_name == 'ChemModel':
            if self.file == 'model':
                model = get_object_or_404(Models.ChemModel, pk=self.element_id)
                xml_file_reaction_names = model.xml_file_reaction_names_file
                xml_file_kinetics = model.xml_file_kinetics_file

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

                response_file = bytes(df.to_csv(index=False), 'utf-8')
            else:
                Response(data=self.viewName + ": KeyError in HTTP parameters. Wrong file type.",
                         status=HTTP_400_BAD_REQUEST)
        elif self.model_name == 'ExperimentBackUp':
            if self.file == 'backup':
                obj = get_object_or_404(Models.ExperimentBackUp, pk=self.element_id)
                file_binary = obj.file_binary
                response_file = file_binary

            else:
                Response(data=self.viewName + ": KeyError in HTTP parameters. Wrong file type.",
                         status=HTTP_400_BAD_REQUEST)
        else:
            Response(data=self.viewName + ": KeyError in HTTP parameters. Wrong model name.",
                     status=HTTP_400_BAD_REQUEST)

        if not response_file:
            return Response('File Not Found!', status=HTTP_400_BAD_REQUEST)

        # response = HttpResponse(response_file)
        # response['Content-Disposition'] = 'attachment; filename= {}'.format(self.element_id)
        # return response
        # print(type(response_file), self.model_name, self.file)
        return Response({'data_bytes': response_file.hex()},  status=HTTP_200_OK)


