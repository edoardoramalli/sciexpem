import os
import django
import requests, json
from dateutil.parser import parse
from django.db.models import Q

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SciExpeM.settings")
django.setup()

from ExperimentManager.Models import *


a = Execution.objects.filter(Q(username='root') & ~Q(execution_end=None) & Q(execution_columns=None))

# print(set([x.experiment.id for x in a]))
#
# exit()


for x in a:
    x.delete()






exit()


import timeit
import xml.etree.ElementTree as ET



exec = Execution.objects.filter(~Q(execution_error=None) & Q(username='root'))

print(sorted([e.experiment.id for e in exec]))


# Simulazioni con errori
print('ERRORI', sorted([e.experiment.id for e in Execution.objects.filter(~Q(execution_error=None))]))

# Simulazioni non concluse
print('Not Ended', sorted([e.experiment.id for e in Execution.objects.filter(execution_end=None)]))

# Simulazioni senza risultati
print('Ended but No columns', sorted(list(set([e.experiment.id for e in Execution.objects.filter(Q(execution_columns=None) & ~Q(execution_end=None))]))))

# Colonne Simulazioni senza CM
# curve_matching_result

query = ExecutionColumn.objects.filter(Q(curve_matching_result=None) &
                                       ~Q(label__in=['T0', 't', 'T', 'P']) &
                                       Q(execution__execution_error=None) &
                                       ~Q(execution__execution_end=None))

print(len(query))

print('No CM and No Exec Error + Exec Ended', sorted(list(set([e.execution.experiment.id for e in query]))))




exit()


import requests, json
import multiprocessing
from tqdm import tqdm

def test_link(doi):
    r = requests.get('https://www.doi.org/{doi}'.format(doi=doi), allow_redirects=True)
    if r.status_code == 200:
        return True, None
    else:
        return False, r.status_code


# if __name__ == '__main__':
#     dois = None
#     with open('dois.out', 'r') as file:
#         dois = json.load(file)
#
#     for doi in tqdm(dois):
#         try:
#             test, info = test_link(doi)
#             if not test:
#                 print(doi, info)
#         except Exception:
#             print(doi)
#             pass
#



dois = None
with open('date_reference_doi.out', 'r') as file:
    dois = json.load(file)

for doi in dois:
    if not dois[doi]:
        print(doi)
