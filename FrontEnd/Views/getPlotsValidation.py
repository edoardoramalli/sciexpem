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


class getPlotsValidation(View.FrontEndBaseView):
    viewName = __name__
    paramsType = {'target': str, 'query': dict, 'chemModel_ids': list}
    required_groups = {'POST': ['READ']}

    def view_post(self, request):

        chem_ids = [i for i in self.chemModel_ids if i != -1]
        r = []

        new = {
            **self.query,
            'execution__experiment__status': 'verified',
            'label': self.target,
            'execution__chemModel__id__in': chem_ids}

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
                # print(current.experimental)

            return Response(json.dumps(r), status=HTTP_200_OK)

        except ExecutionColumnError as e:
            return Response(str(e), status=HTTP_400_BAD_REQUEST)
