import matplotlib.pyplot as plt
import math
import numpy as np

def ratio(a, b, offset):
    return (a + offset) / (b + offset)

a = 0.005
b = 0

x = np.arange(1, 100, 0.1)
y = [ratio(a, b, i) for i in x]

plt.plot(x, y)
plt.show()

