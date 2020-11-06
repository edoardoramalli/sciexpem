import sys, os, django, argparse
from django.conf import settings

import traceback
import pandas as pd

from django.db import transaction

# BEFORE RUNNING THIS SCRIPT, IT IS NECESSARY TO ADD THE ROOT PROJECT FOLDER TO THE PYTHONPATH

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SciExpeM.settings")
django.setup()

from experimentmanager import models


def import_IO_ReSpecThOS(entries):
    counter = 0

    for entry in entries:
        try:
            with transaction.atomic():
                experiment_type = entry[0]
                reactor = entry[1]
                data_group_fields = entry[2]
                additional_info = entry[3]
                output_file = entry[4]
                output_fields = entry[5]

                # Check duplicates
                if models.IOReSpecThOS.objects.filter(experiment_type=experiment_type,
                                                      reactor=reactor,
                                                      data_group_fields=set(data_group_fields),
                                                      additional_info=additional_info,
                                                      output_file=output_file,
                                                      output_fields=set(output_fields)).exists():
                    print("DUPLICATE I/O ReSpecTh/OS: ", entry)
                    continue

                ioReSpecThOS = models.IOReSpecThOS(experiment_type=experiment_type,
                                                   reactor=reactor,
                                                   data_group_fields=data_group_fields,
                                                   additional_info=additional_info,
                                                   output_file=output_file,
                                                   output_fields=output_fields)
                ioReSpecThOS.save()

            counter += 1

        except Exception as err:
            print(entry)
            print(traceback.format_exc())
    return counter


def file_path(string):
    if os.path.isfile(string):
        return string
    else:
        raise FileNotFoundError(string)


def parse_IO_ReSpecThOS(path):
    entries = []

    with open(path, "r") as file:
        header_split = file.readline().strip().split(";")
        for line in file:
            line_split = line.strip().split(";")
            experiment_type = line_split[0]
            reactor = line_split[1]
            data_group_par = line_split[2].split(",")
            add_info = line_split[3]
            os_file = line_split[4]
            os_par = line_split[5].split(",")
            if 0 in (experiment_type, reactor, os_file) or ["0"] in (data_group_par, os_par):
                continue
            else:
                entries.append((experiment_type, reactor, data_group_par, add_info, os_file, os_par))

    return entries


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', type=file_path)

    args = parser.parse_args()

    path = args.path

    entries = parse_IO_ReSpecThOS(path)

    counter = import_IO_ReSpecThOS(entries)

    print("Imported Models: {}/{}".format(counter, len(entries)))


if __name__ == "__main__":
    main()
