import math
import ExperimentManager.Models as Models
import ReSpecTh.units as Unit
from FrontEnd.exceptions import ExecutionColumnError


def applyTransformation(my_list: list, plotscale: str, threshold: float = 1) -> list[float]:
    if plotscale == 'lin':
        list_a = [float(x) for x in my_list]
    elif plotscale == 'log' or plotscale == 'log10':
        list_a = [math.log10(float(x)) if float(x) != 0 else 0 for x in my_list]
    elif plotscale == 'inv':
        list_a = [1000 / float(x) if float(x) != 0 else 0 for x in my_list]
    elif plotscale == 'ln':
        list_a = [math.log(float(x), math.e) if float(x) != 0 else 0 for x in my_list]
    else:
        list_a = []

    # If a y-value is not positive then shift everything until threshold by the same quantity
    # TODO error both shift
    if not all(n >= 0 for n in list_a):
        delta = threshold - min(list_a)
        list_a = [x + delta for x in list_a]

    return list_a


def visualizeExperiment(experiment) -> dict:
    #  experiment status is assumed to be managed

    experiment_interpreter = Models.ExperimentInterpreter.objects.get(name=experiment.experiment_interpreter)

    mapping_list = Models.MappingInterpreter.objects.filter(experiment_interpreter=experiment_interpreter)

    result = {}

    info = {}

    for mapping in mapping_list:
        x_exp_name = mapping.x_exp_name
        x_exp_location = mapping.x_exp_location
        x_transformation = mapping.x_transformation
        x_sim_name = mapping.x_sim_name

        y_exp_name = mapping.y_exp_name
        y_exp_location = mapping.y_exp_location
        y_transformation = mapping.y_transformation
        y_sim_name = mapping.y_sim_name

        if x_sim_name == 'None' or y_sim_name == 'None':
            continue

        filter_x = {'experiment': experiment, x_exp_location: x_exp_name}

        x_dataColumn = Models.DataColumn.objects.get(**filter_x)

        x = applyTransformation(list(x_dataColumn.data), x_transformation)

        filter_y = {'experiment': experiment, y_exp_location: y_exp_name}

        y_dataColumn = Models.DataColumn.objects.get(**filter_y)

        if y_dataColumn.name not in result:
            result[y_dataColumn.name] = []

        if y_dataColumn.name not in info:
            info[y_dataColumn.name] = {}

        y = applyTransformation(list(y_dataColumn.data), y_transformation)

        x_unit_name = x_dataColumn.units if x_transformation != 'inv' else '1000/' + x_dataColumn.units
        x_name = ' [{}] ({})'.format(x_unit_name, x_transformation)
        info[y_dataColumn.name]['xaxis'] = {
            'title': (x_dataColumn.name if x_dataColumn.name else x_dataColumn.label) + x_name}

        y_unit_name = y_dataColumn.units if y_transformation != 'inv' else '1000/' + y_dataColumn.units
        y_name = ' [{}] ({})'.format(y_unit_name, y_transformation)
        info[y_dataColumn.name]['yaxis'] = {
            'title': (y_dataColumn.name if y_dataColumn.name else y_dataColumn.label) + y_name}

        if y_dataColumn.name == 'composition':
            name = y_dataColumn.label
        elif y_dataColumn.name:
            name = y_dataColumn.name
        elif not y_dataColumn.name and y_dataColumn.label:
            name = y_dataColumn.name
        else:
            name = 'No Name'

        result[y_dataColumn.name].append({'x': x, 'y': y,
                                          'type': 'scatter', 'mode': 'markers', 'marker': {'size': 10},
                                          'name': name})

        # TODO devono avere stessa unita

    return {'info': info, 'data': result}


