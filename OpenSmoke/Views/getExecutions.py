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

import json
import random


class getExecutions(View.ExperimentManagerBaseView):
    viewName = __name__
    paramsType = {'username_list': list}

    required_groups = {'POST': []}

    def view_post(self, request):
        created = Execution.objects.filter(username__in=self.username_list, execution_start=None).values_list('id', flat=True)

        created = [int(x) for x in created]

        random.shuffle(created)

        return Response(created, status=HTTP_200_OK)
