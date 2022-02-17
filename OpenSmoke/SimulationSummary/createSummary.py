from django.db.models import Q
from ExperimentManager.Models import *
from ReSpecTh.Tool import pairExecutionExperiment, Consistency


def create_summary(exp_id, chemModel=''):

    query = Q(experiment_id=exp_id) & ~Q(execution_end=None) & ~Q(execution_columns=None)

    if chemModel != '':
        query = query & Q(chemModel__name=chemModel)

    list_simulation = Execution.objects.filter(query)

    consistency = Consistency()

    result = []

    for execution in list_simulation:
        current_model = {
            'model': {'id': execution.chemModel.id, 'name': execution.chemModel.name},
            'pairs': []
        }
        for mapping in execution.experiment.experiment_interpreter.mappings.all():
            list_pair = pairExecutionExperiment(execution=execution, mapping=mapping, consistency=consistency)
            for pair in list_pair:
                if pair['valid']:
                    x_exp_name = pair['x_dataColumn'].name
                    y_exp_name = pair['y_dataColumn'].name

                    units = consistency.get_unit(y_name=y_exp_name, x_name=x_exp_name)
                    x_unit = units[0]
                    y_unit = units[1]

                    x_sim_name = pair['x_execution_column'].label
                    y_sim_name = ', '.join([exec_col.label for exec_col in pair['y_execution_column']])

                    current_pair = {
                        'x_exp_data': pair['x_exp'],
                        'x_exp_name': x_exp_name,
                        'y_exp_data': pair['y_exp'],
                        'y_exp_name': y_exp_name,

                        'x_sim_data': pair['x_sim'],
                        'x_sim_name': x_sim_name,
                        'y_sim_data': pair['y_sim'],
                        'y_sim_name': y_sim_name,

                        'x_unit': x_unit,
                        'y_unit': y_unit

                    }
                    current_model['pairs'].append(current_pair)

        result.append(current_model)

    return result