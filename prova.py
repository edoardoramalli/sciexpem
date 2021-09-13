import os
import django
import requests, json
from dateutil.parser import parse
from django.db.models import Q
import matplotlib.pyplot as plt
import numpy as np
from tqdm import tqdm
from matplotlib.backends.backend_pdf import PdfPages


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SciExpeM.settings")
django.setup()

from ExperimentManager.Models import *


ids = [751, 479, 752, 485, 714, 749, 750]

spec = Specie.objects.get(id=85)

for exp_id in ids:
    exp_obj = Experiment.objects.get(id=exp_id)
    columns = exp_obj.data_columns.all()
    for column in columns:
        if column.label == '[NC6H12]':
            column.species_object.add(spec)
            break