# Local import
import FrontEnd.views as View
import ExperimentManager.Models as Models
from OpenSmoke.OpenSmoke import OpenSmokeParser

# Django import
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST
from django.http import HttpResponse
from django.db import transaction
from django.utils import timezone

# System import
import zipfile
from io import BytesIO


class addExecution(View.FrontEndBaseView):
    viewName = 'addExecution'
    paramsType = {'experiment_id': int, 'chemModel_id': int}
    required_groups = {'GET': ['READ']}

    def view_get(self, request):

        if Models.Execution.objects.filter(experiment_id=self.experiment_id, chemModel_id=self.chemModel_id).exists():
            return Response('addExecution. Execution already exists!', status=HTTP_400_BAD_REQUEST)

        with transaction.atomic():

            experiment = Models.Experiment.objects.get(id=self.experiment_id)
            if experiment.status != 'verified':
                return Response('addExecution. Experiment is not verified!', status=HTTP_400_BAD_REQUEST)

            chemModel = Models.ChemModel.objects.get(id=self.chemModel_id)

            xml_file_kinetics = chemModel.xml_file_kinetics
            xml_file_reaction_names = chemModel.xml_file_reaction_names
            open_smoke_input_file = experiment.os_input_file

            open_smoke_input_text = OpenSmokeParser.create_output(open_smoke_input_file, './kinetics', '.')

            s = BytesIO()
            zf = zipfile.ZipFile(s, "w")
            zf.writestr(zinfo_or_arcname='/kinetics/kinetics.xml', data=xml_file_kinetics)
            zf.writestr(zinfo_or_arcname='/kinetics/reaction_names.xml', data=xml_file_reaction_names)
            zf.writestr(zinfo_or_arcname='input.dic', data=open_smoke_input_text)
            zf.close()

            response_file = s.getvalue()

            new_exec = Models.Execution(
                experiment=experiment,
                chemModel=chemModel,
                execution_start=timezone.localtime(),
                # username=request.user.username,
                username='pippo'
            )

            new_exec.save()

            response = HttpResponse(response_file)
            response['Content-Disposition'] = 'attachment; filename= {}'.format(self.experiment_id)
            return response


