import os, logging, re
# import glob
# from . import models
# from pathlib import Path
from django.utils import timezone
from django import db
import pandas as pd
from OpenSmoke.exceptions import *
import sys
import pathlib
import subprocess
import os
from pint import UnitRegistry
from io import StringIO
import traceback
import ExperimentManager.Models as Model
from CurveMatching.CurveMatching import curveMatchingExecution

__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))


def getColumnNameSimulator(experiment):
    interpreter = experiment.interpreter
    mappings = interpreter.mappings.all()
    mappings_name = set([])
    for mapping in mappings:
        y_name = mapping.y_sim_name
        if y_name == 'composition_x':
            columns = experiment.data_columns.all()
            composition = [column.label[column.label.find("[") + 1:column.label.find("]")] + '_x' for column in columns
                           if
                           column.name == 'composition']
            for comp in composition:
                mappings_name.add(comp)
        else:
            mappings_name.add(y_name)
        x_name = mapping.x_sim_name
        mappings_name.add(x_name)


def check_Experiment_Model(experiment_id, chemModel_id):
    exp = Model.Experiment.objects.get(id=experiment_id)
    chemModel = Model.ChemModel.objects.get(id=chemModel_id)
    initial_species = set([x.specie.preferredKey for x in exp.initial_species.all()])
    supported_species = set(chemModel.supported_species)
    return initial_species.issubset(supported_species)


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
                if unit == '-':
                    unit = 'unitless'
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
    def check_input_string(string: str) -> dict:
        string = string.strip()
        KineticsFolder, OutputFolder, Output, ListOfProfiles, Profile = False, False, False, False, False
        if "@KineticsFolder" in string:
            KineticsFolder = True
        if "@OutputFolder" in string:
            OutputFolder = True
        if "@Output" in string:
            Output = True
        if "@ListOfProfiles" in string:
            ListOfProfiles = True
        if "@Profile" in string:
            Profile = True

        return {'KineticsFolder': KineticsFolder,
                'OutputFolder': OutputFolder,
                'Output': Output,
                'ListOfProfiles': ListOfProfiles,
                'Profile': Profile}

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
        output = False
        string = string.strip()
        for line in string.split("\n"):
            if "@KineticsFolder" in line.split():
                kinetics = True
                output_string += "\t\t@KineticsFolder\t\t\t $PATHKINETICFOLDER$;" + "\n"
            elif "@OutputFolder" in line.split():
                output = True
                output_string += "\t\t@OutputFolder\t\t\t $PATHOUTPUTFOLDER$;" + "\n"
            elif "@Output" in line.split():
                output = True
                output_string += "\t\t@Output\t\t\t $PATHOUTPUTFOLDER$;" + "\n"
            elif "@ListOfProfiles" in line.split():
                output_string += "\t\t@ListOfProfiles\t\t\t $LISTPROFILE$;" + "\n"
            elif "@Profile" in line.split():
                output_string += "\t\t@Profile\t\t\t $PROFILE$;" + "\n"
            else:
                output_string += line + "\n"

        if not (kinetics and output):
            raise OpenSmokeWrongInputFile(
                'Missing @KineticsFolder keyword' if not kinetics else 'Missing @Output keyword')

        return output_string


