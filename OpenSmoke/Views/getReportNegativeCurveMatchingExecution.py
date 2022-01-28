# Local import
import ExperimentManager.views as View
from ExperimentManager.Models import *
from ExperimentManager.exceptions import *
from CurveMatching.CurveMatching import curveMatchingExecution
from OpenSmoke.OpenSmoke import getColumnNameSimulator
from django.db.models import Q, Count, F, Case, When, IntegerField

# Django import
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from django.db import transaction
from django.contrib.auth.models import User
from django.http import FileResponse

import pandas as pd

import json


class getReportNegativeCurveMatchingExecution(View.ExperimentManagerBaseView):
    viewName = __name__
    paramsType = {'username_list': list, 'params': tuple}

    required_groups = {'POST': []}

    def view_post(self, request):
        query = (Q(execution_columns__curve_matching_result__score__lt=0) | Q(
            execution_columns__curve_matching_result__d0L2__lt=0) | Q(
            execution_columns__curve_matching_result__d1L2__lt=0) | Q(
            execution_columns__curve_matching_result__d0Pe__lt=0) | Q(
            execution_columns__curve_matching_result__d1Pe__lt=0) | Q(
            execution_columns__curve_matching_result__shift__lt=0))

        if self.username_list:
            query = query & Q(execution_column__execution__username__in=self.username_list)

        query_object = Execution.objects.filter(query).distinct()

        result = list(query_object.values(*self.params))

        return Response(result, status=HTTP_200_OK)
