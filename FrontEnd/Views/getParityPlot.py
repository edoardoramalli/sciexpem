# Local import
import FrontEnd.views as View
import ExperimentManager.Models as Models
from FrontEnd.exceptions import ExecutionColumnError
from ReSpecTh.Tool import Consistency, pairExecutionExperiment

# Django import
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST

# System import
import json
from FrontEnd.utils import *


class getParityPlot(View.FrontEndBaseView):
    viewName = __name__
    paramsType = {'target': str, 'query': dict, 'models': list}
    defaultParams = {'models': []}
    required_groups = {'POST': ['READ']}

    def view_post(self, request):

        new = {**self.query,
               'execution__experiment__status': 'verified',
               'label': self.target}

        models = check_models(self.models)
        if len(models) > 1:
            new = {**new,
                   'execution__experiment__id__in': common_execution_experiment_id(models[0],
                                                                                   models[1])}

        exec_cols = Models.ExecutionColumn.objects.filter(**new).distinct()

        exec_ids = set([ec.execution.id for ec in exec_cols])

        r = {}

        try:
            for exec_id in exec_ids:
                execution = Models.Execution.objects.get(id=exec_id)
                consistency = Consistency()

                for mapping in execution.experiment.experiment_interpreter.mappings.all():
                    results = pairExecutionExperiment(execution=execution, mapping=mapping, consistency=consistency)
                    for result in results:
                        if not result['valid']:
                            continue

                        x_exp = result['x_exp']
                        y_exp = result['y_exp']

                        max_x_exp = max(x_exp)

                        x_sim = result['x_sim']
                        y_sim = result['y_sim']

                        xy_sim = zip(x_sim, y_sim)
                        xy_sim = [xy for xy in xy_sim if xy[0] <= max_x_exp]
                        x_sim, y_sim = zip(*xy_sim)



                        x_dataColumn = result['x_dataColumn']
                        y_dataColumn = result['y_dataColumn']
                        x_execution_column = result['x_execution_column']
                        y_execution_column = result['y_execution_column']

                        if self.target:
                            if self.target != y_execution_column[0].label:
                                # print(y_execution_column[0].label)
                                continue

                        if x_dataColumn.name in r:
                            r[x_dataColumn.name]['data'] = r[x_dataColumn.name]['data'] + [(max(y_exp), max(y_sim))]
                            r[x_dataColumn.name]['info'] = r[x_dataColumn.name]['info'] + [execution.experiment.id]
                        else:
                            r[x_dataColumn.name] = {'data': [(max(y_exp), max(y_sim))],
                                                    'info': [execution.experiment.id]}

            return Response(json.dumps(r), status=HTTP_200_OK)

        except Exception as e:
            return Response(str(e), status=HTTP_400_BAD_REQUEST)