class OpenSmokeExecutor:

    @staticmethod
    def createExecutionColumn(dataframe, units, file_name, execution):
        if dataframe.isnull().values.any():
            dataframe = dataframe.dropna()
            if execution.execution_error:
                execution.execution_error += '\nNaN values dropped.\n'
            else:
                execution.execution_error = '\nNaN values dropped.\n'
            execution.save()
        list_header = list(dataframe)
        list_allowed = set([])
        for mapping in execution.experiment.experiment_interpreter.mappings.all():
            if any(map(lambda x: x == 'None' or x == 'none',
                       [mapping.x_sim_name, mapping.y_sim_name, mapping.y_exp_name, mapping.x_exp_name])):
                continue
            list_allowed.add(mapping.x_sim_name)
            y_sim_name = mapping.y_sim_name
            if y_sim_name == 'composition_x':
                compositions = Model.DataColumn.objects.filter(experiment=execution.experiment, name='composition')
                for comp in compositions:
                    list_species = comp.species_object.all()
                    for species in list_species:
                        list_allowed.add(species.preferredKey + '_x')
            else:
                list_allowed.add(mapping.y_sim_name)

        list_allowed = list(list_allowed)

        a = set(list_allowed)
        b = set(list_header)
        missing = list(a - b)

        if missing:
            raise MissingColumnExecution(', '.join(missing))

        for header in list_allowed:
            data = Model.ExecutionColumn(label=header,
                                         units=units[header],
                                         data=list(dataframe[header]),
                                         execution=execution,
                                         file_type=file_name)
            data.save()


    @staticmethod
    def read_output_OS_string(text, file_name, execution):
        """
        Given an OS output file string of an execution, create the corresponding execution columns
        Raise: OpenSmokeWrongInputFile. If the file is missing.
        """
        dataframe, units = OpenSmokeParser.parse_output_string(text)
        OpenSmokeExecutor.createExecutionColumn(dataframe, units, file_name, execution)

    @staticmethod
    def read_output_OS_from_path(folder: str, file_name: str, execution):
        """
        Given an OS output file path of an execution, create the corresponding execution columns
        Raise: OpenSmokeWrongInputFile. If the file is missing.
        """
        file_path = os.path.join(folder, file_name + '.out')
        if os.path.isfile(file_path):
            text = open(file_path, errors='strict').read()
            # dataframe, units = OpenSmokeParser.parse_output_string(text)
            # OpenSmokeExecutor.createExecutionColumn(dataframe, units, file_name, execution)
            OpenSmokeExecutor.read_output_OS_string(text=text, file_name=file_name, execution=execution)
        else:
            raise MissingOpenSmokeOutputFile(file_name + '.out')




    @staticmethod
    def execute_tsp(exp_id, chemModel_id, execution_id, solver, files, just_initialized=False):


        path = pathlib.Path(__file__).parent.parent.resolve()
        run_file_path = os.path.join(path, 'runOS.py')

        bashCommand = "tsp -n /home/eramalli/.conda/envs/django/bin/python3.9 {file} ".format(file=run_file_path)
        bashCommand += ' --exp {} --chem {} --exec {} --solver {} --files {} '.format(exp_id, chemModel_id, execution_id,
                                                                                     solver, ' '.join(files))
        if just_initialized:
            return bashCommand

        process = subprocess.Popen(bashCommand, shell=True, stdout=subprocess.PIPE)
        output, error = process.communicate()


    # @staticmethod
    # def execute(exp_id, chemModel_id, execution_id, solver, files):
    #     try:
    #
    #         # IDs already checked by caller function
    #         chemModel = Model.ChemModel.objects.get(id=chemModel_id)
    #         experiment = Model.Experiment.objects.get(id=exp_id)
    #
    #         #  Mandatory fields in the model. So no empty fields
    #         kinetics_file = chemModel.xml_file_kinetics
    #         reaction_names_file = chemModel.xml_file_reaction_names
    #
    #         # Must be present to verify and experiment
    #         open_smoke_input_file = experiment.os_input_file
    #
    #         # Create SandBox
    #         import tempfile
    #
    #         # create a temporary directory
    #         with tempfile.TemporaryDirectory() as sandbox:
    #             kinetic_path = os.path.join(sandbox, "kinetics")
    #             os.mkdir(kinetic_path)
    #
    #             kin_file = open(os.path.join(kinetic_path, "kinetics.xml"), "w+")
    #             kin_file.write(kinetics_file)
    #             kin_file.close()
    #
    #             reac_file = open(os.path.join(kinetic_path, "reaction_names.xml"), "w+")
    #             reac_file.write(reaction_names_file)
    #             reac_file.close()
    #
    #             open_smoke_input_text = OpenSmokeParser.create_output(open_smoke_input_file, kinetic_path, sandbox)
    #             os_file = open(os.path.join(sandbox, "input.dic"), "w+")
    #             os_file.write(open_smoke_input_text)
    #             os_file.close()
    #
    #             bashCommand = ". ~/.bashrc && tsp OpenSMOKEpp_" + solver + ".sh --input " + sandbox + "/input.dic"
    #
    #             import subprocess
    #
    #             process = subprocess.Popen(bashCommand, shell=True, stdout=subprocess.PIPE)
    #             output, error = process.communicate()
    #
    #             output = output.decode('ascii')
    #
    #             # print(output)
    #             #
    #             # print(121312321)
    #             # print(error)
    #             #
    #             print(sandbox)
    #             # #
    #             import time
    #             #
    #             time.sleep(100)
    #
    #             # input('ciaooooo')
    #
    #             if 'Fatal error' in output:
    #                 output = output[output.find('Fatal error:'):]
    #                 msg_error = output[12: output.find('\n')].strip()
    #                 execution = Model.Execution.objects.get(id=execution_id)
    #                 execution.execution_error = msg_error
    #                 execution.save()
    #             else:
    #                 execution = Model.Execution.objects.get(id=execution_id)
    #                 execution.execution_end = timezone.localtime()
    #                 execution.save()
    #                 for file in files:
    #                     OpenSmokeExecutor.read_output_OS_from_path(folder=sandbox, file_name=file, execution=execution)
    #                 curveMatchingExecution(current_execution=execution)
    #
    #     except Exception as e:
    #         execution = Model.Execution.objects.get(id=execution_id)
    #         execution.execution_error = e
    #         execution.save()
    #
    #     finally:
    #         db.close_old_connections()
