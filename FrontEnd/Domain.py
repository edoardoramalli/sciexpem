import numpy as np


class Domain:

    def __init__(self, x_range=(500, 2500), y_range=(0, 50), z_range=(0, 20), x_tick=100, y_tick=1, z_tick=0.5):
        self.x = np.arange(start=x_range[0], stop=x_range[1] + x_tick, step=x_tick)

        self.y = np.arange(start=y_range[0], stop=y_range[1] + y_tick, step=y_tick)
        self.z = np.arange(start=z_range[0], stop=z_range[1] + z_tick, step=z_tick)

        self.matrix = np.zeros(shape=(len(self.x), len(self.y), len(self.z)))
        self.support = np.zeros(shape=(len(self.x), len(self.y), len(self.z)))
        # self.matrix = np.zeros(shape=(len(self.x), len(self.y)))

        pass

    def add_value(self, x, y, z):
        x_index = np.where(self.x == min(self.x, key=lambda e: abs(e - x)))[0][0]
        y_index = np.where(self.y == min(self.y, key=lambda e: abs(e - y)))[0][0]
        z_index = np.where(self.z == min(self.z, key=lambda e: abs(e - z)))[0][0]
        self.matrix[x_index, y_index, z_index] += 1
        self.support[x_index, y_index, z_index] += 1

    def add_value_range(self, x_range, y_range, z_range, value):
        x_index_inf = np.where(self.x == min(self.x, key=lambda e: abs(e - x_range[0])))[0][0]
        y_index_inf = np.where(self.y == min(self.y, key=lambda e: abs(e - y_range[0])))[0][0]
        z_index_inf = np.where(self.z == min(self.z, key=lambda e: abs(e - z_range[0])))[0][0]

        x_index_sup = np.where(self.x == min(self.x, key=lambda e: abs(e - x_range[1])))[0][0]
        y_index_sup = np.where(self.y == min(self.y, key=lambda e: abs(e - y_range[1])))[0][0]
        z_index_sup = np.where(self.z == min(self.z, key=lambda e: abs(e - z_range[1])))[0][0]

        for x in range(x_index_inf, x_index_sup + 1):
            for y in range(y_index_inf, y_index_sup + 1):
                for z in range(z_index_inf, z_index_sup + 1):
                    self.matrix[x, y, z] += value
                    self.support[x, y, z] += 1