# Setuo Django Local
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SciExpeM.settings")
django.setup()

# SciExpeM Import
from ExperimentManager.Models import *
from ExperimentManager.Views.getSimulation import create_summary
from CurveMatching.CurveMatchingPython import CurveMatching

# Third Libraries
from scipy import integrate
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
from tqdm import tqdm
from SplinePoliMi import Spline

# Python Import
from statistics import median, mean, stdev, variance
import json
from itertools import combinations
import math
import warnings
import pandas as pd

plot = True

output_folder = "./H2_IDT/"


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

    def systematic_analysis(self, exp_spline, sim_spline, x_axis, current_excel, exp_id, model):
        x_axis = sorted(x_axis)
        # print(x_axis)
        domain_x = list(self.x_p.keys())

        min_x_axis = min(x_axis)
        max_x_axis = max(x_axis)

        min_domain = min(domain_x)
        max_domain = max(domain_x)

        # Non ho intersezione dei domini

        if max(domain_x) < min_x_axis or min(domain_x) > max_x_axis:
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
            raise NotImplementedError

        elif min_domain < min_x_axis and max_x_axis > max_domain:
            raise NotImplementedError

        x_axis = [t_x for t_x in domain_x if min(x_axis) <= t_x <= max(x_axis)]

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

        expected_weight = 1 / (len(x_axis) - 1)

        for index in range(0, len(x_axis) - 1):
            inf = x_axis[index]
            sup = x_axis[index + 1]

            diz_df['Interval'].append((inf, sup))

            # if plot:
            axes = plt.gca()
            ymin, ymax = axes.get_ylim()
            plt.vlines(x=inf, ymin=0, ymax=ymax, linestyles='dashed')
            plt.vlines(x=sup, ymin=0, ymax=ymax, linestyles='dashed')

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
                df.loc[index, 'Value'] = value
            else:
                value = self.transform(threshold=expected_weight, weight=weight, ratio=row['Value'])
                df.loc[index, 'Value'] = value
            # print(row['Interval'][0], df.loc[index, 'Value'])
            self.add_value(x=row['Interval'][0], value=value, relation=row['Relation'])

        # print(df)

        # Handle NaN

        df.to_excel(current_excel, sheet_name=f'{exp_id}', na_rep='NA')
        # print(len(x_axis))
        # print(df)
        # print(sum)
        # if plot:
        #     plt.show()


def process_summary(exp_id, current_summary, domain_list):
    for model in current_summary:

        model_name = model['model']['name']

        if model_name not in ['POLIMI_1212_C1C3', 'CRECK_2003_C1C3_DME_LTHT']:  # CRECK_2003_C1C3_DME_LTHT
            continue

        for pair in model['pairs']:
            subject = pair['y_sim_name']

            # if subject != 'CO_x':
            #     continue

            # print(subject)

            # if pair['x_exp_name'] != 'temperature' or pair['y_exp_name'] != 'composition':
            #     continue

            if pair['y_unit'] != 'us':
                print('NOOOOOO', pair['y_unit'] )
                # exit()

            # # If the Domain Object does not exist, create it

            if subject not in domain_list[model_name]:
                domain_list[model_name][subject] = Domain(x_range=(0, 1.5), x_tickness=0.025)
                # pdf_list[model_name][subject] = PdfPages(os.path.join(output_folder, f'{model_name}_{subject}.pdf'))
                # excel_list[model_name][subject] = pd.ExcelWriter(
                #     path=os.path.join(output_folder, f'{model_name}_{subject}.xlsx'), engine="openpyxl")

            current_domain = domain_list[model_name][subject]
            # current_pdf = pdf_list[model_name][subject]
            # current_excel = excel_list[model_name][subject]

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
            plt.plot(x_evaluation, spline_exp.evaluate(x_evaluation), 'r-', label="Spline Exp")
            plt.plot(x_evaluation, spline_model.evaluate(x_evaluation), 'b-', label="Spline Model")
            plt.plot(x_exp, y_exp, 'r*', label='Exp Points')
            plt.plot(x_sim, y_sim, 'b*', label='Model Points')
            plt.title(f'SciExpeM ID {exp_id:.0f}: {model_name} - {subject}')
            plt.legend()

            # plt.show()

            current_domain.systematic_analysis(exp_spline=spline_exp,
                                               sim_spline=spline_model,
                                               x_axis=x_exp,
                                               # current_excel=current_excel,
                                               exp_id=exp_id,
                                               model=model)

            # current_pdf.savefig()
            plt.close()


