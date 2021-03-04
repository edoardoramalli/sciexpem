import tempfile
import subprocess
import os
from django.conf import settings


class OptimaPP:

    path = settings.OPTIMAPP_PATH

    @staticmethod
    def txt_to_xml(txt):

        # create a temporary directory
        with tempfile.TemporaryDirectory() as sandbox:
            tmp_txt_file_name = "tmp.txt"
            tmp_txt_file_name_path = os.path.join(sandbox, tmp_txt_file_name)
            tmp_txt_file = open(tmp_txt_file_name_path, "w+")
            tmp_txt_file.write(txt)
            tmp_txt_file.close()

            bashCommand = "cd " + OptimaPP.path + " && "
            bashCommand += " ./OptimaPP TXT_TO_XML "
            bashCommand += tmp_txt_file_name_path
            bashCommand += " -o "
            bashCommand += sandbox

            process = subprocess.Popen(bashCommand, shell=True, stdout=subprocess.PIPE)
            output, error = process.communicate()
            output = str(output)

            txt_start_warning = "-------------------------------------- + ---------------------------------------"

            if error is None:
                error = ""

            error += output[output.find(txt_start_warning) + len(txt_start_warning) + 2: output.rfind("Completed")]

            # print("EDOOOO\n",file=sys.stderr)
            # print(error, file=sys.stderr)

            if not error:
                xml_result_path = os.path.join(sandbox, "tmp.xml")
                xml_file_string = ''.join(open(xml_result_path, "r").readlines())
                return xml_file_string, None
            else:
                return None, error


class TranslatorOptimaPP:
    @staticmethod
    def create_lines(delimiter="\t", **kwargs):
        txt = ""
        keys = kwargs.keys()
        for key in keys:
            c_key = key.replace("__", " ")
            if kwargs[key] is None:
                continue
            txt += c_key + ":" + delimiter + str(kwargs[key]) + "\n"

        return txt

    @staticmethod
    def create_inline(delimiter="\t", **kwargs):
        txt = ""
        keys = kwargs.keys()
        for key in keys:
            c_key = key.replace("__", " ")
            if kwargs[key] is None:
                continue
            txt += c_key + ":" + delimiter + str(kwargs[key]) + delimiter

        return txt

    @staticmethod
    def create_header(experiment, file_paper):
        txt = ""
        if file_paper.references:
            txt += TranslatorOptimaPP.create_lines(Reference__description=file_paper.references)
        if file_paper.reference_doi:
            txt += TranslatorOptimaPP.create_lines(Reference__DOI=file_paper.reference_doi)

        txt += TranslatorOptimaPP.create_lines(File__author="Politecnico di Milano, Italy",
                                               Specification__version=2.2,
                                               File__DOI=experiment.fileDOI,  # M
                                               Experiment__type=experiment.experiment_type,  # M
                                               Apparatus=experiment.reactor)  # M
        return txt

    @staticmethod
    def create_common_experimental_conditions(initial_species, common_properties):
        txt = "Common experimental conditions:\n"
        for prop in common_properties:
            txt += TranslatorOptimaPP.create_inline(Name=prop.name,
                                                    Source_type="reported",
                                                    Unit=prop.units,
                                                    Value=prop.value) + "\n"
        for specie in initial_species:
            txt += TranslatorOptimaPP.create_inline(Name="composition",
                                                    Species=specie.name,
                                                    Source_type="calculated",
                                                    Unit=specie.units,
                                                    Value=specie.value) + "\n"
        return txt

    @staticmethod
    def create_varied_experimental_conditions_and_measured_results(data_group):
        txt = "Varied experimental conditions and measured results:\n"
        txt += TranslatorOptimaPP.create_inline(dataGroupID=data_group[0].dg_id) + "\n"
        ids = set([])
        for index, data in enumerate(data_group):
            id_x = "x" + str(index)
            ids.add(id_x)
            txt += TranslatorOptimaPP.create_inline(Name=data.name,
                                                    Label=data.label,
                                                    Species=data.species[0] if data.species else None,
                                                    Unit=data.units,
                                                    ID=id_x,
                                                    Source_type="reported")
            txt += "\n"
        txt += "\n"
        txt += "Varied values:\n"
        for id in ids:
            txt += str(id) + "\t"
        txt += "\n"
        for index in range(0, len(data_group[0].data)):
            for column in data_group:
                txt += str(column.data[index]) + "\t"
            txt += "\n"
        txt += "\n"
        return txt

    @staticmethod
    def create_volume_time_profile(data_group, offset_dg2):
        txt = "Volume-time profile:\n"
        txt += TranslatorOptimaPP.create_inline(dataGroupID=data_group[0].dg_id) + "\n"
        ids = set([])
        for index, data in enumerate(data_group):
            id_x = "x" + str(offset_dg2 + index)
            ids.add(id_x)
            txt += TranslatorOptimaPP.create_inline(Name=data.name,
                                                    Label=data.label,
                                                    Unit=data.units,
                                                    ID=id_x,
                                                    Source_type="calculated")
            txt += "\n"
        txt += "\n"
        txt += "Profile:\n"
        for id in ids:
            txt += str(id) + "\t"
        txt += "\n"
        for index in range(0, len(data_group[0].data)):
            for column in data_group:
                txt += str(column.data[index]) + "\t"
            txt += "\n"
        txt += "\n"
        return txt

    @staticmethod
    def create_ignition_definition(experiment):
        if experiment.ignition_type is not None:
            split = experiment.ignition_type.split("-")
            txt = "Ignition definition:\n MeasuredQuantity: %s  Type: %s" % (split[0], split[1])
            return txt
        else:
            return ""

    @staticmethod
    def create_OptimaPP_txt(experiment, data_groups, initial_species, common_properties, file_paper):
        txt = ""
        txt += TranslatorOptimaPP.create_header(experiment, file_paper)
        txt += TranslatorOptimaPP.create_common_experimental_conditions(initial_species, common_properties)
        dg1 = []
        dg2 = []
        for column in data_groups:
            if column.dg_id == "dg1":
                dg1.append(column)
            elif column.dg_id == "dg2":
                dg2.append(column)
        offset_dg2 = len(dg1)
        txt += TranslatorOptimaPP.create_varied_experimental_conditions_and_measured_results(dg1)
        if dg2:
            txt += TranslatorOptimaPP.create_volume_time_profile(dg2, offset_dg2)
        if experiment.experiment_type == "ignition delay measurement":
            txt += TranslatorOptimaPP.create_ignition_definition(experiment)
        return txt
