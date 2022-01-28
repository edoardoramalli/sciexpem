# Local import
import FrontEnd.views as View
import ExperimentManager.Models as Models
import ExperimentManager.Serializers as Serializers
from ExperimentManager.Views.getSimulation import create_summary

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
from SplinePoliMi import Spline
import math


def zip_order(xx, yy):
    zz = dict(sorted(zip(xx, yy)))
    return list(zz.keys()), list(zz.values())


def domain_intersection(a_inf, a_sup, b_inf, b_sup):
    aa = set(list(np.arange(math.floor(a_inf), math.floor(a_sup), 1)))
    bb = set(list(np.arange(math.floor(b_inf), math.floor(b_sup), 1)))
    intersection = aa.intersection(bb)
    return min(intersection), max(intersection)


class Store:

    def __init__(self):
        self.couple = {}

    def add(self, pair, value):
        if pair in self.couple:
            self.couple[pair].append(value)
        elif (pair[1], pair[0]) in self.couple:
            self.couple[(pair[1], pair[0])].append(1 / value)
        else:
            self.couple[pair] = [value]


class Domain:

    def __init__(self, x_range, x_tickness):
        self.x_p = {x: [] for x in np.arange(start=x_range[0], stop=x_range[1] + x_tickness, step=x_tickness)}
        self.x_n = {x: [] for x in np.arange(start=x_range[0], stop=x_range[1] + x_tickness, step=x_tickness)}
        # self.y = np.arange(start=y_range[0], stop=y_range[1] + y_tick, step=y_tick)
        # self.z = np.arange(start=z_range[0], stop=z_range[1] + z_tick, step=z_tick)

        # self.matrix = np.zeros(shape=(len(self.x), len(self.y), len(self.z)))
        # self.matrix = np.zeros(shape=(len(self.x), len(self.y)))

        pass

    def add_value(self, x, value, relation):
        # x_index = np.where(self.x == min(self.x, key=lambda e: abs(e - x)))[0][0]
        # y_index = np.where(self.y == min(self.y, key=lambda e: abs(e - y)))[0][0]
        # z_index = np.where(self.z == min(self.z, key=lambda e: abs(e - z)))[0][0]
        # self.matrix[x_index, y_index, z_index] = value
        # pass
        if relation == '+':
            subject = self.x_p
        else:
            subject = self.x_n

        x_index = min(subject, key=lambda e: abs(e - x))
        subject[x_index].append(value)

    def transform(self, threshold, weight, ratio):
        # return np.arctan(weight - threshold) + 1.5

        # if weight >= threshold:
        #     return np.log(weight) + 1
        # else:
        #     return -np.log(weight - 2) + 1

        # if weight < threshold:
        #     return 1
        # else:
        #     return ratio

        if ratio > 10:
            if weight < threshold:
                return 1
            else:
                return ratio
        else:
            return ratio

    def systematic_analysis(self, exp_spline, sim_spline, x_axis, exp_id):
        x_axis = sorted(x_axis)

        domain_x = list(self.x_p.keys())

        min_x_axis = min(x_axis)
        max_x_axis = max(x_axis)

        min_domain = min(domain_x)
        max_domain = max(domain_x)

        # Non ho intersezione dei domini
        # print(x_axis, domain_x)

        if max(domain_x) < min_x_axis or min(domain_x) > max_x_axis:
            print(domain_x, max_x_axis, min_x_axis)
            raise ValueError("No x intersection")

        # dominio dei dati completamente incluso nel dominio di analisi
        elif min_domain < min_x_axis and max_domain > max_x_axis:
            tmp = {x: abs(x - x_axis[0]) for x in domain_x}
            min_tmp = min(tmp, key=tmp.get)
            x_axis[0] = min_tmp

            tmp = {x: abs(x - x_axis[-1]) for x in domain_x}
            min_tmp = min(tmp, key=tmp.get)
            x_axis[-1] = min_tmp

        elif min_domain > min_x_axis and max_domain > max_x_axis:
            # print(domain_x, x_axis)
            # raise NotImplementedError
            pass

        elif min_domain < min_x_axis and max_x_axis > max_domain:
            # print(domain_x, x_axis, exp_id, [t_x for t_x in domain_x if min(x_axis) <= t_x <= max(x_axis)])
            # raise NotImplementedError
            pass



        x_axis = [t_x for t_x in domain_x if min(x_axis) <= t_x <= max(x_axis)]

        if len(x_axis) == 1:
            # TODO con la pressione c'è un caso in cui x_domain è [1, 0.660412912, 0.661189387, 0.662152986, 0.662857293, 0.663648498, 0.664526318, 0.665116249, 1]
            print('attenzione')
            # TODO nella trasformazione tutto viene compressato in un singolo elemento vedi exp 1058
            return

        # print(x_axis)
        def exp(x: float):
            return exp_spline.evaluate(x)

        def sim(x: float):
            return sim_spline.evaluate(x)

        area_sim_tot, err_sim_tot = integrate.quad(sim, min(x_axis), max(x_axis))
        area_exp_tot, err_exp_tot = integrate.quad(exp, min(x_axis), max(x_axis))

        # sum = 0

        # if plot:
        #     print(f'AREA SIM: {area_sim_tot:.5f}')
        #     print(f'AREA EXP: {area_exp_tot:.5f}')

        diz_df = {'Interval': [],
                  'Area Exp Inter': [],
                  'Area Sim Inter': [],
                  'Weight Exp Inter': [],
                  'Weight Sim Inter': [],
                  # 'Value': [],
                  'Real': [],
                  'Relation': []}

        # print(x_axis)

        expected_weight = 1 / (len(x_axis) - 1)

        for index in range(0, len(x_axis) - 1):
            inf = x_axis[index]
            sup = x_axis[index + 1]

            diz_df['Interval'].append((inf, sup))

            area_sim_interval, err_sim = integrate.quad(sim, inf, sup)
            area_sim_interval = max(0, area_sim_interval)

            diz_df['Area Sim Inter'].append(area_sim_interval)

            area_exp_interval, err_exp = integrate.quad(exp, inf, sup)
            area_exp_interval = max(0, area_exp_interval)

            diz_df['Area Exp Inter'].append(area_exp_interval)

            current_weight_exp = area_exp_interval / area_exp_tot
            current_weight_sim = area_sim_interval / area_sim_tot

            diz_df['Weight Exp Inter'].append(current_weight_exp)
            diz_df['Weight Sim Inter'].append(current_weight_sim)

            # Modello sovrastima
            if area_sim_interval >= area_exp_interval:
                relation = '+'
                diz_df['Relation'].append(relation)

                try:
                    ratio = area_sim_interval / area_exp_interval
                    diz_df['Real'].append(ratio)
                except ZeroDivisionError:
                    ratio = 0
                    diz_df['Real'].append(np.NAN)

                # ratio = self.transform(threshold=expected_weight, weight=current_weight_exp, ratio=ratio)


            # Modello sottostima
            else:
                relation = '-'
                diz_df['Relation'].append(relation)

                try:
                    ratio = area_exp_interval / area_sim_interval
                    diz_df['Real'].append(ratio)
                except ZeroDivisionError:
                    ratio = 0
                    diz_df['Real'].append(np.NAN)

                # ratio = self.transform(threshold=expected_weight, weight=current_weight_sim, ratio=ratio)

            # diz_df['Value'].append(ratio)

            # self.add_value(x=x_axis[index], value=ratio, relation=relation)

        df = pd.DataFrame.from_dict(diz_df)

        # print(df)

        df['Value'] = ''

        # print(df)

        # Remove NaN
        NaN_indexes, _ = np.where(df.isna())

        if len(NaN_indexes) > 0:

            diff = abs(area_sim_tot - area_exp_tot)

            guess = diff / len(NaN_indexes)

            for index in NaN_indexes:
                sim_int = df.iloc[index, df.columns.get_loc('Area Exp Inter')]
                exp_int = df.iloc[index, df.columns.get_loc('Area Sim Inter')]

                if sim_int == 0 and exp_int == 0:
                    df.iloc[index, df.columns.get_loc('Value')] = 1
                elif sim_int == 0:
                    df.iloc[index, df.columns.get_loc('Value')] = guess / exp_int
                elif exp_int == 0:
                    df.iloc[index, df.columns.get_loc('Value')] = guess / sim_int

        for index, row in df.iterrows():
            weight = row['Weight Exp Inter'] if row['Relation'] == '+' else row['Weight Sim Inter']
            if row['Value'] == '':
                value = self.transform(threshold=expected_weight, weight=weight, ratio=row['Real'])
                df.loc[index, 'Value'] = float(value)
            else:
                value = self.transform(threshold=expected_weight, weight=weight, ratio=row['Value'])
                df.loc[index, 'Value'] = float(value)
            # print(row['Interval'][0], df.loc[index, 'Value'])
            self.add_value(x=row['Interval'][0], value=value, relation=row['Relation'])

        # print(df)

        return df

        # Handle NaN

        # df.to_excel(current_excel, sheet_name=f'{exp_id}', na_rep='NA')
        # print(len(x_axis))
        # print(df)
        # print(sum)
        # if plot:
        #     plt.show()


