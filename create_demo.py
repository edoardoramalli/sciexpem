import os
import django
from django.db.models import Avg
import numpy as np
from scipy import interpolate, integrate
import json
import matplotlib.pyplot as plt
from tqdm import tqdm
from statistics import median, mean, stdev, variance
from SplinePoliMi import Spline

from dateutil.parser import parse
from django.db.models import Q

from itertools import combinations

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SciExpeM.settings_demo")
django.setup()

from ExperimentManager.Models import *
from ExperimentManager.Views.getSimulation import create_summary

import random
#
models = ChemModel.objects.all()

for model in models:
    if model.id not in [1, 5, 14]:
        model.delete()


exit()

types = set(Experiment.objects.all().values_list('experiment_type', flat=True))

print(types)

keep = []

for t in types:

    a = list(Experiment.objects.filter(experiment_type=t).values_list('id', flat=True))

    keep = keep + a[:100]
    # print(a[:100])

    # continue

if keep:
    for e in Experiment.objects.all():
        if e.id not in keep:
            e.delete()
            # print('edoooooo')







