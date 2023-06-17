import os
import sys
import argparse
import psutil

import requests


import django
import random
from django.db.models import Q, Count, F, Case, When, IntegerField
from django.utils import timezone
import pandas as pd
import numpy as np
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SciExpeM.settings")
django.setup()

from SciExpeM.settings import BASE_DIR
from ExperimentManager.Models import *

from OpenSmoke.SimulationSummary.createSummary import create_summary
from OpenSmoke.SimulationSummary.processSummary import process_summary

from FrontEnd.utils import *
from django.db.models.fields.related import ManyToManyField

a = Experiment._meta.get_field('fuels_object')

model = eval('Experiment')

print()

if type(getattr(getattr(model, '_meta'), 'get_field')('fuels_object')) == ManyToManyField:
    print('caiooo')
else:
    print('nooo')

print(type(a))


exp = Experiment.objects.filter(id=201)[0]

print(exp.fuels_object.all())

exp.fuels_object.clear()

ee = [1]

exp.fuels_object.add(*ee)


# exp.fuels_object.set(1, clear=True)

exp.save()




exit()




edo = exp.data_pairs_raw
print(edo)

dcs = exp.data_columns.all()[0]

# print(dcs.get_raw_dataColumn)

# print(exp.da)





exit()





# dcs = DataColumn.objects.filter(~Q(uncertainty_reference=None))
# dcs = DataColumn.objects.filter(Q(uncertainty_kind='relative'))
#
#
# uu = set([])
#
# for dc in dcs:
#     u = [float(d) for d in dc.data][0]
#     u = round(u, 2)
#     print(u)
#
# print(len(dcs))
#
# exit()

# 358



cms = CurveMatchingResult.objects.filter(execution_column__execution__chemModel__id=24).values_list('score', flat=True)

cms = [float(x) for x in cms]

import numpy as np
a = np.array(cms)
p = np.percentile(a, 25)



import matplotlib.pyplot as plt
import seaborn as sns

# # matplotlib histogram
# plt.hist(cms, color = 'blue', edgecolor = 'black',
#          bins = int(180/5))

# seaborn histogram
sns.distplot(cms, hist=True, kde=False, bins=int(180/5), color='blue', hist_kws={'edgecolor': 'black'})

plt.axvline(p, linestyle='--', color='red', label='25th Percentile')

# Add labels
plt.xlabel('Curve Matching Score')
plt.ylabel('Count')

plt.legend()

# plt.show()

plt.savefig('Validation.pdf', format='pdf')


plt.show()

print(cms)





exit()

exp_ids = list(Execution.objects.filter(chemModel__id=24, experiment__status='verified').values_list('experiment__id', flat=True))


tsv = []

for e in exp_ids:
    c_exp = Experiment.objects.get(id=e)
    e_id = 'ID:' + str(c_exp.id)
    e_reactor = c_exp.reactor
    e_exp_type = c_exp.experiment_type
    e_y = c_exp.file_paper.year if c_exp.file_paper else 'NoYear'

    dcs = c_exp.data_columns.filter(~Q(uncertainty_reference=None))

    if len(dcs) > 0:
        u = round(float([dc.uncertainty_reference.data[0] for dc in dcs][0]), 2)
    else:
        u = random.choice([0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1])

    tsv.append('{}\t{}\tU_{}'.format(e_id, 'has_uncertainty', u))
    tsv.append('{}\t{}\tY_{}'.format(e_id, 'of_year', e_y))
    tsv.append('{}\t{}\tTY_{}'.format(e_id, 'of_type', e_exp_type))
    tsv.append('{}\t{}\tR_{}'.format(e_id, 'of_reactor', e_reactor))
    # tsv.append('{}\t{}\tAuthor{}'.format(e_id, 'has_author', u))

    cms = CurveMatchingResult.objects.filter(execution_column__execution__experiment_id=e)

    for cm in cms:
        t = cm.execution_column.label.replace('_x', '')
        tsv.append('{}\t{}\tT_{}'.format(e_id, 'of_target', t))
        tsv.append('{}\t{}\tS_{}'.format(e_id, 'has_similarity', round(float(cm.score), 1)))


with open('SciExpeM_1.tsv', 'w+') as f:
    for i in tsv:
        f.write(i + '\n')


exit()










cms = CurveMatchingResult.objects.filter(execution_column__execution__id=1850)

chemModel1 = ChemModel.objects.get(id=24)
chemModel2 = ChemModel.objects.get(id=31)

common_exp = common_execution_experiment_id(chemModel1.id, chemModel2.id)

tot = 0

fuels = {}

targets = {}

years ={}

for e_id in common_exp:
    e = Experiment.objects.get(id=e_id)
    f = tuple(sorted(e.fuels))
    fuels[f] = fuels.get(f, 0) + 1
    if e.file_paper:
        y = e.file_paper.year
    else:
        y = -1
    years[y] = years.get(y, 0) + 1
    for p in e.pairs:
        c = p['y']
        if c.name == 'evaluated standard deviation':
            print(e.id, p['y'], p['x'])
        t = c.name if c.name != 'composition' else c.species_object.all()[0].preferredKey
        targets[t] = targets.get(t, 0) + 1


print(fuels)
print(targets)
print(years)

exit()



