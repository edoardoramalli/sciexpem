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
from SciExpeM.settings import SCIEXPEM_FILESYSTEM_FOLDER

# System import
import json
from threading import Thread
import os


class collectFiles(View.FrontEndBaseView):
    viewName = __name__
    # TODO prima files are un dict ora è un list --> cambio API front end
    paramsType = {'execution_id': int, 'files': list, 'errors': str, 'automatic': bool}
    defaultParams = {'automatic': False}
    required_groups = {'POST': []}

    def view_post(self, request):
        # TODO con restart execution si potrebbe generare un eccezione, se rinizio
        # Stessa cosa se ho cancellato l'execution,  non trova l'id dell exec
        # Bisognorebbe mandare trigger a worker di interrompere. DIfficile da fare.... Accettiamo ma non salviamo niente....

        execution = Models.Execution.objects.filter(id=self.execution_id)

        # QUIIIII dovrei aver risolto come dicevo prima
        if len(execution) == 0:
            return Response(status=HTTP_200_OK)
        else:
            execution = execution[0]

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
                    query_result = list(filter(lambda f: f['file'] == file and f['type'] == 'result', self.files))[0]
                    OpenSmokeExecutor.read_output_OS_string(text=query_result['content'], file_name=file, execution=execution)

                # Save Output.xml files
                query_result = list(filter(lambda f: f['file'] == 'Output.xml' and f['type'] == 'Output.xml', self.files))
                if len(query_result) <= 0:
                    raise ValueError('Missing Output.xml files')

                exec_path = os.path.join(SCIEXPEM_FILESYSTEM_FOLDER, 'Execution', str(self.execution_id))
                os.makedirs(exec_path, exist_ok=True)

                for output_file in query_result:
                    case = output_file['case']

                    if case is None:
                        dir_path = exec_path
                        rel_path = os.path.join('Execution', str(self.execution_id), output_file['file'])
                    else:
                        dir_path = os.path.join(exec_path, 'Case{}'.format(case))
                        os.makedirs(dir_path, exist_ok=True)
                        rel_path = os.path.join('Execution', str(self.execution_id), 'Case{}'.format(case), output_file['file'])

                    file_path = os.path.join(dir_path, output_file['file'])

                    with open(file_path, 'w') as file:
                        file.write(output_file['content'])

                    ef = Models.ExecutionFile(case=case, type=output_file['type'], path=rel_path, execution=execution)
                    ef.save()

            except MissingColumnExecution as e:
                if self.automatic:
                    execution.execution_end = timezone.localtime()
                    execution.execution_error = str(e)
                    execution.save()
                    return Response(status=HTTP_200_OK)
                else:
                    return Response(self.viewName + ": " + str(e), status=HTTP_400_BAD_REQUEST)

            except Exception as e:
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

