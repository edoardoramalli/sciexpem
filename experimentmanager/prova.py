import os
import django
from django.db import transaction

# BEFORE RUNNING THIS SCRIPT, IT IS NECESSARY TO ADD THE ROOT PROJECT FOLDER TO THE PYTHONPATH

# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SciExpeM.settings")
# django.setup()

# from experimentmanager import models
#
# from opensmoke import OpenSmokeExecutor
#
# exp = models.Experiment.objects.filter(pk=44)[0] #g000001_X
# model = models.ChemModel.objects.filter(pk=4)[0] #2003
#
# OpenSmokeExecutor.execute(exp, model)
#
#
# #
# import pandas as pd
# df = pd.DataFrame()
# df["torque"] = [1,23]
#
# {
#     "torque": pd.Series([1, 2, 2, 3], dtype="pint[lbf ft]"),
#     "angular_velocity": pd.Series([1, 2, 2, 3], dtype="pint[rpm]"),
# })
#


from APISciExpeM import APISciExpeM

API = APISciExpeM(username="Edoardo", password="123456")

# path_respecth_file = "/Users/edoardo/Dropbox/SciExpem/OpenSmoke++/Simulazioni/Respecth_H2/g00000001_x.xml"
# API.importExperiment(path_respecth_file, verbose=True)


a = API.getExperiment(fileDOI="10.24388/g00000001_x")[0]
# df = API.getData(a)

example_execution = API.getExecution(experiment__fileDOI="10.24388/g00000001_x")
df = API.getExecutionData(example_execution[0])


API.getOutliner()



# from curve_matching import CurveMatchingExecutor
#
# exp = models.Experiment.objects.filter(pk=44)[0]
# print("Experiment:", exp.fileDOI)
#
# t0 = models.ExecutionColumn.objects.filter(pk=51)[0]
# slope = models.ExecutionColumn.objects.filter(pk=60)[0]
#
# curve_matching = CurveMatchingExecutor("path")
#
# curve_matching.execute_CM(execution_column_x=t0, execution_column_y=slope)

# from opensmoke import OpenSmokeParser
#
# path = "/Users/edoardo/Dropbox/SciExpem/OpenSmoke++/Simulazioni/CRECK_1412/H2_indirect_v2_0_preliminary/x10001018.xml.dic"
#
# out = OpenSmokeParser.parse_input(path)
#
# out = OpenSmokeParser.create_output(out, "/Users/Edo", "/Users/Elena")
# print(out)