obj_exec = Execution.objects.filter(id__in=common_exp)

exps = [e.experiment for e in obj_exec]

fuels = list(set([tuple(e.fuels) for e in exps]))

reactors = list(set([e.reactor for e in exps]))

exp_types = list(set([e.experiment_type for e in exps]))

targets = set()

for e in obj_exec:
    ec = e.execution_columns.all()
    for c in ec:
        if c.is_y:
            targets.add(c.label)

targets = list(targets)

print(fuels)
print(reactors)
print(exp_types)
print(targets)

from statistics import mean, median, stdev, variance

def edo(ll, digits=3):
    ll = list(ll)
    edo = ''
    if len(ll) > 0:
        # edo += '({}) [{}, {}] - '.format(len(ll), round(min(ll), digits), round(max(ll), digits))
        # edo += 'M:{} Me:{} '.format(round(mean(ll), digits), round(median(ll), digits))
        # edo += '{} | {} '.format(round(mean(ll), digits), round(median(ll), digits))

        edo += '{}#{}#{}#{}#'.format(round(min(ll), digits), round(max(ll), digits), round(mean(ll), digits), round(median(ll), digits))
    if len(ll) > 1:
        # edo += 'StDev:{} V:{}'.format(round(stdev(ll), digits), round(variance(ll), digits))
        edo += '{}#{}#'.format(round(stdev(ll), digits), round(variance(ll), digits))

    return edo


def analyze_model(model):
    print('Analyzing model {}'.format(model.name))
    for type in exp_types:
        c = CurveMatchingResult.objects.filter(
            execution_column__execution__experiment__experiment_type=type,
            execution_column__execution__chemModel=model,
            execution_column__execution__experiment__id__in=common_exp,
        ).values_list('score', flat=True)

        print(type, edo(c))

        for r in reactors:
            c_r = CurveMatchingResult.objects.filter(
                execution_column__execution__experiment__experiment_type=type,
                execution_column__execution__experiment__reactor=r,
                execution_column__execution__chemModel=model,
                execution_column__execution__experiment__id__in=common_exp,
            ).values_list('score', flat=True)

            print('\t', r, edo(c_r)) if len(c_r) > 0 else None

            for f in fuels:
                c_f = CurveMatchingResult.objects.filter(
                    execution_column__execution__experiment__experiment_type=type,
                    execution_column__execution__experiment__reactor=r,
                    execution_column__execution__chemModel=model,
                    execution_column__execution__experiment__fuels=f,
                    execution_column__execution__experiment__id__in=common_exp,
                ).values_list('score', flat=True)

                print('\t\t', f, edo(c_f)) if len(c_f) > 0 else None

                for t in targets:
                    c_t = CurveMatchingResult.objects.filter(
                        execution_column__execution__experiment__experiment_type=type,
                        execution_column__execution__experiment__reactor=r,
                        execution_column__execution__chemModel=model,
                        execution_column__execution__experiment__fuels=f,
                        execution_column__label=t,
                        execution_column__execution__experiment__id__in=common_exp,
                    ).values_list('score', flat=True)

                    print('\t\t\t', t, edo(c_t)) if len(c_t) > 0 else None


def diff_model(model1, model2):
    print('Comparing model {} and {}'.format(model1.name, model2.name))
    for type in sorted(exp_types):
        c = CurveMatchingResult.objects.filter(
            execution_column__execution__experiment__experiment_type=type,
            execution_column__execution__chemModel=model1,
            execution_column__execution__experiment__id__in=common_exp,
        )

        cc_p = []
        cc_n = []

        for cm in c:
            v = cm.score - cm.get_equivalent(model2).score
            if v > 0:
                cc_p.append(v)
            else:
                cc_n.append(v)

        print(type, edo(cc_n))

        for r in sorted(reactors):
            c_r = CurveMatchingResult.objects.filter(
                execution_column__execution__experiment__experiment_type=type,
                execution_column__execution__experiment__reactor=r,
                execution_column__execution__chemModel=model1,
                execution_column__execution__experiment__id__in=common_exp,
            )

            cc_r_p = []
            cc_r_n = []

            for cm in c_r:
                v = cm.score - cm.get_equivalent(model2).score
                if v > 0:
                    cc_r_p.append(v)
                else:
                    cc_r_n.append(v)

            print('\t', r, edo(cc_r_n)) if len(cc_r_p) > 0 or len(cc_r_n) > 0 else None

            for f in sorted(fuels):
                c_f = CurveMatchingResult.objects.filter(
                    execution_column__execution__experiment__experiment_type=type,
                    execution_column__execution__experiment__reactor=r,
                    execution_column__execution__chemModel=model1,
                    execution_column__execution__experiment__fuels=f,
                    execution_column__execution__experiment__id__in=common_exp,
                )

                cc_f_p = []
                cc_f_n = []

                for cm in c_f:
                    v = cm.score - cm.get_equivalent(model2).score
                    if v > 0:
                        cc_f_p.append(v)
                    else:
                        cc_f_n.append(v)

                print('\t\t', f, edo(cc_f_n)) if len(cc_f_p) > 0 or len(cc_f_n) > 0 else None

                for t in sorted(targets):
                    c_t = CurveMatchingResult.objects.filter(
                        execution_column__execution__experiment__experiment_type=type,
                        execution_column__execution__experiment__reactor=r,
                        execution_column__execution__chemModel=model1,
                        execution_column__execution__experiment__fuels=f,
                        execution_column__label=t,
                        execution_column__execution__experiment__id__in=common_exp,
                    )

                    cc_t_p = []
                    cc_t_n = []

                    for cm in c_t:
                        v = cm.score - cm.get_equivalent(model2).score
                        if v > 0:
                            cc_t_p.append(v)
                        else:
                            cc_t_n.append(v)

                    print('\t\t\t', t, edo(cc_t_n)) if len(cc_t_p) > 0 or len(cc_t_n) > 0 else None


