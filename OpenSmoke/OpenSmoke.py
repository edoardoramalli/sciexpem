import os, logging, re
# import glob
# from . import models
# from pathlib import Path
from django.utils import timezone
import pandas as pd
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
    def parse_header_output(header, SI):
        unit_name = header[header.find("[") + 1: header.find("]")] if header.find("[") else None
        label = header[: header.find("[")] if header.find("[") else None

        return label, getattr(SI, unit_name)

    @staticmethod
    def parse_output_string(output):
        import tempfile
        with tempfile.TemporaryDirectory() as sandbox:
            path = os.path.join(sandbox, "tmp.out")
            output_file = open(path, "w+")
            output_file.write(output)
            output_file.close()

            header = []
            prop = {}
            with open(path, "r") as file:
                header = [x[: x.rfind("(")] for x in file.readline().strip().split()]
                for h in header:
                    h_split = h.split("[")
                    name = h_split[0]
                    try:
                        unit = h_split[1].replace("]", "")
                    except IndexError:
                        unit = "unitless"
                    prop[name] = unit

            df = pd.read_csv(path, delim_whitespace=True, skiprows=1, names=prop.keys())
            return df, prop

    @staticmethod
    def parse_output(path):
        header = []
        prop = {}
        with open(path, "r") as file:
            header = [x[: x.rfind("(")] for x in file.readline().strip().split()]
            for h in header:
                h_split = h.split("[")
                name = h_split[0]
                try:
                    unit = h_split[1].replace("]", "")
                except IndexError:
                    unit = "unitless"
                prop[name] = unit

        df = pd.read_csv(path, delim_whitespace=True, skiprows=1, names=prop.keys())
        return df, prop

    @staticmethod
    def parse_input_path(path):
        output_string = ""
        with open(path, 'r') as file:
            for line in file:
                if "@KineticsFolder" in line:
                    output_string += "\t\t@KineticsFolder\t\t\t $PATHKINETICFOLDER$;" + "\n"
                elif "@OutputFolder" in line:
                    output_string += "\t\t@OutputFolder\t\t\t $PATHOUTPUTFOLDER$;" + "\n"
                else:
                    output_string += line
        return output_string

    @staticmethod
    def parse_input_string(string):  # TODO Se non ci sono queste righe bisognerebbe lanciare un'eccezione
        output_string = ""
        for line in string.split("\n"):
            if "@KineticsFolder" in line:
                output_string += "\t\t@KineticsFolder\t\t\t $PATHKINETICFOLDER$;" + "\n"
            elif "@OutputFolder" in line:
                output_string += "\t\t@OutputFolder\t\t\t $PATHOUTPUTFOLDER$;" + "\n"
            else:
                output_string += line + "\n"
        return output_string


class OpenSmokeExecutor:

    @staticmethod
    def read_output_OS(folder, file_name, execution):
        path = os.path.join(folder, file_name + '.out')
        dataframe, units = OpenSmokeParser.parse_output(path)

        list_header = list(dataframe)
        for header in list_header:
            data = Model.ExecutionColumn(label=header,
                                          units=units[header],
                                          data=list(dataframe[header]),
                                          execution=execution,
                                          file_type=file_name)
            data.save()

    @staticmethod
    def execute(exp_id, chemModel_id, execution_id, solver):
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
                os_file = open(os.path.join(sandbox, "input.xml.dic"), "w+")
                os_file.write(open_smoke_input_text)
                os_file.close()

                bashCommand = ". ~/.bashrc && OpenSMOKEpp_" + solver + ".sh --input " + sandbox + "/input.xml.dic"

                import subprocess

                process = subprocess.Popen(bashCommand, shell=True, stdout=subprocess.PIPE)
                output, error = process.communicate()

                # print(output)

                if not error:

                    execution = Model.Execution.objects.get(id=execution_id)
                    execution.execution_end = timezone.localtime()
                    execution.save()

                    # TODO I NOMI DEI FILE SONO HARCODATI. LI DOVREI PRENDERE O DAL MAPPING O BOH
                    # TODO FORSE DATO IL TIPO DI EXP SO QUALI FILE GENERA!
                    OpenSmokeExecutor.read_output_OS(folder=sandbox, file_name='ParametricAnalysisIDT',
                                                     execution=execution)
                    OpenSmokeExecutor.read_output_OS(folder=sandbox, file_name='ParametricAnalysis',
                                                     execution=execution)

                    curveMatchingExecution(current_execution=execution)

                else:
                    # print(error)
                    Model.Execution.objects.get(id=execution_id).delete()
        except Exception as e:
            # print("ECCEZIONE" + str(e))
            Model.Execution.objects.get(id=execution_id).delete()

