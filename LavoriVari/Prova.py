# Setuo Django Local
import os
import django
from django.db.models import Q

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SciExpeM.settings")
django.setup()

# SciExpeM Import
from ExperimentManager.Models import *
from ExperimentManager.Views.getSimulation import create_summary
from CurveMatching.CurveMatchingPython import CurveMatching
from CurveMatching import CurveMatching

# query = ~Q(fuels=None)
#
# a = list(Experiment.objects.filter(query).values_list('fuels', flat=True))
#
# flat_list = [item for sublist in a for item in sublist]
#
# print(set(flat_list))
import pandas as pd
a = {'NH3', 'n-C10H22', 'SO2', 'H2S', 'C6H6', 'C10H7CH3', 'C5H6', 'CO', 'C2H4', 'H2', 'C3H6', 'CH3OCH3', 'C2H6', 'CH4'}

from statistics import mean
a = list(CurveMatchingResult.objects.filter(
    execution_column__execution__chemModel__name='CRECK_2003_C1C3_DME_LTHT',
    execution_column__label='C2H6_x',
    execution_column__execution__experiment__fuels__contains=['H2'],
).values('score', 'error', 'd0L2', 'd1L2', 'd0Pe', 'd1Pe', 'shift'))
# print(a)

df = pd.DataFrame(a)
df = df.apply(pd.to_numeric, downcast='float')
print(df.describe())


b = list(CurveMatchingResult.objects.filter(
    execution_column__execution__chemModel__name='POLIMI_1212_C1C3',
    execution_column__label='C2H6_x',
    execution_column__execution__experiment__fuels__contains=['H2'],
).values('score', 'error', 'd0L2', 'd1L2', 'd0Pe', 'd1Pe', 'shift'))
# print(a)

df = pd.DataFrame(b)
df = df.apply(pd.to_numeric, downcast='float')
print(df.describe())


exit()

# for f in a:
#      print(f)
#      query = ~Q(execution_end=None) & Q(execution_error=None) & Q(experiment__fuels__contains=[f]) & ~Q(experiment__experiment_type='ignition delay measurement')  & ~Q(experiment__experiment_type='laminar burning velocity measurement') & Q(experiment__status='verified')
#      L = list(Execution.objects.filter(query).distinct().values_list('experiment__id', 'chemModel__name'))
#      print(L)

# L = [715, 721, 727, 633, 680, 681, 682, 683, 684, 695, 697, 698, 699, 632, 874, 213, 693, 633, 632, 634, 634, 635, 635, 680, 681, 682, 683, 684, 692, 692, 693, 694, 694, 695, 696, 696, 697, 698, 699, 702, 702, 703, 703, 705, 705, 768, 768, 465, 751, 752, 750, 210, 749, 217, 416, 415, 714, 485, 479, 632, 633, 634, 635, 680, 681, 682, 683, 684, 693, 694, 695, 697, 698, 699, 702, 703, 717, 723, 705, 699, 903, 874, 855, 868, 680, 850, 872, 719, 919, 868, 684, 865, 910, 873, 889, 970, 920, 828, 829, 830, 908, 683, 869, 913, 897, 886, 683, 839, 922, 885, 878, 725, 895, 831, 719, 725, 699, 911, 901, 950, 950, 919, 917, 972, 903, 890, 918, 900, 917, 915, 912, 869, 894, 717, 871, 887, 923, 896, 894, 877, 828, 923, 921, 902, 879, 938, 936, 856, 954, 838, 715, 954, 681, 715, 924, 854, 899, 884, 916, 859, 719, 684, 912, 853, 920, 906, 837, 879, 852, 895, 856, 854, 884, 934, 858, 891, 880, 723, 909, 888, 893, 870, 982, 836, 837, 839, 947, 417, 213, 213, 217, 934, 876, 698, 901, 858, 864, 859, 891, 727, 721, 890, 880, 723, 900, 909, 697, 888, 682, 924, 836, 946, 892, 913, 877, 875, 870, 886, 921, 905, 878, 936, 902, 752, 876, 983, 698, 851, 727, 721, 697, 682, 972, 947, 835, 850, 838, 852, 946, 915, 916, 872, 873, 898, 910, 680, 918, 717, 889, 865, 887, 871, 896, 970, 855, 908, 897, 922, 885, 938, 725, 899, 906, 681, 835, 864, 911, 907, 892, 875, 898, 853, 905, 904, 851, 893, 210, 415, 416, 417, 465, 479, 714, 485, 749, 750, 751, 419, 907, 419, 1230]

