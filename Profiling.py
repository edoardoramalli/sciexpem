import os
import django
import requests, json
from dateutil.parser import parse
from django.db.models import Q

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SciExpeM.settings")
django.setup()

from ExperimentManager.Models import *

import pandas as pd
from tqdm import tqdm

import math


print('------- INITIAL SPECIES --------------------------------')
# for initial in InitialSpecie.objects.all():
#     possible = []
#     possible = Specie.objects.filter(preferredKey=initial.name)
#     if len(possible) == 0:
#         possible = Specie.objects.filter(names__contains=[initial.name])
#
#         if len(possible) == 0:
#             print('ZERO --> ', initial.id, initial.name)
#         elif len(possible) > 1:
#             print('MORE --> ', initial.id)
#         else:
#             initial.specie = possible[0]
#             initial.save()
#     elif len(possible) > 1:
#         print('MORE --> ', initial.id)
#     else:
#         initial.specie = possible[0]
#         initial.save()


print('------- DATA COLUMNS --------------------------------')

r  = []

for dc in DataColumn.objects.all():
    species = dc.species

    # species_object = dc.species_object.all()
    # print([s.InChI for s in species_object])

    # print(species_object)

    if species:
        for specie in species:
            possible = []

            possible = Specie.objects.filter(preferredKey=specie)
            if len(possible) == 0:
                possible = Specie.objects.filter(names__contains=[specie])

                if len(possible) == 0:
                    print('ZERO --> ', dc.id, dc.label)
                elif len(possible) > 1:
                    print('MORE --> ', dc.id, species)
                    r += species
                else:
                    dc.species_object.add(possible[0])
                    dc.save()
            elif len(possible) > 1:
                print('MORE --> ', dc.id, species)
                r += species
            else:
                dc.species_object.add(possible[0])
                dc.save()

print(list(set(r)))

print('------- EXEC COLUMNS --------------------------------')

for dc in ExecutionColumn.objects.all():
    species = dc.species

    if species:
        print('edo')
        for specie in species:
            possible = []

            possible = Specie.objects.filter(preferredKey=specie)
            if len(possible) == 0:
                possible = Specie.objects.filter(names__contains=[specie])

                if len(possible) == 0:
                    print('ZERO --> ', dc.id, dc.label)
                elif len(possible) > 1:
                    print('MORE --> ', dc.id, species)
                else:
                    dc.species_object.add(possible[0])
                    dc.save()
            elif len(possible) > 1:
                print('MORE --> ', dc.id, species)
            else:
                dc.species_object.add(possible[0])
                dc.save()

exit()

result = set([])

species = list(DataColumn.objects.all().values('species').distinct())

for s in species:
    if s['species']:
        for i in s['species']:
            result.add(i)

species = list(ExecutionColumn.objects.all().values('species').distinct())

for s in species:
    if s['species']:
        for i in s['species']:
            result.add(i)

for s in result:
    print(s)

exit()
for e in execs:
    if not CurveMatchingResult.objects.filter(execution_column=e).exists():
        print('Non Esiste {} - EXP {}'.format(e.id, e.execution.experiment.id))

exit()

r = set([])

for exec_col in tqdm(execs):
    a = False
    for i in exec_col.data:
        if math.isnan(i):
            r.add(exec_col.execution.id)
            a = True
            break
    if a:
        exec_col.data = [x for x in exec_col.data if not math.isnan(x)]
        exec_col.save()

print(r)

exit()

exit()

# ----- Fuel -------

fuels = ['H2', 'C2H4', 'n-C10H22', 'H2S', 'CO', 'C6H6', 'C3H6', 'CH4', 'C2H6', 'CH3OCH3', 'C5H6', 'NH3', 'SO2',
         'C10H7CH3']

# 10.24388


for f in fuels:
    query = Q(fileDOI__contains='zenodo', fuels=None)  # & ~Q(experiment_interpreter=None)
    exps = len(Experiment.objects.filter(query).distinct())
    exec = len(Execution.objects.filter(experiment__fileDOI__contains='zenodo', experiment__fuels__contains=[f]).values(
        'experiment__id').distinct())
    # exec = 0
    print('FUEL {}: {}  - EXEC {}'.format(f, exps, exec))

exit()

exit()
# ----- Reference -----


# duplicate Takahashi, F., Mizomoto, M., Ikai,S., Alternative Energy Sources III, 1983, (5), 447-457.
# duplicate Taylor., S.C., Ph.D. thesis, University of Leeds, 1991.


fileDOIS = FilePaper.objects.all().distinct()

results = {}

for file in tqdm(fileDOIS):
    txt = ''
    if file.author:
        txt += file.author + ' - '
    if file.journal:
        txt += file.journal + ', '
    if file.year:
        txt += str(file.year) + ', '
    if file.volume:
        txt += '(' + file.volume + '), '
    if file.page:
        txt += file.page
    if file.reference_doi:
        file.description = txt

        file.save()

exit()

for file in tqdm(fileDOIS):
    try:
        r = requests.get('https://opencitations.net/index/api/v1/metadata/' + file.reference_doi)
        json = r.json()[0]
        year = json.get('year')
        author = json.get('author')
        volume = json.get('volume')
        title = json.get('title')
        page = json.get('page')
        journal = json.get('source_title')

        file.year = year
        file.author = author
        file.volume = volume
        file.title = title
        file.page = page
        file.journal = journal

        file.save()


    except Exception as e:
        print()
        print(e)
        print('ERRORE:', file.reference_doi, 'ID:', file.id)

exit()