class Consistency:

    def __init__(self):
        self.result = {}
        self.info = {}
        self.unit = {}
        self.experimental = {}

    def add_result(self, x_name: str, y_name: str, result: dict):
        if y_name not in self.result:
            self.result[y_name] = {x_name: []}
        else:
            if x_name not in self.result[y_name]:
                self.result[y_name][x_name] = []
        self.result[y_name][x_name].append(result)  # TODO no duplicate

    def add_experimental(self, x_name: str, y_name: str, result: dict, key: str):
        if y_name not in self.experimental:
            self.experimental[y_name] = {x_name: {key: {}}}
        else:
            if x_name not in self.experimental[y_name]:
                self.experimental[y_name][x_name] = {key: {}}
        self.experimental[y_name][x_name][key] = result

    def add_unit(self, x_name: str, y_name: str, x_unit: str, y_unit: str):
        if y_name not in self.unit:
            self.unit[y_name] = {x_name: (x_unit, y_unit)}
        else:
            if x_name not in self.unit[y_name]:
                self.unit[y_name][x_name] = (x_unit, y_unit)

    def add_info(self, x_name: str, y_name: str, x_axis: dict, y_axis: dict):
        if y_name not in self.info:
            self.info[y_name] = {x_name: {'xaxis': x_axis, 'yaxis': y_axis}}
        else:
            if x_name not in self.info[y_name]:
                self.info[y_name][x_name] = {'xaxis': x_axis, 'yaxis': y_axis}

    def get_unit(self, x_name: str, y_name: str, ):
        return self.unit[y_name][x_name]


def pairExecutionExperiment(execution, mapping, consistency):
    """
    Return the experiment and execution curve pair, with the same unit and same transformation
    """

    threshold = 1
    valid = True

    x_exp_name = mapping.x_exp_name
    x_exp_location = mapping.x_exp_location
    x_sim_name = mapping.x_sim_name
    x_sim_location = mapping.x_sim_location
    x_transformation = mapping.x_transformation

    y_exp_name = mapping.y_exp_name
    y_exp_location = mapping.y_exp_location
    y_transformation = mapping.y_transformation
    y_sim_name = mapping.y_sim_name
    y_sim_location = mapping.y_sim_location

    file = mapping.file

    if x_sim_name == 'None' or y_sim_name == 'None':
        return {'valid': False}

    # X EXP

    filter_x = {'experiment': execution.experiment, x_exp_location: x_exp_name}

    x_dataColumn = Models.DataColumn.objects.get(**filter_x)

    # Y EXP

    filter_y = {'experiment': execution.experiment, y_exp_location: y_exp_name}

    y_dataColumn = Models.DataColumn.objects.get(**filter_y)

    # For each experimental data in the same config add the units of the axis
    consistency.add_unit(x_name=x_dataColumn.name,
                         y_name=y_dataColumn.name,
                         x_unit=x_dataColumn.units,
                         y_unit=y_dataColumn.units)

    # It is not necessary to convert the experimental data. They impose the unit !
    # But we need to apply the transformation, and to keep consistency we do anyway
    x_exp = applyTransformation(
        my_list=Unit.convert_list(my_list=list(x_dataColumn.data),
                                  unit=x_dataColumn.units,
                                  desired_unit=consistency.get_unit(x_name=x_dataColumn.name,
                                                                    y_name=y_dataColumn.name)[0]),
        plotscale=x_transformation,
        threshold=threshold)
    y_exp = applyTransformation(
        my_list=Unit.convert_list(my_list=list(y_dataColumn.data),
                                  unit=y_dataColumn.units,
                                  desired_unit=consistency.get_unit(x_name=x_dataColumn.name,
                                                                    y_name=y_dataColumn.name)[1]),
        plotscale=y_transformation,
        threshold=threshold)

    # X SIM
    execution_filter_x = {'execution': execution,
                          'file_type': file,
                          x_sim_location: x_sim_name}

    x_execution_column = Models.ExecutionColumn.objects.filter(**execution_filter_x)

    if not x_execution_column.exists():
        raise ExecutionColumnError
    else:
        x_execution_column = x_execution_column[0]

    x_sim = applyTransformation(
        my_list=Unit.convert_list(my_list=list(x_execution_column.data),
                                  unit=x_execution_column.units,
                                  desired_unit=consistency.get_unit(x_name=x_dataColumn.name,
                                                                    y_name=y_dataColumn.name)[0]),
        plotscale=x_transformation,
        threshold=threshold)

    # Y SIM

    execution_filter_y = {'execution': execution,
                          'file_type': file,
                          y_sim_location: y_sim_name}

    y_execution_column = Models.ExecutionColumn.objects.filter(**execution_filter_y)

    if not y_execution_column.exists():
        raise ExecutionColumnError
    else:
        y_execution_column = y_execution_column[0]

    y_sim = applyTransformation(
        my_list=Unit.convert_list(my_list=list(y_execution_column.data),
                                  unit=y_execution_column.units,
                                  desired_unit=consistency.get_unit(x_name=x_dataColumn.name,
                                                                    y_name=y_dataColumn.name)[1]),
        plotscale=y_transformation,
        threshold=threshold)

    result = {
        'valid': valid,
        'x_exp': x_exp,
        'y_exp': y_exp,
        'x_sim': x_sim,
        'y_sim': y_sim,
        'x_dataColumn': x_dataColumn,
        'y_dataColumn': y_dataColumn,
        'x_execution_column': x_execution_column,
        'y_execution_column': y_execution_column
    }

    return result


