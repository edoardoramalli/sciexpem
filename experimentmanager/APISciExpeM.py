import django
import os
import pandas as pd

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SciExpeM.settings")
django.setup()

from experimentmanager import models
from django.db import transaction


class APISciExpeM:
    def __init__(self, username, password):
        import datetime

        print("--> Authenticated as", username, "Time:", datetime.datetime.now())

    def importModelOS(self, path, verbose):
        dirs = [folder for folder in os.listdir(path) if os.path.isdir(os.path.join(path, folder, "kinetics"))]
        counter = 0

        for f in dirs:
            try:
                with transaction.atomic():

                    name = f
                    model_path = os.path.join(path, name, "kinetics")

                    kinetics_file = os.path.join(model_path, "kinetics.xml")
                    reaction_names_file = os.path.join(model_path, "reaction_names.xml")

                    if not os.path.isfile(kinetics_file):
                        if verbose:
                            print("Folder", model_path, "does not contains kinetics.xml")
                        continue

                    if not os.path.isfile(reaction_names_file):
                        if verbose:
                            print("Folder", model_path, "does not contains reaction_names.xml")
                        continue

                    xml_file_kinetics = open(kinetics_file).read()
                    xml_file_reaction_names = open(reaction_names_file).read()

                    # Check duplicates
                    if models.ChemModel.objects.filter(name=name).exists():
                        # print("DUPLICATE MODEL: ", name)
                        continue

                    chemModel = models.ChemModel(name=name,
                                                 xml_file_kinetics=xml_file_kinetics,
                                                 xml_file_reaction_names=xml_file_reaction_names)
                    chemModel.save()

                counter += 1

            except Exception as err:
                print(f)

        if verbose:
            print("Imported Models: {}/{}".format(counter, len(dirs)))

    def importExperimentInputOS(self, path, verbose=False):
        import glob
        from opensmoke import OpenSmokeParser
        if os.path.isfile(path):
            input_files = [path]
        else:
            input_files = glob.glob(path + '/**/*.xml.dic', recursive=True)

        counter = 0

        for file in input_files:
            experiment_name = file[file.rfind("/") + 1:].replace(".xml.dic", "")
            try:
                with transaction.atomic():

                    related_experiment = models.Experiment.objects.filter(fileDOI__contains=experiment_name)

                    if not related_experiment:
                        # print("Related Experiment not found:", experiment_name)
                        continue
                    else:
                        related_experiment = related_experiment[0]

                    # Check duplicates
                    if models.OpenSmokeInput.objects.filter(experiment=related_experiment).exists():
                        # print("Duplicate OpenSmoke Input: ", experiment_name)
                        continue

                    file_string = OpenSmokeParser.parse_input(file)

                    OpenSmokeInput = models.OpenSmokeInput(experiment=related_experiment, file=file_string)
                    OpenSmokeInput.save()

                counter += 1

            except Exception as err:
                print(file)
        if verbose:
            print("Imported OpenSmoke Input: {}/{}".format(counter, len(input_files)))


    def importExperiment(self, path, verbose=False):
        import glob
        from respecth import ReSpecTh
        if os.path.isfile(path):
            respecth_files = [path]
        else:
            respecth_files = glob.glob(path + '/**/*.xml', recursive=True)
        counter = 0
        if verbose:
            print("Imported ReSpecTh Files: {}/{}".format(counter, len(respecth_files)), end="")
        for index, f in enumerate(respecth_files):
            try:
                with transaction.atomic():
                    r = ReSpecTh.from_file(f)

                    initial_composition = r.initial_composition()
                    reactor = r.apparatus
                    experiment_type = r.experiment_type
                    fileDOI = r.fileDOI

                    # check duplicates
                    if models.Experiment.objects.filter(fileDOI=fileDOI).exists():
                        # print("DUPLICATE: ", fileDOI)
                        continue

                    it = r.get_ignition_type()
                    o = None
                    if it is not None:
                        o = it.attrib.get("target") + " " + it.attrib.get("type")

                    paper = models.FilePaper(title=r.getBiblio())
                    paper.save()

                    xml_file = open(f).read()

                    e = models.Experiment(reactor=reactor, experiment_type=experiment_type, fileDOI=fileDOI,
                                          ignition_type=o,
                                          file_paper=paper, temp=False, xml_file=xml_file)
                    e.save()


                    columns_groups = r.extract_columns_multi_dg()
                    for g in columns_groups:
                        for c in g:
                            co = models.DataColumn(experiment=e, **c)
                            co.save()

                    common_properties = r.common_properties()
                    for c in common_properties:
                        cp = models.CommonProperty(experiment=e, **c)
                        cp.save()

                    initial_species = r.initial_composition()
                    for i in initial_species:
                        ip = models.InitialSpecie(experiment=e, **i)
                        ip.save()

                counter += 1
                if verbose:
                    print("\rImported ReSpecTh Files: {}/{}".format(counter, len(respecth_files)), end="")

            except Exception as err:
                print(err)
                pass
        print("")
        return

    def printExperiment(self, list_experiments):
        for exp in list_experiments:
            print("Experiment:", exp.fileDOI)

    def getExperiment(self, **kwargs):
        query = models.Experiment.objects.filter(**kwargs)
        return query

    def getExperimentData(self, experiment):
        df = pd.DataFrame()
        data_columns = experiment.data_columns.all()
        import pint_pandas
        PA_ = pint_pandas.PintArray
        for column in data_columns:
            df[column.name] = PA_(column.data, dtype=column.units)

        return df

    def getModel(self, **kwargs):
        if kwargs is not None:
            query = models.ChemModel.objects.filter(**kwargs)
        else:
            query = models.ChemModel.objects.all()
        return query

    def printModel(self, list_model):
        for model in list_model:
            print("Model:", model.name)

    def executeOS(self, experiment, model):
        from opensmoke import OpenSmokeExecutor
        for m in model:
            for exp in experiment:
                OpenSmokeExecutor.execute(exp, m)

    def getExecution(self, **kwargs):
        query = models.Execution.objects.filter(**kwargs)
        return query

    def getExecutionData(self, execution):
        df = pd.DataFrame()
        data_columns = execution.execution_columns.all()
        import pint_pandas
        from pint import UnitRegistry
        SI = UnitRegistry()
        # TODO FIX PATH
        SI.load_definitions('/Users/edoardo/Documents/GitHub/sciexpem/experimentmanager/units.def')
        PA_ = pint_pandas.PintArray
        pint_pandas.PintType.ureg = SI

        for column in data_columns:
            df[column.label] = PA_(column.data, dtype=SI(column.units).units)

        return df

    def executeCM(self, verbose=False):
        from curve_matching import execute_curve_matching_django

        executions = models.Execution.objects.all()
        if verbose:
            print("Execute CM: {}/{}".format(0, len(executions)), end="")
        for index, exec in enumerate(executions):
            if verbose:
                print("\rExecute CM: {}/{}".format(index + 1, len(executions)), end="")
            execute_curve_matching_django(exec)
        if verbose:
            print("")

    def comparePlot(self, experiment):
        respecth_data = self.getExperimentData(experiment)

        import plotly.graph_objects as go
        fig = go.Figure()


        # ReSpecTh Plot
        fig.add_trace(go.Scatter(x=[float(i.magnitude) for i in respecth_data["temperature"]],
                                 y=[float(i.magnitude) for i in respecth_data["ignition delay"]],
                                 name='ReSpecTh',
                                 mode='markers',
                                 line=dict(color='firebrick', width=4)))

        # Get All execution of this experiment

        executions = models.Execution.objects.filter(experiment=experiment)

        for exec in executions:
            temp = models.ExecutionColumn.objects.get(execution=exec, label="T0")
            slope = models.ExecutionColumn.objects.get(execution=exec, label="tau_T(slope)")
            fig.add_trace(go.Scatter(x=[float(i) for i in temp.data],
                                     y=[float(i) * 1e+06 for i in slope.data],
                                     name=exec.chemModel.name,
                                     line = dict(dash='dash')))

        fig.update_layout(title=experiment.fileDOI,
                          yaxis_title='IDT [us]',
                          xaxis_title='T0 [k]')

        fig.show()


    def getOutliner(self, verbose=False):
        from django.db.models import Q
        result_CM = models.CurveMatchingResult.objects.filter(~(Q(index=float(-1)) | Q(index=float(-2)) | Q(index=float(-3))))

        experiment = models.Experiment.objects.all()

        results = {}

        for exp in experiment:
            CRECK_2003_H2 = result_CM.filter(execution__experiment=exp, execution__chemModel__name="CRECK_2003_H2")
            CRECK_1412_H2 = result_CM.filter(execution__experiment=exp, execution__chemModel__name="CRECK_1412_H2")
            if len(CRECK_1412_H2) + len(CRECK_2003_H2) == 2:
                results[exp.fileDOI] = (CRECK_2003_H2[0].index, CRECK_1412_H2[0].index)

        variations = {}

        for result in results:
            var = (results[result][0] - results[result][1]) / results[result][1] * 100
            variations[result] = var

        # print(variations)

        import plotly.figure_factory as ff

        x = [round(abs(float(i)), 3) for i in variations.values()]
        # print(x)
        hist_data = [[0.747, 0.497, 0.454, 0.147, 6.827, 0.723, 0.593, 0.772, 1.061, 55.036, 1.084, 10.485, 1.32, 2.542, 1.761, 7.772, 4.197, 0.106, 5.044, 2.579, 1.712, 0.849, 23.016, 15.921]
]
        group_labels = ['distplot']  # name of the dataset

        print(hist_data)

        fig = ff.create_distplot(hist_data, group_labels, bin_size=5, rug_text=[list(variations.keys())])
        fig.show()







