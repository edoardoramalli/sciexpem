from OpenSmoke.OpenSmoke import OpenSmokeParser
from OpenSmoke.Tools import create_list_string_profiles
import ExperimentManager.Models as Model
import os


def createFilesSimulation_utils(exec_id, exp_id, chemModel_id):

    chemModel = Model.ChemModel.objects.get(id=chemModel_id)
    experiment = Model.Experiment.objects.get(id=exp_id)

    results = {}

    profile_names = []

    if experiment.data_columns.filter(dg_label__contains='history').exists():

    # if experiment.reactor == 'rapid compression machine':  # TODO migliorare per altri casi con profili

        # profile_path = os.path.join(folderPath, "profiles")
        # os.makedirs(profile_path, exist_ok=True)

        for index, profile_string in enumerate(create_list_string_profiles(exp_id=exp_id)):
            path_profile = './profiles/profile_{}.csv'.format(index)
            profile_names.append(path_profile)
            results[path_profile] = profile_string


    #  Mandatory fields in the database model. So no empty fields
    kinetics_file = chemModel.xml_file_kinetics
    reaction_names_file = chemModel.xml_file_reaction_names

    # Must be present to verify and experiment
    open_smoke_input_file = experiment.os_input_file

    results['./kinetics/kinetics.xml'] = kinetics_file
    results['./kinetics/reaction_names.xml'] = reaction_names_file

    open_smoke_input_text = OpenSmokeParser.create_output(file=open_smoke_input_file, model_path='./kinetics/',
                                                          output_path='./results/'.format(exec_id),
                                                          profiles=' '.join(profile_names))

    results['input.dic'] = open_smoke_input_text

    return results


def createFolderSimulation_utils(exp_id, chemModel_id, folderPath):
    # IDs already checked by caller function
    chemModel = Model.ChemModel.objects.get(id=chemModel_id)
    experiment = Model.Experiment.objects.get(id=exp_id)

    profile_names = []

    if experiment.reactor == 'rapid compression machine':  # TODO migliorare per altri casi con profili

        profile_path = os.path.join(folderPath, "profiles")
        os.makedirs(profile_path, exist_ok=True)

        for index, profile_string in enumerate(create_list_string_profiles(exp_id=exp_id)):
            name_path = os.path.join(profile_path, 'profile_{}.csv'.format(index))
            profile_names.append(name_path)
            os_file = open(name_path, "w+")
            os_file.write(profile_string)
            os_file.close()

    #  Mandatory fields in the database model. So no empty fields
    kinetics_file = chemModel.xml_file_kinetics
    reaction_names_file = chemModel.xml_file_reaction_names

    # Must be present to verify and experiment
    open_smoke_input_file = experiment.os_input_file

    kinetic_path = os.path.join(folderPath, "kinetics")
    os.makedirs(kinetic_path, exist_ok=True)

    kin_file = open(os.path.join(kinetic_path, "kinetics.xml"), "w+")
    kin_file.write(kinetics_file)
    kin_file.close()

    reac_file = open(os.path.join(kinetic_path, "reaction_names.xml"), "w+")
    reac_file.write(reaction_names_file)
    reac_file.close()

    open_smoke_input_text = OpenSmokeParser.create_output(file=open_smoke_input_file, model_path=kinetic_path,
                                                          output_path=folderPath, profiles=' '.join(profile_names))
    os_file = open(os.path.join(folderPath, "input.dic"), "w+")
    os_file.write(open_smoke_input_text)
    os_file.close()