diff_model(chemModel1, chemModel2)

# analyze_model(chemModel1)
#
# analyze_model(chemModel2)

exit()
# 4212 3708

exp = Experiment.objects.filter(id=2384)[0]

dcs = exp.data_columns.all()

exec = Execution.objects.get(id=4212)

exec_dcs = exec.execution_columns.all()

exec2 = Execution.objects.get(id=3708)

exec2_dcs = exec2.execution_columns.all()

x_exp = [float(i) for i in dcs[1].data]
y_exp = [float(i) for i in dcs[0].data]

x_sim_1 = [float(i) for i in exec_dcs[1].data]
y_sim_1 = [float(i) for i in exec_dcs[0].data]

x_sim_2 = [float(i) for i in exec2_dcs[1].data]
y_sim_2 = [float(i) for i in exec2_dcs[0].data]

import matplotlib.pyplot as plt


def conver_x(x_l):
    return [1000 / i for i in x_l]


def conver_y(y_l):
    import math
    return [math.log10(i) for i in y_l]


# plt.plot(conver_x(x_exp), conver_y(y_exp), 'o', label='Experiment')
# plt.plot(conver_x(x_sim_1), conver_y(y_sim_1), '--', label='Simulation 1')
# plt.plot(conver_x(x_sim_2), conver_y(y_sim_2), '.-', label='Simulation 2')

plt.plot(conver_x(x_exp), y_exp, 'o', label='Experiment')
plt.plot(conver_x(x_sim_1), y_sim_1, '--', label='Simulation 1')
plt.plot(conver_x(x_sim_2), y_sim_2, '.-', label='Simulation 2')
plt.yscale('log', base=10)

# plt.show()


from CurveMatching.CurveMatching import curveMatchingExecution

print(conver_x(x_exp))
print(conver_y(y_exp))
print(conver_x(x_sim_1))
print(conver_y(y_sim_1))

curveMatchingExecution(exec)

exit()

a = {'execution_column__label': 'H2O_x', 'execution_column__execution__experiment__fuels__contains': ['H2'],
     'execution_column__execution__chemModel__id': 31}
a_id = 31
b = {'execution_column__label': 'H2O_x', 'execution_column__execution__experiment__fuels__contains': ['H2'],
     'execution_column__execution__chemModel__id': 24}
b_id = 24

from statistics import stdev, variance, mean, median, StatisticsError


def generate_df(diz):
    ticks = list(diz.keys())
    result = {'Interval': [], 'Avg': [], 'StDev': [], 'Count': []}

    for index in range(0, len(ticks)):

        if len(diz[ticks[index]]) > 0:
            media = mean(diz[ticks[index]])
        else:
            media = 1

        if len(diz[ticks[index]]) > 1:
            dev = stdev(diz[ticks[index]])
        else:
            dev = 0

        result['Interval'].append(ticks[index])
        result['Avg'].append(media)
        result['StDev'].append(dev)
        result['Count'].append(len(diz[ticks[index]]))

    # print(result)

    df = pd.DataFrame.from_dict(result)
    return df


def merge_dict(diz1, diz2):
    # merfe dict 2 into dict 1
    for x in diz2:
        if x not in diz1:
            diz1[x] = diz2[x]
        else:
            for y in diz2[x]:
                if y not in diz1[x]:
                    diz1[x][y] = diz2[x][y]
                else:
                    diz1[x][y] = {**diz1[x][y], **diz2[x][y]}
    return diz1


