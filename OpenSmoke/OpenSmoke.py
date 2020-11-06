import os, logging, re
# import glob
# from . import models
# from pathlib import Path
import pandas as pd
from pint import UnitRegistry
from io import StringIO

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
    def parse_output(path):
        column_label = []
        column_unit = {}

        SI = UnitRegistry()
        # TODO FIX PATH
        SI.load_definitions('/Users/edoardo/Documents/GitHub/sciexpem/experimentmanager/units.def')

        with open(path, "r") as file:
            header = re.sub('&+', '&', file.readline().replace(" ", "&"))[:-2]
            header_split = [x[:x.rfind("(")] for x in header.strip().split("&")]
            for header in header_split:
                label, unit = OpenSmokeParser.parse_header_output(header, SI)
                column_label.append(label)
                column_unit[label] = unit

            string_file = '&'.join(column_label) + "\n"

            for line in file:
                row = re.sub('&+', '&', line.replace(" ", "&"))[:-2]
                string_file += row + "\n"

        data = pd.read_csv(StringIO(string_file), sep="&")
        df = pd.DataFrame(data, columns=column_label)

        return df, column_unit

    @staticmethod
    def parse_input(path):
        output_string = ""
        with open(path, 'r') as file:
            for line in file:
                if "@KineticsFolder" in line:
                    output_string += "@KineticsFolder $PATHKINETICFOLDER$;" + "\n"
                elif "@OutputFolder" in line:
                    output_string += "@OutputFolder $PATHOUTPUTFOLDER$;" + "\n"
                else:
                    output_string += line
        return output_string


class OpenSmokeExecutor:

    @staticmethod
    def execute(experiment, chemModel):
        from experimentmanager import models

        if models.Execution.objects.filter(experiment=experiment, chemModel=chemModel).exists():
            return

        kinetics_file = chemModel.xml_file_kinetics
        reaction_names_file = chemModel.xml_file_reaction_names

        try:
            open_smoke_input = models.OpenSmokeInput.objects.filter(experiment=experiment)[0]
        except IndexError:
            return

        open_smoke_input_file = open_smoke_input.file

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

            # print(sandbox)
            # input("wait")

            bashCommand = ". ~/.zshrc && OpenSMOKEpp_BatchReactor.sh --input " + sandbox + "/input.xml.dic"

            import subprocess

            process = subprocess.Popen(bashCommand, shell=True, stdout=subprocess.PIPE)
            output, error = process.communicate()

            if not error:
                # input("wait 2")
                execution = models.Execution(chemModel=chemModel, experiment=experiment)
                execution.save()

                # print("---> Fine OS", experiment.fileDOI, chemModel.name)

                # TODO a seconda del tipo di exp ParametricAnalysisIDT.out o ParametricAnalysis.out
                dataframe, units = OpenSmokeParser.parse_output(os.path.join(sandbox, "ParametricAnalysisIDT.out"))

                list_header = list(dataframe)
                for header in list_header:
                    data = models.ExecutionColumn(label=header,
                                                  units=units[header],
                                                  data=list(dataframe[header]),
                                                  execution=execution)
                    data.save()


    # @staticmethod
    # def parse_file(input_file):
    #     file_content = dict()
    #
    #     with open(input_file, "r") as fp:
    #
    #         dictionary_name = None  # string
    #         open_key = None  # a key not closed
    #         open_value = None
    #
    #         for l in fp:
    #             line = l.strip()
    #
    #             if line.startswith(r"//"):
    #                 continue
    #
    #             if open_key:
    #                 open_value += " " + line  # a new line is considered as a space
    #                 if open_value.endswith(";"):
    #                     file_content[dictionary_name][open_key[1:]] = open_value[
    #                                                                   :-1]  # remove starting "@" and handling ";"
    #                     open_key = open_value = None
    #                 else:
    #                     continue
    #             elif line.startswith(r"{"):
    #                 continue
    #             elif line.startswith(r"Dictionary"):
    #                 dictionary_name = line[len("Dictionary "):]
    #                 file_content[dictionary_name] = dict()
    #             elif line.startswith(r"@"):
    #                 if dictionary_name == None:
    #                     logging.exception("Parsing error: entry not inside a dictionary.")
    #                 key, value = line.split(None, 1)
    #
    #                 if value.endswith(";"):
    #                     file_content[dictionary_name][key[1:]] = value[:-1]  # remove starting "@" and handling ";"
    #                 else:  # the value is not ended in a single line
    #                     open_key = key
    #                     open_value = value
    #             elif line.startswith(r"}"):
    #                 dictionary_name = None
    #
    #         return file_content
    #
    # # TODO: unire con parse_file
    # @staticmethod
    # def parse_string(input_file):
    #     file_content = dict()
    #
    #     dictionary_name = None  # string
    #     open_key = None  # a key not closed
    #     open_value = None
    #
    #     for l in input_file.splitlines():
    #         line = l.strip()
    #
    #         if line.startswith(r"//"):
    #             continue
    #
    #         if open_key:
    #             open_value += " " + line  # a new line is considered as a space
    #             if open_value.endswith(";"):
    #                 file_content[dictionary_name][open_key[1:]] = open_value[
    #                                                               :-1]  # remove starting "@" and handling ";"
    #                 open_key = open_value = None
    #             else:
    #                 continue
    #         elif line.startswith(r"{"):
    #             continue
    #         elif line.startswith(r"Dictionary"):
    #             dictionary_name = line[len("Dictionary "):]
    #             file_content[dictionary_name] = dict()
    #         elif line.startswith(r"@"):
    #             if dictionary_name == None:
    #                 logging.exception("Parsing error: entry not inside a dictionary.")
    #             key, value = line.split(None, 1)
    #
    #             if value.endswith(";"):
    #                 file_content[dictionary_name][key[1:]] = value[:-1]  # remove starting "@" and handling ";"
    #             else:  # the value is not ended in a single line
    #                 open_key = key
    #                 open_value = value
    #         elif line.startswith(r"}"):
    #             dictionary_name = None
    #
    #     return file_content
    #
    # @staticmethod
    # def generate_string(file_content):
    #     s = ""
    #     for dictionary_name in file_content:
    #         s += 'Dictionary ' + dictionary_name + "\n"
    #         s += '{\n'
    #
    #         dictionary = file_content[dictionary_name]
    #         for key in dictionary:
    #             s += '\t\t@' + key + '\t' + dictionary[key] + ';\n'
    #
    #         s += '}\n'
    #
    #     return s
    #
    # @staticmethod
    # def generate_file(file_content, file_name):
    #     with open(file_name, 'w') as fp:
    #         fp.write(r'//OpenSmoke File input automatically generated' + '\n')
    #
    #         fp.write(OpenSmokeParser.generate_string(file_content))





