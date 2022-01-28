import os
import sys
import argparse
import psutil

import platform
print(platform.node())





exit()
import django
from django.db.models import Q, Count, F, Case, When, IntegerField
from django.utils import timezone

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SciExpeM.settings")
django.setup()

# SciExpeM Import
from ReSpecTh.Tool import Consistency, resultExecutionVisualization, pairExecutionExperiment, visualizeExecution
from ExperimentManager.Models import *

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
