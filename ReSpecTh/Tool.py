import math
import ExperimentManager.Models as Models
import ReSpecTh.units as Unit


def applyTransformation(my_list: list, plotscale: str, threshold: float = 1) -> list[float]:  # TODO  cosa succede se x è 0?
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

    if not all(n > 0 for n in list_a):
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

        y_exp_name = mapping.y_exp_name
        y_exp_location = mapping.y_exp_location
        y_transformation = mapping.y_transformation

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

    def add_experimental(self, x_name: str, y_name: str, result: dict):
        if y_name not in self.experimental:
            self.experimental[y_name] = {x_name: result}
        else:
            if x_name not in self.experimental[y_name]:
                self.experimental[y_name][x_name] = result

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
    x_exp = applyTransformation(Unit.convert_list(my_list=list(x_dataColumn.data),
                                                  unit=x_dataColumn.units,
                                                  desired_unit=consistency.get_unit(x_name=x_dataColumn.name,
                                                                                    y_name=y_dataColumn.name)[0])
                                , x_transformation)
    y_exp = applyTransformation(Unit.convert_list(my_list=list(y_dataColumn.data),
                                                  unit=y_dataColumn.units,
                                                  desired_unit=consistency.get_unit(x_name=x_dataColumn.name,
                                                                                    y_name=y_dataColumn.name)[1])
                                , y_transformation)

    # X SIM
    execution_filter_x = {'execution': execution,
                          'file_type': file,
                          x_sim_location: x_sim_name}

    x_execution_column = Models.ExecutionColumn.objects.get(**execution_filter_x)

    x_sim = applyTransformation(Unit.convert_list(my_list=list(x_execution_column.data),
                                                  unit=x_execution_column.units,
                                                  desired_unit=consistency.get_unit(x_name=x_dataColumn.name,
                                                                                    y_name=y_dataColumn.name)[0]),
                                x_transformation)

    # Y SIM

    execution_filter_y = {'execution': execution,
                          'file_type': file,
                          y_sim_location: y_sim_name}

    y_execution_column = Models.ExecutionColumn.objects.get(**execution_filter_y)

    y_sim = applyTransformation(Unit.convert_list(my_list=list(y_execution_column.data),
                                                  unit=y_execution_column.units,
                                                  desired_unit=consistency.get_unit(x_name=x_dataColumn.name,
                                                                                    y_name=y_dataColumn.name)[1]),
                                y_transformation)

    return x_exp, y_exp, x_sim, y_sim, x_dataColumn, y_dataColumn


def visualizeExecution(execution, consist=None) -> dict:
    #  experiment status is assumed to be managed

    experiment_interpreter = Models.ExperimentInterpreter.objects.get(name=execution.experiment.experiment_interpreter)

    mapping_list = Models.MappingInterpreter.objects.filter(experiment_interpreter=experiment_interpreter)

    consistency = Consistency() if consist is None else consist

    for mapping in mapping_list:
        x_exp, y_exp, x_sim, y_sim, x_dataColumn, y_dataColumn = pairExecutionExperiment(execution, mapping,
                                                                                         consistency)

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

        consistency.add_experimental(x_name=x_dataColumn.name,
                                     y_name=y_dataColumn.name,
                                     result={'x': x_exp, 'y': y_exp,
                                             'type': 'scatter', 'mode': 'markers', 'marker': {'size': 10},
                                             'name': execution.experiment.fileDOI})

        # ADD SIM
        consistency.add_result(x_name=x_dataColumn.name,
                               y_name=y_dataColumn.name,
                               result={'x': x_sim, 'y': y_sim,
                                       'type': 'scatter', 'mode': 'lines+markers', 'marker': {'size': 10},
                                       'name': execution.chemModel.name})

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
            consistency.result[y_key][x_key].append(consistency.experimental[y_key][x_key])

    return {'info': consistency.info, 'data': consistency.result}
