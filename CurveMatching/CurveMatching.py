import os
import ExperimentManager.Models as Model
from ReSpecTh.units import convert
from CurveMatching.CurveMatchingPython import CurveMatching
from SciExpeM import settings
from ReSpecTh.Tool import pairExecutionExperiment, Consistency
from statistics import mean


import threading
lock = threading.Lock()

running_cm = False


def blocking_execute_cm(**kwargs):
    with lock:
        r = executeCurveMatching(**kwargs)
    return r


def executeCurveMatching(x_exp, y_exp, x_sim, y_sim, uncertainty=[], **kwargs):
    library_path = os.path.join(settings.BASE_DIR, CurveMatching.__name__, "CurveMatchingPython.o")

    if not os.path.isfile(library_path):
        raise FileNotFoundError('CurveMatching executable not found.')

    if len(x_exp) > settings.CM_POINTS or len(x_sim) > settings.CM_POINTS:
        raise ValueError('Too many values to compute curve matching')

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
    try:
        # if current_execution.execution_end is None or current_execution.execution_error is not None:
        #     raise ValueError('Execution ({}) not ended or with errors.'.format(current_execution.id))
        if len(current_execution.execution_columns.all()) <= 1:
            raise ValueError('Execution ({}) not enough columns.'.format(current_execution.id))
        if any(ll > 1000 for ll in [len(c.data) for c in current_execution.execution_columns.all()]):
            print('pipppooo')
            raise ValueError('Compute Curve Matching: Execution ({}) with too many data.')
    except ValueError as e:
        print('eoooooo', e)
        c_text = current_execution.execution_error
        if c_text:
            c_text += '\n' + str(e)
        else:
            c_text = str(e)
        current_execution.execution_error = c_text
        current_execution.save()
        return

    experiment = current_execution.experiment
    mappings_list = experiment.experiment_interpreter.mappings.all()

    consistency = Consistency()

    for mapping in mappings_list:

        results = pairExecutionExperiment(execution=current_execution, mapping=mapping, consistency=consistency)

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

            if y_dataColumn.uncertainty_reference:
                uncertainty_data = y_dataColumn.uncertainty_reference.data
                if y_dataColumn.uncertainty_kind == 'absolute':
                    uncertainty_data = [float(e) / float(y_exp[index]) for index, e in enumerate(uncertainty_data)]
            else:
                uncertainty_data = []

            indexes = blocking_execute_cm(x_exp=x_exp, y_exp=y_exp,
                                          x_sim=x_sim, y_sim=y_sim,
                                          uncertainty=uncertainty_data,
                                          numberOfBootstrapVariations=80,
                                          possibleNegativeOrdinates=True)

            values = {'score': indexes['score'],
                      'error': indexes['error'],
                      'd0L2': indexes['d0L2'],
                      'd1L2': indexes['d1L2'],
                      'd0Pe': indexes['d0Pe'],
                      'd1Pe': indexes['d1Pe'],
                      'shift': indexes['shift']}

            # Attenzione stiamo sbagliando la media:
            # Se un dato sperimentale della composizione è la somma di due o più specie
            # ma il modello li da singoli, noi dobbiamo fare la somma e poi fare il cm con questa
            # ma dopo a chi lo do il cm? il cm viene associato ad una executionColumn.
            # La mia policy è che lo stesso valore è associato a tutte le colonne execution coinvolte però falsi
            # le indagini statistiche in qualche modo però anche il fatto che loro misurano più specie insieme
            # è falsato
            # Diciamo che il numero di cmresults per una singola esecuzione può essere maggiore rispetto al numero di
            # datacolumns
            for exec_column in y_execution_column:
                cm_result, created = Model.CurveMatchingResult.objects.update_or_create(defaults=values,
                                                                                        execution_column=exec_column)

            #sleep(0.5)  # qualche volta da errore in malloc forse perchè è troppo veloce a rilasciare la memoria?


def getCurveMatching(query: dict) -> list:
    """
    Given a query about an experiment, returns the CM
    :type query: dict
    :rtype: list
    """

    cm_results = Model.CurveMatchingResult.objects.filter(**query).distinct().values(
        'score', 'error', 'd0L2', 'd1L2', 'd0Pe', 'd1Pe', 'shift',
        'execution_column__execution__experiment__fileDOI',
        'execution_column__execution__chemModel__name',
        'execution_column__label',
        'execution_column__execution__experiment__id'
    )

    # print(cm_results)
    #
    # return {}

    exp_cm = {}

    for result in cm_results:
        exp_doi = result['execution_column__execution__experiment__fileDOI']
        model_name = result['execution_column__execution__chemModel__name']
        execution_column_name = result['execution_column__label']
        exp_id = result['execution_column__execution__experiment__id']
        score = round(result['score'], 5)
        error = round(result['error'], 5)
        d0L2 = round(result['d0L2'], 5)
        d1L2 = round(result['d1L2'], 5)
        d0Pe = round(result['d0Pe'], 5)
        d1Pe = round(result['d1Pe'], 5)
        shift = round(result['shift'], 5)
        if exp_doi not in exp_cm:
            exp_cm[exp_doi] = {'id': exp_id, 'models': {model_name: []}}
        elif model_name not in exp_cm[exp_doi]['models']:
            exp_cm[exp_doi]['models'][model_name] = []
        exp_cm[exp_doi]['models'][model_name].append(
            {'execution_column_name': execution_column_name,
             'score': score,
             'error': error,
             'd0L2': d0L2,
             'd1L2': d1L2,
             'd0Pe': d0Pe,
             'd1Pe': d1Pe,
             'shift': shift,
             })

    result = []

    for exp in exp_cm:
        tmp = []
        for model_name in exp_cm[exp]['models']:
            avg_score = mean([diz['score'] for diz in exp_cm[exp]['models'][model_name]])
            avg_score_error = mean([diz['error'] for diz in exp_cm[exp]['models'][model_name]])
            avg_score_d0L2 = mean([diz['d0L2'] for diz in exp_cm[exp]['models'][model_name]])
            avg_score_d1L2 = mean([diz['d1L2'] for diz in exp_cm[exp]['models'][model_name]])
            avg_score_d0Pe = mean([diz['d0Pe'] for diz in exp_cm[exp]['models'][model_name]])
            avg_score_d1Pe = mean([diz['d1Pe'] for diz in exp_cm[exp]['models'][model_name]])
            avg_score_shift = mean([diz['shift'] for diz in exp_cm[exp]['models'][model_name]])
            tmp.append({
                'name': model_name,
                'score': round(float(avg_score), 5),
                'error': round(float(avg_score_error), 5),
                'd0L2': round(float(avg_score_d0L2), 5),
                'd1L2': round(float(avg_score_d1L2), 5),
                'd0Pe': round(float(avg_score_d0Pe), 5),
                'd1Pe': round(float(avg_score_d1Pe), 5),
                'shift': round(float(avg_score_shift), 5),
                'details': exp_cm[exp]['models'][model_name]
            })
        result.append({'id': exp_cm[exp]['id'], 'fileDOI': exp, 'models': tmp})

    return result
