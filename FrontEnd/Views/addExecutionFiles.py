# Local import
import FrontEnd.views as View
import ExperimentManager.Models as Models
from CurveMatching.CurveMatching import curveMatchingExecution
from OpenSmoke.OpenSmoke import OpenSmokeExecutor
from OpenSmoke.exceptions import *
# Django import
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from django.db import transaction
from django.utils import timezone

# System import
import json
from threading import Thread


def run_cm(execution):
    curveMatchingExecution(current_execution=execution)


class addExecutionFiles(View.FrontEndBaseView):
    viewName = 'addExecutionFiles'
    paramsType = {'execution_id': int, 'files': dict}
    required_groups = {'POST': ['READ']}


    def view_post(self):
        with transaction.atomic():

            execution = Models.Execution.objects.get(id=self.execution_id)
            experiment_interpreter = execution.experiment.experiment_interpreter
            mappings = Models.MappingInterpreter.objects.filter(experiment_interpreter=experiment_interpreter)
            files = list(set([mapping.file for mapping in mappings]))
            try:
                for file in files:
                    OpenSmokeExecutor.read_output_OS_string(text=self.files[file], file_name=file, execution=execution)
            except MissingColumnExecution as e:
                return Response(self.viewName + ": " + str(e), status=HTTP_400_BAD_REQUEST)

            execution.execution_end = timezone.localtime()
            execution.save()

            Thread(target=run_cm, args=(execution,)).start()

            return Response(status=HTTP_200_OK)

