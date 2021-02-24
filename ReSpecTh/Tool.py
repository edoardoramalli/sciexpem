import math
import ExperimentManager.Models as Models


def applyTransformation(my_list: list, plotscale: str, threshold: float = 1) -> list[float]:  # TODO  cosa succede se x è 0?
    if plotscale == 'lin':
        list_a = [float(x) for x in my_list]
    elif plotscale == 'log' or plotscale == 'log10':
        list_a = [math.log10(float(x)) for x in my_list]
    elif plotscale == 'inv':
        list_a = [1000 / float(x) for x in my_list]
    elif plotscale == 'ln':
        list_a = [math.log(float(x), math.e) for x in my_list]
    else:
        list_a = []

    if not all(n > 0 for n in list_a):
        delta = threshold - min(list_a)
        list_a = [x + delta for x in list_a]

    return list_a


def visualizeExperiment(experiment) -> dict:
    #  experiment status is assumed to be managed

    experiment_interpreter = Models.ExperimentInterpreter.objects.get(name=experiment.experiment_interpreter)

    mapping_list = Models.MappingInterpreter.objects.filter(experiment_interpreter=experiment_interpreter)

    result = []

    info = {}

    for mapping in mapping_list:
        x_exp_name = mapping.x_exp_name
        x_exp_location = mapping.x_exp_location
        x_transformation = mapping.x_transformation

        y_exp_name = mapping.y_exp_name
        y_exp_location = mapping.y_exp_location
        y_transformation = mapping.y_transformation

        filter_x = {'experiment': experiment, x_exp_location: x_exp_name}

        x_dataColumn = Models.DataColumn.objects.get(**filter_x)

        x = applyTransformation(list(x_dataColumn.data), x_transformation)

        filter_y = {'experiment': experiment, y_exp_location: y_exp_name}

        y_dataColumn = Models.DataColumn.objects.get(**filter_y)

        y = applyTransformation(list(y_dataColumn.data), y_transformation)

        x_unit_name = x_dataColumn.units if x_transformation != 'inv' else '1000/' + x_dataColumn.units
        x_name = ' [{}] ({})'.format(x_unit_name, x_transformation)
        info['xaxis'] = {'title': (x_dataColumn.name if x_dataColumn.name else x_dataColumn.label) + x_name}

        y_unit_name = y_dataColumn.units if y_transformation != 'inv' else '1000/' + y_dataColumn.units
        y_name = ' [{}] ({})'.format(y_unit_name, y_transformation)
        info['yaxis'] = {'title': (y_dataColumn.name if y_dataColumn.name else y_dataColumn.label) + y_name}

        result.append({'x': x, 'y': y,
                       'type': 'scatter', 'mode': 'markers', 'marker': {'size': 10},
                       'name': y_dataColumn.name if y_dataColumn.name else y_dataColumn.label})

        # TODO devono avere stessa unita e stessa proprietà altrimenti in spazi diversi

    return {'info': info, 'data': result}
