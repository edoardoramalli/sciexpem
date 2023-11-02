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

            process = subprocess.Popen(bashCommand, shell=True, stdout=subprocess.PIPE, encoding='utf-8')
            output, error = process.communicate()
            output = str(output)

            txt_start_warning = "-------------------------------------- + ---------------------------------------"

            if error is None:
                error = ""

            error += output[output.find(txt_start_warning) + len(txt_start_warning) + 1: output.rfind("Completed")]

            error_split = [x.replace('\t', '').strip() for x in error.split('\n') if x.replace('\t', '').strip()]

            still = []
            for e in error_split:
                if 'Type check' in e:
                    continue
                elif 'Warning!' in e:
                    continue
                else:
                    still.append(e)

            error = '\n'.join(still)

            # print("EDOOOO\n",file=sys.stderr)

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
    def create_inline(delimiter="\t", species_used=None, **kwargs):
        txt = ""
        keys = kwargs.keys()
        for key in keys:
            c_key = key.replace("__", " ")
            if kwargs[key] is None:
                continue
            if key == 'Species_LIST':
                for index, species in enumerate(kwargs[key]):
                    if species.preferredKey in species_used:
                        preferredKey = species.preferredKey + '_' + str(species_used[species.preferredKey])
                        species_used[species.preferredKey] += 1
                    else:
                        preferredKey = species.preferredKey
                        species_used[species.preferredKey] = 1

                    if species.preferredKey:
                        txt += "Species:" + delimiter + preferredKey + delimiter
                    if species.chemName:
                        txt += "Chemical_name:" + delimiter + species.chemName + delimiter
                    if species.CAS:
                        txt += "CAS:" + delimiter + species.CAS + delimiter
                    if species.InChI:
                        txt += "InChI:" + delimiter + species.InChI + delimiter
                    if species.SMILES:
                        txt += "SMILES:" + delimiter + species.SMILES + delimiter

            else:
                txt += c_key + ":" + delimiter + str(kwargs[key]) + delimiter

        return txt

    @staticmethod
    def create_header(experiment, file_paper):
        txt = ""
        if file_paper.description:
            txt += TranslatorOptimaPP.create_lines(Reference__description=file_paper.description)
        if file_paper.reference_doi:
            txt += TranslatorOptimaPP.create_lines(Reference__DOI=file_paper.reference_doi)
        if file_paper.author:
            txt += TranslatorOptimaPP.create_lines(Reference__document__author=file_paper.author)
        if file_paper.page:
            txt += TranslatorOptimaPP.create_lines(Reference__document__pages=file_paper.page)
        if file_paper.journal:
            txt += TranslatorOptimaPP.create_lines(Reference__document__journal=file_paper.journal)
        if file_paper.title:
            txt += TranslatorOptimaPP.create_lines(Reference__document__title=file_paper.title)
        if file_paper.volume:
            txt += TranslatorOptimaPP.create_lines(Reference__document__volume=file_paper.volume)
        if file_paper.year:
            txt += TranslatorOptimaPP.create_lines(Reference__document__year=file_paper.year)

        txt += TranslatorOptimaPP.create_lines(File__author="Politecnico di Milano, Italy",
                                               Specification__version=2.3,
                                               File__DOI=experiment.fileDOI,  # M
                                               Experiment__type=experiment.experiment_type,  # M
                                               Apparatus=experiment.reactor)  # M
        if experiment.reactor_modes:
            for mode in experiment.reactor_modes:
                txt += TranslatorOptimaPP.create_lines(Operation__mode=mode)

        return txt

    @staticmethod
    def create_common_experimental_conditions(initial_species, common_properties, species_used):
        txt = "Common experimental conditions:\n"
        for prop in common_properties:
            txt += TranslatorOptimaPP.create_inline(Name=prop.name,
                                                    Source_type=prop.source_type,
                                                    Unit=prop.units,
                                                    Value=prop.value) + "\n"
        for i_species in initial_species:
            if i_species.species.preferredKey in species_used:
                preferredKey = i_species.species.preferredKey + '_' + str(species_used[i_specie.specie.preferredKey])
                species_used[i_species.species.preferredKey] += 1
            else:
                preferredKey = i_species.species.preferredKey
                species_used[i_species.species.preferredKey] = 1

            txt += TranslatorOptimaPP.create_inline(Name="composition",
                                                    Species=preferredKey,
                                                    Chemical_name=i_species.species.chemName,
                                                    CAS=i_species.species.CAS,
                                                    InChI=i_species.species.InChI,
                                                    SMILES=i_species.species.SMILES,
                                                    Source_type=i_species.source_type,
                                                    Unit=i_species.units,
                                                    Value=i_species.value) + "\n"
        return txt

    @staticmethod
    def create_varied_experimental_conditions_and_measured_results(data_group, offset, species_used):
        txt = TranslatorOptimaPP.create_inline(dataGroupID=data_group[0].dg_id,
                                               dataGroupLabel=data_group[0].dg_label) + "\n"

        tmp = []
        # To be sure that the uncertainty are at the end and I can refer them...
        for column in data_group:
            if not column.uncertainty_kind:
                tmp.insert(0, column)
            else:
                tmp.append(column)

        id_association = {}
        ids = []
        for index, data in enumerate(tmp):
            id_x = "x" + str(index + offset)
            ids.append(id_x)
            id_association[data] = id_x
            if not data.uncertainty_kind:
                txt += TranslatorOptimaPP.create_inline(Name=data.name,
                                                        Label=data.label,
                                                        Species_LIST=data.species_object.all(),
                                                        Unit=data.units,
                                                        ID=id_x,
                                                        Source_type=data.source_type,
                                                        species_used=species_used)
            else:
                txt += TranslatorOptimaPP.create_inline(Name=data.name,
                                                        Label=data.label,
                                                        Species_LIST=data.species_object.all(),
                                                        species_used=species_used,
                                                        Unit=data.units,
                                                        ID=id_x,
                                                        Source_type=data.source_type,
                                                        Reference=id_association[data.uncertainty],
                                                        Kind=data.uncertainty_kind,
                                                        Bound=data.uncertainty_bound)
            txt += "\n"

        txt += "\n"
        txt += "Varied values:\n"
        for id in ids:
            txt += str(id) + "\t"
        txt += "\n"
        for index in range(0, len(tmp[0].data)):
            for column in tmp:
                txt += str(column.data[index]) + "\t"
            txt += "\n"
        txt += "\n"
        return txt

    @staticmethod
    def create_profile(data_group, offset):
        txt = "Volume-time profile:\n"
        txt += TranslatorOptimaPP.create_inline(dataGroupID=data_group[0].dg_id,
                                                dataGroupLabel=data_group[0].dg_label,
                                                dataPointLink=';'.join(data_group[0].data_group_profile)) + "\n"

        tmp = data_group

        ids = []
        for index, data in enumerate(tmp):
            id_x = "x" + str(index + offset)
            ids.append(id_x)
            txt += TranslatorOptimaPP.create_inline(Name=data.name,
                                                    Label=data.label,
                                                    Unit=data.units,
                                                    ID=id_x,
                                                    Source_type=data.source_type)

            txt += "\n"
        txt += "\n"
        txt += "Profile:\n"
        for id in ids:
            txt += str(id) + "\t"
        txt += "\n"
        for index in range(0, len(tmp[0].data)):
            for column in tmp:
                txt += str(column.data[index]) + "\t"
            txt += "\n"
        txt += "\n"
        return txt

    @staticmethod
    def create_ignition_definition(experiment):
        if experiment.ignition_type is not None:
            split = experiment.ignition_type.split("-")
            txt = "Ignition definition:\nMeasuredQuantity: %s  Type: %s" % (split[0], split[1])
            return txt
        else:
            return ""

    @staticmethod
    def create_OptimaPP_txt(experiment, data_groups, initial_species, common_properties, file_paper):
        species_used = {}

        txt = ""
        txt += TranslatorOptimaPP.create_header(experiment, file_paper)
        txt += TranslatorOptimaPP.create_common_experimental_conditions(initial_species, common_properties,
                                                                        species_used)

        data_groups_dict = {}
        data_groups_dict_profile = {}
        for column in data_groups:
            if not (column.data_group_profile or column.dg_label in ['V-t history', 'p-t history', 'T-t history']):
                if column.dg_id not in data_groups_dict:
                    data_groups_dict[column.dg_id] = [column]
                else:
                    data_groups_dict[column.dg_id].append(column)
            else:
                if column.dg_id not in data_groups_dict_profile:
                    data_groups_dict_profile[column.dg_id] = [column]
                else:
                    data_groups_dict_profile[column.dg_id].append(column)

        data_groups_dict = dict(sorted(data_groups_dict.items()))
        data_groups_dict_profile = dict(sorted(data_groups_dict_profile.items()))

        txt += "Varied experimental conditions and measured results:\n"

        offset_id = 1
        for dg in data_groups_dict:
            txt += TranslatorOptimaPP.create_varied_experimental_conditions_and_measured_results(data_groups_dict[dg],
                                                                                                 offset_id,
                                                                                                 species_used)
            offset_id += len(data_groups_dict[dg])

        for dg in data_groups_dict_profile:
            txt += TranslatorOptimaPP.create_profile(data_groups_dict_profile[dg], offset_id)
            offset_id += len(data_groups_dict_profile[dg])

        if experiment.experiment_type == "ignition delay measurement":
            txt += TranslatorOptimaPP.create_ignition_definition(experiment)

        return txt