def plot_summary(df_sovrastima, df_sottostima, summary_pdf, subject, model_name, ax1, ax2, ax11, ax22, color):
    ticks_sovrastima = df_sovrastima['Interval']
    freqs_sovrastima = df_sovrastima['Count']
    avg_sovrastima = df_sovrastima['Avg']
    deviation_sovrastima = df_sovrastima['StDev']

    ticks_sottostima = df_sottostima['Interval']
    freqs_sottostima = df_sottostima['Count']
    avg_sottostima = df_sottostima['Avg']
    deviation_sottostima = df_sottostima['StDev']

    # make a plot

    ax1.plot(ticks_sovrastima, avg_sovrastima, label=model_name, color=color)
    # ax1.fill_between(ticks_sovrastima,
    #                  [max(1, x) for x in avg_sovrastima - deviation_sovrastima],
    #                  avg_sovrastima + deviation_sovrastima,
    #                  alpha=0.3)

    # make a plot with different y-axis using second axis object
    # ax11.bar(ticks_sovrastima, freqs_sovrastima, width=20, color='lightblue')

    # Sottostima

    # make a plot
    ax2.plot(ticks_sottostima, avg_sottostima, label=model_name, color=color)
    # ax2.fill_between(ticks_sottostima, [max(1, x) for x in avg_sottostima - deviation_sottostima], avg_sottostima + deviation_sottostima, alpha=0.3)

    # make a plot with different y-axis using second axis object
    # ax22.bar(ticks_sottostima, freqs_sottostima, width=20, color='lightblue')

    # summary_pdf.savefig()
    # plt.close()


def print_summary(df_sovrastima, df_sottostima, model_name, subject):
    writer = pd.ExcelWriter(os.path.join(output_folder, model_name + '_' + subject + '.xlsx'), mode='a',
                            engine="openpyxl")
    df_sovrastima.to_excel(writer, sheet_name='Summary_Overestimate')
    df_sottostima.to_excel(writer, sheet_name='Summary_Underestimate')
    writer.close()


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


def analisi_intervalli(exps):

    domains = {'POLIMI_1212_C1C3': {}, 'CRECK_2003_C1C3_DME_LTHT': {}}
    # pdfs = {'POLIMI_1212_C1C3': {}, 'CRECK_2003_C1C3_DME_LTHT': {}}
    #
    # excels = {'POLIMI_1212_C1C3': {}, 'CRECK_2003_C1C3_DME_LTHT': {}}

    for exp_id in tqdm(exps):
        # print('EXP ID:', exp_id)

        # if exp_id != 205:
        #     continue

        # Given an Exp return all the pairs for each simulated model
        current_summary = create_summary(exp_id)
        #
        # print(current_summary)
        #
        # exit()

        process_summary(exp_id=exp_id, current_summary=current_summary, domain_list=domains)

        # break

    # for model in pdfs:
    #     for subject in pdfs[model]:
    #         pdfs[model][subject].close()
    #         excels[model][subject].close()

    # exit()

    # summary = PdfPages(os.path.join(output_folder, 'Summary.pdf'))

    color_list = ['blue', 'red', 'green', 'yellow']

    for subject in domains[list(domains.keys())[0]]:
        fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True, gridspec_kw={'hspace': 0})
        ax11 = ax1.twinx()
        ax22 = ax2.twinx()
        ax1.set_title(subject)

        # set x-axis label
        ax1.set_xlabel("T[K]", fontsize=14)
        # set y-axis label
        ax1.set_ylabel("Ratio", fontsize=14)
        # set x-axis label
        ax2.set_xlabel("T[K]", fontsize=14)
        # set y-axis label
        ax2.set_ylabel("Ratio", fontsize=14)
        ax11.set_ylabel("Frequency", alpha=0.5, color="royalblue", fontsize=14)
        ax22.set_ylabel("Frequency", alpha=0.5, color="royalblue", fontsize=14)

        ax2.invert_yaxis()
        ax22.invert_yaxis()

        lunghezza = len(domains[list(domains.keys())[0]][subject].x_p)

        freq_sovrastima = np.zeros(lunghezza)
        freq_sottostima = np.zeros(lunghezza)

        ticks_sottostima = np.zeros(lunghezza)
        ticks_sovrastima = np.zeros(lunghezza)

        for index, model_name in enumerate(domains):
            # print(domains[domain][subject].x)

            df_sovrastima = generate_df(diz=domains[model_name][subject].x_p)
            df_sottostima = generate_df(diz=domains[model_name][subject].x_n)

            ticks_sovrastima = df_sovrastima['Interval']
            ticks_sottostima = df_sottostima['Interval']

            freq_sottostima = np.maximum(freq_sottostima, df_sottostima['Count'])
            freq_sovrastima = np.maximum(freq_sottostima, df_sovrastima['Count'])

            # print(list(df_sovrastima['Count']))

            # Prepare Plot

            plot_summary(df_sovrastima=df_sovrastima,
                         df_sottostima=df_sottostima,
                         summary_pdf=summary,
                         subject=subject,
                         model_name=model_name,
                         ax1=ax1,
                         ax2=ax2,
                         ax11=ax11,
                         ax22=ax22,
                         color=color_list[index])

            print_summary(df_sovrastima=df_sovrastima, df_sottostima=df_sottostima, model_name=model_name,
                          subject=subject)

            # plt.show()
        ax11.bar(ticks_sovrastima, freq_sovrastima, width=0.025, color='royalblue', alpha=0.2)
        ax22.bar(ticks_sottostima, freq_sottostima, width=0.025, color='royalblue', alpha=0.2)
        ax1.legend()
        ax2.legend()
        summary.savefig()
        plt.close()

    # summary.close()




if __name__ == "__main__":
    analisi_intervalli()
    # analisi_rapporti()