def interval(query, chem_id):
    default = {'execution_column__execution__experiment__status': 'verified'}

    new = {**default, **query}

    exps = CurveMatchingResult.objects.filter(**new).values_list(
        'execution_column__execution__experiment__id', flat=True).distinct()

    chemModel = ChemModel.objects.get(id=chem_id)

    domains = {chemModel.name: {}}

    details = {}

    r = {}

    # return Response(json.dumps(a), status=HTTP_200_OK)

    for exp_id in exps:
        # Given an Exp return all the pairs for each simulated model
        # if exp_id !=1058:
        #     continue

        current_summary = create_summary(exp_id=exp_id, chemModel=chemModel.name)

        # Dato un exp, restituisce tutte le coppie x, y, di tutti i modelli simulati (o di quello selezionato)
        current_result = process_summary(exp_id=exp_id, current_summary=current_summary, domain_list=domains)

        r = merge_dict(r, current_result)

        continue

        print(current_result)

        exit()

        for x_name in current_result:
            if x_name not in details:
                details[x_name] = {}

            for subject in current_result[x_name]:
                if subject not in details[x_name]:
                    details[x_name][subject] = {}

                # print(exp_id, x_name, subject)

                df = current_result[x_name][subject].where(pd.notnull(current_result[x_name][subject]), -1)

                if subject == 'C2H4_x':
                    print('ele', exp_id, len(df))
                    # print(df)

                # df["Area Exp Inter"] = df.Value.astype(float)
                # df["Area Sim Inter"] = df.Value.astype(float)
                # df["Weight Exp Inter"] = df.Value.astype(float)
                # df["Weight Sim Inter"] = df.Value.astype(float)
                # df["Real"] = df.Real.astype(float)
                # df["Value"] = df.Value.astype(float)

                df = df.astype({'Area Exp Inter': float,
                                'Area Sim Inter': float,
                                'Weight Exp Inter': float,
                                'Weight Sim Inter': float,
                                'Real': float,
                                'Value': float,
                                })

                # print(df.dtypes)

                df = df.round({'Area Exp Inter': 3,
                               'Area Sim Inter': 3,
                               'Weight Exp Inter': 3,
                               'Weight Sim Inter': 3,
                               'Real': 3,
                               'Value': 3,
                               })

                details[x_name][subject][exp_id] = df.to_dict('records')

    print(r)

    exit()

    result = {}
    # TODO ASSUNZIONE UN SOLO MODELLO ALLA VOLTA
    current_model = chemModel.name

    for x_name in domains[current_model]:
        if x_name not in result:
            result[x_name] = {}

        for subject in domains[current_model][x_name]:
            # print('edooo', subject)
            if subject not in details[x_name]:
                continue
            if subject not in result[x_name]:
                result[x_name][subject] = {}

            lunghezza = len(domains[current_model][x_name][subject].x_p)

            freq_sovrastima = np.zeros(lunghezza)
            freq_sottostima = np.zeros(lunghezza)

            ticks_sottostima = np.zeros(lunghezza)
            ticks_sovrastima = np.zeros(lunghezza)

            # for index, model_name in enumerate(domains):
            #     # print(domains[domain][subject].x)

            df_sovrastima = generate_df(diz=domains[current_model][x_name][subject].x_p)

            # print('pippo', sum([len(domains[current_model][x_name][subject].x_n[i]) for i in domains[current_model][x_name][subject].x_n]) +  sum([len(domains[current_model][x_name][subject].x_p[i]) for i in domains[current_model][x_name][subject].x_p]))

            df_sottostima = generate_df(diz=domains[current_model][x_name][subject].x_n)

            # print(chem_id, subject, len(df_sovrastima) + len(df_sottostima))

            if subject == 'C2H4_x':
                print('FINAL', chem_id, list(domains[current_model][x_name][subject].x_p.values()))
                print('FINAL', chem_id, list(domains[current_model][x_name][subject].x_n.values()))

            ticks_sovrastima = df_sovrastima['Interval']
            ticks_sottostima = df_sottostima['Interval']

            freq_sottostima = np.maximum(freq_sottostima, df_sottostima['Count'])
            freq_sovrastima = np.maximum(freq_sottostima, df_sovrastima['Count'])

            result[x_name][subject]['sovrastima'] = {'x': list(df_sovrastima['Interval']),
                                                     'y': list(df_sovrastima['Avg']),
                                                     'error_y': list(df_sovrastima['StDev']),
                                                     'count': list(freq_sovrastima)}

            result[x_name][subject]['sottostima'] = {'x': list(df_sottostima['Interval']),
                                                     'y': list(df_sottostima['Avg']),
                                                     'error_y': list(df_sottostima['StDev']),
                                                     'count': list(freq_sottostima)}

            if subject == 'C2H4_x':
                print('FINAL', chem_id, sum(freq_sottostima) + sum(freq_sovrastima))

            # print(x_name, subject, chem_id, len(list(freq_sottostima)) + len(list(freq_sovrastima)))

            result[x_name][subject]['details'] = details[x_name][subject]


interval(a, a_id)
interval(b, b_id)

exit()

exit()
import subprocess


#
# bashCommand = 'cd edoooo'
# process = subprocess.Popen(bashCommand, shell=True, stdout=subprocess.PIPE)
# output, error = process.communicate()
# output = output.decode('ascii')
# error = error.decode('ascii') if error else ''

def sizeof_fmt(num, suffix="B"):
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(num) < 1024.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}Yi{suffix}"


files = Execution.objects.all()

diz = {}

for e in files:
    if e.folder_size:
        if e.folder_size > 100000000:
            print(e.experiment.id)
        diz[e.chemModel.id] = diz.get(e.chemModel.id, []) + [e.folder_size]

import statistics

for model in diz:
    print(model, sizeof_fmt(statistics.mean(diz[model])), sizeof_fmt(max(diz[model])))

# print(diz)


exit()


def edo(n, k):
    return ((n * k * 8) + (n * k * (16 * 8)) + (n * (16 * 8)) + (n * 10 * 8) + (263 * 8)) / (1000 * 8)


e = '<?xml version="1.0" encoding="utf-8"?><opensmoke version="0.1a"><Type> HomogeneousReactor </Type><additional>6time [s] 2temperature [K] 3pressure [Pa] 4mol-weight [kg/kmol] 5density [kg/m3] 6heat-release [W/m3] 7</additional><t-p-mw>1 2 3</t-p-mw><mass-fractions>'

