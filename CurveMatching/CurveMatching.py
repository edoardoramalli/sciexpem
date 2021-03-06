import os
import ExperimentManager.Models as Model
from ReSpecTh.units import convert
from CurveMatching.CurveMatchingPython import CurveMatching
from SciExpeM import settings
from ReSpecTh.Tool import pairExecutionExperiment, Consistency
from statistics import mean


def executeCurveMatching(x_exp, y_exp, x_sim, y_sim, uncertainty=[], **kwargs):
    library_path = os.path.join(settings.BASE_DIR, CurveMatching.__name__, "CurveMatchingPython.o")

    if not os.path.isfile(library_path):
        raise FileNotFoundError('CurveMatching executable not found.')

    x_exp = [float(e) for e in x_exp]
    y_exp = [float(e) for e in y_exp]
    x_sim = [float(e) for e in x_sim]
    y_sim = [float(e) for e in y_sim]
    uncertainty = [float(e) for e in uncertainty]

    score, error = CurveMatching.execute(
        x_exp=x_exp,
        y_exp=y_exp,
        x_sim=x_sim,
        y_sim=y_sim,
        uncertainty=uncertainty,
        verbose=False,
        library_path=library_path,
        **kwargs)

    return score, error


def curveMatchingExecution(current_execution):
    experiment = current_execution.experiment
    mappings_list = Model.MappingInterpreter.objects.filter(
        experiment_interpreter__name=experiment.experiment_interpreter)

    consistency = Consistency()

    for mapping in mappings_list:
        # file = mapping.file
        #
        # x_transformation = mapping.x_transformation
        # y_transformation = mapping.y_transformation
        #
        # # Lato Esperimento
        # x_exp_name = mapping.x_exp_name
        # x_exp_location = mapping.x_exp_location
        # y_exp_name = mapping.y_exp_name
        # y_exp_location = mapping.y_exp_location
        #
        # x_exp_params = {'experiment': experiment, x_exp_location: x_exp_name}
        # y_exp_params = {'experiment': experiment, y_exp_location: y_exp_name}
        # x_exp_dc = Model.DataColumn.objects.get(**x_exp_params)
        # y_exp_dc = Model.DataColumn.objects.get(**y_exp_params)
        #
        # x_exp_units = x_exp_dc.units
        # x_exp_data = x_exp_dc.data
        # x_exp_plotscale = x_exp_dc.plotscale
        #
        # y_exp_units = y_exp_dc.units
        # y_exp_data = y_exp_dc.data
        # y_exp_plotscale = y_exp_dc.plotscale
        #
        # # Lato Simulazione
        #
        # x_sim_name = mapping.x_sim_name
        # x_sim_location = mapping.x_sim_location
        # y_sim_name = mapping.y_sim_name
        # y_sim_location = mapping.y_sim_location
        #
        # x_sim_params = {'execution': current_execution, x_sim_location: x_sim_name, 'file_type': file}
        # y_sim_params = {'execution': current_execution, y_sim_location: y_sim_name, 'file_type': file}
        #
        # x_sim_ec = Model.ExecutionColumn.objects.get(**x_sim_params)
        # y_sim_ec = Model.ExecutionColumn.objects.get(
        #     **y_sim_params)  # ATTENZIONE è questa che verrà presa come rif per il CM
        #
        # x_sim_units = x_sim_ec.units
        # x_sim_data = x_sim_ec.data
        #
        # y_sim_units = y_sim_ec.units
        # y_sim_data = y_sim_ec.data
        #
        # # Converto x_axis nella stessa unità di misura e plotscale
        #
        # x_exp_data, x_sim_data = convert(list_a=x_exp_data, unit_a=x_exp_units,
        #                                  list_b=x_sim_data, unit_b=x_sim_units,
        #                                  plotscale=x_transformation)
        #
        # # Converto y_axis nella stessa unità di misura e plotscale
        #
        # y_exp_data, y_sim_data = convert(list_a=y_exp_data, unit_a=y_exp_units,
        #                                  list_b=y_sim_data, unit_b=y_sim_units,
        #                                  plotscale=y_transformation)
        #
        # # Provo ad invertire la conversione
        #
        # if not all(x >= 0 for x in x_exp_data) or not all(x >= 0 for x in x_sim_data) or \
        #         not all(x >= 0 for x in y_exp_data) or not all(x >= 0 for x in y_sim_data):
        #     x_exp_data, x_sim_data = convert(list_a=x_sim_data, unit_a=x_sim_units,
        #                                      list_b=x_exp_data, unit_b=x_exp_units,
        #                                      plotscale=x_transformation)
        #
        #     # Converto y_axis nella stessa unità di misura e plotscale
        #
        #     y_exp_data, y_sim_data = convert(list_a=y_sim_data, unit_a=y_sim_units,
        #                                      list_b=y_exp_data, unit_b=y_exp_units,
        #                                      plotscale=y_transformation)
        #
        # # Se sono negativo non applico la transformazione
        #
        # if not all(x >= 0 for x in x_exp_data) or not all(x >= 0 for x in x_sim_data) or \
        #         not all(x >= 0 for x in y_exp_data) or not all(x >= 0 for x in y_sim_data):
        #     x_exp_data, x_sim_data = convert(list_a=x_exp_data, unit_a=x_exp_units,
        #                                      list_b=x_sim_data, unit_b=x_sim_units,
        #                                      plotscale='lin')
        #
        #     # Converto y_axis nella stessa unità di misura e plotscale
        #
        #     y_exp_data, y_sim_data = convert(list_a=y_exp_data, unit_a=y_exp_units,
        #                                      list_b=y_sim_data, unit_b=y_sim_units,
        #                                      plotscale='lin')

        result = pairExecutionExperiment(execution=current_execution, mapping=mapping, consistency=consistency)

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

        # TODO non controlliamo se c'è incertezza

        score, error = executeCurveMatching(x_exp=x_exp, y_exp=y_exp, x_sim=x_sim, y_sim=y_sim)

        cm_result = Model.CurveMatchingResult(execution_column=y_execution_column, score=score, error=error)
        cm_result.save()


def getCurveMatching(query: dict) -> list:
    """
    Given a query about an experiment, returns the CM
    :type query: dict
    :rtype: list
    """

    cm_results = Model.CurveMatchingResult.objects.filter(**query).distinct()

    exp_cm = {}

    for result in cm_results:
        exp_doi = result.execution_column.execution.experiment.fileDOI
        model_name = result.execution_column.execution.chemModel.name
        execution_column_name = result.execution_column.label
        if exp_doi not in exp_cm:
            exp_cm[exp_doi] = {model_name: []}
        elif model_name not in exp_cm[exp_doi]:
            exp_cm[exp_doi][model_name] = []
        exp_cm[exp_doi][model_name].append(
            {'execution_column_name': execution_column_name, 'score': result.score, 'error': result.error})

    result = []

    for exp in exp_cm:
        tmp = []
        for model_name in exp_cm[exp]:
            avg_score = mean([diz['score'] for diz in exp_cm[exp][model_name]])
            avg_score_error = mean([diz['error'] for diz in exp_cm[exp][model_name]])
            tmp.append({
                'name': model_name,
                'score': float(avg_score),
                'error': float(avg_score_error),
                'details': exp_cm[exp][model_name]
            })
        result.append({'fileDOI': exp, 'models': tmp})

    return result
