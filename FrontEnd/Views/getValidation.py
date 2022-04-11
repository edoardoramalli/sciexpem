# Local import
import FrontEnd.views as View
import ExperimentManager.Models as Models
import ExperimentManager.Serializers as Serializers
from FrontEnd.utils import *
# Django import
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST

# System import
import json
from statistics import stdev, variance, mean, median, StatisticsError


class getValidation(View.FrontEndBaseView):
    viewName = 'getValidation'
    paramsType = {'query': dict, 'models': list}
    defaultParams = {'models': []}
    required_groups = {'POST': ['READ']}

    def view_post(self, request):
        new = {'execution_column__execution__experiment__status': 'verified', **self.query}

        models = check_models(self.models)

        if len(models) == 0:
            return Response('Empty Model List', status=HTTP_400_BAD_REQUEST)

        if len(models) > 1:
            common = common_execution_experiment_id(models[0], models[1])
            new = {**new, 'execution_column__execution__experiment__id__in': common}

        queryset = {model_id: Models.CurveMatchingResult.objects.filter(**new) for model_id in models}

        results = {model_id: [] for model_id in models}

        for model in queryset:
            # model_tot[model] = queryset[model].values('execution_column__execution__experiment__id').distinct().count()
            for cm in queryset[model]:

                score = float(cm.score)
                d0L2 = float(cm.d0L2)
                d1L2 = float(cm.d1L2)
                d0Pe = float(cm.d0Pe)
                d1Pe = float(cm.d1Pe)
                shift = float(cm.shift)

                info = {'score': score, 'd0L2': d0L2, 'd1L2': d1L2, 'd0Pe': d0Pe, 'd1Pe': d1Pe, 'shift': shift, 'id': cm.execution_column.execution.experiment.id}

                results[model].append(info)

        return Response(results, status=HTTP_200_OK)