# class InputFile():
#     def __init__(self, content, main_field):
#         # self.path = path
#         self.content = content
#         self.main_field = main_field
#
#     def change_model(self, new_model):
#         self.main.pop('KineticsPreProcessor', None)
#         self.main.pop('KineticsFolder', None)
#
#         self.main['KineticsFolder'] = new_model.path

    # @property
    # def main(self):
    #     return self.content[self.main_field]
    #
    # # return the dictionary corresponding to a certain name
    # def get_dict(self, name):
    #     dict_name = self.main.get(name, None)
    #     if dict_name:
    #         return self.content[dict_name]
    #     else:
    #         return None

    # def _refresh_file(self):
    #    OpenSmokeParser.generate_file(self.content, self.path)

    # @classmethod
    # def from_file(cls, path, main_field):
    #     if not os.path.exists(path):
    #         logging.exception("The specified input path does not exists.")
    #
    #     content = OpenSmokeParser.parse_file(path)
    #     return cls(content, main_field)
    #
    # def __str__(self):
    #     return OpenSmokeParser.generate_string(self.content)


# def get_input_template(model, exp_type, version="1", templateFolder="."):
#     templateFolder = Path(__location__) / "data/templates"
#     template_name = "{}_{}_{}_template.dic".format(model, exp_type, version)
#     path = templateFolder / template_name
#     inputFile = InputFile.from_file(path, model)
#     return inputFile


# def read_moles(s):
#     tokens = s.split()
#     couples = [[i, j] for i, j in zip(tokens[::2], tokens[1::2])]
#     return couples
#
#
# def read_initial_species(s, units, role=None):
#     couples = read_moles(s)
#     initial_species = []
#     for c in couples:
#         initial_species.append(models.InitialSpecie(name=c[0], units=units, amount=c[1], role=role))
#
#     return initial_species