# ----- Experiment -----

experiments = Experiment.objects.all()

duplicates = {}

for exp in tqdm(experiments):
    if exp.id in [item for sublist in duplicates.values() for item in sublist]:
        continue
    if exp.experiment_type == 'flame':
        continue
    commons = exp.common_properties.all()
    species = exp.initial_species.all()
    diz_11 = {c.name: c.value for c in commons}
    diz_12 = {c.name: c.value for c in species}

    flat_list = [item for sublist in duplicates.values() for item in sublist]

    possible = Experiment.objects.filter(experiment_type=exp.experiment_type, reactor=exp.reactor).exclude(
        id__in=flat_list + [exp.id])

    for p in possible:
        commons2 = p.common_properties.all()
        species2 = p.initial_species.all()
        diz_21 = {c.name: c.value for c in commons2}
        diz_22 = {c.name: c.value for c in species2}

        if diz_11 == diz_21 and diz_12 == diz_22:
            duplicates[exp.id] = duplicates.get(exp.id, []) + [p.id]
            # print(diz_11, diz_21, diz_12, diz_22)
            #
            # print(exp.id, p.id)

print(duplicates)
exit()

record = []

results = {}


def elsevier(doi):
    r = requests.get('https://api.elsevier.com/content/article/doi/{doi}'.format(doi=doi),
                     headers={'Accept': 'application/json'},
                     data={'view': 'FULL',
                           'xml-decode': 'false'})
    response = r.json()
    if r.status_code == 200:
        date = response['full-text-retrieval-response']['coredata']['prism:coverDate']
        return date
    else:
        return False


species = []

# exec_columns = ExecutionColumn.objects.all()
#
# for exec in exec_columns:
#     if exec.species:
#         species += exec.species

record_common = []

common_properties = CommonProperty.objects.all()

for common in common_properties:
    record_common.append({
        'name': common.name,
        'units': common.units,
        'value': float(common.value),
        'source_type': common.source_type,
    })

record_inital = []

initial_species = CommonProperty.objects.all()

for common in initial_species:
    record_inital.append({
        'name': common.name,
        'units': common.units,
        'value': float(common.value),
        'source_type': common.source_type,
    })

record_data_columns = []

data_columns = DataColumn.objects.all()

for common in data_columns:
    record_data_columns.append({
        'name': common.name,
        'units': common.units,
        'data': [float(x) for x in common.data],
        'source_type': common.source_type,
        'dg_id': common.dg_id,
        'dg_label': common.dg_label,
        'label': common.label,
        'species': common.species,
        'data_group_profile': common.data_group_profile,
    })

df = pd.DataFrame(record_common)
df.to_csv('common_properties.out')

df = pd.DataFrame(record_inital)
df.to_csv('intial_species.out')

df = pd.DataFrame(record_data_columns)
df.to_csv('data_columns.out')

# with open('common_properties.out', 'w+') as file:
#     json.dump(record_common, file)
#
# with open('intial_species.out', 'w+') as file:
#     json.dump(record_inital, file)
#
# with open('data_columns.out', 'w+') as file:
#     json.dump(record_data_columns, file)

for exp in tqdm(experiments):

    data_columns = exp.data_columns.all()
    for column in data_columns:
        if column.species:
            species += column.species

    # results[exp.fileDOI] = len(data_columns.data)
    # record.append({
    #     'fileDOI': exp.fileDOI,
    #     'reactor': exp.reactor,
    #     'experiment_type': exp.experiment_type,
    #     'file_paper': exp.file_paper.reference_doi,
    #     'ignition_type': exp.ignition_type,
    #     'fuels': exp.fuels,
    #     'status': exp.status,
    #     'phi_inf': exp.phi_inf,
    #     'phi_sup': exp.phi_sup,
    #     't_inf': exp.t_inf,
    #     't_sup': exp.t_sup,
    #     'p_inf': exp.p_inf,
    #     'p_sup': exp.p_sup,
    #     'username': exp.username,
    # })

print(list(set(species)))

exit()

with open('doi_points.out', 'w+') as file:
    json.dump(results, file)

# df = pd.DataFrame(record)
# df.to_csv('experiments.data')
# print(df.head())

exit()
print('Number of experiments: {}'.format(len(experiments)))

# DOI
dois = Experiment.objects.all().values('fileDOI').distinct()
print('Number of distinct experiments: {}'.format(len(dois)))

# Reactor
reactors = Experiment.objects.all().values('reactor').distinct()
reactors_null = Experiment.objects.filter(reactor=None)
print('Number of distinct reactors: {} - {}'.format(len(reactors), list(reactors)))
print('Number of null reactors: {}'.format(len(reactors_null)))

# Exp Type
experiment_type = Experiment.objects.all().values('experiment_type').distinct()
experiment_type_null = Experiment.objects.filter(experiment_type=None)
print('Number of distinct experiment_type: {} - {}'.format(len(experiment_type), list(experiment_type)))
print('Number of null experiment_type: {}'.format(len(experiment_type_null)))

# Ignition Type
ignition_type = Experiment.objects.all().values('ignition_type').distinct()
ignition_type_null = Experiment.objects.filter(ignition_type=None)
print('Number of distinct ignition_type: {} - {}'.format(len(ignition_type), list(ignition_type)))
print('Number of null ignition_type: {}'.format(len(ignition_type_null)))

# Ignition delay measurement
idt = Experiment.objects.filter(experiment_type='ignition delay measurement').values('ignition_type')
print('Number of distinct ignition_type: {} '.format(len(idt)))
