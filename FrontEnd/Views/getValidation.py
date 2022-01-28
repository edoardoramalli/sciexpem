# Local import
import FrontEnd.views as View
import ExperimentManager.Models as Models
import ExperimentManager.Serializers as Serializers

# Django import
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK

# System import
import json
from statistics import stdev, variance, mean, median, StatisticsError


class getValidation(View.FrontEndBaseView):
    viewName = 'getValidation'
    paramsType = {'query': dict}
    required_groups = {'POST': ['READ']}

    def view_post(self, request):
        # file_paper = Models.Experiment.objects.get(id=self.exp_id).file_paper
        funcs = [len, min, max, stdev, variance, mean, median]

        def apply_funcs(fun, value_list):
            try:
                return round(fun(value_list), 3)
            except (StatisticsError, ValueError):
                return None

        # model1_id = self.chemModel_id
        # model2_id = 5

        # list_models = [model1_id]
        list_models = [1]

        new = {'execution_column__execution__experiment__status': 'verified', **self.query}

        queryset = {
            model_id: Models.CurveMatchingResult.objects.filter(**new).distinct() for
            model_id in list_models}

        results = {model_id: {'score': [], 'd0L2': [], 'd1L2': [], 'd0Pe': [], 'd1Pe': [], 'shift': []} for model_id in
                   list_models}

        def merge_diz(diz1, diz2):
            for i in diz2:
                if i in diz1:
                    diz1[i] = {**diz1[i], **diz2[i]}
                else:
                    diz1[i] = diz2[i]
            return diz1

        model_tot = {}

        for model in queryset:
            model_tot[model] = queryset[model].values('execution_column__execution__experiment__id').distinct().count()
            for cm in queryset[model]:
                score = float(cm.score)
                d0L2 = float(cm.d0L2)
                d1L2 = float(cm.d1L2)
                d0Pe = float(cm.d0Pe)
                d1Pe = float(cm.d1Pe)
                shift = float(cm.shift)

                if all([a != -1 and a != 0 for a in [score, d0L2, d1L2, d0Pe, d1Pe, shift]]):
                    results[model]['score'].append(score)
                    results[model]['d0L2'].append(d0L2)
                    results[model]['d1L2'].append(d1L2)
                    results[model]['d0Pe'].append(d0Pe)
                    results[model]['d1Pe'].append(d1Pe)
                    results[model]['shift'].append(shift)

        final = {}
        for model in results:
            for item in results[model]:
                tmp = {fun.__name__: apply_funcs(fun, results[model][item]) for fun in funcs}
                tmp = {**tmp, 'total': model_tot[model]}
                if item in final:
                    final = merge_diz(final, {item: tmp})
                else:
                    final[item] = tmp

        final_final = []

        for item in final:
            final_final.append({'name': item, **final[item]})


        return Response(json.dumps(final_final), status=HTTP_200_OK)
