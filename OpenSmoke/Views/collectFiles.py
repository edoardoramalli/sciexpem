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


class collectFiles(View.FrontEndBaseView):
    viewName = __name__
    paramsType = {'execution_id': int, 'files': dict, 'errors': str, 'automatic': bool}
    defaultParams = {'automatic': False}
    required_groups = {'POST': []}

    def view_post(self, request):
        execution = Models.Execution.objects.get(id=self.execution_id)

        if self.errors:
            if execution.execution_error:
                execution.execution_error = execution.execution_error + '\n' + self.errors
            else:
                execution.execution_error = self.errors

            execution.execution_end = timezone.localtime()
            execution.save()
            return Response(status=HTTP_200_OK)

        experiment_interpreter = execution.experiment.experiment_interpreter
        mappings = Models.MappingInterpreter.objects.filter(experiment_interpreter=experiment_interpreter)
        files = list(set([mapping.file for mapping in mappings]))

        # raise ValueError('edoooo')
        with transaction.atomic():
            try:
                for file in files:
                    OpenSmokeExecutor.read_output_OS_string(text=self.files[file], file_name=file, execution=execution)
            except MissingColumnExecution as e:
                if self.automatic:
                    execution.execution_end = timezone.localtime()
                    execution.execution_error = str(e)
                    execution.save()
                    return Response(status=HTTP_200_OK)
                else:
                    return Response(self.viewName + ": " + str(e), status=HTTP_400_BAD_REQUEST)

            execution.execution_end = timezone.localtime()
            execution.save()

            def create_and_start_cm():
                Thread(target=curveMatchingExecution, args=(execution,)).start()

            transaction.on_commit(create_and_start_cm)

        return Response(status=HTTP_200_OK)

