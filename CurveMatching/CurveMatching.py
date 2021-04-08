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

    indexes = CurveMatching.execute(
        x_exp=x_exp,
        y_exp=y_exp,
        x_sim=x_sim,
        y_sim=y_sim,
        uncertainty=uncertainty,
        verbose=False,
        library_path=library_path,
        **kwargs)

    return indexes


def curveMatchingExecution(current_execution):
    experiment = current_execution.experiment
    mappings_list = experiment.experiment_interpreter.mappings.all()

    consistency = Consistency()

    for mapping in mappings_list:

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

        indexes = executeCurveMatching(x_exp=x_exp, y_exp=y_exp, x_sim=x_sim, y_sim=y_sim)

        cm_result = Model.CurveMatchingResult(execution_column=y_execution_column,
                                              score=indexes['score'],
                                              error=indexes['error'],
                                              d0L2=indexes['d0L2'],
                                              d1L2=indexes['d1L2'],
                                              d0Pe=indexes['d0Pe'],
                                              d1Pe=indexes['d1Pe'],
                                              shift=indexes['shift'])

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
            {'execution_column_name': execution_column_name,
             'score': result.score,
             'error': result.error,
             'd0L2': result.d0L2,
             'd1L2': result.d1L2,
             'd0Pe': result.d0Pe,
             'd1Pe': result.d1Pe,
             'shift': result.shift,
             })

    result = []

    for exp in exp_cm:
        tmp = []
        for model_name in exp_cm[exp]:
            avg_score = mean([diz['score'] for diz in exp_cm[exp][model_name]])
            avg_score_error = mean([diz['error'] for diz in exp_cm[exp][model_name]])
            avg_score_d0L2 = mean([diz['d0L2'] for diz in exp_cm[exp][model_name]])
            avg_score_d1L2 = mean([diz['d1L2'] for diz in exp_cm[exp][model_name]])
            avg_score_d0Pe = mean([diz['d0Pe'] for diz in exp_cm[exp][model_name]])
            avg_score_d1Pe = mean([diz['d1Pe'] for diz in exp_cm[exp][model_name]])
            avg_score_shift = mean([diz['shift'] for diz in exp_cm[exp][model_name]])
            tmp.append({
                'name': model_name,
                'score': float(avg_score),
                'error': float(avg_score_error),
                'd0L2': float(avg_score_d0L2),
                'd1L2': float(avg_score_d1L2),
                'd0Pe': float(avg_score_d0Pe),
                'd1Pe': float(avg_score_d1Pe),
                'shift': float(avg_score_shift),
                'details': exp_cm[exp][model_name]
            })
        result.append({'fileDOI': exp, 'models': tmp})

    return result