def visualizeExecution(execution, consist=None) -> dict:
    #  experiment status is assumed to be managed

    experiment_interpreter = Models.ExperimentInterpreter.objects.get(name=execution.experiment.experiment_interpreter)

    mapping_list = Models.MappingInterpreter.objects.filter(experiment_interpreter=experiment_interpreter)

    consistency = Consistency() if consist is None else consist

    for mapping in mapping_list:
        result = pairExecutionExperiment(execution=execution, mapping=mapping, consistency=consistency)

        if not result['valid']:
            continue
            
        x_exp = result['x_exp']
        y_exp = result['y_exp']
        x_sim = result['x_sim']
        y_sim = result['y_sim']
        x_dataColumn = result['x_dataColumn']
        y_dataColumn = result['y_dataColumn']
        x_execution_column = result['x_execution_column']
        y_execution_column = result['y_execution_column']

        x_unit_name = x_dataColumn.units if mapping.x_transformation != 'inv' else '1000/' + x_dataColumn.units
        x_name = ' [{}] ({})'.format(x_unit_name, mapping.x_transformation)
        y_unit_name = y_dataColumn.units if mapping.y_transformation != 'inv' else '1000/' + y_dataColumn.units
        y_name = ' [{}] ({})'.format(y_unit_name, mapping.y_transformation)
        consistency.add_info(x_name=x_dataColumn.name,
                             y_name=y_dataColumn.name,
                             x_axis={
                                 'title': (x_dataColumn.name if x_dataColumn.name else x_dataColumn.label) + x_name},
                             y_axis={
                                 'title': (y_dataColumn.name if y_dataColumn.name else y_dataColumn.label) + y_name})

        # ADD EXP

        exp_name = execution.experiment.fileDOI if y_dataColumn.name != 'composition' else execution.experiment.fileDOI + ' ' + y_dataColumn.label

        consistency.add_experimental(x_name=x_dataColumn.name,
                                     y_name=y_dataColumn.name,
                                     key=exp_name,
                                     result={'x': x_exp, 'y': y_exp,
                                             'type': 'scatter', 'mode': 'markers', 'marker': {'size': 10},
                                             'name': exp_name})

        sim_name = execution.chemModel.name if y_dataColumn.name != 'composition' else execution.chemModel.name + ' ' + y_dataColumn.label

        # ADD SIM
        consistency.add_result(x_name=x_dataColumn.name,
                               y_name=y_dataColumn.name,
                               result={'x': x_sim, 'y': y_sim,
                                       'type': 'scatter', 'mode': 'lines+markers', 'marker': {'size': 10},
                                       'name': sim_name})

    return consistency


def visualizeAllExecution(experiment):
    execution_list = Models.Execution.objects.filter(experiment=experiment)
    #  experiment status is assumed to be managed

    consistency = Consistency()

    # For cycle with the same consistency means 'consistency' and aggregate results
    for execution in execution_list:
        visualizeExecution(execution=execution, consist=consistency)

    return consistency


def resultExecutionVisualization(consistency):
    for y_key in consistency.result:
        for x_key in consistency.result[y_key]:
            consistency.result[y_key][x_key] += consistency.experimental[y_key][x_key].values()
    return {'info': consistency.info, 'data': consistency.result}
