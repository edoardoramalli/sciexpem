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


def visualizeSingleDataGroup(data_group, mapping_list, experiment):
    result = []
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

        filter_x = {'experiment': experiment, x_exp_location: x_exp_name, 'dg_id': data_group}

        x_dataColumn = Models.DataColumn.objects.get(**filter_x)

        x = applyTransformation(list(x_dataColumn.data), x_transformation)

        filter_y = {'experiment': experiment, y_exp_location: y_exp_name, 'dg_id': data_group}

        y_dataColumn = Models.DataColumn.objects.filter(**filter_y)

        for y_element in y_dataColumn:

            uncertainty = y_element.uncertainty_reference

            uncertainty_dict = {}

            if uncertainty:
                uncertainty_dict['visible'] = True
                if uncertainty.uncertainty_kind == 'relative':
                    uncertainty_dict['type'] = 'percent'
                    uncertainty_dict['array'] = [float(x) * 100 for x in uncertainty.data]
                else:
                    # C'è da applicare le transformation
                    pass

            if experiment.experiment_type != 'ignition delay measurement':
                y = applyTransformation(list(y_element.data), y_transformation)
            else:
                y = applyTransformation(list(y_element.data), 'lin')

            x_unit_name = x_dataColumn.units if x_transformation != 'inv' else '1000/' + x_dataColumn.units
            x_name = ' [{}] ({})'.format(x_unit_name, x_transformation)
            info['xaxis'] = {
                'title': (x_dataColumn.name if x_dataColumn.name else x_dataColumn.label) + x_name,
                'linecolor': 'lightgrey',
                'linewidth': 2,
                'mirror': True
            }

            y_unit_name = y_element.units if y_transformation != 'inv' else '1000/' + y_element.units
            y_name = ' [{}] ({})'.format(y_unit_name, y_transformation)
            info['yaxis'] = {
                'title': (y_element.name if y_element.name else y_element.label) + y_name,
                'linecolor': 'lightgrey',
                'linewidth': 2,
                'mirror': True
            }
            if experiment.experiment_type == 'ignition delay measurement':
                info['yaxis']['type'] = 'log'

            if y_element.name == 'composition':
                name = '+'.join([specie.preferredKey for specie in y_element.species_object.all()])
            elif y_element.name:
                name = y_element.name
            elif not y_element.name and y_element.label:
                name = y_element.name
            else:
                name = 'No Name'

            tmp = {'x': x, 'y': y, 'type': 'scatter', 'mode': 'markers', 'marker': {'size': 10}, 'name': name}

            if uncertainty:
                tmp['error_y'] = uncertainty_dict
            result.append(tmp)

        # TODO devono avere stessa unita

    return info, result


