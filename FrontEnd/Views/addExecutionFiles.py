# Local import
import FrontEnd.views as View
import ExperimentManager.Models as Models
from CurveMatching.CurveMatching import curveMatchingExecution
from OpenSmoke.OpenSmoke import OpenSmokeExecutor
# Django import
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from django.db import transaction
from django.utils import timezone

# System import
import json


class addExecutionFiles(View.FrontEndBaseView):
    viewName = 'addExecutionFiles'
    paramsType = {'execution_id': int, 'files': dict}
    required_groups = {'POST': ['READ']}

    def view_post(self): # TODO deve essere asincrono non si può aspettare il CM !!!
        with transaction.atomic():
            execution = Models.Execution.objects.get(id=self.execution_id)
            experiment_interpreter = execution.experiment.experiment_interpreter
            mappings = Models.MappingInterpreter.objects.filter(experiment_interpreter__name=experiment_interpreter)
            files = list(set([mapping.file for mapping in mappings]))

            for file in files:
                OpenSmokeExecutor.read_output_OS_string(text=self.files[file], file_name=file, execution=execution)

            curveMatchingExecution(current_execution=execution)

            execution.execution_end = timezone.localtime()
            execution.save()

            return Response(status=HTTP_200_OK)

