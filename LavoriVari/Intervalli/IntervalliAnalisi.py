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
        self.x = {x: [] for x in np.arange(start=x_range[0], stop=x_range[1] + x_tickness, step=x_tickness)}
        # self.y = np.arange(start=y_range[0], stop=y_range[1] + y_tick, step=y_tick)
        # self.z = np.arange(start=z_range[0], stop=z_range[1] + z_tick, step=z_tick)

        # self.matrix = np.zeros(shape=(len(self.x), len(self.y), len(self.z)))
        # self.matrix = np.zeros(shape=(len(self.x), len(self.y)))

        pass

    def add_value(self, x, value):
        # x_index = np.where(self.x == min(self.x, key=lambda e: abs(e - x)))[0][0]
        # y_index = np.where(self.y == min(self.y, key=lambda e: abs(e - y)))[0][0]
        # z_index = np.where(self.z == min(self.z, key=lambda e: abs(e - z)))[0][0]
        # self.matrix[x_index, y_index, z_index] = value
        # pass
        x_index = min(self.x, key=lambda e: abs(e - x))
        self.x[x_index].append(value)

    def systematic_analysis(self, exp_spline, sim_spline, x_axis, n_ticks=10):
        x_axis = np.linspace(start=min(x_axis), stop=max(x_axis), num=n_ticks)

        def exp(x: float):
            return exp_spline.evaluate(x)

        def sim(x: float):
            return sim_spline.evaluate(x)

        area_sim_tot, err_sim_tot = integrate.quad(sim, min(x_axis), max(x_axis))
        area_exp_tot, err_exp_tot = integrate.quad(exp, min(x_axis), max(x_axis))

        for index in range(0, len(x_axis) - 1):
            inf = x_axis[index]
            sup = x_axis[index + 1]
            area_sim_interval, err_sim = integrate.quad(sim, inf, sup)

            # area_sim_interval = (area_sim_interval / area_sim_tot) * area_sim_interval

            area_exp_interval, err_exp = integrate.quad(exp, inf, sup)

            # area_exp_interval = (area_exp_interval / area_exp_tot) * area_exp_interval

            # plt.plot(x_axis, sim(x_axis))
            # plt.show()


            # if area_exp_interval != 0:
                # variation = abs(area_sim - area_exp) * 100 / area_exp
                # variation = abs(area_sim_interval - area_exp_interval) * (area_sim_tot - area_exp_tot) / (area_sim_tot + area_exp_tot)
            if area_sim_interval == 0:
                area_sim_interval += 1e-20
            if area_exp_interval == 0:
                area_exp_interval += 1e-20
            tmp = (area_sim_interval / area_exp_interval)

            #
            if tmp < 1:
                variation = 1 / tmp
            else:
                variation = tmp


            aree_ratio = (area_sim_interval - area_exp_interval) / (area_sim_tot - area_exp_tot)

            if aree_ratio > 0.01:
                ratio2 = variation
            else:
                ratio2 = 1

            print(ratio2)


            # print(f'X-inf: {inf:.2f} - X-sup:{sup:.2f} - ratio:{variation:.5f} - ratio2:{ratio2:.5f} - Sim Int area:{area_sim_interval:.2e} - Exp Int area:{area_exp_interval:.2e} - Sim TOT area:{area_sim_tot:.2e} - Sim Exp area:{area_exp_tot:.2e}')

            self.add_value(x=x_axis[index], value=ratio2)



