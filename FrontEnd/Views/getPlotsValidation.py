# Local import
import FrontEnd.views as View
import ExperimentManager.Models as Models
from ReSpecTh.Tool import visualizeExecution, resultExecutionVisualization
from FrontEnd.exceptions import ExecutionColumnError

# Django import
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST

# System import
import json
from collections import defaultdict
from FrontEnd.utils import *

class getPlotsValidation(View.FrontEndBaseView):
    viewName = __name__
    paramsType = {'target': str, 'query': dict, 'chemModel_ids': list, 'common_experiments': bool}
    defaultParams = {'common_experiments': False}
    required_groups = {'POST': ['READ']}

    def view_post(self, request):
        #
        # print(self.target)
        # print(self.query)
        # print(self.chemModel_ids)
        # print(self.common_experiments)

        chem_ids = [i for i in self.chemModel_ids if i != -1]
        r = []

        new = {
            **self.query,
            'execution__experiment__status': 'verified',
            'label': self.target,
            'execution__chemModel__id__in': chem_ids}

        models = check_models(self.chemModel_ids)
        if self.common_experiments and len(models) > 1:
            new = {**new, 'execution__experiment__id__in': common_execution_experiment_id(models[0], models[1])}

        exec_cols = Models.ExecutionColumn.objects.filter(**new).distinct()

        exec_ids = set([ec.execution.id for ec in exec_cols])

        exps = defaultdict(list)

        for exec_id in exec_ids:
            execution = Models.Execution.objects.get(id=exec_id)
            exps[execution.experiment.id].append(execution)

        try:
            for exp in exps:
                current = None
                for execution in exps[exp]:
                    consistency = visualizeExecution(execution, target=self.target, consist=current)
                    if not current:
                        current = consistency
                r.append(resultExecutionVisualization(current))


            return Response(json.dumps(r), status=HTTP_200_OK)

        except ExecutionColumnError as e:
            return Response(str(e), status=HTTP_400_BAD_REQUEST)