# target = ['CRECK_2003_C1C3_DME_LTHT', 'POLIMI_1212_C1C3']
#
# L = sorted(L)
#
# a = []
# b = []
# c = []
#
# for exp in L:
#      e = Experiment.objects.get(id=exp)
#      if  e.p_inf < 5:
#           a.append(exp)
#      elif 5 < e.p_inf < 20:
#           b.append(exp)
#      else:
#           c.append(exp)
#
# print(sorted(a))
# print(sorted(b))
# print(sorted(c))

# [898, 828, 934, 938, 908, 894, 868, 970, 951, 887, 972, 858, 895, 874, 900, 891, 854, 877, 911, 889, 943, 918, 855, 920, 916, 878, 870, 942, 910, 941, 919, 949, 873, 884, 953, 915, 888, 879, 893, 940, 871, 909, 875, 902, 876, 924, 872, 892, 856, 903, 896, 897, 880, 950, 859, 945, 948, 952, 869, 922, 864, 923, 954, 890, 899, 936, 901, 886, 865, 921, 885, 913, 917, 912, 939]

# r = []
#
# for exp in L:
#     q = ~Q(execution_end=None) & Q(experiment__id=exp)
#     if 'POLIMI_1212_C1C3' not in list(Execution.objects.filter(q).distinct().values_list('chemModel__name', flat=True)):
#         r.append(exp)
#
# print(sorted(r))


# a = {'x_exp_data': [0.616853932584254, 0.6179775280898946, 0.6696629213483266, 0.6921348314606717, 0.6629213483146008, 0.7202247191011385, 0.7426966292134836, 0.7539325842696593, 0.7707865168539092, 0.7831460674157062, 0.8460674157303202, 0.830337078651683, 0.8898876404494174, 0.9022471910112662, 0.9224719101123402, 0.9280898876404534, 0.9404494382022747, 0.966292134831491, 0.9764044943820334, 1.00786516853934, 1.0247191011235495, 1.0359550561797646],
#      'x_exp_name': 'temperature',
#      'y_exp_data': [1.9488372093022932, 2.0, 2.065116279069619, 2.060465116278999, 2.0837209302325825, 2.2651162790697343, 2.288372093023245, 2.3674418604651293, 2.2976744186047577, 2.390697674418675, 2.516279069767495, 2.581395348837185, 2.75813953488371, 2.7674418604651296, 2.851162790697657, 2.874418604651169, 2.8697674418604557, 2.9255813953488468, 3.023255813953508, 3.1162790697674523, 3.232558139534881, 3.2558139534883725],
#      'y_exp_name': 'ignition delay',
#      'x_sim_data': [1.0526315789473684, 1.0, 0.9523809523809523, 0.9090909090909091, 0.8695652173913043, 0.8333333333333334, 0.8, 0.7692307692307693, 0.7407407407407407, 0.7142857142857143, 0.6896551724137931, 0.6666666666666666, 0.6451612903225806, 0.625, 0.6060606060606061],
#      'x_sim_name': 'T0',
#      'y_sim_data': [3.77536567430401, 3.3098691765003556, 3.0624954927323276, 2.8786557971839257, 2.7288730013695153, 2.600746546429012, 2.487952868269312, 2.3872148273659906, 2.2967847144654634, 2.2133618079842856, 2.1374674183266062, 2.066475759067516, 2.001387956395598, 1.9404387830975893, 1.8839293093805975],
#      'y_sim_name': 'tau_OH(slope)',
#      'x_unit': 'K',
#      'y_unit': 'us'}
#
#
# import matplotlib.pyplot as plt
#
# plt.plot(a['x_exp_data'], a['y_exp_data'], 'o')
# plt.plot(a['x_sim_data'], a['y_sim_data'])
# plt.show()
