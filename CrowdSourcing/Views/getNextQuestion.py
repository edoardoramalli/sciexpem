import CrowdSourcing.views as View
from random import choices

from CrowdSourcing import models
from ExperimentManager.Models import *
from ReSpecTh.Tool import pairExecutionExperiment, Consistency

# Django import
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST


def extract_next(current):
    participants = models.Participant.objects.all().exclude(username='base')

    done = {}
    for p in participants:
        for q in p.done:
            done[int(q)] = done.get(int(q), 0) + 1

    base = [int(e) for e in models.Participant.objects.get(username='base').done]

    current_participant, created = models.Participant.objects.get_or_create(username=current,
                                                                            defaults={'username': current, 'done': []})

    current = [int(e) for e in current_participant.done]

    remaining = set(base).difference(set(current))

    never_done = set(base).difference(set(done.keys()))

    pesi = {possible: 1 if possible not in never_done else 100 for possible in remaining}

    return choices(population=list(pesi.keys()), weights=list(pesi.values()), k=1)[0]


class getNextQuestion(View.CrowdSourcingBaseView):
    viewName = 'getNextQuestion'
    paramsType = {}
    # paramsType = {'status': str, 'exp_id': int}

    required_groups = {'POST': []}

    def view_post(self, request):

        username = request.user.username

        # username = 'root'

        total = len(models.Participant.objects.get(username='base').done)

        current_participant, created = models.Participant.objects.get_or_create(username=username,
                                                                                defaults={'username': username,
                                                                                          'done': []})
        remaining = total - len(current_participant.done)

        if remaining > 0:
            experiment_id = extract_next(current=username)

            list_simulation = Execution.objects.filter(experiment_id=experiment_id)

            if len(list_simulation) < 2:
                pass # TODO

            consistency = Consistency()

            edoardo = {}

            fake_names_models = {}

            names = list(range(150))

            for execution in list_simulation:

                current_model_id = execution.chemModel.id
                current_model_name = execution.chemModel.name

                for mapping in execution.experiment.experiment_interpreter.mappings.all():
                    list_pair = pairExecutionExperiment(execution=execution, mapping=mapping, consistency=consistency)
                    for pair in list_pair:
                        if pair['valid']:
                            x_exp_name = pair['x_dataColumn'].name
                            y_exp_name = pair['y_dataColumn'].name
                            y_exp_name_id = pair['y_dataColumn'].id
                            x_exp_name_id = pair['x_dataColumn'].id

                            y_execution_column_id = pair['y_execution_column'].id

                            fake_names_models[y_execution_column_id] = 'Model' + str(names.pop(0))

                            if y_exp_name == 'composition':
                                name = ', '.join(pair['y_dataColumn'].species)
                            else:
                                name = y_exp_name

                            if y_exp_name_id not in edoardo:
                                units = consistency.get_unit(y_name=y_exp_name, x_name=x_exp_name)
                                x_unit = units[0]
                                y_unit = units[1]

                                if y_exp_name == 'ignition delay':
                                    x_unit = '1000 / K'

                                edoardo[y_exp_name_id] = {
                                    'y_exp_name_id': y_exp_name_id,
                                    'y_exp_name': name,
                                    'plot': {'x': pair['x_exp'],
                                             'y': pair['y_exp'],
                                             'type': 'scatter', 'mode': 'markers',
                                             'marker': {'size': 10},
                                             'name': 'Experimental Data'},
                                    'layout': {'xaxis': {'title': x_exp_name + ' [{}]'.format(x_unit)},
                                               'yaxis': {'title': y_exp_name + ' [{}]'.format(y_unit)}},
                                    'models': []}

                            edoardo[y_exp_name_id]['models'].append({'y_execution_column_id': y_execution_column_id,
                                                                     'fake_name': fake_names_models[
                                                                         y_execution_column_id],
                                                                     'plot': {'x': pair['x_sim'],
                                                                              'y': pair['y_sim'],
                                                                              'type': 'scatter',
                                                                              'mode': 'lines+markers',
                                                                              'marker': {'size': 10},
                                                                              'name': fake_names_models[
                                                                                  y_execution_column_id]}})

            response = {'total': total, 'remaining': remaining, 'data': edoardo, 'experiment_id': experiment_id, }

        else:
            response = {'total': total, 'remaining': remaining}

        return Response(response, status=HTTP_200_OK)