print(len(e))
print(edo(365, 609), ' kB')

exit()

# ese = ExecutionFile.objects.filter(case=None).values_list('id', flat=True)
#
# for f in ese:
#     if not f.path.startswith('Execution'):
#         f.path = 'Execution/' + f.path
#         f.save()


# print(ese.num_files)


exit()

exit()

print(BASE_DIR)

models = ChemModel.objects.all()

for model in models:
    print(model.xml_file_reaction_names_file)
    exit()
    # path = os.path.join(BASE_DIR, 'ChemModels', str(model.id))
    # os.makedirs(path, exist_ok=True)
    # path_kinetics = os.path.join(path, 'kinetics.xml')
    # path_reactions = os.path.join(path, 'reaction_names.xml')
    # with open(path_kinetics, 'w+') as file:
    #     file.write(model.xml_file_kinetics)
    # with open(path_reactions, 'w+') as file:
    #     file.write(model.xml_file_reaction_names)
    # model.xml_file_kinetics = path_kinetics
    # model.xml_file_reaction_names = path_reactions
    # model.save()

exit()

# SciExpeM Import
from ReSpecTh.Tool import Consistency, resultExecutionVisualization, pairExecutionExperiment, visualizeExecution
from ExperimentManager.Models import *

chemModel = ChemModel.objects.get(id=5)

domains = {chemModel.name: {}}

details = {}


# return Response(json.dumps(a), status=HTTP_200_OK)


def generate_df(diz):
    ticks = list(diz.keys())
    result = {'Interval': [], 'Avg': [], 'StDev': [], 'Count': []}

    # print(diz)

    for index in range(0, len(ticks)):

        if len(diz[ticks[index]]) > 0:
            media = mean(diz[ticks[index]])
        else:
            media = 1

        if len(diz[ticks[index]]) > 1:
            dev = stdev(diz[ticks[index]])
        else:
            dev = 0

        result['Interval'].append(ticks[index])
        result['Avg'].append(media)
        result['StDev'].append(dev)
        result['Count'].append(len(diz[ticks[index]]))

    df = pd.DataFrame.from_dict(result)
    return df


exps = [205]

for exp_id in exps:
    # Given an Exp return all the pairs for each simulated model
    # if exp_id !=1058:
    #     continue
    current_summary = create_summary(exp_id)

    current_result = process_summary(exp_id=exp_id, current_summary=current_summary, domain_list=domains)

    for x_name in current_result:
        if x_name not in details:
            details[x_name] = {}

        for subject in current_result[x_name]:
            if subject not in details[x_name]:
                details[x_name][subject] = {}

            # print(exp_id, x_name, subject)

            df = current_result[x_name][subject].where(pd.notnull(current_result[x_name][subject]), -1)

            # df["Area Exp Inter"] = df.Value.astype(float)
            # df["Area Sim Inter"] = df.Value.astype(float)
            # df["Weight Exp Inter"] = df.Value.astype(float)
            # df["Weight Sim Inter"] = df.Value.astype(float)
            # df["Real"] = df.Real.astype(float)
            # df["Value"] = df.Value.astype(float)

            df = df.astype({'Area Exp Inter': float,
                            'Area Sim Inter': float,
                            'Weight Exp Inter': float,
                            'Weight Sim Inter': float,
                            'Real': float,
                            'Value': float,
                            })

            # print(df.dtypes)

            df = df.round({'Area Exp Inter': 3,
                           'Area Sim Inter': 3,
                           'Weight Exp Inter': 3,
                           'Weight Sim Inter': 3,
                           'Real': 3,
                           'Value': 3,
                           })

            details[x_name][subject][exp_id] = df.to_dict('records')

result = {}
# TODO ASSUNZIONE UN SOLO MODELLO ALLA VOLTA
current_model = chemModel.name

for x_name in domains[current_model]:
    if x_name not in result:
        result[x_name] = {}

    for subject in domains[current_model][x_name]:
        if subject not in details[x_name]:
            continue
        if subject not in result[x_name]:
            result[x_name][subject] = {}

        lunghezza = len(domains[current_model][x_name][subject].x_p)

        freq_sovrastima = np.zeros(lunghezza)
        freq_sottostima = np.zeros(lunghezza)

        ticks_sottostima = np.zeros(lunghezza)
        ticks_sovrastima = np.zeros(lunghezza)

        # for index, model_name in enumerate(domains):
        #     # print(domains[domain][subject].x)

        df_sovrastima = generate_df(diz=domains[current_model][x_name][subject].x_p)
        df_sottostima = generate_df(diz=domains[current_model][x_name][subject].x_n)

        ticks_sovrastima = df_sovrastima['Interval']
        ticks_sottostima = df_sottostima['Interval']

        freq_sottostima = np.maximum(freq_sottostima, df_sottostima['Count'])
        freq_sovrastima = np.maximum(freq_sottostima, df_sovrastima['Count'])

        result[x_name][subject]['sovrastima'] = {'x': list(df_sovrastima['Interval']),
                                                 'y': list(df_sovrastima['Avg']),
                                                 'error_y': list(df_sovrastima['StDev']),
                                                 'count': list(freq_sovrastima)}

        result[x_name][subject]['sottostima'] = {'x': list(df_sottostima['Interval']),
                                                 'y': list(df_sottostima['Avg']),
                                                 'error_y': list(df_sottostima['StDev']),
                                                 'count': list(freq_sottostima)}
        result[x_name][subject]['details'] = details[x_name][subject]

