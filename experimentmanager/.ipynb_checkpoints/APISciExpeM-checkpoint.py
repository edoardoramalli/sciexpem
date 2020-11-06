import django
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SciExpeM.settings")
django.setup()

from experimentmanager import models
from django.db import transaction

class APISciExpeM:
    def __init__(self, username, password):

        print("--> Authenticated as", username)

    def importExperiment(self, path, verbose=False):
        import glob
        from respecth import ReSpecTh
        if os.path.isfile(path):
            respecth_files = [path]
        else:
          respecth_files = glob.glob(path + '/**/*.xml', recursive=True)
        counter = 0
        if verbose:
            print("Imported ReSpecTh Files: {}/{}".format(counter, len(respecth_files)), end="")
        for index, f in enumerate(respecth_files):
            if verbose:
                print("\rImported ReSpecTh Files: {}/{}".format(index, len(respecth_files)), end="")
            try:
                with transaction.atomic():
                    r = ReSpecTh.from_file(f)

                    initial_composition = r.initial_composition()
                    reactor = r.apparatus
                    experiment_type = r.experiment_type
                    fileDOI = r.fileDOI

                    # check duplicates
                    if models.Experiment.objects.filter(fileDOI=fileDOI).exists():
                        # print("DUPLICATE: ", fileDOI)
                        continue

                    it = r.get_ignition_type()
                    o = None
                    if it is not None:
                        o = it.attrib.get("target") + " " + it.attrib.get("type")

                    paper = models.FilePaper(title=r.getBiblio())
                    paper.save()

                    xml_file = open(f).read()

                    e = models.Experiment(reactor=reactor, experiment_type=experiment_type, fileDOI=fileDOI,
                                          ignition_type=o,
                                          file_paper=paper, temp=False, xml_file=xml_file)
                    e.save()

                    columns_groups = r.extract_columns_multi_dg()
                    for g in columns_groups:
                        for c in g:
                            co = models.DataColumn(experiment=e, **c)
                            co.save()

                    common_properties = r.common_properties()
                    for c in common_properties:
                        cp = models.CommonProperty(experiment=e, **c)
                        cp.save()

                    initial_species = r.initial_composition()
                    for i in initial_species:
                        ip = models.InitialSpecie(experiment=e, **i)
                        ip.save()

                counter += 1

            except Exception as err:
                pass
        print("")
        return

        
    
    