def visualizeExperiment(experiment) -> dict:
    #  experiment status is assumed to be managed
    experiment_interpreter = experiment.interpreter

    mapping_list = experiment_interpreter.mappings.all()

    result_dg = {}

    info_dg = {}

    columns_list = Models.DataColumn.objects.filter(experiment=experiment, dg_label="experimental_data")

    columns_list_dg = {column.dg_id for column in columns_list}

    for dg in columns_list_dg:
        info_dg['Data Group ({})'.format(dg)], result_dg['Data Group ({})'.format(dg)] = visualizeSingleDataGroup(dg,
                                                                                                                  mapping_list,
                                                                                                                  experiment)

    return {'data': result_dg, 'info': info_dg}


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
        return [{'valid': False}]

    # Y EXP

    filter_y = {'experiment': execution.experiment, y_exp_location: y_exp_name}

    y_dataColumn = Models.DataColumn.objects.filter(**filter_y)

    result = []

    for current_y in y_dataColumn:

        # X EXP

        filter_x = {'experiment': execution.experiment, x_exp_location: x_exp_name, 'dg_id': current_y.dg_id}
        try:
            x_dataColumn = Models.DataColumn.objects.get(**filter_x)
        except Models.DataColumn.DoesNotExist:
            # TODO
            print(x_dataColumn)

        # For each experimental data in the same config add the units of the axis
        consistency.add_unit(x_name=x_dataColumn.name,
                             y_name=current_y.name,
                             x_unit=x_dataColumn.units,
                             y_unit=current_y.units)

        # It is not necessary to convert the experimental data. They impose the unit !
        # But we need to apply the transformation, and to keep consistency we do anyway
        x_exp = applyTransformation(
            my_list=Unit.convert_list(my_list=list(x_dataColumn.data),
                                      unit=x_dataColumn.units,
                                      desired_unit=consistency.get_unit(x_name=x_dataColumn.name,
                                                                        y_name=current_y.name)[0]),
            plotscale=x_transformation,
            threshold=threshold)
        y_exp = applyTransformation(
            my_list=Unit.convert_list(my_list=list(current_y.data),
                                      unit=current_y.units,
                                      desired_unit=consistency.get_unit(x_name=x_dataColumn.name,
                                                                        y_name=current_y.name)[1]),
            plotscale=y_transformation,
            threshold=threshold)

        # X SIM
        execution_filter_x = {'execution': execution,
                              'file_type': file,
                              x_sim_location: x_sim_name}

        x_execution_column = Models.ExecutionColumn.objects.filter(**execution_filter_x)

        if not x_execution_column.exists():
            # TODO salvare msg errore
            raise ExecutionColumnError
        else:
            x_execution_column = x_execution_column[0]
            # TODO cosa fare se più colonne?

        x_sim = applyTransformation(
            my_list=Unit.convert_list(my_list=list(x_execution_column.data),
                                      unit=x_execution_column.units,
                                      desired_unit=consistency.get_unit(x_name=x_dataColumn.name,
                                                                        y_name=current_y.name)[0]),
            plotscale=x_transformation,
            threshold=threshold)

        def get_Y_ExecutionColumn(execution_filter_y):
            y_execution_column = Models.ExecutionColumn.objects.filter(**execution_filter_y)

            if not y_execution_column.exists():
                print(execution_filter_y)
                raise ExecutionColumnError
            else:
                y_execution_column = y_execution_column[0]

            y_sim = applyTransformation(
                my_list=Unit.convert_list(my_list=list(y_execution_column.data),
                                          unit=y_execution_column.units,
                                          desired_unit=consistency.get_unit(x_name=x_dataColumn.name,
                                                                            y_name=current_y.name)[1]),
                plotscale=y_transformation,
                threshold=threshold)
            return y_sim, y_execution_column


        # Y SIM
        if current_y.name != 'composition':
            execution_filter_y = {'execution': execution,
                                  'file_type': file,
                                  y_sim_location: y_sim_name}

            y_sim, y_execution_column = get_Y_ExecutionColumn(execution_filter_y=execution_filter_y)
        else:
            dataColumnSpecies = current_y.species_object.all()

            y_sim_tot = [0] * len(x_execution_column.data)
            y_execution_column_tot = []

            for specie_object in dataColumnSpecies:
                specie = [name + '_x' for name in specie_object.names]
                execution_filter_y = {'execution': execution,
                                      'file_type': file,
                                      y_sim_location + '__in': specie}

                y_sim_partial, y_execution_column_partial = get_Y_ExecutionColumn(execution_filter_y=execution_filter_y)

                y_sim_tot = [x + y for x, y in zip(y_sim_partial, y_sim_tot)]
                y_execution_column_tot.append(y_execution_column_partial)

            y_execution_column = y_execution_column_tot
            y_sim = y_sim_tot


        result.append({
            'valid': valid,
            'x_exp': x_exp,
            'y_exp': y_exp,
            'x_sim': x_sim,
            'y_sim': y_sim,
            'x_dataColumn': x_dataColumn,
            'y_dataColumn': current_y,
            'x_execution_column': x_execution_column,
            'y_execution_column': y_execution_column
        })

    return result


def visualizeExecution(execution, consist=None) -> dict:
    #  experiment status is assumed to be managed

    consistency = Consistency() if consist is None else consist

    for mapping in execution.experiment.experiment_interpreter.mappings.all():
        results = pairExecutionExperiment(execution=execution, mapping=mapping, consistency=consistency)

        for result in results:
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
                                     'title': (y_dataColumn.name if y_dataColumn.name else y_dataColumn.label) + y_name,
                                        'type': 'lin' if execution.experiment.experiment_type != 'ignition delay measurement' else 'log'})

            # ADD EXP

            exp_name = execution.experiment.fileDOI if y_dataColumn.name != 'composition' else execution.experiment.fileDOI + ' ' + y_dataColumn.label

            x_exp, y_exp = zip(*sorted(zip(x_exp, y_exp)))

            consistency.add_experimental(x_name=x_dataColumn.name,
                                         y_name=y_dataColumn.name,
                                         key=exp_name,
                                         result={'x': x_exp,
                                                 'y': y_exp if execution.experiment.experiment_type != 'ignition delay measurement' else [10**e for e in y_exp],
                                                 'type': 'scatter', 'mode': 'markers', 'marker': {'size': 10},
                                                 'name': exp_name})

            sim_name = execution.chemModel.name if y_dataColumn.name != 'composition' else execution.chemModel.name + ' ' + y_dataColumn.label

            x_sim, y_sim = zip(*sorted(zip(x_sim, y_sim)))

            # ADD SIM
            consistency.add_result(x_name=x_dataColumn.name,
                                   y_name=y_dataColumn.name,
                                   result={'x': x_sim,
                                           'y': y_sim if execution.experiment.experiment_type != 'ignition delay measurement' else [10**e for e in y_sim],
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

