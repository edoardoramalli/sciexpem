import os, logging, re
# import glob
# from . import models
# from pathlib import Path
from django.utils import timezone
from django import db
import pandas as pd
from OpenSmoke.exceptions import *
import sys
from pint import UnitRegistry
from io import StringIO
import ExperimentManager.Models as Model
from CurveMatching.CurveMatching import curveMatchingExecution

__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))


class OpenSmokeParser:
    def __init__(self):
        pass

    @staticmethod
    def create_output(file, model_path, output_path):
        output_file = file.replace("$PATHKINETICFOLDER$", model_path).replace("$PATHOUTPUTFOLDER$", output_path)
        return output_file

    @staticmethod
    def parse_output_string(output_str: str) -> (object, dict):
        """
        Given a string of OS output, returns a Dataframe a dictionary with the association property <-> unit
        Raise: MissingOpenSmokeOutputFile --> Pandas raise EmptyDataError if the output_str is empty
        """
        buffer_str = StringIO(output_str)
        prop = {}
        # Extract header from OS output file
        header = [x[: x.rfind("(")] for x in output_str.split('\n')[0].strip().split()]
        for h in header:
            h_split = h.split("[")
            name = h_split[0]
            try:
                unit = h_split[1].replace("]", "")
            except IndexError:
                if '_x' in name:
                    unit = "mole fraction"
                elif '_w' in name:
                    unit = 'mass fraction'
                else:
                    unit = "unitless"
            prop[name] = unit
        try:
            df = pd.read_csv(buffer_str, delim_whitespace=True, skiprows=1, names=prop.keys())
        except pd.errors.EmptyDataError:
            raise MissingOpenSmokeOutputFile

        return df, prop

    @staticmethod
    def parse_input_string(string: str) -> str:
        """
        Given a generic input OS file generate the template usable for every model changing
        $PATHKINETICFOLDER$ and $PATHOUTPUTFOLDER$
        Raise: OpenSmokeWrongInputFile. If the input OS file does not have @KineticsFolder or @OutputFolder line
        :rtype: str. The template input OS file.
        """
        output_string = ""
        kinetics = False
        reaction_names = False
        for line in string.split("\n"):
            if "@KineticsFolder" in line:
                kinetics = True
                output_string += "\t\t@KineticsFolder\t\t\t $PATHKINETICFOLDER$;" + "\n"
            elif "@OutputFolder" in line:
                reaction_names = True
                output_string += "\t\t@OutputFolder\t\t\t $PATHOUTPUTFOLDER$;" + "\n"
            else:
                output_string += line + "\n"

        if not (kinetics and reaction_names):
            raise OpenSmokeWrongInputFile

        return output_string


class OpenSmokeExecutor:

    @staticmethod
    def createExecutionColumn(dataframe, units, file_name, execution):
        list_header = list(dataframe)
        for header in list_header:
            data = Model.ExecutionColumn(label=header,
                                         units=units[header],
                                         data=list(dataframe[header]),
                                         execution=execution,
                                         file_type=file_name)
            data.save()

    @staticmethod
    def read_output_OS_from_path(folder: str, file_name: str, execution):
        """
        Given an OS output file path of an execution, create the corresponding execution columns
        Raise: OpenSmokeWrongInputFile. If the file is missing.
        """
        dataframe, units = OpenSmokeParser.parse_output_string(open(os.path.join(folder, file_name + '.out')).read())
        OpenSmokeExecutor.createExecutionColumn(dataframe, units, file_name, execution)

    @staticmethod
    def read_output_OS_string(text, file_name, execution):
        """
        Given an OS output file string of an execution, create the corresponding execution columns
        Raise: OpenSmokeWrongInputFile. If the file is missing.
        """
        dataframe, units = OpenSmokeParser.parse_output_string(text)
        OpenSmokeExecutor.createExecutionColumn(dataframe, units, file_name, execution)

    @staticmethod
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

                bashCommand = ". ~/.bashrc && echo | OpenSMOKEpp_" + solver + ".sh --input " + sandbox + "/input.dic"

                import subprocess

                process = subprocess.Popen(bashCommand, shell=True, stdout=subprocess.PIPE)
                output, error = process.communicate()


                if not error:
                    execution = Model.Execution.objects.get(id=execution_id)
                    execution.execution_end = timezone.localtime()
                    execution.save()
                    for file in files:
                        OpenSmokeExecutor.read_output_OS_from_path(folder=sandbox, file_name=file, execution=execution)
                    curveMatchingExecution(current_execution=execution)
                else:
                    Model.Execution.objects.get(id=execution_id).delete()
        except Exception as e:
            # logger stampa errori
            print(e)
            Model.Execution.objects.get(id=execution_id).delete()

        finally:
            db.close_old_connections()
