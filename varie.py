import os
import django
from django.db.models import Avg
import numpy as np
from scipy import interpolate, integrate
import json
import matplotlib.pyplot as plt
from tqdm import tqdm
from statistics import median, mean, stdev, variance
from SplinePoliMi import Spline

from dateutil.parser import parse
from django.db.models import Q

from itertools import combinations

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SciExpeM.settings")
django.setup()

from ExperimentManager.Models import *
from ExperimentManager.Views.getSimulation import create_summary


def zip_order(xx, yy):
    zz = dict(sorted(zip(xx, yy)))
    return list(zz.keys()), list(zz.values())


class Domain:

    def __init__(self, x_range, x_tick):
        self.x = {x: [] for x in np.arange(start=x_range[0], stop=x_range[1] + x_tick, step=x_tick)}
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

    def generate_list(self, minimum, maximum, n_ticks):
        frequency = (maximum - minimum) / n_ticks
        return [minimum + (i * frequency) for i in range(n_ticks + 1)]

    def systematic_analysis(self, exp_spline, sim_spline, x_axis, n_ticks=10):
        x_axis = self.generate_list(minimum=min(x_axis), maximum=max(x_axis), n_ticks=n_ticks)

        # result = []

        def exp(x: float):
            return exp_spline.evaluate(x)

        def sim(x: float):
            return sim_spline.evaluate(x)

        # for tick in x_axis:
        #     y_exp_v = exp(tick)
        #     y_sim_v = sim(tick)
        #     variation = (y_sim_v - y_exp_v) * 100 / y_exp_v
        #
        #
        #     self.add_value(x=tick, value=variation)
        #     # result.append(variation)
        for index in range(0, len(x_axis) - 1):
            inf = x_axis[index]
            sup = x_axis[index + 1]
            area_sim, err_sim = integrate.quad(sim, inf, sup)
            area_exp, err_exp = integrate.quad(exp, inf, sup)
            # y_exp_v = exp(tick)
            # y_sim_v = sim(tick)
            if area_exp != 0:
                variation = abs(area_sim - area_exp) * 100 / area_exp
                self.add_value(x=x_axis[index], value=variation)
            # result.append(variation)

        # return result


# d = Domain(x_range=(1000, 2000), x_tick=25)

# exit()


# a = [1, 2, 3, 4]
#
# b = [2, 4, 6, 8]
#
# c = (np.asarray(b) / np.asarray(a))
#
# print(c)
# print(1/c)
#
# exit()
#
# exp_id = 231

with open('exp.list', 'r') as file:
    exps = json.load(file)

models = {'POLIMI_1212_C1C3': {}, 'CRECK_2003_C1C3_DME_LTHT': {}}
# domains = {}


edo = []


import time
index = 0
for exp_id in tqdm(exps):
    # time.sleep(0.1)

    index += 1

    sim_models = create_summary(exp_id)
    # if index == 179 or index == 180:
    #     break



    for model in sim_models:
        model_name = model['model']['name']
        if not (model_name == 'CRECK_2003_C1C3_DME_LTHT' or model_name == 'POLIMI_1212_C1C3'):
            continue

        for pair in model['pairs']:

            subject = pair['y_sim_name']
            if pair['x_exp_name'] != 'temperature' or pair['y_exp_name'] != 'composition':
                continue

            if subject not in models[model_name]:
                models[model_name][subject] = Domain(x_range=(1000, 2000), x_tick=25)

            current_domain = models[model_name][subject]

            x_exp, y_exp = zip_order(xx=pair['x_exp_data'], yy=pair['y_exp_data'])
            x_sim, y_sim = zip_order(xx=pair['x_sim_data'], yy=pair['y_sim_data'])

            edo.append({'x': x_exp, 'y': y_exp})
            edo.append({'x': x_sim, 'y': y_sim})

            # continue


            # try:  # gli elementi devono essere oridinati
            #     exp_interp_coeff = interpolate.splrep(x_exp, y_exp, s=5E7)
            #     sim_interp_coeff = interpolate.splrep(x_sim, y_sim, s=5E7)
            # except TypeError:  # se ho <= 3 elementi errore
            #     continue
            # plt.plot(x_exp, y_exp, '*')
            # plt.plot(x_sim, y_sim, '^')
            #
            # y_exp_interpolate = interpolate.splev(x_exp, exp_interp_coeff)
            # y_sim_interpolate = interpolate.splev(x_exp, sim_interp_coeff)
            #
            # plt.plot(x_exp, y_exp_interpolate, '--')
            # plt.plot(x_exp, y_sim_interpolate, '-.')
            #
            # plt.title(subject)
            #
            # plt.show()
            current_domain.systematic_analysis(exp_spline=Spline(x=x_exp, y=y_exp),
                                               sim_spline=Spline(x=x_sim, y=y_sim),
                                               x_axis=x_exp,
                                               n_ticks=10)
            # print(y_exp)
            # print(y_sim)
            #
            # comb = combinations(y_exp.keys(), 2)
            # for i in list(comb):
            #     y1 = np.asarray(y_exp[i[0]])
            #     y2 = np.asarray(y_exp[i[1]])
            #     result_exp[i] = y1 / y2
            #
            #     y3 = np.asarray(y_sim[i[0]])
            #     y4 = np.asarray(y_sim[i[1]])
            #     result_sim[i] = y3 / y4
            #
            # print(result_exp)
            # print(result_sim)


# with open('dati.json', 'w+') as file:
#     json.dump(edo, file )

# print(models['POLIMI_1212_C1C3'])

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
    # print(domains[domain].x.keys())
    # print(domains[domain].x.values())
    plt.plot(list_x, list_y, label='POLIMI_1212_C1C3')
    plt.plot(list_x_1, list_y_1, label='CRECK_2003_C1C3_DME_LTHT')
    plt.title(domain)
    plt.ylabel('Variation Exp - Sim (%)')
    plt.xlabel('Temperature [K]')

    plt.legend()
    plt.savefig(domain + '.png')
    plt.show()
    plt.close()
    # plt.show()
    # print(domain, models[model_name][domain].x)
