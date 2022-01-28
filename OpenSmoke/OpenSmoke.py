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
    initial_species = [x.specie for x in exp.initial_species.all()]
    dc_species = []
    for x in exp.data_columns.all():
        for s in x.species_object.all():
            dc_species.append(s)

    all_species = initial_species + dc_species

    supported_species = set(chemModel.supported_species)

    passed = True


    for specie in all_species:
        names = set(specie.names)  # qui c'è anche preffered key per forza
        if not names & supported_species: # se l'intersezione tra i names e le supported species è vuota
            passed = False
            break
    return passed


class OpenSmokeParser:
    def __init__(self):
        pass

    @staticmethod
    def create_output(file, model_path, output_path, profiles=None):
        output_file = file.replace("$PATHKINETICFOLDER$", model_path).replace("$PATHOUTPUTFOLDER$", output_path)
        if profiles:
            output_file = output_file.replace("$LISTPROFILE$", profiles)
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

        list_names = []
        for h in header:
            h_split = h.split("[")
            name = h_split[0]
            list_names.append(name)
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
            # seen = set()
            # dupes = [x for x in list_names if x in seen or seen.add(x)]
            # print('edoo', dupes)
            # TODO se per sbaglio nell'input file di OS si richiede due volte la stessa specie, l'output file di OS avrà due volte la stessa colonna e si smongola tutto!
            df = pd.read_csv(buffer_str, delim_whitespace=True, skiprows=1, names=list_names)
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

        left_space = '\t' * 2

        first_inner_space = ' '
        second_inner_space = ' ' * 3

        isStarted = False
        isOpen = False

        inline_profile = False

        output_string = ""
        kinetics = False
        output = False
        string = string.strip()
        split_string = string.split('\n')

        buffer_space = 35

        for line_number, line in enumerate(split_string):
            line = line.strip()
            if line == '':
                continue

            if line.startswith('//'):
                output_string += line.strip() + '\n'
                continue

            if 'Dictionary' in line:
                isStarted = True
                tmp_split = line.split()
                if len(tmp_split) > 2:
                    raise OpenSmokeWrongInputFile("Bad definition of dictionary at line " + str(line_number))
                if isOpen:
                    raise OpenSmokeWrongInputFile("Missing closing dictionary symbol '}' at line " + str(line_number))
                output_string += '\n' + line.strip()
                continue

            if '{' in line:
                if isStarted:
                    isOpen = True
                else:
                    raise OpenSmokeWrongInputFile("Missing dictionary definition at line " + str(line_number))
                output_string += '\n' + line.strip() + '\n'
                continue

            if '}' in line:
                if isOpen:
                    isOpen = False
                    isStarted = False
                else:
                    raise OpenSmokeWrongInputFile("Dictionary is closed but not opened at line " + str(line_number))
                output_string += '\n' + line.strip() + '\n'
                continue

            if line.startswith('@'):
                if not isOpen:
                    raise OpenSmokeWrongInputFile("Missing opening dictionary symbol '{' at line " + str(line_number))

                split_line = line.split('//')

                line = split_line[0]

                if ';' not in line:
                    raise OpenSmokeWrongInputFile("Missing closing line character ';' at line {}".format(line_number))

                line = line.replace(';', ' ')

                line = line.split()

                remainder = ''
                if len(split_line) > 1:
                    remainder = split_line[1]
                    print('remainder')
                    print(remainder)

                tmp = ''

                for index_split, split in enumerate(line):
                    current_space = first_inner_space * (buffer_space - len(split))
                    if "@KineticsFolder" in split:
                        kinetics = True
                        tmp += "@KineticsFolder" + current_space + "$PATHKINETICFOLDER$"
                        break
                    elif "@OutputFolder" in line:
                        output = True
                        tmp += "@OutputFolder" + current_space + "$PATHOUTPUTFOLDER$"
                        break
                    elif "@Output" in line:
                        output = True
                        tmp += "@Output" + current_space + "$PATHOUTPUTFOLDER$"
                        break
                    elif "@ListOfProfiles" in line:
                        tmp += "@ListOfProfiles" + current_space + "$LISTPROFILE$"
                        break
                    # elif "@Profile" in line:
                    #     tmp += "@Profile" + current_space + "$PROFILE$"
                    #     break
                    else:
                        if split == ';':
                            break
                        if index_split == 0:
                            tmp += split + current_space
                        else:
                            tmp += split + second_inner_space

                output_string += left_space + tmp.strip() + ';'
                if remainder:
                    output_string += second_inner_space + '//    ' + remainder.strip()
                output_string += '\n'
            # elif line.startswith('@') and 'Profile' in line:
            #     inline_profile = True
            # elif ';' in line:
            #     inline_profile = False
            # elif inline_profile:
            #     pass
            else:
                raise OpenSmokeWrongInputFile("Invalid line " + str(line_number))

        if not (kinetics and output):
            raise OpenSmokeWrongInputFile(
                'Missing @KineticsFolder keyword' if not kinetics else 'Missing @Output keyword')

        return output_string.strip()


class OpenSmokeExecutor:

    @staticmethod
    def createExecutionColumn(dataframe, units, file_name, execution):
        dataframe = dataframe.drop_duplicates()
        # Be sure that the execution has not any execution columns:
        if execution.execution_columns.all():
            execution.execution_columns.all().delete()

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

        if execution.experiment.reactor == 'rapid compression machine':
            for col in list(dataframe.columns):
                if col.startswith('tau1_'):
                    suffix = col.split('_')[1]
                    break
            # TODO in teoria non ci importa il suffisso tanto per le rcm non c'è distinzione tra slope, max, intercept, etc..
            dataframe['tau'] = dataframe['tau1_{}'.format(suffix)] - dataframe['tau2_{}'.format(suffix)]
            units['tau'] = units['tau1_{}'.format(suffix)]

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
            raise MissingOpenSmokeOutputFile('It is missing ' + file_name + '.out')

    @staticmethod
    def execute_tsp(exp_id, chemModel_id, execution_id, solver, files, just_initialized=False):

        path = pathlib.Path(__file__).parent.parent.resolve()
        run_file_path = os.path.join(path, 'runOS.py')

        bashCommand = "tsp -n /home/eramalli/.conda/envs/django/bin/python3.9 {file} ".format(file=run_file_path)
        bashCommand += ' --exp {} --chem {} --exec {} --solver {} --files {} '.format(exp_id, chemModel_id,
                                                                                      execution_id,
                                                                                      solver, ' '.join(files))
        if just_initialized:
            return bashCommand

        process = subprocess.Popen(bashCommand, shell=True, stdout=subprocess.PIPE)
        output, error = process.communicate()

        # import runOS
        #
        # runOS.execute(exp_id, chemModel_id, execution_id, solver, files)

        # print(output)
        # print(error)

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
