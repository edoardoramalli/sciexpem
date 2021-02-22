import os
import traceback
import ExperimentManager.Models as Model
from . import CurveMatchingPython
from django.db import transaction

from ReSpecTh.units import convert




class CurveMatchingExecutor():
    def __init__(self, curve_matching_path):
        self.curve_matching_path = curve_matching_path
        # self.curve_matching = CurveMatchingPython.CurveMatchingPython("/Users/edoardo/Documents/GitHub/sciexpem/experimentmanager/CurveMatchingPython.o")
        self.curve_matching = CurveMatchingPython(
            "/Users/edoardo/PycharmProjects/SciExpeM/CurveMatching/CurveMatchingPython.o")
        # TODO FIX ABS PATH

    def execute_CM(self, execution_column_x, execution_column_y):
        execution = execution_column_x.execution
        experiment = execution.experiment

        if models.CurveMatchingResult.objects.filter(execution=execution).exists():
            return

        # X,Y Execution column come from the same execution
        if execution_column_x.execution != execution_column_y.execution:
            return

        # Check if curve matching is already computed
        if models.CurveMatchingResult.objects.filter(execution=execution).exists():
            return

        try:

            data_column_exp_x = models.DataColumn.objects.filter(experiment=experiment,
                                                                 name="temperature")[0]
            data_column_exp_x = data_column_exp_x.data

            data_column_exp_y = models.DataColumn.objects.filter(experiment=experiment,
                                                                 name="ignition delay")[0]
        except IndexError:
            # print("Experiment PK", experiment.pk, "Not found temperature or IDT")
            return

        data_column_exp_unit_y = data_column_exp_y.units

        data_column_exp_y = data_column_exp_y.data

        if data_column_exp_unit_y == "us":
            factor = 1e+06
        elif data_column_exp_unit_y == "ms":
            factor = 1e+03
        else:
            raise ValueError("Errore unità misura:", data_column_exp_unit_y)

        execution_column_sim_x = execution_column_x.data
        execution_column_sim_y = execution_column_y.data

        data_column_exp_x = [float(item) for item in data_column_exp_x]
        data_column_exp_y = [float(item) for item in data_column_exp_y]
        execution_column_sim_x = [float(item) for item in execution_column_sim_x]
        execution_column_sim_y = [float(item) * factor for item in execution_column_sim_y]

        score, error = self.curve_matching.execute(x_exp=data_column_exp_x,
                                                   y_exp=data_column_exp_y,
                                                   x_sim=execution_column_sim_x,
                                                   y_sim=execution_column_sim_y,
                                                   verbose=False)
        try:
            with transaction.atomic():

                curve_matching_result = models.CurveMatchingResult(execution=execution,
                                                                   index=score,
                                                                   error=error)

                curve_matching_result.save()
        except Exception as err:
            print(traceback.format_exc())

    # def __execute(self):
    #     command = os.path.join(self.curve_matching_path, r"Curve Matching.exe")
    #     out = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True,
    #                          cwd=self.curve_matching_path)
    #     return out

    # def extract_CM_results(self):
    #     path = os.path.join(self.curve_matching_path, 'Results', '*Kmatrix*.csv')
    #     path = glob.glob(path)[0]
    #     df = pd.read_csv(path, header=[0, 1], index_col=0)
    #     columns = pd.DataFrame(df.columns.tolist())
    #     columns.loc[columns[0].str.startswith('Unnamed:'), 0] = np.nan
    #     columns[0] = columns[0].fillna(method='ffill')
    #     df.columns = pd.MultiIndex.from_tuples(columns.to_records(index=False).tolist())
    #     return df

    # # for an experiment and a set of models (default: all the available models for the experiment)
    # # returns a list [(e1, m1), (e2, m2), ...] of experiment/model dataframes as needed for CurveMatching
    # def get_CM_dataframes(self, exp_id, target_models=None):
    #     exp_table = get_experiment_table(exp_id)
    #     models_table = get_models_table(exp_id, target_models=target_models)
    #
    #     r = []
    #     x_axis = exp_table.columns[0]
    #     for i in range(1, len(exp_table.columns)):
    #         column = exp_table.columns[i]
    #
    #         columns_exp = exp_table[[x_axis, column]]
    #
    #         mc = [c for c in models_table.columns if c.startswith(x_axis + "_") or c.startswith(column + "_")]
    #
    #         columns_mod = models_table[mc]
    #
    #         r.append((columns_exp, columns_mod))
    #     return r

    # def flush_output_folder(self):
    #     shutil.rmtree(self.output_path)
    #     os.makedirs(self.output_path)

    # def write_CM_dataframes(self, dataframes):
    #     for i in dataframes:
    #         name = i[0].columns[1]
    #         i[0].to_csv(os.path.join(self.output_path, name + "_exp.txt"), sep="\t", index=False)
    #         i[1].to_csv(os.path.join(self.output_path, name + "_mod.txt"), sep="\t", index=False)

    def store_results(self, r, exp_id):
        for index, row in r.iterrows():
            ecs = Model.ExecutionColumn.objects.filter(execution__chemModel__name=index, execution__experiment=exp_id)

            for d in ecs:
                name = d.name.replace(" ", "-") if d.species is None else d.species[0]
                if name in row:
                    index, error = row[name]['Index'], row[name]['Error']
                    cm = Model.CurveMatchingResult(index=index, error=error, execution_column=d)
                    cm.save()


