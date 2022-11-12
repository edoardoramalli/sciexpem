# Local import
import FrontEnd.views as View
import ExperimentManager.Models as Models
import ExperimentManager.Serializers as Serializers

# Django import
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK

# System import
import json
from statistics import stdev, variance, mean, median, StatisticsError
import pandas as pd


class getFuelValidation(View.FrontEndBaseView):
    viewName = 'getFuelValidation'
    paramsType = {'chemModel_list': list}
    required_groups = {'POST': ['READ']}

    def view_post(self, request):

        flat_set = set([])

        for chemModel_id in self.chemModel_list:
            fuels = Models.CurveMatchingResult.objects.filter(execution_column__execution__chemModel__id=chemModel_id).values_list('execution_column__execution__experiment__fuels', flat=True).distinct()
            for f in fuels:
                flat_set.add(tuple(f))

        flat_list = set([frozenset(x) for x in flat_set])
        flat_list = [list(i) for i in flat_list]

        return Response(json.dumps(flat_list), status=HTTP_200_OK)

        # print(df)

        # xF = pd.ExcelFile('/home/eramalli/Report2.xlsx')

        # xF = pd.ExcelFile('/Users/edoardo/Documents/GitHub/sciexpem/LavoriVari/Validazione/Results/Report2.xlsx')

        # fuels = xF.sheet_names

        # diz = {fuel: [] for fuel in fuels}
        #
        # counter = 0
        #
        # for fuel in fuels:
        #     df = pd.read_excel(xF, fuel)
        #
        #     df = df.where(pd.notnull(df), 0)
        #
        #     for index, row in df.iterrows():
        #         counter += 1
        #         diz[fuel].append({
        #             'key': counter,
        #             'experiment_type': row['experiment_type'],
        #             'reactor': row['reactor'],
        #             'T': (row['t_inf'], row['t_sup']),
        #             'P': (row['p_inf'], row['p_sup']),
        #             'phi': (row['phi_inf'], row['phi_sup']),
        #             'mean_Model1': round(row['Model 1 - mean'], 3),
        #             'len_Model1': row['Model 1 - len'],
        #             'stdev_Model1': round(row['Model 1 - stdev'], 3),
        #             'mean_Model2': round(row['Model 2 - mean'], 3),
        #             'len_Model2': row['Model 2 - len'],
        #             'stdev_Model2': round(row['Model 2 - stdev'], 3),
        #             'exps_Model2': row['Model 2 - Exp'],
        #             'exps_Model1': row['Model 1 - Exp'],
        #         })
        #
        # return Response(json.dumps(diz), status=HTTP_200_OK)


