import sys, os, django, argparse
from django.conf import settings

import traceback
import glob


from django.db import transaction

# BEFORE RUNNING THIS SCRIPT, IT IS NECESSARY TO ADD THE ROOT PROJECT FOLDER TO THE PYTHONPATH


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SciExpeM.settings")
django.setup()

from experimentmanager import models


def import_models(files, path):
    counter = 0

    for f in files:
        try:
            with transaction.atomic():

                name = f
                model_path = os.path.join(path, name, "kinetics")

                kinetics_file = os.path.join(model_path, "kinetics.xml")
                reaction_names_file = os.path.join(model_path, "reaction_names.xml")

                if not os.path.isfile(kinetics_file):
                    print("Folder", model_path, "does not contains kinetics.xml")
                    continue

                if not os.path.isfile(reaction_names_file):
                    print("Folder", model_path, "does not contains reaction_names.xml")
                    continue

                xml_file_kinetics = open(kinetics_file).read()
                xml_file_reaction_names = open(reaction_names_file).read()

                # Check duplicates
                if models.ChemModel.objects.filter(name=name).exists():
                    print("DUPLICATE MODEL: ", name)
                    continue

                chemModel = models.ChemModel(name=name,
                                             xml_file_kinetics=xml_file_kinetics,
                                             xml_file_reaction_names=xml_file_reaction_names)
                chemModel.save()

            counter += 1

        except Exception as err:
            print(f)
            print(traceback.format_exc())
    return counter


def dir_path(string):
    if os.path.isdir(string):
        return string
    else:
        raise NotADirectoryError(string)


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('--path', type=dir_path)

    args = parser.parse_args()

    path = args.path

    # Get all folder names as model names if they have a kinetics subfolder --> TODO extend control rules
    dirs = [folder for folder in os.listdir(path) if os.path.isdir(os.path.join(path, folder, "kinetics"))]

    counter = import_models(dirs, path)

    print("Imported Models: {}/{}".format(counter, len(dirs)))


if __name__ == "__main__":
    main()

