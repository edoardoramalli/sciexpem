"""
Utilities for debuggin postprocessor
"""
import pandas as pd
import matplotlib.pyplot as plt

def RatesPlot(self, time, matrixOfRates, numberOfReaction):

    plt.plot(time, matrixOfRates[:,numberOfReaction], 'b--')
    plt.show()

def PrintMatrix(self, m, name):

    df = pd.DataFrame(m)
    fileName = name + '.xlsx'
    df.to_excel(excel_writer = fileName)

def Print2Matrix(self, m1, m2, name):

    df = pd.DataFrame([m1,m2])
    fileName = name + '.xlsx'
    df.to_excel(excel_writer = fileName)
