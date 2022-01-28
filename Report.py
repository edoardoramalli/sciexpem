# Setuo Django Local
import os
import django
from django.db.models import Q, Count, F

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SciExpeM.settings")
django.setup()

# SciExpeM Import
from ExperimentManager.Models import *

from tabulate import tabulate

# Exp Valid but without any execution

no_execution = list(Experiment.objects.filter(status='verified').annotate(n_exec=Count('executions', distinct=True)).filter(n_exec=0).order_by('username', 'id').values('username', 'id'))
print('---> Exp No Executed ---')
print()
print(tabulate([[item['id'], item['username']] for item in no_execution],
               headers=['Exp ID', 'Username']))
print()

# # Execution not yet ended

# not_ended = list(
#     Execution.objects.filter(execution_end=None).values('id', 'experiment__id', 'execution_error', 'username').order_by('experiment__id', 'id'))
#
# print('---> Exec Not Ended ---')
# print()
# print(tabulate([[item['experiment__id'], item['id'], item['execution_error'], item['username']] for item in not_ended],
#                headers=['Exp ID', 'Exec ID', 'Error', 'Username']))
# print()

# Execution ended but with errors

# query = ~Q(execution_end=None) & ~Q(execution_error=None)
#
# ended_with_errors = list(
#     Execution.objects.filter(query).values('id', 'experiment__id', 'execution_error', 'username').order_by('username', 'experiment__id', 'id'))
# print('---> Exec Ended, with Errors  ---')
# print()
# print(tabulate([[item['experiment__id'], item['id'], item['execution_error'], item['username']] for item in ended_with_errors],
#                headers=['Exp ID', 'Exec ID', 'Error', 'Username']))
# print()

# Execution ended  but no execution_columns
# query = ~Q(execution_end=None)
#
# ended_no_errors_no_execution_columns = list(
#     Execution.objects.filter(query).annotate(n_cols=Count('execution_columns', distinct=True)).filter(
#         n_cols__lte=1).values('id',
#                               'experiment__id').order_by('experiment__id', 'id'))
#
# print('---> Exec Ended, No Errors, No Exec Columns ---')
# print()
# print(tabulate([[item['experiment__id'], item['id'], ] for item in ended_no_errors_no_execution_columns],
#                headers=['Exp ID', 'Exec ID']))
# print()


# query = Q(execution_end=None) & Q(execution_start=None)
#
# no_started = list(Execution.objects.filter(query).values('id', 'experiment__id').order_by('experiment__id', 'id'))
#
#
# print('---> Exec created but not started ---')
# print()
# print(tabulate([[item['experiment__id'], item['id'], ] for item in no_started], headers=['Exp ID', 'Exec ID']))
# print()


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

print('---> Missing Curve Matching ---')
print()
print(tabulate([[item['experiment__id'], item['id'], ] for item in no_curve_matching], headers=['Exp ID', 'Exec ID']))
print()



# print(no_curve_matching)
#
# print([item['id'] for item in no_curve_matching])


# TODO curve_matching con valori strani -1, 0, -2?