# print(len(exp_dubbi))


exit()

from ExperimentManager.Serializers import *

from django.core import serializers

from OpenSmoke.Tools import create_list_string_profiles
from OpenSmoke.OpenSmoke import OpenSmokeParser

import pandas as pd

# a = CurveMatchingResult.objects.filter(score=-1, execution_column__execution__chemModel__id=24).values_list('execution_column__execution__id', flat=True).distinct()
#
# print(list(a))
#
#
# exit()


e_18 = set(Execution.objects.filter(chemModel__id=12).values_list('experiment__id', flat=True))
e_21 = set(Execution.objects.filter(chemModel__id=24).values_list('experiment__id', flat=True))

print(e_18 - e_21)
print(e_21 - e_18)

exit()
# e = Execution.objects.get(id=1435)

# a = Execution.objects.filter(id=1435).annotate(
#             n_cols=Count('execution_columns', distinct=True),
#             n_cm=Count('execution_columns__curve_matching_result', distinct=True),
#             n_groups=Count(Case(
#                 When(experiment__data_columns__dg_label='experimental_data', then='experiment__data_columns__dg_id')), distinct=True))[0]

# a = Execution.objects.filter(id=2103).annotate(
#             n_cols=Count('execution_columns', distinct=True),
#             n_cm=Count('execution_columns__curve_matching_result', distinct=True))[0]
#
#
# print(a.n_cm, a.n_cols)
# print(len(a.execution_columns.all()))
# for c in a.execution_columns.all():
#     print(c.id, c.label,)

# print()
# print(e.experiment.id)
#
# for c in Experiment.objects.get(id=e.experiment.id).data_columns.all():
#     print(c.id, c.label, c.dg_id)
#

