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
import hashlib
import os


from SciExpeM import settings


class getUpdate(View.ExperimentManagerBaseView):
    viewName = __name__
    paramsType = {}

    required_groups = {'POST': []}

    def view_post(self, request):

        files = ['main.py', 'Job.py', 'utils.py', 'template_pbs.pbs']

        str_file = {}

        for file in files:
            with open(os.path.join(settings.BASE_DIR, 'SciExpeMWorker', file),  'r') as f:
                str_file[file] = f.read()

        return Response(str_file, status=HTTP_200_OK)
