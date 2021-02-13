# # import logging
# #
# # # logging.basicConfig(filename='app.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s')
# # logging.warning('This will get logged to a file')
#
# import sys, os, django, argparse
# from django.conf import settings
# from ReSpecTh import respecth
# import traceback
# import glob
#
#
# from django.db import transaction
#
# # BEFORE RUNNING THIS SCRIPT, IT IS NECESSARY TO ADD THE ROOT PROJECT FOLDER TO THE PYTHONPATH
#
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SciExpeM.settings")
# django.setup()
#
# from ExperimentManager import models
#
# models.Experiment.objects.all().delete()
#
#
# def import_jsons(files):
#     counter = 0
#
#     print("Imported ReSpecTh Files: {}/{}".format(counter, len(respecth_files)), end="")
#     for index, f in enumerate(files):
#         print("\rImported ReSpecTh Files: {}/{}".format(index, len(respecth_files)), end="")
#         try:
#             with transaction.atomic():
#                 r = respecth.ReSpecTh.from_file(f)
#
#                 initial_composition = r.initial_composition()
#                 reactor = r.apparatus
#                 experiment_type = r.experiment_type
#                 fileDOI = r.fileDOI
#
#                 #check duplicates
#                 if models.Experiment.objects.filter(fileDOI=fileDOI).exists():
#                     print("DUPLICATE: ", fileDOI)
#                     continue
#
#                 it = r.get_ignition_type()
#                 o = None
#                 if it is not None:
#                     o = it.attrib.get("target") + " " + it.attrib.get("type")
#
#                 paper = models.FilePaper(title=r.getBiblio())
#                 paper.save(username="root")
#
#                 xml_file = open(f).read()
#
#                 e = models.Experiment(reactor=reactor,
#                                       experiment_type=experiment_type,
#                                       fileDOI=fileDOI,
#                                       ignition_type=o,
#                                       file_paper=paper,
#                                       xml_file=xml_file)
#                 e.save(username="root")
#
#                 columns_groups = r.extract_columns_multi_dg()
#                 for g in columns_groups:
#                     for c in g:
#                         co = models.DataColumn(experiment=e, **c)
#                         co.save(username="root")
#
#                 common_properties = r.common_properties()
#                 for c in common_properties:
#                     cp = models.CommonProperty(experiment=e, **c)
#                     cp.save(username="root")
#
#                 initial_species = r.initial_composition()
#                 for i in initial_species:
#                     ip = models.InitialSpecie(experiment=e, **i)
#                     ip.save(username="root")
#
#             counter += 1
#
#         except Exception as err:
#             print(f)
#             print(traceback.format_exc())
#     return counter
#
#
# def dir_path(string):
#     if os.path.isdir(string):
#         return string
#     else:
#         raise NotADirectoryError(string)
#
# parser = argparse.ArgumentParser()
# parser.add_argument('--path', type=dir_path)
#
# args = parser.parse_args()
#
# path = args.path
#
# respecth_files = glob.glob(path + '/**/*.xml', recursive=True)
#
# counter = import_jsons(respecth_files)
#
# print("\rImported ReSpecTh Files: {}/{}".format(counter, len(respecth_files)))
#
#
# path = "../Files/ignition_definition_types"
#
# a = open(path, "r").read().split("\n")
# print(a)