exit()
#
#
#
#
# d = {'t': 's', 'csi': 'm', 'T0': 'K', 'P0': 'Pa', 'T': 'K', 'P': 'Pa', 'v': 'm/s', 'rho': 'kg/m3', 'MW': 'kg/kmol',
#      'C7H8_x': 'mole fraction', 'C7H7_x': 'mole fraction', 'C7H6_x': 'mole fraction', 'C7H5_x': 'mole fraction',
#      'C5H5_x': 'mole fraction', 'C5H6_x': 'mole fraction', 'C6H6_x': 'mole fraction', 'CYC6H4_x': 'mole fraction',
#      'C6H2_x': 'mole fraction', 'C5H3_x': 'mole fraction', 'C4H6_x': 'mole fraction', 'C4H4_x': 'mole fraction',
#      'C4H2_x': 'mole fraction', 'C3H4-A_x': 'mole fraction', 'C3H4-P_x': 'mole fraction', 'C3H3_x': 'mole fraction',
#      'C2H4_x': 'mole fraction', 'C2H2_x': 'mole fraction', 'CH4_x': 'mole fraction', 'CH3_x': 'mole fraction',
#      'H2_x': 'mole fraction', 'AR_x': 'mole fraction', 'C6H5C2H_x': 'mole fraction', 'C6H5C2H3_x': 'mole fraction',
#      'C6H5C2H5_x': 'mole fraction', 'INDENYL_x': 'mole fraction', 'INDENE_x': 'mole fraction',
#      'C10H8_x': 'mole fraction', 'C12H8_x': 'mole fraction', 'BIPHENYL_x': 'mole fraction',
#      'FLUORENE_x': 'mole fraction', 'C6H5CH2C6H5_x': 'mole fraction', 'C14H10_x': 'mole fraction',
#      'C6H5C2H4C6H5_x': 'mole fraction', 'C16H10_x': 'mole fraction', 'FULVENE_x': 'mole fraction',
#      'C7H8_w': 'mass fraction', 'C7H7_w': 'mass fraction', 'C7H6_w': 'mass fraction', 'C7H5_w': 'mass fraction',
#      'C5H5_w': 'mass fraction', 'C5H6_w': 'mass fraction', 'C6H6_w': 'mass fraction', 'CYC6H4_w': 'mass fraction',
#      'C6H2_w': 'mass fraction', 'C5H3_w': 'mass fraction', 'C4H6_w': 'mass fraction', 'C4H4_w': 'mass fraction',
#      'C4H2_w': 'mass fraction', 'C3H4-A_w': 'mass fraction', 'C3H4-P_w': 'mass fraction', 'C3H3_w': 'mass fraction',
#      'C2H4_w': 'mass fraction', 'C2H2_w': 'mass fraction', 'CH4_w': 'mass fraction', 'CH3_w': 'mass fraction',
#      'H2_w': 'mass fraction', 'AR_w': 'mass fraction', 'C6H5C2H_w': 'mass fraction', 'C6H5C2H3_w': 'mass fraction',
#      'C6H5C2H5_w': 'mass fraction', 'INDENYL_w': 'mass fraction', 'INDENE_w': 'mass fraction',
#      'C10H8_w': 'mass fraction', 'C12H8_w': 'mass fraction', 'BIPHENYL_w': 'mass fraction',
#      'FLUORENE_w': 'mass fraction', 'C6H5CH2C6H5_w': 'mass fraction', 'C14H10_w': 'mass fraction',
#      'C6H5C2H4C6H5_w': 'mass fraction', 'C16H10_w': 'mass fraction', 'FULVENE_w': 'mass fraction',
#      'C7H8_x0': 'mole fraction', 'C7H7_x0': 'mole fraction', 'C7H6_x0': 'mole fraction', 'C7H5_x0': 'mole fraction',
#      'C5H5_x0': 'mole fraction', 'C5H6_x0': 'mole fraction', 'C6H6_x0': 'mole fraction', 'CYC6H4_x0': 'mole fraction',
#      'C6H2_x0': 'mole fraction', 'C5H3_x0': 'mole fraction', 'C4H6_x0': 'mole fraction', 'C4H4_x0': 'mole fraction',
#      'C4H2_x0': 'mole fraction', 'C3H4-A_x0': 'mole fraction', 'C3H4-P_x0': 'mole fraction', 'C3H3_x0': 'mole fraction',
#      'C2H4_x0': 'mole fraction', 'C2H2_x0': 'mole fraction', 'CH4_x0': 'mole fraction', 'CH3_x0': 'mole fraction',
#      'H2_x0': 'mole fraction', 'AR_x0': 'mole fraction', 'C6H5C2H_x0': 'mole fraction', 'C6H5C2H3_x0': 'mole fraction',
#      'C6H5C2H5_x0': 'mole fraction', 'INDENYL_x0': 'mole fraction', 'INDENE_x0': 'mole fraction',
#      'C10H8_x0': 'mole fraction', 'C12H8_x0': 'mole fraction', 'BIPHENYL_x0': 'mole fraction',
#      'FLUORENE_x0': 'mole fraction', 'C6H5CH2C6H5_x0': 'mole fraction', 'C14H10_x0': 'mole fraction',
#      'C6H5C2H4C6H5_x0': 'mole fraction', 'C16H10_x0': 'mole fraction', 'FULVENE_x0': 'mole fraction',
#      'C7H8_w0': 'mass fraction', 'C7H7_w0': 'mass fraction', 'C7H6_w0': 'mass fraction', 'C7H5_w0': 'mass fraction',
#      'C5H5_w0': 'mass fraction', 'C5H6_w0': 'mass fraction', 'C6H6_w0': 'mass fraction', 'CYC6H4_w0': 'mass fraction',
#      'C6H2_w0': 'mass fraction', 'C5H3_w0': 'mass fraction', 'C4H6_w0': 'mass fraction', 'C4H4_w0': 'mass fraction',
#      'C4H2_w0': 'mass fraction', 'C3H4-A_w0': 'mass fraction', 'C3H4-P_w0': 'mass fraction', 'C3H3_w0': 'mass fraction',
#      'C2H4_w0': 'mass fraction', 'C2H2_w0': 'mass fraction', 'CH4_w0': 'mass fraction', 'CH3_w0': 'mass fraction',
#      'H2_w0': 'mass fraction', 'AR_w0': 'mass fraction', 'C6H5C2H_w0': 'mass fraction', 'C6H5C2H3_w0': 'mass fraction',
#      'C6H5C2H5_w0': 'mass fraction', 'INDENYL_w0': 'mass fraction', 'INDENE_w0': 'mass fraction',
#      'C10H8_w0': 'mass fraction', 'C12H8_w0': 'mass fraction', 'BIPHENYL_w0': 'mass fraction',
#      'FLUORENE_w0': 'mass fraction', 'C6H5CH2C6H5_w0': 'mass fraction', 'C14H10_w0': 'mass fraction',
#      'C6H5C2H4C6H5_w0': 'mass fraction', 'C16H10_w0': 'mass fraction', 'FULVENE_w0': 'mass fraction'}
#
# print(d.keys())
#
# with open('/Users/edoardo/Desktop/ParametricAnalysis.out', 'r') as f:
# # df = pd.read_csv(f, delim_whitespace=True)
# #
# #
# # for i, c in enumerate(list(df.columns)):
# #     print(c, list(d.keys())[i])
# #
# #
# # print(df.columns)
#
#     OpenSmokeParser.parse_output_string(f.read())
#
# exit()
#
# print(create_list_string_profiles(1741))
#
# exit()
#
# obj = Experiment.objects.get(id=752)
#
# a = ExperimentSerializer(obj).data
#
# for key in a:
#     print(key)
# if key == 'file_paper':
#     fp = FilePaperSerializer(FilePaper.objects.get(id=a[key]['id']), fields=tuple(
#         ['id', 'description', 'reference_doi', 'author', 'title', 'volume', 'journal', 'year', 'page']))
# a[key] = fp.data
# # print(fp.data)
# elif key == 'common_properties':
# tmp = []
# for cp in a[key]:
#     ser = CommonPropertySerializer(CommonProperty.objects.get(id=cp['id']),
#                                    fields=tuple(['id', 'name', 'units', 'value', 'source_type']))
# tmp.append(ser.data)
# a[key] = tmp
# elif key == 'initial_species':
# tmp = []
# for cp in a[key]:
#     ser = InitialSpecieSerializer(InitialSpecie.objects.get(id=cp['id']),
#                                   fields=tuple(['id', 'specie', 'units', 'value', 'source_type']))
# j_ser = ser.data
# if j_ser['specie']:
#     j_ser['specie'] = SpecieSerializer(Specie.objects.get(id=j_ser['specie']['id']), fields=tuple(
#         ['id', 'InChI', 'preferredKey', 'names', 'CAS', 'SMILES', 'chemName', 'formula'])).data
# tmp.append(j_ser)
# a[key] = tmp
# elif key == 'data_columns':
# tmp = []
# for cp in a[key]:
#     ser = DataColumnSerializer(DataColumn.objects.get(id=cp['id']), fields=tuple(
#         ['id', 'name', 'units', 'data', 'dg_id', 'label', 'species', 'uncertainty_reference', 'species_object']))
# j_ser = ser.data
# kk = []
# for sp in j_ser['species_object']:
#     edo = SpecieSerializer(Specie.objects.get(id=sp['id']), fields=tuple(
#         ['id', 'InChI', 'preferredKey', 'names', 'CAS', 'SMILES', 'chemName', 'formula'])).data
# kk.append(edo)
#
# j_ser['species_object'] = kk
#
# tmp.append(j_ser)
# a[key] = tmp
#
# import json
#
# with open('/users/edoardo/Desktop/Example_3_(752).json', 'w') as f:
#     f.write(json.dumps(a, indent=4))
# # print()
#
# # assuming obj is a model instance
#
# exit()
#
# # a = Experiment.objects.get(id=202)
# # b = Experiment.objects.get(id=203)
# # model = ChemModel.objects.get(id=5)
# #
# # a_exec = Execution(experiment=a, chemModel=model, username='edoardo')
# # a_exec.save()
# #
# # import time
#
# #         time.sleep(30)
# #
# #         b_exec = Execution(experiment=b, chemModel=model, username='edoardo')
# #         b_exec.save()
# #
# #         #
# #         # es = Execution.objects.all()
# #         #
# #         #
# #         # for e in es:
# #         #     e.execution_created = e.execution_start
# #         #     e.save()
# #
# #         exit()
# #
# #         chemModel_id = 14
# #         target = 'H2_x'
# #
# #         chem_ids = [chemModel_id, 12]
# #         r = []
# #
# #         new = {
# # # **self.query,
# # 'execution__experiment__status': 'verified',
# # 'label': target,
# # 'execution__chemModel__id__in': chem_ids}
# #
# # print(new)
# #
# # exec_cols = ExecutionColumn.objects.filter(**new).distinct()
# #
# # exec_ids = set([ec.execution.id for ec in exec_cols])
# #
# # print(exec_ids)
# #
# # from collections import defaultdict
# #
# # exps = defaultdict(list)
# #
# # for exec_id in exec_ids:
# #     execution = Execution.objects.get(id=exec_id)
# # exps[execution.experiment.id].append(execution)
# #
# # print(exps)
# #
# # for exp in exps:
# #     for
# # execution in exps[exp]:
# # consistency = visualizeExecution(execution, target=target)
# # r.append(resultExecutionVisualization(consistency))
# #
# # print(r)
# #
# # exit()
# #
# # import os
# # import django
# # from django.db.models import Q, Count, F
# #
# # os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SciExpeM.settings")
# # django.setup()
# #
# # # SciExpeM Import
# # from ExperimentManager.Models import *
# #
# # from tqdm import tqdm
# #
# # from OpenSmoke.Tools import create_profile_string
# #
# # exp_id = 691
# #
# # exp = Experiment.objects.get(id=exp_id)
# #
# # exit()
# #
# #
# # def checkUnique(experiment):
# #     # Remember to exclude 'experiment'
# #     # print(len(experiment.initial_species.all()))
# #     possible_equal = Experiment.objects.filter(
# #         experiment_type=experiment.experiment_type,
# #         reactor=experiment.reactor).annotate(num_species=Count('initial_species'),
# #                                              num_common=Count('common_properties')).filter(
# #         num_species=len(experiment.initial_species.all()), num_common=len(experiment.common_properties.all())).exclude(
# #         id=experiment.id)
# #
# #     r = []
# #
# #     if possible_equal.exists():
# #         for possible in possible_equal:
# #             # r.append(possible.id)
# #             initial_equal = experiment.compare_equality(other=possible, prop='InitialSpecie')
# #             common_equal = experiment.compare_equality(other=possible, prop='CommonProperty')
# #             if initial_equal and common_equal:
# #                 r.append(possible.id)
# #
# #     return r
# #
# #
# # query = Experiment.objects.all()
# #
# # exps_ids = list(Experiment.objects.all().values_list('id', flat=True))
# #
# # for exp in tqdm(exps_ids):
# #     exp_obj = Experiment.objects.get(id=exp)
# #     if exp_obj.reactor != 'flame':
# #         r = checkUnique(exp_obj)
# #         if r:
# #             print(exp, '-->', r)
# #             for e in r:
# #                 try:
# #                     exps_ids.remove(e)
# #                 except ValueError:
# #                     pass
