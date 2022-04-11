# Local import
import FrontEnd.views as View
import ExperimentManager.Models as Models
import ExperimentManager.Serializers as Serializers
from OpenSmoke.SimulationSummary.createSummary import create_summary
from OpenSmoke.SimulationSummary.processSummary import process_summary

# Django import
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK

# System import
import json
import numpy as np
import pandas as pd
from tqdm import tqdm
from statistics import stdev, variance, mean, median, StatisticsError

from scipy import integrate

import math

#
# def zip_order(xx, yy):
#     zz = dict(sorted(zip(xx, yy)))
#     return list(zz.keys()), list(zz.values())
#
#
# def domain_intersection(a_inf, a_sup, b_inf, b_sup):
#     aa = set(list(np.arange(math.floor(a_inf), math.floor(a_sup), 1)))
#     bb = set(list(np.arange(math.floor(b_inf), math.floor(b_sup), 1)))
#     intersection = aa.intersection(bb)
#     return min(intersection), max(intersection)
#

def merge_dict(diz1, diz2):
    # merfe dict 2 into dict 1
    for x in diz2:
        if x not in diz1:
            diz1[x] = diz2[x]
        else:
            for y in diz2[x]:
                if y not in diz1[x]:
                    diz1[x][y] = diz2[x][y]
                else:
                    diz1[x][y] = {**diz1[x][y], **diz2[x][y]}
    return diz1


def generate_df(diz):
    ticks = list(diz.keys())
    result = {'Interval': [], 'Avg': [], 'StDev': [], 'Count': []}

    # print(diz)

    for index in range(0, len(ticks)):

        if len(diz[ticks[index]]) > 0:
            media = mean(diz[ticks[index]])
        else:
            media = 1

        if len(diz[ticks[index]]) > 1:
            dev = stdev(diz[ticks[index]])
        else:
            dev = 0

        result['Interval'].append(ticks[index])
        result['Avg'].append(media)
        result['StDev'].append(dev)
        result['Count'].append(len(diz[ticks[index]]))

    df = pd.DataFrame.from_dict(result)
    return df


class getIntervalAnalysis(View.FrontEndBaseView):
    viewName = 'getIntervalAnalysis'
    paramsType = {'query': dict, 'chemModel_id': int}
    required_groups = {'POST': ['READ']}

    def view_post(self, request):

        default = {'execution_column__execution__experiment__status': 'verified'}

        new = {**default, **self.query}

        # print(self.query, self.chemModel_id)

        exps = Models.CurveMatchingResult.objects.filter(**new).values_list(
            'execution_column__execution__experiment__id', flat=True).distinct()



        chemModel = Models.ChemModel.objects.get(id=self.chemModel_id)

        domains = {chemModel.name: {}}

        details = {}

        # return Response(json.dumps(a), status=HTTP_200_OK)

        r = {}

        for exp_id in exps:
            # Given an Exp return all the pairs for each simulated model
            # if exp_id !=1058:
            #     continue
            current_summary = create_summary(exp_id)

            current_result = process_summary(exp_id=exp_id, current_summary=current_summary, domain_list=domains)

            r = merge_dict(r, current_result)


        #     for x_name in current_result:
        #         if x_name not in details:
        #             details[x_name] = {}
        #
        #         for subject in current_result[x_name]:
        #             if subject not in details[x_name]:
        #                 details[x_name][subject] = {}
        #
        #             # print(exp_id, x_name, subject)
        #
        #             df = current_result[x_name][subject].where(pd.notnull(current_result[x_name][subject]), -1)
        #
        #             # df["Area Exp Inter"] = df.Value.astype(float)
        #             # df["Area Sim Inter"] = df.Value.astype(float)
        #             # df["Weight Exp Inter"] = df.Value.astype(float)
        #             # df["Weight Sim Inter"] = df.Value.astype(float)
        #             # df["Real"] = df.Real.astype(float)
        #             # df["Value"] = df.Value.astype(float)
        #
        #             df = df.astype({'Area Exp Inter': float,
        #                             'Area Sim Inter': float,
        #                             'Weight Exp Inter': float,
        #                             'Weight Sim Inter': float,
        #                             'Real': float,
        #                             'Value': float,
        #                             })
        #
        #             # print(df.dtypes)
        #
        #             df = df.round({'Area Exp Inter': 3,
        #                            'Area Sim Inter': 3,
        #                            'Weight Exp Inter': 3,
        #                            'Weight Sim Inter': 3,
        #                            'Real': 3,
        #                            'Value': 3,
        #                            })
        #
        #             details[x_name][subject][exp_id] = df.to_dict('records')
        #
        #
        #
        # result = {}
        # # TODO ASSUNZIONE UN SOLO MODELLO ALLA VOLTA
        # current_model = chemModel.name
        #
        # for x_name in domains[current_model]:
        #     if x_name not in result:
        #         result[x_name] = {}
        #
        #     for subject in domains[current_model][x_name]:
        #         if subject not in details[x_name]:
        #             continue
        #         if subject not in result[x_name]:
        #             result[x_name][subject] = {}
        #
        #         lunghezza = len(domains[current_model][x_name][subject].x_p)
        #
        #         freq_sovrastima = np.zeros(lunghezza)
        #         freq_sottostima = np.zeros(lunghezza)
        #
        #         ticks_sottostima = np.zeros(lunghezza)
        #         ticks_sovrastima = np.zeros(lunghezza)
        #
        #         # for index, model_name in enumerate(domains):
        #         #     # print(domains[domain][subject].x)
        #
        #         df_sovrastima = generate_df(diz=domains[current_model][x_name][subject].x_p)
        #         df_sottostima = generate_df(diz=domains[current_model][x_name][subject].x_n)
        #
        #         ticks_sovrastima = df_sovrastima['Interval']
        #         ticks_sottostima = df_sottostima['Interval']
        #
        #         freq_sottostima = np.maximum(freq_sottostima, df_sottostima['Count'])
        #         freq_sovrastima = np.maximum(freq_sottostima, df_sovrastima['Count'])
        #
        #         result[x_name][subject]['sovrastima'] = {'x': list(df_sovrastima['Interval']),
        #                                                  'y': list(df_sovrastima['Avg']),
        #                                                  'error_y': list(df_sovrastima['StDev']),
        #                                                  'count': list(freq_sovrastima)}
        #
        #         result[x_name][subject]['sottostima'] = {'x': list(df_sottostima['Interval']),
        #                                                  'y': list(df_sottostima['Avg']),
        #                                                  'error_y': list(df_sottostima['StDev']),
        #                                                  'count': list(freq_sottostima)}
        #         result[x_name][subject]['details'] = details[x_name][subject]

        # return Response(result, status=HTTP_200_OK)

        return Response(r, status=HTTP_200_OK)
