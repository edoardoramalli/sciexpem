import sys, os, django, argparse
from django.conf import settings

import traceback
import glob


from django.db import transaction

# BEFORE RUNNING THIS SCRIPT, IT IS NECESSARY TO ADD THE ROOT PROJECT FOLDER TO THE PYTHONPATH


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SciExpeM.settings")
django.setup()

from experimentmanager import models


def import_input(files):
    counter = 0

    for file in files:
        experiment_name = file[file.rfind("/") + 1:].replace(".xml.dic", "")
        try:
            with transaction.atomic():

                related_experiment = models.Experiment.objects.filter(fileDOI__contains=experiment_name)

                if not related_experiment:
                    print("Related Experiment not found:", experiment_name)
                    continue
                else:
                    related_experiment = related_experiment[0]

                # Check duplicates
                if models.OpenSmokeInput.objects.filter(experiment=related_experiment).exists():
                    print("Duplicate OpenSmoke Input: ", experiment_name)
                    continue

                OpenSmokeInput = models.OpenSmokeInput(experiment=related_experiment, path=file)
                OpenSmokeInput.save()

            counter += 1

        except Exception as err:
            print(file)
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

    input_files = glob.glob(path + '/**/*.xml.dic', recursive=True)

    counter = import_input(input_files)

    print("Imported OpenSmoke Input: {}/{}".format(counter, len(input_files)))


if __name__ == "__main__":
    main()

