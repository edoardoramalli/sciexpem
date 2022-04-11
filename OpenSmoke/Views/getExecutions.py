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
from django.utils import timezone
import pandas as pd

import json
import random


class getExecutions(View.ExperimentManagerBaseView):
    viewName = __name__
    paramsType = {'username_list': list, 'computer': str, 'free_cores': int, 'num_cores': int, 'max_jobs': int, 'active_jobs': int}
    defaultParams = {'computer': None, 'free_cores': -1, 'num_cores': -1, 'max_jobs': -1, 'active_jobs': -1}
    required_groups = {'POST': []}

    def view_post(self, request):
        created = Execution.objects.filter(username__in=self.username_list, execution_start=None).values_list('id', flat=True)

        created = [int(x) for x in created]

        random.shuffle(created)

        if self.computer:
            values = {'free_cores': self.free_cores,
                      'num_cores': self.num_cores,
                      'max_jobs': self.max_jobs,
                      'active_jobs': self.active_jobs,
                      'last_contact': timezone.now}
            worker, _ = WorkManager.objects.update_or_create(defaults=values, computer=self.computer)

        return Response(created, status=HTTP_200_OK)
