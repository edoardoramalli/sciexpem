from threading import Thread
import os
import django
import requests, json
from dateutil.parser import parse
from django.db.models import Q

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SciExpeM.settings")
django.setup()
from django.db import transaction
from ExperimentManager.Models import *
from django.utils import timezone
from OpenSmoke.OpenSmoke import OpenSmokeParser, OpenSmokeExecutor, check_Experiment_Model
from tqdm import tqdm
import time

model_id = 4

bar = tqdm(Experiment.objects.filter(status='verified'))
for x in bar:
    bar.set_description("Processing ID {}".format(x.id))
    with transaction.atomic():
        query = Execution.objects.filter(experiment=x, chemModel__id=model_id)
        if query.exists():
            pass
        else:
            exp = x
            model = ChemModel.objects.get(id=model_id)

            if not check_Experiment_Model(experiment_id=exp.id, chemModel_id=model_id):
                continue

            new_exec = Execution(experiment=exp,
                                 chemModel=model,
                                 execution_start=timezone.localtime(),
                                 username='root')
            new_exec.save()

            solver = exp.experiment_interpreter.solver

            mapping_files = list(set([mapping.file for mapping in exp.experiment_interpreter.mappings.all()]))

            Thread(target=OpenSmokeExecutor.execute,
                   args=(x.id, model_id, new_exec.id, solver, mapping_files)).start()

            time.sleep(60)