def analisi_intervalli():
    pdfs = {'POLIMI_1212_C1C3': {}, 'CRECK_2003_C1C3_DME_LTHT': {}}

    with open('./exp.list', 'r') as file:
        exps = json.load(file)

    models = {'POLIMI_1212_C1C3': {}, 'CRECK_2003_C1C3_DME_LTHT': {}}

    index = 0

    for exp_id in tqdm(exps):

        # Given an Exp return all the pairs for each simulated model
        sim_models = create_summary(exp_id)

        # index  +=1

        for model in sim_models:

            model_name = model['model']['name']
            if not (model_name == 'CRECK_2003_C1C3_DME_LTHT' or model_name == 'POLIMI_1212_C1C3'):
                continue
            # if model_name == 'POLIMI_1212_C1C3':
            #     continue

            for pair in model['pairs']:
                subject = pair['y_sim_name']
                if pair['x_exp_name'] != 'temperature' or pair['y_exp_name'] != 'composition':
                    continue

                # If the Domain Object does not exist, create it
                if subject not in models[model_name]:
                    models[model_name][subject] = Domain(x_range=(1000, 2000), x_tickness=20)
                    pdfs[model_name][subject] = PdfPages(f'{model_name}_{subject}.pdf')

                current_domain = models[model_name][subject]
                current_pdf = pdfs[model_name][subject]

                x_exp, y_exp = pair['x_exp_data'], pair['y_exp_data']
                x_sim, y_sim = pair['x_sim_data'], pair['y_sim_data']

                spline_exp = Spline(x=x_exp, y=y_exp)
                spline_model = Spline(x=x_sim, y=y_sim)

                if True:
                    x_evaluation = np.linspace(min(x_exp), max(x_exp), 100)
                    plt.plot(x_evaluation, spline_exp.evaluate(x_evaluation), 'r-', label="Spline Exp")
                    plt.plot(x_evaluation, spline_model.evaluate(x_evaluation), 'b-', label="Spline Model")
                    plt.plot(x_exp, y_exp, 'r*', label='Exp Points')
                    plt.plot(x_sim, y_sim, 'b*', label='Model Points')
                    plt.title(f'SciExpeM ID: {exp_id} - {model_name} - {subject}')
                    plt.legend()
                    current_pdf.savefig()
                    plt.close()

                current_domain.systematic_analysis(exp_spline=spline_exp,
                                                   sim_spline=spline_model,
                                                   x_axis=x_exp,
                                                   n_ticks=20)

        # if index == 10:
        #     break



    for model in pdfs:
        for subject in pdfs[model]:
            pdfs[model][subject].close()

    summary = PdfPages('Summmary.pdf')

    for domain in models['POLIMI_1212_C1C3']:
        list_x = []
        list_y = []
        list_x_1 = []
        list_y_1 = []
        for tick in models['POLIMI_1212_C1C3'][domain].x:
            x = tick
            y = mean(models['POLIMI_1212_C1C3'][domain].x[tick]) if len(
                models['POLIMI_1212_C1C3'][domain].x[tick]) > 0 else -1
            if y != -1:
                list_x.append(x)
                list_y.append(y)
        for tick in models['CRECK_2003_C1C3_DME_LTHT'][domain].x:
            x = tick
            y = mean(models['CRECK_2003_C1C3_DME_LTHT'][domain].x[tick]) if len(
                models['CRECK_2003_C1C3_DME_LTHT'][domain].x[tick]) > 0 else -1
            if y != -1:
                list_x_1.append(x)
                list_y_1.append(y)

        plt.plot(list_x, list_y, label='POLIMI_1212_C1C3')
        plt.plot(list_x_1, list_y_1, label='CRECK_2003_C1C3_DME_LTHT')
        plt.title(domain)
        plt.ylabel('Variation Exp - Sim (%)')
        plt.xlabel('Temperature [K]')

        plt.legend()
        summary.savefig()
        plt.show()
        plt.close()
        # plt.show()
        # print(domain, models[model_name][domain].x)

    summary.close()


