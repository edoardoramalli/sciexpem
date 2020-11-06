import sys, os, django, argparse
# BEFORE RUNNING THIS SCRIPT, IT IS NECESSARY TO ADD THE ROOT PROJECT FOLDER TO THE PYTHONPATH

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SciExpeM.settings")
django.setup()

from experimentmanager import models

models.Experiment.objects.all().delete()
models.OpenSmokeInput.objects.all().delete()
models.Execution.objects.all().delete()
models.ExecutionColumn.objects.all().delete()
models.CurveMatchingResult.objects.all().delete()
models.DataColumn.objects.all().delete()