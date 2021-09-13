# Local import
import ExperimentManager.views as View
from ExperimentManager.Models import *
from ExperimentManager.exceptions import *
from CurveMatching.CurveMatching import curveMatchingExecution
from OpenSmoke.OpenSmoke import getColumnNameSimulator
from django.http import HttpResponse


# Django import
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from django.db import transaction
from django.contrib.auth.models import User
from django.http import FileResponse

# System import
import zipfile
from io import BytesIO
import tempfile
import os

import pandas as pd

def create_report(exp_list, chemModel_list=[]):
    pass



class getReportSimulation(View.ExperimentManagerBaseView):
    viewName = 'getReportSimulation'
    paramsType = {'exp_list': list, 'chemModel_list': list}
    required_groups = {'POST': ['READ']}

    def view_post(self, request):

        if not self.exp_list:
            return Response('getReportSimulation. Select at least one experiment.', status=HTTP_400_BAD_REQUEST)
        self.exp_list = [int(x) for x in self.exp_list]
        self.chemModel_list = [int(x) for x in self.chemModel_list] if self.chemModel_list else None

        query = {
            'experiment__id__in': self.exp_list,
        }
        if self.chemModel_list:
            query['chemModel__id__in'] = self.chemModel_list

        execution_list = list(Execution.objects.filter(**query).distinct().values_list('id', flat=True))

        models = {}

        reports = {}

        for exec_id in execution_list:
            execution = Execution.objects.get(id=exec_id)
            model_name = execution.chemModel.name
            models[model_name] = models.get(model_name, []) + [execution]

        for model in models:
            result = []
            for execution in models[model]:
                exec_columns = execution.execution_columns.all()
                experiment = execution.experiment
                exp_id = experiment.id
                exp_doi = experiment.fileDOI
                model_name = execution.chemModel.name
                model_id = execution.chemModel.id
                fuels = experiment.fuels
                reactor = experiment.reactor
                exp_type = experiment.experiment_type
                phi = (float(experiment.phi_inf), float(experiment.phi_sup))
                temperature = (float(experiment.t_inf), float(experiment.t_sup))
                pressure = (float(experiment.p_inf), float(experiment.p_sup))
                for c in exec_columns:
                    if hasattr(c, 'curve_matching_result'):
                        d0L2 = float(c.curve_matching_result.d0L2)
                        d1L2 = float(c.curve_matching_result.d1L2)
                        d0Pe = float(c.curve_matching_result.d0Pe)
                        d1Pe = float(c.curve_matching_result.d1Pe)
                        score = float(c.curve_matching_result.score)
                        shift = float(c.curve_matching_result.shift)
                        error = float(c.curve_matching_result.error)
                        result.append({
                            'Experiment DOI': exp_doi,
                            'Exp SciExpeM ID': exp_id,
                            'Chem Model': model_name,
                            'Chem Model ID': model_id,
                            'Experiment Type': exp_type,
                            'Reactor': reactor,
                            'Target': c.label,
                            'Fuels': fuels,
                            'Phi': phi,
                            'Pressure (Bar)': pressure,
                            'Temperature (K)': temperature,
                            'Score': score,
                            'Error': error,
                            'd0L2': d0L2,
                            'd1L2': d1L2,
                            'd0Pe': d0Pe,
                            'd1Pe': d1Pe,
                            'shift': shift,
                        })

            reports[model] = pd.DataFrame(result)

        s = BytesIO()

        zf = zipfile.ZipFile(s, "w")

        for model in reports:
            output = BytesIO()
            reports[model].to_excel(output)
            zf.writestr(zinfo_or_arcname=model + '.xlsx', data=output.getvalue())

        zf.close()
        response_file = s.getvalue()

        response = HttpResponse(response_file)
        response['Content-Type'] = 'application/x-zip-compressed'
        response['Content-Disposition'] = 'attachment; filename=report.zip'
        return response

            # response = HttpResponse(response_file)
            # response['Content-Type'] = 'application/x-zip-compressed'
            # response['Content-Disposition'] = 'attachment; filename=report.zip'
            # return response

            # with tempfile.TemporaryDirectory() as sandbox:
            #     path = os.path.join(sandbox, 'report.zip')
            #     with open(path, 'wb') as file:
            #         file.write(response_file)
            #
            #
            #     # print(sandbox)
            #     # import time
            #     # time.sleep(60)
            #     # input('ciaoooo')
            #
            #     return sendfile(request, filename=path, attachment=True)

