# Setuo Django Local
import os
import django
from django.db.models import Q, Count, F

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SciExpeM.settings")
django.setup()

# SciExpeM Import
from ExperimentManager.Models import *

from tabulate import tabulate


# # Execution not yet ended
#
# not_ended = list(Execution.objects.filter(execution_end=None).values_list('id', 'experiment__id'))
#
# print(not_ended)
#
# # Execution ended but with errors
#
# query = ~Q(execution_end=None) & ~Q(execution_error=None)
#
# ended_with_errors = list(Execution.objects.filter(query).values_list('id', 'experiment__id', 'execution_error'))
# print(ended_with_errors)
#
# # Execution ended with no errors but no execution_columns
# query = ~Q(execution_end=None) & Q(execution_error=None)
#
# ended_no_errors_no_execution_columns = list(
#     Execution.objects.filter(query).annotate(n_cols=Count('execution_columns', distinct=True)).filter(
#         n_cols__lte=1).values_list('id',
#                                    'experiment__id'))
#
# print(ended_no_errors_no_execution_columns)

##### Curve Matching #####

query = ~Q(execution_end=None) & Q(execution_error=None)

no_curve_matching = list(Execution.objects
                         .filter(query)
                         .annotate(
    n_cols=Count('execution_columns', distinct=True),
    n_cm=Count('execution_columns__curve_matching_result', distinct=True),
    n_groups=Count('experiment__data_columns__dg_id', distinct=True))
                         .filter(n_cm__lt=F('n_cols') - F('n_groups'))
                         .values('id',
                                 'experiment__id',
                                 'n_cols',
                                 'n_cm',
                                 'n_groups')
                         .order_by('experiment__id', 'id'))

print(tabulate([[item['experiment__id'], item['id'], ] for item in no_curve_matching], headers=['Exp ID', 'Exec ID']))

print(no_curve_matching)

print([item['id'] for item in no_curve_matching])
