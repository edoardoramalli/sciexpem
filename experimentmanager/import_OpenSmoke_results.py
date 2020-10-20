import sys, os, django, argparse

import traceback

from django.db import transaction


# BEFORE RUNNING THIS SCRIPT, IT IS NECESSARY TO ADD THE ROOT PROJECT FOLDER TO THE PYTHONPATH

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SciExpeM.settings")
django.setup()

from experimentmanager import models
from experimentmanager.opensmoke import OpenSmokeParser


def dir_path(string):
    if os.path.isdir(string):
        return string
    else:
        raise NotADirectoryError(string)


def parse_OpenSmoke_output(files, model_name, path):
    counter = 0

    print("Imported OpenSmoke Output: {}/{}".format(counter, len(files)), end="")
    for index, file in enumerate(files):
        print("\rImported OpenSmoke Output: {}/{}".format(counter, len(files)), end="")
        # Check link Output <--> Experiment
        related_experiment = models.Experiment.objects.filter(fileDOI__contains=file)
        if not related_experiment:
            print("Corresponding experiment not found:", file)
            continue
        else:
            related_experiment = related_experiment[0]

        # Check Link Output <--> ChemModel
        chem_model = models.ChemModel.objects.filter(name=model_name)[0]
        if not chem_model:
            print("Corresponding model not found:", model_name)
            continue

        try:
            with transaction.atomic():
                # Create Execution DB Object
                if not models.Execution.objects.filter(chemModel=chem_model, experiment=related_experiment).exists():
                    execution = models.Execution(chemModel=chem_model, experiment=related_experiment)
                    execution.save()
                    # TODO a seconda del tipo di exp ParametricAnalysisIDT.out o ParametricAnalysis.out
                    dataframe, units = OpenSmokeParser.parse_output(os.path.join(
                        path, file, "ParametricAnalysisIDT.out"))

                    list_header = list(dataframe)
                    for header in list_header:
                        data = models.ExecutionColumn(name=header,
                                                      units=units[header],
                                                      data=list(dataframe[header]),
                                                      execution=execution)
                        data.save()

                    counter += 1

        except Exception as err:
            print(file)
            print(traceback.format_exc())

    return counter


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', type=dir_path)
    parser.add_argument('--model', type=str)

    args = parser.parse_args()

    path = args.path
    model_name = args.model

    list_model_names = [m.name for m in models.ChemModel.objects.all()]

    if model_name not in list_model_names:
        print("Model list:", list_model_names)
        raise ValueError("Model Name does not exists")

    dirs = [folder for folder in os.listdir(path)
            if os.path.isfile(os.path.join(path, folder, "ParametricAnalysis.out"))]

    counter = parse_OpenSmoke_output(dirs, model_name, path)

    print("\rImported OpenSmoke Output: {}/{}".format(counter, len(dirs)))


if __name__ == "__main__":
    main()
