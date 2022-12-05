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


class startExecution(View.ExperimentManagerBaseView):
    viewName = __name__
    paramsType = {'execution_id': int, 'computer': str}
    defaultParams = {'computer': None}

    required_groups = {'POST': []}

    def view_post(self, request):

        with transaction.atomic():
            ese = Execution.objects.select_for_update().get(id=self.execution_id)
            if ese.execution_start is None:
                ese.execution_start = timezone.localtime()
                ese.computer = self.computer
                ese.save()

                experiment_interpreter = ese.experiment.experiment_interpreter
                mappings = MappingInterpreter.objects.filter(experiment_interpreter=experiment_interpreter)
                output_files = list(set([mapping.file for mapping in mappings]))

                backup_chemModel_name = ese.backup_chemModel.name if ese.backup_chemModel else None

                # TODO se per qualche motivo non c'è il file di backup e quindi lancia un file not found bisgona inoltrare l'errore all'uitente  e non un 500

                input_files = createFilesSimulation_utils(exec_id=ese.id,
                                                          exp_id=ese.experiment.id,
                                                          chemModel_id=ese.chemModel.id,
                                                          backup_cheModel_name=backup_chemModel_name)

                # print(input_files.keys())

                return Response({
                    'solver': ese.experiment.experiment_interpreter.solver,
                    'input_files': input_files,
                    'output_files': output_files}, status=HTTP_200_OK)
            else:
                return Response('Simulation already started', status=HTTP_400_BAD_REQUEST)
