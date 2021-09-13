import os
import django
import requests, json
from dateutil.parser import parse
from django.db.models import Q
import matplotlib.pyplot as plt
import numpy as np
from tqdm import tqdm
from matplotlib.backends.backend_pdf import PdfPages
from random import randint

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SciExpeM.settings")
django.setup()


class Domain:

    def __init__(self, x_range, y_range, z_range, x_tick, y_tick, z_tick):
        self.x = np.arange(start=x_range[0], stop=x_range[1] + x_tick, step=x_tick)
        self.y = np.arange(start=y_range[0], stop=y_range[1] + y_tick, step=y_tick)
        # self.z = np.arange(start=z_range[0], stop=z_range[1] + z_tick, step=z_tick)

        # self.matrix = np.zeros(shape=(len(self.x), len(self.y), len(self.z)))

        self.matrix = np.zeros(shape=(len(self.x), len(self.y)))

        pass

    def add_value(self, x, y, z, value):
        x_index = np.where(self.x == min(self.x, key=lambda e: abs(e - x)))[0][0]
        y_index = np.where(self.y == min(self.y, key=lambda e: abs(e - y)))[0][0]
        # z_index = np.where(self.z == min(self.z, key=lambda e: abs(e - z)))[0][0]
        # self.matrix[x_index, y_index, z_index] = value
        self.matrix[x_index, y_index] = value

        pass

    def add_value_range(self, x_range, y_range, z_range, value):
        x_index_inf = np.where(self.x == min(self.x, key=lambda e: abs(e - x_range[0])))[0][0]
        y_index_inf = np.where(self.y == min(self.y, key=lambda e: abs(e - y_range[0])))[0][0]
        # z_index_inf = np.where(self.z == min(self.z, key=lambda e: abs(e - z_range[0])))[0][0]

        x_index_sup = np.where(self.x == min(self.x, key=lambda e: abs(e - x_range[1])))[0][0]
        y_index_sup = np.where(self.y == min(self.y, key=lambda e: abs(e - y_range[1])))[0][0]
        # z_index_sup = np.where(self.z == min(self.z, key=lambda e: abs(e - z_range[1])))[0][0]

        for x in range(x_index_inf, x_index_sup + 1):
            for y in range(y_index_inf, y_index_sup + 1):
                # for z in range(z_index_inf, z_index_sup + 1):
                #     self.matrix[x, y, z] += value
                self.matrix[x, y] += value

    def plot(self):
        # fig = plt.figure()
        # ax = fig.add_subplot(projection='3d')
        #
        # x = [self.x[e] for e in np.nonzero(self.matrix)[0]]
        # y = [self.y[e] for e in np.nonzero(self.matrix)[1]]
        # z = [self.z[e] for e in np.nonzero(self.matrix)[2]]
        #
        # c = [self.matrix[x, y, z] for (x, y, z) in zip(*np.nonzero(self.matrix))]

        # x = np.random.standard_normal(100)
        # y = np.random.standard_normal(100)
        # z = np.random.standard_normal(100)
        # c = np.random.standard_normal(100)

        cm = plt.cm.get_cmap('RdYlGn')

        # img = ax.scatter(x, y, z, c=c, cmap=cm, vmax=10, vmin=1)
        # fig.colorbar(img)
        # ax.set_xlabel('Temperature [K]')
        # ax.set_ylabel('Pressure [Bar]')
        # ax.set_zlabel('Phi')

        X, Y = np.meshgrid(self.x, self.y)
        Z = self.matrix.transpose()

        # Z = np.where(self.matrix.transpose() == 1, randint(3, 10), self.matrix.transpose())


        print(Z)

        print(X.shape, Y.shape, Z.shape)

        plt.contour(X, Y, Z, 100, cmap=cm)
        plt.ylabel('Pressure [Bar]')
        plt.xlabel('Temperature [K]')
        plt.savefig('Coverage.png')
        plt.colorbar()

        plt.show()


from ExperimentManager.Models import *

exps = Experiment.objects.all()

domain = Domain(x_range=(750, 2000), x_tick=25,
                y_range=(0, 40), y_tick=10,
                z_range=(0, 20), z_tick=1)


for exp in tqdm(exps):
    t_inf = exp.t_inf
    t_sup = exp.t_sup
    p_inf = exp.p_inf
    p_sup = exp.p_sup
    phi_inf = exp.phi_inf
    phi_sup = exp.phi_sup

    if all([t_inf, t_sup, p_inf, p_sup, phi_inf, phi_sup]):
        # print([t_inf, t_sup, p_inf, p_sup, phi_inf, phi_sup])
        domain.add_value_range(x_range=(t_inf, t_sup), y_range=(p_inf, p_sup), z_range=(phi_inf, phi_sup), value=1)

# print(domain.matrix)
print(np.count_nonzero(domain.matrix<=5))
print(domain.matrix.shape, domain.matrix.size)
domain.plot()
