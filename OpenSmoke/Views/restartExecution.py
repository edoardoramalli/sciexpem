# Local import
import ExperimentManager.views as View
from ExperimentManager.Models import *
from ExperimentManager.exceptions import *
from CurveMatching.CurveMatching import curveMatchingExecution
from OpenSmoke.utils import createFilesSimulation_utils
from django.db.models import Q
from django.utils import timezone
# Django import
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from django.db import transaction
from django.contrib.auth.models import User
from django.http import FileResponse
from django.http import HttpResponse

import pandas as pd
import zipfile
from io import StringIO

import json


class restartExecution(View.ExperimentManagerBaseView):
    viewName = __name__
    paramsType = {'execution_id': int}

    required_groups = {'POST': []}

    def view_post(self, request):

        ese = Execution.objects.get(id=self.execution_id)

        if ese.execution_end == None:
            return Response('Simulation not ended yet', status=HTTP_400_BAD_REQUEST)

        ese.execution_start = None
        ese.execution_end = None
        ese.computer = None
        ese.execution_error = None


        ese.save()

        # TODO in futuro migliorare questa cosa: dare più opzioni di riavvio: cancello tutto, cancello solo exec columns e tengo output.xml

        for ec in ese.execution_columns.all():
            ec.delete()

        return Response(status=HTTP_200_OK)

