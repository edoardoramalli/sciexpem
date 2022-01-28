import os
import django
from django.db.models import Q, Count, F
from django.utils import timezone

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SciExpeM.settings")
django.setup()

from ExperimentManager.Models import *

import json
import random

with open('/Users/edoardo/Downloads/SciExpeM_InsertForm (1).json', 'r') as f:
    diz_experiment = json.loads(f.read())

print(diz_experiment)

diz_experiment['fileDOI'] = 'tmp_' + str(random.randint(0, int(1e20)))
diz_experiment['username'] = 'andrea.nobili'

print(diz_experiment['os_input_file'])

list_objects = getattr(Experiment, 'createExperiment')(diz_experiment)

