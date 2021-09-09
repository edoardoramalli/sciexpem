import argparse
import os
import sys


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SciExpeM.settings")

import django
django.setup()


from OpenSmoke.OpenSmoke import OpenSmokeParser, OpenSmokeExecutor
from django.utils import timezone
from CurveMatching.CurveMatching import curveMatchingExecution
from django import db



import ExperimentManager.Models as Model
import subprocess


def execute(exp_id, chemModel_id, execution_id, solver, files):
    try:

        # IDs already checked by caller function
        chemModel = Model.ChemModel.objects.get(id=chemModel_id)
        experiment = Model.Experiment.objects.get(id=exp_id)

        #  Mandatory fields in the model. So no empty fields
        kinetics_file = chemModel.xml_file_kinetics
        reaction_names_file = chemModel.xml_file_reaction_names

        # Must be present to verify and experiment
        open_smoke_input_file = experiment.os_input_file

        # Create SandBox
        import tempfile

        # create a temporary directory
        with tempfile.TemporaryDirectory() as sandbox:
            kinetic_path = os.path.join(sandbox, "kinetics")
            os.mkdir(kinetic_path)

            kin_file = open(os.path.join(kinetic_path, "kinetics.xml"), "w+")
            kin_file.write(kinetics_file)
            kin_file.close()

            reac_file = open(os.path.join(kinetic_path, "reaction_names.xml"), "w+")
            reac_file.write(reaction_names_file)
            reac_file.close()

            open_smoke_input_text = OpenSmokeParser.create_output(open_smoke_input_file, kinetic_path, sandbox)
            os_file = open(os.path.join(sandbox, "input.dic"), "w+")
            os_file.write(open_smoke_input_text)
            os_file.close()

            bashCommand = ". ~/.bashrc && OpenSMOKEpp_" + solver + ".sh --input " + sandbox + "/input.dic"

            process = subprocess.Popen(bashCommand, shell=True, stdout=subprocess.PIPE)
            output, error = process.communicate()

            output = output.decode('ascii')

            # print(output)
            #
            # print(121312321)
            # print(error)
            #
            # print(sandbox)
            # #
            # import time
            #
            # time.sleep(100)

            # input('ciaooooo')

            if 'Fatal error' in output:
                output = output[output.find('Fatal error:'):]
                msg_error = output[12: output.find('\n')].strip()
                execution = Model.Execution.objects.get(id=execution_id)
                execution.execution_error = msg_error
                execution.save()
            else:
                execution = Model.Execution.objects.get(id=execution_id)
                execution.execution_end = timezone.localtime()
                execution.save()
                for file in files:
                    OpenSmokeExecutor.read_output_OS_from_path(folder=sandbox, file_name=file, execution=execution)

                curveMatchingExecution(current_execution=execution)

    except Exception as e:
        execution = Model.Execution.objects.get(id=execution_id)
        execution.execution_error = e
        execution.save()

    finally:
        db.close_old_connections()


def main():
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--files', metavar='F', type=str, nargs='+',
                        help='an integer for the accumulator')
    parser.add_argument('--exp', dest='experiment', type=int,
                        help='sum the integers (default: find the max)')
    parser.add_argument('--chem', dest='chemModel', type=int,
                        help='sum the integers (default: find the max)')
    parser.add_argument('--solver', dest='solver', type=str,
                        help='sum the integers (default: find the max)')
    parser.add_argument('--exec', dest='execution', type=int,
                        help='sum the integers (default: find the max)')

    args = parser.parse_args()

    exp_id = args.experiment
    chemModel_id = args.chemModel
    execution_id = args.execution
    solver = args.solver
    files = args.files

    execute(exp_id=exp_id, chemModel_id=chemModel_id, execution_id=execution_id, solver=solver, files=files)


if __name__ == "__main__":
    main()
