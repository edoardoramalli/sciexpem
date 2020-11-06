import sys, os, django, argparse

import traceback

from django.db import transaction


# BEFORE RUNNING THIS SCRIPT, IT IS NECESSARY TO ADD THE ROOT PROJECT FOLDER TO THE PYTHONPATH

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SciExpeM.settings")
django.setup()

from experimentmanager import models

from django.db.models import Q

from curve_matching import CurveMatchingExecutor, execute_curve_matching_django

executions = models.Execution.objects.all()
models = models.ChemModel.objects.filter(Q(name="CRECK_1412_H2") | Q(name="CRECK_2003_H2"))

print("Execute CM: {}.{} / {}.{}".format(0, 0, len(executions) - 1, len(models) - 1), end="")

for index_m, model in enumerate(models):
    for index, exec in enumerate(executions):
        print("\rExecute CM: {}.{} / {}.{}".format(index, index_m, len(executions) -1, len(models)-1), end="")
        execute_curve_matching_django(exec)
print("")