def execute_curve_matching_django(execution):
    t0 = Model.ExecutionColumn.objects.filter(execution=execution, label="T0")[0]
    try:
        slope = Model.ExecutionColumn.objects.filter(execution=execution, label="tau_T(slope)")[0]
    except IndexError:
        # print("Error Exec PK", execution.pk)
        return

    curve_matching_executor = CurveMatchingExecutor("path")
    curve_matching_executor.execute_CM(execution_column_x=t0, execution_column_y=slope)


from CurveMatching.CurveMatchingPython import CurveMatching
from SciExpeM import settings


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
    mappings_list = Model.MappingInterpreter.objects.filter(experiment_interpreter__name=experiment.experiment_interpreter)

    for mapping in mappings_list:
        file = mapping.file

        x_transformation = mapping.x_transformation
        y_transformation = mapping.y_transformation

        # Lato Esperimento
        x_exp_name = mapping.x_exp_name
        x_exp_location = mapping.x_exp_location
        y_exp_name = mapping.y_exp_name
        y_exp_location = mapping.y_exp_location

        x_exp_params = {'experiment': experiment, x_exp_location: x_exp_name}
        y_exp_params = {'experiment': experiment, y_exp_location: y_exp_name}
        x_exp_dc = Model.DataColumn.objects.get(**x_exp_params)
        y_exp_dc = Model.DataColumn.objects.get(**y_exp_params)

        x_exp_units = x_exp_dc.units
        x_exp_data = x_exp_dc.data
        x_exp_plotscale = x_exp_dc.plotscale

        y_exp_units = y_exp_dc.units
        y_exp_data = y_exp_dc.data
        y_exp_plotscale = y_exp_dc.plotscale

        # Lato Simulazione

        x_sim_name = mapping.x_sim_name
        x_sim_location = mapping.x_sim_location
        y_sim_name = mapping.y_sim_name
        y_sim_location = mapping.y_sim_location

        x_sim_params = {'execution': current_execution, x_sim_location: x_sim_name, 'file_type': file}
        y_sim_params = {'execution': current_execution, y_sim_location: y_sim_name, 'file_type': file}

        x_sim_ec = Model.ExecutionColumn.objects.get(**x_sim_params)
        y_sim_ec = Model.ExecutionColumn.objects.get(**y_sim_params) # ATTENZIONE è questa che verrà presa come rif per il CM

        x_sim_units = x_sim_ec.units
        x_sim_data = x_sim_ec.data

        y_sim_units = y_sim_ec.units
        y_sim_data = y_sim_ec.data

        # Converto x_axis nella stessa unità di misura e plotscale

        x_exp_data, x_sim_data = convert(list_a=x_exp_data, unit_a=x_exp_units,
                                         list_b=x_sim_data, unit_b=x_sim_units,
                                         plotscale=x_transformation)

        # Converto y_axis nella stessa unità di misura e plotscale

        y_exp_data, y_sim_data = convert(list_a=y_exp_data, unit_a=y_exp_units,
                                         list_b=y_sim_data, unit_b=y_sim_units,
                                         plotscale=y_transformation)

        # Provo ad invertire la conversione

        if not all(x >= 0 for x in x_exp_data) or not all(x >= 0 for x in x_sim_data) or \
            not all(x >= 0 for x in y_exp_data) or not all(x >= 0 for x in y_sim_data):

            x_exp_data, x_sim_data = convert(list_a=x_sim_data, unit_a=x_sim_units,
                                             list_b=x_exp_data, unit_b=x_exp_units,
                                             plotscale=x_transformation)

            # Converto y_axis nella stessa unità di misura e plotscale

            y_exp_data, y_sim_data = convert(list_a=y_sim_data, unit_a=y_sim_units,
                                             list_b=y_exp_data, unit_b=y_exp_units,
                                             plotscale=y_transformation)

        # Se sono negativo non applico la transformazione

        if not all(x >= 0 for x in x_exp_data) or not all(x >= 0 for x in x_sim_data) or \
            not all(x >= 0 for x in y_exp_data) or not all(x >= 0 for x in y_sim_data):
            x_exp_data, x_sim_data = convert(list_a=x_exp_data, unit_a=x_exp_units,
                                             list_b=x_sim_data, unit_b=x_sim_units,
                                             plotscale='lin')

            # Converto y_axis nella stessa unità di misura e plotscale

            y_exp_data, y_sim_data = convert(list_a=y_exp_data, unit_a=y_exp_units,
                                             list_b=y_sim_data, unit_b=y_sim_units,
                                             plotscale='lin')


        # TODO non controlliamo se c'è incertezza

        score, error = executeCurveMatching(x_exp=x_exp_data, y_exp=y_exp_data, x_sim=x_sim_data, y_sim=y_sim_data)

        cm_result = Model.CurveMatchingResult(execution_column=y_sim_ec, score=score, error=error)
        cm_result.save()