def process_summary(exp_id, current_summary, domain_list):
    results = {}
    for model in current_summary:
        model_name = model['model']['name']
        if model_name not in list(domain_list.keys()):  # CRECK_2003_C1C3_DME_LTHT
            continue
        #
        #
        # if exp_id == 235 and model_name == 'CRECK_2003_SYNGAS':
        #     print(model)



        for pair in model['pairs']:
            subject = pair['y_sim_name']

            # if subject != 'CO_x':
            #     continue

            # print(subject)

            if pair['x_exp_name'] == 'pressure':
                # TODO da rivedere! Suprattuto so ho lo stesso subject ma una volta con la t ed una volta con la p la x_domain non torna
                continue

            # if pair['y_unit'] != 'us':
            #     print('NOOOOOO', pair['y_unit'])
            #     # exit()

            # # If the Domain Object does not exist, create it

            x_name = pair['x_exp_name']

            if x_name not in domain_list[model_name]:
                domain_list[model_name][x_name] = {}

            if subject not in domain_list[model_name][x_name]:
                if pair['x_exp_name'] == 'temperature' and pair['y_exp_name'] == 'composition':
                    domain_list[model_name][x_name][subject] = Domain(x_range=(500, 2000), x_tickness=25)
                elif pair['x_exp_name'] == 'temperature' and pair['y_exp_name'] == 'ignition delay':
                    domain_list[model_name][x_name][subject] = Domain(x_range=(0, 1.5), x_tickness=0.025)
                elif pair['x_exp_name'] == 'pressure' and pair['y_exp_name'] == 'composition':
                    domain_list[model_name][x_name][subject] = Domain(x_range=(0, 50), x_tickness=1)
                elif pair['x_exp_name'] == 'time' and pair['y_exp_name'] == 'composition':
                    domain_list[model_name][x_name][subject] = Domain(x_range=(0, 10), x_tickness=0.2)
                elif pair['x_exp_name'] == 'equivalence ratio' and pair['y_exp_name'] == 'laminar burning velocity':
                    domain_list[model_name][x_name][subject] = Domain(x_range=(0, 50), x_tickness=0.5)
                    # print('heeereeeee')
                else:
                    raise ValueError(pair['x_exp_name'], pair['y_exp_name'])

            # print(subject, pair['x_exp_name'], pair['y_exp_name'])

            current_domain = domain_list[model_name][x_name][subject]

            x_exp, y_exp = pair['x_exp_data'], pair['y_exp_data']
            x_sim, y_sim = pair['x_sim_data'], pair['y_sim_data']

            # CODICE PER NORMALIZZAZIONE
            # x_exp = [(x - min(x_exp)) / (max(x_exp) - min(x_exp)) for x in x_exp]
            # y_exp = [(x - min(y_exp)) / (max(y_exp) - min(y_exp)) for x in y_exp]
            # x_sim = [(x - min(x_sim)) / (max(x_sim) - min(x_sim)) for x in x_sim]
            # y_sim = [(x - min(y_sim)) / (max(y_sim) - min(y_sim)) for x in y_sim]

            # GENERO SPLINE DAI DATI SPERIMENTALI E DAL MODELLO
            spline_exp = Spline(x=x_exp, y=y_exp)
            spline_model = Spline(x=x_sim, y=y_sim)

            # if plot:
            x_evaluation = np.linspace(min(x_exp), max(x_exp), 100)

            # plt.show()

            df = current_domain.systematic_analysis(exp_spline=spline_exp,
                                                    sim_spline=spline_model,
                                                    x_axis=x_exp,
                                                    exp_id=exp_id)

            # print(df)
            if x_name not in results:
                results[x_name] = {}

            if df is not None:
                results[x_name][subject] = df

    return results


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

        exps = Models.CurveMatchingResult.objects.filter(**new).values_list(
            'execution_column__execution__experiment__id', flat=True).distinct()

        chemModel = Models.ChemModel.objects.get(id=self.chemModel_id)

        domains = {chemModel.name: {}}

        details = {}

        # return Response(json.dumps(a), status=HTTP_200_OK)

        for exp_id in exps:
            # Given an Exp return all the pairs for each simulated model
            # if exp_id !=1058:
            #     continue
            current_summary = create_summary(exp_id)

            current_result = process_summary(exp_id=exp_id, current_summary=current_summary, domain_list=domains)

            for x_name in current_result:
                if x_name not in details:
                    details[x_name] = {}

                for subject in current_result[x_name]:
                    if subject not in details[x_name]:
                        details[x_name][subject] = {}

                    # print(exp_id, x_name, subject)

                    df = current_result[x_name][subject].where(pd.notnull(current_result[x_name][subject]), -1)

                    # df["Area Exp Inter"] = df.Value.astype(float)
                    # df["Area Sim Inter"] = df.Value.astype(float)
                    # df["Weight Exp Inter"] = df.Value.astype(float)
                    # df["Weight Sim Inter"] = df.Value.astype(float)
                    # df["Real"] = df.Real.astype(float)
                    # df["Value"] = df.Value.astype(float)

                    df = df.astype({'Area Exp Inter': float,
                                    'Area Sim Inter': float,
                                    'Weight Exp Inter': float,
                                    'Weight Sim Inter': float,
                                    'Real': float,
                                    'Value': float,
                                    })

                    # print(df.dtypes)

                    df = df.round({'Area Exp Inter': 3,
                                   'Area Sim Inter': 3,
                                   'Weight Exp Inter': 3,
                                   'Weight Sim Inter': 3,
                                   'Real': 3,
                                   'Value': 3,
                                   })

                    details[x_name][subject][exp_id] = df.to_dict('records')



        result = {}
        # TODO ASSUNZIONE UN SOLO MODELLO ALLA VOLTA
        current_model = chemModel.name

        for x_name in domains[current_model]:
            if x_name not in result:
                result[x_name] = {}

            for subject in domains[current_model][x_name]:
                if subject not in details[x_name]:
                    continue
                if subject not in result[x_name]:
                    result[x_name][subject] = {}

                lunghezza = len(domains[current_model][x_name][subject].x_p)

                freq_sovrastima = np.zeros(lunghezza)
                freq_sottostima = np.zeros(lunghezza)

                ticks_sottostima = np.zeros(lunghezza)
                ticks_sovrastima = np.zeros(lunghezza)

                # for index, model_name in enumerate(domains):
                #     # print(domains[domain][subject].x)

                df_sovrastima = generate_df(diz=domains[current_model][x_name][subject].x_p)
                df_sottostima = generate_df(diz=domains[current_model][x_name][subject].x_n)

                ticks_sovrastima = df_sovrastima['Interval']
                ticks_sottostima = df_sottostima['Interval']

                freq_sottostima = np.maximum(freq_sottostima, df_sottostima['Count'])
                freq_sovrastima = np.maximum(freq_sottostima, df_sovrastima['Count'])

                result[x_name][subject]['sovrastima'] = {'x': list(df_sovrastima['Interval']),
                                                         'y': list(df_sovrastima['Avg']),
                                                         'error_y': list(df_sovrastima['StDev']),
                                                         'count': list(freq_sovrastima)}

                result[x_name][subject]['sottostima'] = {'x': list(df_sottostima['Interval']),
                                                         'y': list(df_sottostima['Avg']),
                                                         'error_y': list(df_sottostima['StDev']),
                                                         'count': list(freq_sottostima)}
                result[x_name][subject]['details'] = details[x_name][subject]

        return Response(result, status=HTTP_200_OK)
