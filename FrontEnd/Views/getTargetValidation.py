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
import pandas as pd


class getTargetValidation(View.FrontEndBaseView):
    viewName = __name__
    paramsType = {'chemModel_list': list}
    required_groups = {'POST': ['READ']}

    def view_post(self, request):

        targets = []

        for chemModel_id in self.chemModel_list:
            # TODO non va bene! in realtà dobbiamo distinguere x e y assieme e non solo y. altrimenti metteso assieme y con T e con P
            targets += Models.CurveMatchingResult.objects.filter(
                execution_column__execution__chemModel__id=chemModel_id).values_list('execution_column__label',
                                                                                     flat=True).distinct()
            # for e in set([item for sublist in targets for item in sublist]):
            #     flat_set.add(e)

        flat_list = list(set(targets))

        return Response(json.dumps(flat_list), status=HTTP_200_OK)
