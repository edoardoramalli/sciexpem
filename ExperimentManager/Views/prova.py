# Local import
import ExperimentManager.views as View
from ExperimentManager.Models import *
from ExperimentManager.exceptions import *
from CurveMatching.CurveMatching import curveMatchingExecution
from OpenSmoke.OpenSmoke import getColumnNameSimulator
from django.db.models import Q

# Django import
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from django.db import transaction
from django.contrib.auth.models import User
from django.http import FileResponse

import pandas as pd


class prova(View.ExperimentManagerBaseView):
    viewName = 'prova'
    paramsType = {}
    # paramsType = {'status': str, 'exp_id': int}

    required_groups = {'POST': []}

    def view_post(self, request):
        # users = []
        #
        # for user in User.objects.all():
        #     users.append({'username': user.username,
        #                   'first_name': user.first_name,
        #                   'last_name': user.last_name,
        #                   'email': user.email,
        #                   'is_staff': user.is_staff,
        #                   'groups': [group for group in list(user.groups.values_list('name', flat=True))]})


        # # file = open('/Users/edoardo/Documents/GitHub/sciexpem/Files/fuels', 'r')
        # r = FileResponse(filename='/Users/edoardo/Documents/GitHub/sciexpem/Files/fuels', as_attachment=True)
        # # file.close()
        # r['Content-Type'] = 'application/octet-stream'
        # return r


        # a = [140, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160]
        #
        # models = {}
        #
        # for exec_id in a:
        #     execution = Execution.objects.get(id=exec_id)
        #     model_name = execution.chemModel.name
        #     models[model_name] = models.get(model_name, []) + [execution]
        #
        # for model in models:
        #     result = []
        #     for execution in models[model]:
        #         exec_columns = execution.execution_columns.all()
        #         experiment = execution.experiment
        #         exp_id = experiment.id
        #         exp_doi = experiment.fileDOI
        #         model_name = execution.chemModel.name
        #         fuels = experiment.fuels
        #         reactor = experiment.reactor
        #         exp_type = experiment.experiment_type
        #         phi = (experiment.phi_inf, experiment.phi_sup)
        #         temperature = (experiment.t_inf, experiment.t_sup)
        #         pressure = (experiment.p_inf, experiment.p_sup)
        #         for c in exec_columns:
        #             if hasattr(c, 'curve_matching_result'):
        #                 d0L2 = float(c.curve_matching_result.d0L2)
        #                 d1L2 = float(c.curve_matching_result.d1L2)
        #                 d0Pe = float(c.curve_matching_result.d0Pe)
        #                 d1Pe = float(c.curve_matching_result.d1Pe)
        #                 score = float(c.curve_matching_result.score)
        #                 shift = float(c.curve_matching_result.shift)
        #                 error = float(c.curve_matching_result.error)
        #                 result.append({
        #                     'Experiment DOI': exp_doi,
        #                     'Exp SciExpeM ID': exp_id,
        #                     'Chem Model': model_name,
        #                     'Experiment Type': exp_type,
        #                     'Reactor': reactor,
        #                     'Object': c.label,
        #                     'Fuels': fuels,
        #                     'Phi': phi,
        #                     'Pressure (Bar)': pressure,
        #                     'Temperature (K)': temperature,
        #                     'Score': score,
        #                     'Error': error,
        #                     'd0L2': d0L2,
        #                     'd1L2': d1L2,
        #                     'd0Pe': d0Pe,
        #                     'd1Pe': d1Pe,
        #                     'shift': shift,
        #                 })
        #
        #     df = pd.DataFrame(result)
        #     print(df)


        # species = set([])
        #
        # intial = InitialSpecie.objects.all()
        # for i in intial:
        #     species.add(i.name)
        #
        # dc = DataColumn.objects.filter(name='composition')
        # print(len(dc))
        # for d in dc:
        #     for s in d.species:
        #         species.add(s)
        #
        # print(species)
        # print(len(species))
        # r = []
        #
        # ended = Execution.objects.filter(~Q(execution_end=None))
        #
        #
        # print(list(set([exec.experiment.id for exec in ended if exec.experiment.status=='verified'])))
        #
        # for end in ended:
        #     exec_columns = end.execution_columns.all()
        #     tmp = True
        #     for column in exec_columns:
        #         if CurveMatchingResult.objects.filter(execution_column=column).exists():
        #             tmp = False
        #             break
        #     if tmp:
        #         r.append(end.id)
        #
        #
        # print(len(ended))
        # print(r)

        # r = {}
        #
        #
        #
        # executions = Execution.objects.filter(experiment__fuels=['H2'], experiment__status='verified').exclude(execution_end=None)
        #
        # for exec in executions:
        #     exp_id = exec.experiment.id
        #     r[exp_id] = r.get(exp_id, 0) + 1
        #
        #
        # print([k for k in r if r[k] > 1])
        #
        # # Execution.objects.get(id=208).delete()

        import time
        time.sleep(20)

        print('edoooooooooooooo')

        return Response(status=HTTP_200_OK)
