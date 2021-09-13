from OpenSmoke.OpenSmoke import OpenSmokeParser

import ExperimentManager.Models as Model
import os


def createFolderSimulation_utils(exp_id, chemModel_id, folderPath):
    # IDs already checked by caller function
    chemModel = Model.ChemModel.objects.get(id=chemModel_id)
    experiment = Model.Experiment.objects.get(id=exp_id)

    #  Mandatory fields in the model. So no empty fields
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

    open_smoke_input_text = OpenSmokeParser.create_output(open_smoke_input_file, kinetic_path, folderPath)
    os_file = open(os.path.join(folderPath, "input.dic"), "w+")
    os_file.write(open_smoke_input_text)
    os_file.close()