# # TODO add exceptions, to finish
# def input_file_to_experiment(s):
#     content = OpenSmokeParser.parse_string(s)
#
#     common_properties = []
#     initial_species = []
#
#     if 'BatchReactor' in content:
#         input_file = InputFile(content, 'BatchReactor')
#         inlet_dict = input_file.get_dict('InitialStatus')
#
#         pressure = inlet_dict.get('Pressure', None)
#         pressure_amount = pressure.split()[0]
#         pressure_units = pressure.split()[1]
#
#         if not pressure:
#             return None
#         else:
#             common_properties.append(models.CommonProperty(name="pressure", units=pressure_units, value=pressure_amount))
#
#         if 'Moles' in inlet_dict:
#             pass
#         elif 'FuelMoles' in inlet_dict and 'OxidizerMoles' in inlet_dict and 'EquivalenceRatio' in inlet_dict:
#             phi = inlet_dict['EquivalenceRatio']
#             fuel_moles = read_initial_species(inlet_dict['FuelMoles'], 'moles', 'fuel')
#             oxidizer_moles = read_initial_species(inlet_dict['OxidizerMoles'], 'moles', 'oxidizer')
#
#             common_properties.append(models.CommonProperty(name="phi", units="unitless", value=phi))
#             initial_species.extend(fuel_moles)
#             initial_species.extend(oxidizer_moles)
#
#         return common_properties, initial_species


