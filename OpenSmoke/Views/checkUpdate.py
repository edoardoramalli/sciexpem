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


class checkUpdate(View.ExperimentManagerBaseView):
    viewName = __name__
    paramsType = {}

    required_groups = {'POST': []}

    def view_post(self, request):

        files = ['main_sciexpem_worker.py', 'job_sciexpem_worker.py', 'utils_sciexpem_worker.py', 'template_pbs.pbs']

        h = hashlib.md5()

        hash_file = {}

        for file in files:
            with open(os.path.join(settings.BASE_DIR, 'SciExpeMWorker', file),  'r') as f:
                h.update(str.encode(f.read()))
                hash_file[file] = h.hexdigest()

        return Response(hash_file, status=HTTP_200_OK)
