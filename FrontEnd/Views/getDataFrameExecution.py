# Local import
import FrontEnd.views as View
import ExperimentManager.Models as Models
from FrontEnd.exceptions import ExecutionColumnError
from ReSpecTh.Tool import Consistency, pairExecutionExperiment

# Django import
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from django.core.exceptions import FieldError
# System import
import json

import pandas as pd
from FrontEnd.utils import *

class getDataFrameExecution(View.FrontEndBaseView):
    viewName = __name__
    paramsType = {'chemModel_id': str, 'attributes': tuple, 'models': list}
    defaultParams = {'models': []}
    required_groups = {'POST': ['READ']}

    def view_post(self, request):
        try:
            new = {'execution_column__execution__experiment__status': 'verified', 'execution_column__execution__chemModel__id': self.chemModel_id}

            models = check_models(self.models)
            if len(models) > 1:
                new = {**new,
                       'execution_column__execution__experiment__id__in': common_execution_experiment_id(models[0],
                                                                                                         models[1])}
            cms = Models.CurveMatchingResult.objects.filter(**new).distinct().values(*self.attributes)
        except FieldError as e:
            return Response(str(e), status=HTTP_400_BAD_REQUEST)

        df = pd.DataFrame(cms)
        df = df.fillna('')

        return Response(df.to_dict('records'), status=HTTP_200_OK)