def analisi_rapporti():
    pdfs = {'POLIMI_1212_C1C3': {}, 'CRECK_2003_C1C3_DME_LTHT': {}}

    with open('./exp.list', 'r') as file:
        exps = json.load(file)

    stores = {'POLIMI_1212_C1C3': {'exp': Store(), 'sim': Store()}, 'CRECK_2003_C1C3_DME_LTHT': {'exp': Store(), 'sim': Store()}}

    stores_total = {'POLIMI_1212_C1C3': Store(), 'CRECK_2003_C1C3_DME_LTHT': Store()}

    for exp_id in tqdm(exps):

        # Given an Exp return all the pairs for each simulated model
        sim_models = create_summary(exp_id)

        for model in sim_models:
            model_name = model['model']['name']
            if not (model_name == 'CRECK_2003_C1C3_DME_LTHT' or model_name == 'POLIMI_1212_C1C3'):
                continue

            # print(model['pairs'])

            couples_exp = {}
            couples_model = {}

            for pair in model['pairs']:

                subject = pair['y_sim_name']
                if pair['y_exp_name'] != 'composition':
                    continue

                subject_exp = pair['y_exp_name'] if pair['y_exp_name'] != 'composition' else subject

                couples_exp[subject_exp] = {'x': pair['x_exp_data'], 'y': pair['y_exp_data']}
                couples_model[subject_exp] = {'x': pair['x_sim_data'], 'y': pair['y_sim_data']}

            if len(couples_exp) > 2:
                for combination in combinations(couples_exp.keys(), 2):
                    a = combination[0]
                    b = combination[1]

                    x1_exp_tmp = couples_exp[a]['x']
                    y1_exp_tmp = couples_exp[a]['y']


                    spline_exp_1 = Spline(x=x1_exp_tmp, y=y1_exp_tmp)

                    x2_exp_tmp = couples_exp[b]['x']
                    y2_exp_tmp = couples_exp[b]['y']

                    print(a, b)
                    print(x1_exp_tmp)
                    print(y1_exp_tmp)
                    print(x2_exp_tmp)
                    print(y2_exp_tmp)

                    spline_exp_2 = Spline(x=x2_exp_tmp, y=y2_exp_tmp)

                    def exp_1(x: float):
                        return spline_exp_1.evaluate(x)

                    def exp_2(x: float):
                        return spline_exp_2.evaluate(x)

                    x_inf, x_sup = domain_intersection(a_inf=min(x1_exp_tmp), a_sup=max(x1_exp_tmp),
                                                       b_inf=min(x2_exp_tmp), b_sup=max(x2_exp_tmp))

                    area_exp_1, err_exp = integrate.quad(exp_1, x_inf, x_sup)
                    area_exp_2, err_exp = integrate.quad(exp_2, x_inf, x_sup)

                    exp_area_ratio = area_exp_1 / area_exp_2

                    stores[model_name]['exp'].add(pair=combination, value=exp_area_ratio)

                    x1_sim_tmp = couples_model[a]['x']
                    y1_sim_tmp = couples_model[a]['y']

                    spline_sim_1 = Spline(x=x1_sim_tmp, y=y1_sim_tmp)

                    x2_sim_tmp = couples_model[b]['x']
                    y2_sim_tmp = couples_model[b]['y']

                    print(x1_sim_tmp)
                    print(y1_sim_tmp)
                    print(x2_sim_tmp)
                    print(y2_sim_tmp)

                    print(area_exp_1, area_exp_2, exp_area_ratio)


                    spline_sim_2 = Spline(x=x2_sim_tmp, y=y2_sim_tmp)

                    def sim_1(x: float):
                        return spline_sim_1.evaluate(x)

                    def sim_2(x: float):
                        return spline_sim_2.evaluate(x)

                    x_inf, x_sup = domain_intersection(a_inf=min(x1_sim_tmp), a_sup=max(x1_sim_tmp),
                                                       b_inf=min(x2_sim_tmp), b_sup=max(x2_sim_tmp))

                    area_sim_1, err_exp = integrate.quad(sim_1, x_inf, x_sup)
                    area_sim_2, err_exp = integrate.quad(sim_2, x_inf, x_sup)

                    sim_area_ratio = area_sim_1 / area_sim_2

                    print(area_sim_1, area_sim_2, sim_area_ratio)

                    exit()

                    stores[model_name]['sim'].add(pair=combination, value=sim_area_ratio)

                    variation = (sim_area_ratio - exp_area_ratio) * 100 / exp_area_ratio

                    stores_total[model_name].add(pair=combination, value=variation)

                    # x_sim_tmp = np.array()
                    # y_sim_tmp = np.array()
                # print(list(combinations(couples_exp.keys(), 2)))
                # print(list(combinations(couples_model.keys(), 2)))
            # exit()



    with open('POLIMI_1212_C1C3_exp.json', 'w+') as file:
        obj = stores['POLIMI_1212_C1C3']['exp'].couple
        obj = {str(key[0]) + '/' + str(key[1]): obj[key] for key in obj}
        json.dump(obj, file)

    with open('POLIMI_1212_C1C3_sim.json', 'w+') as file:
        obj = stores['POLIMI_1212_C1C3']['exp'].couple
        obj = {str(key[0]) + '/' + str(key[1]): obj[key] for key in obj}
        json.dump(obj, file)

    with open('CRECK_2003_C1C3_DME_LTHT_exp.json', 'w+') as file:
        obj = stores['CRECK_2003_C1C3_DME_LTHT']['exp'].couple
        obj = {str(key[0]) + '/' + str(key[1]): obj[key] for key in obj}
        json.dump(obj, file)

    with open('CRECK_2003_C1C3_DME_LTHT_sim.json', 'w+') as file:
        obj = stores['CRECK_2003_C1C3_DME_LTHT']['sim'].couple
        obj = {str(key[0]) + '/' + str(key[1]): obj[key] for key in obj}
        json.dump(obj, file)

    with open('POLIMI_1212_C1C3_tot.json', 'w+') as file:
        obj = stores_total['POLIMI_1212_C1C3'].couple
        obj = {str(key[0]) + '/' + str(key[1]): obj[key] for key in obj}
        json.dump(obj, file)

    with open('CRECK_2003_C1C3_DME_LTHT_tot.json', 'w+') as file:
        obj = stores_total['CRECK_2003_C1C3_DME_LTHT'].couple
        obj = {str(key[0]) + '/' + str(key[1]): obj[key] for key in obj}
        json.dump(obj, file)



    # print(exp_store.couple)


if __name__ == "__main__":
    analisi_intervalli()
    # analisi_rapporti()