# def experimentToInputFile(e):
#     if e.run_type() == models.EType.batch_idt:
#         ### RETRIEVE TEMPLATE
#         input_file = get_input_template("BatchReactor", "parT", "1")
#
#         ### RETRIEVE EXPERIMENTAL DATA
#         pressure = e.common_properties.get(name="pressure")
#         pressure_value, pressure_units = pressure.value, pressure.units
#
#         temperature = e.data_columns.get(name="temperature")
#         min_temp, max_temp = min(temperature.data), max(temperature.data)
#         temperature_units = temperature.units
#
#         initial_species = e.initial_species.all()
#
#         ### GENERATE FILE
#         input_file.get_dict("InitialStatus")['Pressure'] = str(pressure_value) + " " + pressure_units
#         input_file.get_dict("InitialStatus")['Temperature'] = str(
#             min_temp) + " " + temperature_units  # useless but required
#         input_file.get_dict("InitialStatus")['Moles'] = " ".join(
#             i.name.upper() + " " + str(i.amount) for i in initial_species)
#         input_file.get_dict("ParametricAnalysis")['MinimumValue'] = str(min_temp) + " " + temperature_units
#         input_file.get_dict("ParametricAnalysis")['MaximumValue'] = str(max_temp) + " " + temperature_units
#         return input_file
#
#     elif e.run_type() == models.EType.stirred_parT:
#         ### RETRIEVE TEMPLATE
#         input_file = get_input_template("PerfectlyStirredReactor", "parT", "1")
#
#         ### RETRIEVE EXPERIMENTAL DATA
#         pressure = e.common_properties.get(name="pressure")
#         pressure_value, pressure_units = pressure.value, pressure.units
#
#         residence_time = e.common_properties.get(name="residence time")
#         residence_time_value, residence_time_units = residence_time.value, residence_time.units
#
#         volume = e.common_properties.get(name="volume")
#         volume_value, volume_units = volume.value, volume.units
#
#         temperature = e.data_columns.get(name="temperature")
#         min_temp, max_temp = min(temperature.data), max(temperature.data)
#         temperature_units = temperature.units
#
#         species_lists = e.data_columns.filter(species__isnull=False).values_list('species',
#                                                                                  flat=True)  # each column has a list of spieces
#         output_species = [s for sl in species_lists for s in sl]  # flatten in a single list of species
#
#         initial_species = e.initial_species.all()
#
#         ### GENERATE FILE
#         input_file.main['Volume'] = str(volume_value) + " " + volume_units
#         input_file.main['ResidenceTime'] = str(residence_time_value) + " " + residence_time_units
#
#         input_file.get_dict("InletStatus")['Pressure'] = str(pressure_value) + " " + pressure_units
#         input_file.get_dict("InletStatus")['Temperature'] = str(
#             min_temp) + " " + temperature_units  # useless but required
#         input_file.get_dict("InletStatus")['Moles'] = " ".join(
#             i.name.upper() + " " + str(i.amount) for i in initial_species)
#         input_file.get_dict("ParametricAnalysis")['MinimumValue'] = str(min_temp) + " " + temperature_units
#         input_file.get_dict("ParametricAnalysis")['MaximumValue'] = str(max_temp) + " " + temperature_units
#
#         input_file.get_dict("Options")['OutputSpecies'] = " ".join(output_species)
#         return input_file
#
#     elif e.run_type() == models.EType.flow_isothermal_parT:
#         input_file = get_input_template("PlugFlowReactor", "parT", "1")
#
#         ### RETRIEVE EXPERIMENTAL DATA
#         pressure = e.common_properties.get(name="pressure")
#         pressure_value, pressure_units = pressure.value, pressure.units
#
#         residence_time = e.common_properties.get(name="residence time")
#         residence_time_value, residence_time_units = residence_time.value, residence_time.units
#
#         temperature = e.data_columns.get(name="temperature")
#         min_temp, max_temp = min(temperature.data), max(temperature.data)
#         temperature_units = temperature.units
#
#         species_lists = e.data_columns.filter(species__isnull=False).values_list('species',
#                                                                                  flat=True)  # each column has a list of spieces
#         output_species = [s for sl in species_lists for s in sl]  # flatten in a single list of species
#
#         initial_species = e.initial_species.all()
#
#         ### GENERATE FILE
#         input_file.main['ResidenceTime'] = str(residence_time_value) + " " + residence_time_units
#
#         input_file.get_dict("InletStatus")['Pressure'] = str(pressure_value) + " " + pressure_units
#         input_file.get_dict("InletStatus")['Temperature'] = str(
#             min_temp) + " " + temperature_units  # useless but required
#         input_file.get_dict("InletStatus")['Moles'] = " ".join(
#             i.name.upper() + " " + str(i.amount) for i in initial_species)
#         input_file.get_dict("ParametricAnalysis")['MinimumValue'] = str(min_temp) + " " + temperature_units
#         input_file.get_dict("ParametricAnalysis")['MaximumValue'] = str(max_temp) + " " + temperature_units
#
#         input_file.get_dict("Options")['OutputSpecies'] = " ".join(output_species)
#         return input_file
#
#
#     elif e.run_type() == models.EType.flame_parPhi:
#         input_file = get_input_template("PlugFlowReactor", "parT", "1")
#
#         ### RETRIEVE EXPERIMENTAL DATA
#         pressure = e.common_properties.get(name="pressure")
#         pressure_value, pressure_units = pressure.value, pressure.units
#
#         residence_time = e.common_properties.get(name="residence time")
#         residence_time_value, residence_time_units = residence_time.value, residence_time.units
#
#         temperature = e.data_columns.get(name="temperature")
#         min_temp, max_temp = min(temperature.data), max(temperature.data)
#         temperature_units = temperature.units
#
#         species_lists = e.data_columns.filter(species__isnull=False).values_list('species',
#                                                                                  flat=True)  # each column has a list of spieces
#         output_species = [s for sl in species_lists for s in sl]  # flatten in a single list of species
#
#         initial_species = e.initial_species.all()
#
#         ### GENERATE FILE
#         input_file.main['ResidenceTime'] = str(residence_time_value) + " " + residence_time_units
#
#         input_file.get_dict("InletStatus")['Pressure'] = str(pressure_value) + " " + pressure_units
#         input_file.get_dict("InletStatus")['Temperature'] = str(
#             min_temp) + " " + temperature_units  # useless but required
#         input_file.get_dict("InletStatus")['Moles'] = " ".join(
#             i.name.upper() + " " + str(i.amount) for i in initial_species)
#         input_file.get_dict("ParametricAnalysis")['MinimumValue'] = str(min_temp) + " " + temperature_units
#         input_file.get_dict("ParametricAnalysis")['MaximumValue'] = str(max_temp) + " " + temperature_units
#
#         input_file.get_dict("Options")['OutputSpecies'] = " ".join(output_species)
#         return input_file
#
#     return None


# def retrieve_opensmoke_execution(e_id, model_names=None, model_ids=None, output_root=".\output_experiments"):
#     if model_names is None and model_ids is not None:
#         model_names = list(models.ChemModel.objects.filter(id__in=model_ids).values_list('name', flat=True))
#         print(model_names)
#
#
#     file_paths = []
#     for mn in model_names:
#         p = output_root + "\{}__{}*".format(e_id, mn)
#         print(p)
#         fp = glob.glob(p)
#
#         for i in fp:
#             if os.path.isdir(i):
#                 file_paths.append(i)
#
#     return file_paths


